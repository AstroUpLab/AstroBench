# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Rebuild original task hardware with Blender, without robot or cabin assets.

blender -b -P assets/workcells/publicbuild.py -- --asset all
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import zipfile

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
BUILD_PROVENANCE = {}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rows(m):
    return [[float(x) for x in row] for row in m]


def frame(pos=(0, 0, 0), yaw=0):
    m = Matrix.Rotation(yaw, 4, 'Z')
    m.translation = Vector(pos)
    return rows(m)


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def file_record(path, root, role):
    return dict(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size, role=role)


def empty(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj


def parent_keep(obj, parent):
    pose = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = pose


def prepare():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.
    bpy.context.scene.gravity = (0, 0, 0)


def supports_in_asset(mod, transform, name, functions):
    before = set(bpy.data.objects)
    for function in functions:
        getattr(mod, function)()
    bpy.context.view_layer.update()
    support = empty(name)
    objects = set(bpy.data.objects) - before - {support}
    roots = [o for o in objects if o.parent not in objects]
    for o in roots:
        o.matrix_world = transform @ o.matrix_world
        parent_keep(o, support)
    return support, objects


def clean_scene():
    # Geometry metadata is carried in parts.json. The .blend contains no private
    # source references, executable text blocks, animation or drivers.
    for ob in bpy.data.objects:
        ob.animation_data_clear()
        for key in list(ob.keys()):
            del ob[key]
    for datablocks in (bpy.data.materials, bpy.data.node_groups, bpy.data.meshes, bpy.data.curves):
        for block in datablocks:
            if hasattr(block, 'animation_data_clear'):
                block.animation_data_clear()
            for key in list(block.keys()):
                del block[key]
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
    if bpy.data.libraries:
        raise RuntimeError('Linked libraries are forbidden in the public asset')
    for image in bpy.data.images:
        if image.source == 'FILE' and not image.packed_file:
            raise RuntimeError('Unpacked image dependency: ' + image.name)
    for font in bpy.data.fonts:
        if font.filepath and font.filepath != '<builtin>':
            raise RuntimeError('External font dependency: ' + font.name)


def node_records():
    bpy.context.view_layer.update()
    records = {}
    for obj in bpy.data.objects:
        records[obj.name] = dict(type=obj.type, parent=obj.parent.name if obj.parent else None,
                                 transform_asset=rows(obj.matrix_world), transform_parent=rows(obj.matrix_local))
    return records


def output_models(out, asset_id, targets, joints, initial, robot, extra):
    clean_scene()
    for target_id, target in targets.items():
        for key in ('root_object', 'moving_object', 'lid_object', 'card_object'):
            name = target.get(key)
            if name and name in bpy.data.objects:
                bpy.data.objects[name]['semantic_id'] = target_id
    parts = dict(schema='astrobench.workcell.parts.v1', asset_id=asset_id, units='m', coordinate_frame='asset',
                 up_axis='Z', matrix_convention='row-listed 4x4, column vectors',
                 nodes=node_records(), semantic_targets=targets, joints=joints, initial_state=initial,
                 robot_attachment_frames=robot, **extra)
    write(out/'parts.json', parts)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(asset_id+'.blend')), compress=True)
    # Export a neutral geometry format. The editable .blend retains procedural
    # finishes; GLB uses the corresponding base-color/metallic/roughness values.
    for obj in list(bpy.data.objects):
        if obj.type in ('CURVE', 'FONT', 'SURFACE'):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='MESH')
    bpy.ops.export_scene.gltf(filepath=str(out/(asset_id+'.glb')), export_format='GLB',
                             export_animations=False, export_extras=True, export_yup=True,
                             export_apply=True, export_cameras=False, export_lights=False)
    files = [file_record(p, out, 'editable_model' if p.suffix=='.blend' else 'neutral_model' if p.suffix=='.glb'
                         else 'semantics' if p.name=='parts.json' else 'collision' if p.name.startswith('collision') else 'source')
             for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json' and p.suffix not in ('.blend1','.pyc')]
    manifest = dict(schema='astrobench.workcell.asset.v1', asset_id=asset_id, units='m', up_axis='Z',
                    license='Apache-2.0', **BUILD_PROVENANCE, files=files, files_sha256={f['path']:f['sha256'] for f in files},
                    semantic_targets=targets, initial_state=initial, robot_attachment_frames=robot,
                    gltf_from_asset=rows(Matrix.Rotation(-math.pi/2, 4, 'X')),
                    collision={'index':'collision.json','archive':'collision_meshes.zip','extract_directory':'collision_meshes'},
                    source_builder='../publicbuild.py', **extra)
    write(out/'manifest.json', manifest)
    print(json.dumps({'asset': asset_id, 'objects':len(parts['nodes']), 'files':len(files)}), flush=True)


def archive_collision(out, collision):
    meshdir = out/'collision_meshes'
    archive = out/'collision_meshes.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(meshdir.rglob('*.obj')):
            z.write(path, path.relative_to(out).as_posix())
    collision['mesh_archive'] = {'path':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                                 'extract_directory':meshdir.name}
    write(out/'collision.json', collision)
    shutil.rmtree(meshdir)


def melfi_collision(out, data, card, joints, targets):
    ex = module(HERE/'rrm_tb1/source/export_collision.py', 'melfi_mesh_export')
    ex.EXPORT_ROOT = out.resolve()
    graph = bpy.context.evaluated_depsgraph_get()
    bodies = {'card': {'root_object':card['root'].name,'motion_type':'dynamic_compound',
                       'initial_transform':rows(card['root'].matrix_world), 'primitives':[
                           {'type':'box','center':[0,0,0],'half_extents':[.050,.001,.055]},
                           *[{'type':'cylinder','center':[x,-.008,-.012],'axis':[0,0,1],'radius':.0066,'height':.056}
                             for x in (-.030,-.010,.010,.030)]]}}
    moving = set([card['root'], *card['root'].children_recursive])
    for i, box in enumerate(data['boxes']):
        lid = box['lid_root']
        members = set([lid, *lid.children_recursive]); moving |= members
        body = {'root_object':lid.name, 'motion_type':'kinematic_articulation',
                'initial_transform':rows(lid.matrix_world), 'triangle_meshes':[]}
        for n,obj in enumerate(sorted(members,key=lambda o:o.name)):
            if obj.type not in ('MESH','CURVE','FONT'): continue
            rec=ex.geometry(obj,lid.matrix_world,graph)
            if rec:
                rec['obj_path']=ex.obj_file(out/'collision_meshes'/f'lid_{i}'/f'{n:04d}.obj',rec)
                rec.pop('vertices');rec.pop('triangles');body['triangle_meshes'].append(rec)
        bodies[f'lid/{i}']=body
    for target_id,target in targets.items():
        retention=target['retention'];members={bpy.data.objects[n] for n in [retention['band_object'],*retention['end_objects']]}
        moving |= members
        bodies['retention/'+target_id]={'root_object':target['root_object'],'motion_type':'runtime_elastic_strip',
            'visual_objects':[o.name for o in members],'centerlines_parent':retention['centerlines_parent'],
            'endpoint_constraints':retention['endpoint_constraints'],'parameters':retention['runtime_elastic_model'],
            'collision_rule':'Build strip contact from centerline, width and thickness; do not load these movable parts as static surfaces.',
            'width_m':retention['width_m'],'thickness_m':retention['thickness_m']}
    static=[]
    for n,obj in enumerate(sorted(bpy.data.objects,key=lambda o:o.name)):
        if obj in moving or obj.type not in ('MESH','CURVE','FONT'):continue
        rec=ex.geometry(obj,Matrix.Identity(4),graph)
        if rec:
            rec['coordinate_frame']='asset'
            rec['obj_path']=ex.obj_file(out/'collision_meshes'/'static'/f'{n:04d}.obj',rec)
            rec.pop('vertices');rec.pop('triangles');static.append(rec)
    collision={'schema':'astrobench.workcell.collision.v1','units':'m','bodies':bodies,'static_meshes':static,'joints':joints,
               'dynamic_rule':'Card uses authored compound primitives. Lid surfaces use kinematic triangle collision with the named hinge; use material-preserving convex decomposition if the backend requires dynamic rigid lids.',
               'static_rule':'Concave triangle surfaces retain the box openings and perforations.',
               'summary':{'body_count':len(bodies),'static_mesh_count':len(static)}}
    archive_collision(out,collision)


def build_melfi(out):
    prepare()
    mod=module(HERE/'melfi_v6/source/melfi.py','public_melfi')
    data=mod.build(box_angles=(85,85,85))
    for box in data['boxes'][:2]:mod.set_lid_pose(box,0)
    card=mod.create_vial_card(origin=(-.375,.35,.25));card['root'].rotation_euler.z=-math.pi/2
    world_from_asset=Matrix.Translation(Vector((.25,-.215,1.02))) @ Matrix.Rotation(math.pi/2,4,'Z')
    supports=module(HERE/'melfi_v6/source/supports.py','melfi_supports')
    supports_in_asset(supports, world_from_asset.inverted(),'MELFI_Workcell_support',('mounting_frame','floor_pedestal'))
    bpy.context.view_layer.update()
    targets={};joints=[]
    for id_,box in zip(('Front_quarter_box','Middle_quarter_box','Rear_half_box'),data['boxes']):
        c=list(box['center_local']);z=c[2]
        frames={'target':frame(c), 'opening':frame((c[0],c[1],z+.200),-math.pi/2),
                'inserted':frame((c[0],c[1],z+.0565),-math.pi/2),
                'approach':frame((c[0],c[1],z+.225),-math.pi/2)}
        frames['inserted_card']=frames['inserted']
        paddle=box['lid_latch_paddle'];lid=box['lid_root']
        band=box['manual_retention_band']
        released=[list((band.data.vertices[i].co+band.data.vertices[i+1].co)/2) for i in range(0,len(band.data.vertices),2)]
        retained=[[.101,0,.096],[.070,0,.103],[.020,0,.1125],[.0035,0,.1125],[-.0035,0,.1125],[-.025,0,.1135],[mod.LID_LEFT+.002,0,.116]]
        end_names=[o.name for o in box['root'].children if any(key in o.name for key in ('_band_free_end_fold','_band_end_connector','_band_end_seam'))]
        length=sum((Vector(b)-Vector(a)).length for a,b in zip(retained,retained[1:]))
        retention={'band_object':band.name,'end_objects':end_names,'coordinate_frame_object':box['root'].name,
                   'width_m':.014,'thickness_m':.00065,'default_state':'released',
                   'centerlines_parent':{'released':released,'retained_around_card':retained},
                   'endpoint_constraints':{'fixed_start_parent':released[0],'retained_end_parent':retained[-1],
                     'free_end_latch':'constrain only when the connector is physically engaged; release for insertion/extraction motion'},
                   'runtime_elastic_model':{'model':'elastic strip or a rod/contact discretization preserving strip width',
                     'rest_length_m':length*.99,'axial_stiffness_n_per_m':100.,'axial_damping_ns_per_m':.5,
                     'mass_kg':.002,'friction_coefficient':.6,'parameter_provenance':'AstroBench engineering parameters',
                     'force_measurement':'Compute from resolved elastic/contact forces after settling; never assign a constant retention_force_n.'}}
        targets[id_]={'target_id':id_,'root_object':box['root'].name,'lid_object':lid.name,
                      'latch_object':paddle.name,'card_object':card['root'].name,'active':True,'retention':retention,
                      'goal_frame_asset':frames,'frame_provenance':'AstroBench task frames in metres; pose frame uses card local orientation.',
                      'latch_closed_rotation_y_rad':float(paddle.get('closed_rotation_y_rad',0)),
                      'latch_open_rotation_y_rad':float(paddle.get('open_rotation_y_rad',0))}
        joints.append({'id':id_+'/lid','type':'revolute','object':lid.name,'parent':lid.parent.name,
                       'axis_parent':[0,1,0],'origin_parent':list(lid.location),'limits_rad':[0,math.radians(85)],
                       'initial_rad':lid.rotation_euler.y,'actuation':'runtime joint; visual latch coupling is a reset pose'})
    initial={'lid_angles_rad':[0.,0.,math.radians(85)],'card_transform_asset':rows(card['root'].matrix_world)}
    robot={'base':{'transform_asset':rows(world_from_asset.inverted() @ Matrix.Translation(Vector((-.25,-.60,.85)))),
                   'role':'fixed robot mounting flange'}, 'world_from_asset':rows(world_from_asset),
           'robot_asset':'provided by runtime; no robot CAD is bundled'}
    melfi_collision(out,data,card,joints,targets)
    output_models(out,'melfi_v6',targets,joints,initial,robot,
                  {'dimensions':data['dimensions'],'source_references':['https://ntrs.nasa.gov/api/citations/20190001390/downloads/20190001390.pdf',
                     'https://www.esa.int/esapub/bulletin/bullet109/chapter5_bul109.pdf']})


def build_rrm(out,args):
    src=HERE/'rrm_tb1/source'
    sys.path.insert(0,str(src))
    ex=module(src/'export_collision.py','public_rrm_collision')
    ex.export(out/'collision.json',72,args.sma_row,args.sma_col,args.captive_index)
    collision=json.loads((out/'collision.json').read_text())
    # Rebuild the visual state after decomposition; both use identical sources.
    prepare()
    tp=module(src/'task_panel.py','public_rrm_panel');tools=module(src/'tools.py','public_rrm_tools')
    data=tp.build(sma_index=(args.sma_row,args.sma_col),captive_index=args.captive_index)
    tooldata={kind:tools.build(kind) for kind in ('fdv1','sma','captive')}
    parked={'fdv1':(.06,-.36,.12),'sma':(.23,-.36,.12),'captive':(-.30,-.36,.04)}
    for kind,tool in tooldata.items():tool['root'].location=parked[kind]
    sup=module(src/'supports.py','rrm_supports')
    layout=json.loads((src/'layout_config.json').read_text())
    world_from_asset=Matrix(layout['world_from_asset'])
    tooldata['fdv1']['root'].matrix_world=Matrix(layout['ready_pose']['tool_transform_asset'])
    _,support_objs=supports_in_asset(sup,world_from_asset.inverted(),'RRM_Workcell_support',('make_supports',))
    bpy.context.view_layer.update()
    # Collision body meshes are body-local; update poses to match the GLB.
    for body in collision['bodies'].values():
        obj=bpy.data.objects[body['root_object']]
        body['initial_transform']=rows(obj.matrix_world)
        parent_id=body.get('parent_body')
        parent_obj=bpy.data.objects[collision['bodies'][parent_id]['root_object']] if parent_id else None
        body['transform_in_parent']=rows(parent_obj.matrix_world.inverted() @ obj.matrix_world) if parent_obj else rows(obj.matrix_world)
        body['original_visual_meshes']=[m['name'] for m in body.pop('meshes')]
        for part in body['convex_parts']:
            part['vertex_count']=len(part.pop('vertices'));part['triangle_count']=len(part.pop('triangles'))
    for mesh in collision['static_meshes']:
        mesh['vertex_count']=len(mesh.pop('vertices'));mesh['triangle_count']=len(mesh.pop('triangles'));mesh['coordinate_frame']='asset'
    graph=bpy.context.evaluated_depsgraph_get()
    for n,obj in enumerate(sorted(support_objs,key=lambda o:o.name)):
        if obj.type not in ('MESH','CURVE','FONT'):continue
        rec=ex.geometry(obj,Matrix.Identity(4),graph)
        if rec:
            rec['obj_path']=ex.obj_file(out/'collision_meshes'/'supports'/f'{n:04d}.obj',rec)
            rec['coordinate_frame']='asset';rec['collision_only']=bool(obj.get('collision_only',False))
            rec.pop('vertices');rec.pop('triangles');collision['static_meshes'].append(rec)
    collision['environment_planes']=layout['runtime_assets']['collision_proxies']
    for obj in list(support_objs):
        if obj.get('collision_only',False):bpy.data.objects.remove(obj,do_unlink=True)
    collision['summary']['static_mesh_count']=len(collision['static_meshes'])
    collision['dynamic_rule']='Use body-local convex_parts; initial_transform places each body in the asset frame. Original visual surfaces are in the GLB.'
    targets={};joints=[]
    for id_,kind in [('FDV1','fdv1')]+[(f'SMA_{r}_{c}','sma') for r in range(1,4) for c in range(1,4)]+[(f'captive_{i}','captive') for i in (1,2)]:
        active=kind=='fdv1' or (kind=='sma' and id_==f'SMA_{args.sma_row}_{args.sma_col}') or (kind=='captive' and id_==f'captive_{args.captive_index}')
        r,c=(map(int,id_.split('_')[1:]) if kind=='sma' else (args.sma_row,args.sma_col))
        index=int(id_.split('_')[1]) if kind=='captive' else args.captive_index
        spec=tp.specifications((r,c),index)['tasks'][kind]
        task=data['tasks'][kind]
        moving=task['moving_root'].name if active else f'RRM_TB1_SMA_cap_{r}_{c}' if kind=='sma' else f'RRM_TB1_Captive_fastener_{index}'
        targets[id_]={'target_id':id_,'kind':kind,'root_object':moving,'moving_object':moving,'active':active,
                      'goal_frame_asset':{'target':spec['seat_matrix_panel'],'tool_contact':spec['tool_contact_matrix_panel']},
                      'parameters':spec['benchmark_parameters'],'tool_root_object':tooldata[kind]['root'].name,
                      'tool_tcp_local':[0,0,.120], 'adapter_object':tooldata[kind]['spindle_root'].name,
                      'driver_object':tooldata[kind]['root'].name,
                      'nominal_retained_cap_in_adapter':rows(Matrix(spec['tool_contact_matrix_panel']).inverted() @ Matrix(spec['seat_matrix_panel'])),
                      'rebuild':{'sma_row':r,'sma_col':c,'captive_index':index}}
        if active:
            targets[id_]['seat_position_parent']=list(task['seat_position_parent'])
            joints.append({'id':id_+'/thread','object':moving,'type':'helical_then_free' if kind!='captive' else 'helical_captive',
                           'axis_local':[0,0,1],'pitch_m':spec['benchmark_parameters']['thread_pitch_m'],
                           'limits_axial_m':[0,spec['benchmark_parameters'].get('max_travel_m',spec['benchmark_parameters'].get('thread_release_travel_m'))],
                           'runtime_body':'target/'+kind,'initial_angle_rad':0.,'initial_axial_m':0.})
    for kind,tool in tooldata.items():
        joints.append({'id':'tool/'+kind+'/spindle','type':'revolute_detachable','object':tool['spindle_root'].name,
                       'parent':tool['root'].name,'axis_local':[0,0,1],'limits_rad':None,'attachment':'runtime detachable drive coupling at local Z=.064 m'})
    robot={'base':{'transform_asset':rows(world_from_asset.inverted() @ Matrix(layout['robot_base_world'])),
                   'transform_world':layout['robot_base_world'],'role':'fixed flange on the 28 mm floor mounting plate'},
           'world_from_asset':layout['world_from_asset'],'robot_asset':'provided by runtime; no robot CAD is bundled'}
    initial={'selected_sma_index':[args.sma_row,args.sma_col],'selected_captive_index':args.captive_index,
             'fastener_angle_rad':0.,'fastener_axial_m':0.,'tool_parking_positions_asset':parked,
             'default_display_tool':'fdv1','ready_tool_transform_asset':layout['ready_pose']['tool_transform_asset']}
    archive_collision(out,collision)
    output_models(out,'rrm_tb1',targets,joints,initial,robot,
                  {'layout':layout,'ready_pose':layout['ready_pose'],'dimensions':{'plate_m':[.400,.530,.006]},'source_references':['https://www.nasa.gov/nexis/rrm-phase-1/',
                     'https://ntrs.nasa.gov/api/citations/20110013452/downloads/20110013452.pdf']})


def main():
    global BUILD_PROVENANCE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset',choices=('melfi_v6','rrm_tb1','all'),default='all')
    parser.add_argument('--output-root',type=Path,default=HERE)
    parser.add_argument('--sma-row',type=int,choices=(1,2,3),default=2)
    parser.add_argument('--sma-col',type=int,choices=(1,2,3),default=2)
    parser.add_argument('--captive-index',type=int,choices=(1,2),default=1)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    args.output_root=args.output_root.resolve()
    if args.output_root != HERE:
        args.output_root.mkdir(parents=True,exist_ok=True)
        for file in HERE.iterdir():
            if file.is_file() and file.name != 'hashmanifest.json':shutil.copy2(file,args.output_root/file.name)
        for id_ in ('melfi_v6','rrm_tb1'):
            shutil.copytree(HERE/id_,args.output_root/id_,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.blend1'))
    for asset in (('melfi_v6','rrm_tb1') if args.asset=='all' else (args.asset,)):
        out=args.output_root.resolve()/asset;out.mkdir(parents=True,exist_ok=True)
        source_files=[dict(path=p.relative_to(HERE).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(HERE.rglob('*')) if p.is_file() and (p.suffix=='.py' or p.name in ('reference_profile.json','layout_config.json'))]
        BUILD_PROVENANCE={'source_files':source_files,'builder_sha256':{f['path']:f['sha256'] for f in source_files if '/' not in f['path']},'canonical_source_sha256':hashlib.sha256(json.dumps(source_files,sort_keys=True,separators=(',',':')).encode()).hexdigest(), 'build_args':{'sma_row':args.sma_row,'sma_col':args.sma_col,'captive_index':args.captive_index} if asset=='rrm_tb1' else {}}
        if args.output_root != HERE and (HERE/asset/'manifest.json').exists():
            BUILD_PROVENANCE['derived_from_manifest_sha256']=hashlib.sha256((HERE/asset/'manifest.json').read_bytes()).hexdigest()
        if asset=='melfi_v6':build_melfi(out)
        else:build_rrm(out,args)


if __name__=='__main__':
    # Exit explicitly after synchronous exports; some headless hosts otherwise
    # stall while the audio backend shuts down. Library imports do not exit.
    import os
    import traceback
    code=0
    try:main()
    except Exception:
        traceback.print_exc()
        code=1
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
