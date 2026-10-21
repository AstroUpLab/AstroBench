# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Load an editable workcell and reset its geometry to a task initial state.

blender -b -P assets/workcells/load_asset.py -- --asset melfi_v6 \
  --task card_extract --target Rear_half_box --save /tmp/melfi_extract.blend

This is a scene/reset interface. Contact forces, attachment and task completion
must be measured by the runtime; no motion policy or outcome is generated.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

HERE=Path(__file__).resolve().parent
MELFI_TASKS=('card_transfer_to_mouth','card_insert','card_extract','lid_open','lid_close')
RRM_TASKS=('fdv1_remove_stow','sma_remove_stow','captive_loosen','captive_tighten')


def load(asset_id,asset_root=HERE):
    directory=Path(asset_root).resolve()/asset_id
    parts=json.loads((directory/'parts.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(directory/(asset_id+'.blend')))
    return parts



def rows(matrix):
    return [[float(x) for x in row] for row in matrix]


def restore(parts):
    """Restore intrinsic asset coordinates, including after world placement."""
    placement=bpy.data.objects.get('AstroBench_world_placement')
    if placement:
        for obj in list(placement.children):
            pose=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=pose
        bpy.data.objects.remove(placement,do_unlink=True)
    for name,record in parts['nodes'].items():
        obj=bpy.data.objects.get(name)
        if obj:
            obj.matrix_local=Matrix(record['transform_parent'])
            obj.hide_render=False;obj.hide_viewport=False
            if obj.rigid_body:obj.rigid_body.enabled=True
    bpy.context.view_layer.update()


def select_tool(parts,kind):
    """Other tool variants stay in the library but are inactive in this scene."""
    roots={t['kind']:t['tool_root_object'] for t in parts['semantic_targets'].values()}
    inactive=[]
    for other,name in roots.items():
        root=bpy.data.objects[name]
        for obj in [root,*root.children_recursive]:
            off=other!=kind;obj.hide_render=off;obj.hide_viewport=off
            if obj.rigid_body:obj.rigid_body.enabled=not off
            if off:inactive.append(obj.name)
    return inactive


def place(parts,placement='asset',report=None):
    """Place the whole asset after reset. Repeated calls are idempotent."""
    if placement not in ('asset','world'):raise ValueError('Unknown placement '+placement)
    container=bpy.data.objects.get('AstroBench_world_placement')
    if not container:
        roots=[bpy.data.objects[name] for name,rec in parts['nodes'].items()
               if rec['parent'] is None and name in bpy.data.objects]
        container=bpy.data.objects.new('AstroBench_world_placement',None)
        bpy.context.collection.objects.link(container)
        for obj in roots:
            pose=obj.matrix_world.copy();obj.parent=container
            obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=pose
    matrix=Matrix(parts['robot_attachment_frames']['world_from_asset']) if placement=='world' else Matrix.Identity(4)
    container.matrix_world=matrix;bpy.context.view_layer.update()
    report={} if report is None else report
    report.update(placement=placement,scene_from_asset=rows(matrix))
    report['robot_base_transform_scene']=rows(matrix @ Matrix(parts['robot_attachment_frames']['base']['transform_asset']))
    if 'object_transforms_asset' in report:
        report['object_transforms_scene']={name:rows(bpy.data.objects[name].matrix_world)
                                          for name in report['object_transforms_asset']}
    return report


def ready(parts):
    """Apply the centered waiting pose. The runtime supplies the robot model."""
    if parts['asset_id']!='rrm_tb1':raise ValueError('Ready preset is defined for RRM')
    restore(parts)
    preset=parts['ready_pose'];kind=preset['tool_kind']
    target=next(t for t in parts['semantic_targets'].values() if t['kind']==kind)
    tool=bpy.data.objects[target['tool_root_object']]
    tool.matrix_world=Matrix(preset['tool_transform_asset'])
    inactive=select_tool(parts,kind);bpy.context.view_layer.update()
    return {'asset_id':parts['asset_id'],'pose_kind':'centered_waiting_pose','task_outcome':False,'units':'m',
            'robot_ready_pose':preset,'inactive_tool_objects':inactive,
            'object_transforms_asset':{tool.name:rows(tool.matrix_world)},
            'observations':'Set the runtime robot base, arm and gripper from robot_ready_pose; this static preset is not a task rollout.'}


def set_retention_pose(target,state):
    """Reset visible band geometry; a runtime separately resolves elastic forces."""
    config=target['retention'];points=config['centerlines_parent'][state]
    band=bpy.data.objects[config['band_object']];half=config['width_m']/2
    vertices=[(x,y+side*half,z) for x,y,z in points for side in (-1,1)]
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)]
    band.data.clear_geometry();band.data.from_pydata(vertices,[],faces);band.data.update()
    delta=Vector(points[-1])-Vector(config['centerlines_parent']['released'][-1])
    for name in config['end_objects']:bpy.data.objects[name].location+=delta
    return [band.name,*config['end_objects']]

def reset(parts,task_id,target_id):
    """Apply only geometry. Return exact reset object transforms for the adapter."""
    if target_id not in parts['semantic_targets']:raise ValueError('Unknown target '+target_id)
    target=parts['semantic_targets'][target_id]
    if not target['active']:
        selection=target['rebuild']
        raise ValueError('Rebuild selected target with publicbuild.py: --sma-row {sma_row} --sma-col {sma_col} --captive-index {captive_index}'.format(**selection))
    restore(parts)
    changed=[]
    if parts['asset_id']=='melfi_v6':
        if task_id not in MELFI_TASKS:raise ValueError('Task is not a MELFI task')
        for other in parts['semantic_targets'].values():
            band_state='retained_around_card' if other['target_id']==target_id and task_id=='card_extract' else 'released'
            changed.extend(set_retention_pose(other,band_state))
            lid=bpy.data.objects[other['lid_object']]
            opened=other['target_id']==target_id and task_id!='lid_open'
            lid.rotation_euler.y=math.radians(85) if opened else 0.
            paddle=bpy.data.objects[other['latch_object']]
            paddle.rotation_euler.y=other['latch_open_rotation_y_rad'] if opened else other['latch_closed_rotation_y_rad']
            changed.extend((lid.name,paddle.name))
        card=bpy.data.objects[target['card_object']]
        frames=target['goal_frame_asset']
        if task_id=='card_extract':card.matrix_world=Matrix(frames['inserted'])
        elif task_id=='card_insert':card.matrix_world=Matrix(frames['opening'])
        elif task_id=='card_transfer_to_mouth':
            card.matrix_world=Matrix(frames['opening']) @ Matrix.Translation((.12,0,0))
        changed.append(card.name)
    else:
        if task_id not in RRM_TASKS:raise ValueError('Task is not an RRM task')
        kind=target['kind']
        expected='fdv1' if task_id=='fdv1_remove_stow' else 'sma' if task_id=='sma_remove_stow' else 'captive'
        if kind!=expected:raise ValueError('Task and target kinds differ')
        moving=bpy.data.objects[target['moving_object']]
        moving.location=target['seat_position_parent']
        moving.rotation_euler.z=0.
        if task_id=='captive_tighten':
            moving.location.z+=.0021
            moving.rotation_euler.z=6*math.pi
        tool=bpy.data.objects[target['tool_root_object']]
        tool.matrix_world=Matrix(target['goal_frame_asset']['tool_contact']) @ Matrix.Translation((0,0,.10))
        # Put the tool dock latches in their open reset pose. Their radial axes
        # and base positions are explicit scene geometry, not a contact result.
        if kind in ('fdv1','sma'):
            for i,direction in enumerate((1,-1)):
                name=f'RRM_TB1_STOW_{kind}_radial_lock_{i}'
                obj=bpy.data.objects.get(name)
                if obj:
                    obj.location.x+=direction*.004
                    changed.append(name)
        changed.extend((moving.name,tool.name))
        inactive=select_tool(parts,kind)
    bpy.context.view_layer.update()
    return {'asset_id':parts['asset_id'],'task_id':task_id,'target_id':target_id,'units':'m',
            'object_transforms_asset':{name:[[float(x) for x in row] for row in bpy.data.objects[name].matrix_world] for name in changed},
            'inactive_tool_objects':inactive if parts['asset_id']=='rrm_tb1' else [],
            'observations':'Runtime must measure contacts, retention, containment and joint velocities after reset.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asset',required=True,choices=('melfi_v6','rrm_tb1'))
    p.add_argument('--asset-root',type=Path,default=HERE)
    p.add_argument('--task',choices=MELFI_TASKS+RRM_TASKS)
    p.add_argument('--ready',action='store_true',help='RRM centered waiting pose and runtime joint preset')
    p.add_argument('--placement',choices=('asset','world'),default='asset')
    p.add_argument('--target')
    p.add_argument('--save',type=Path)
    p.add_argument('--receipt',type=Path)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.ready and (args.task or args.target):p.error('--ready cannot be combined with --task/--target')
    if not args.ready and (not args.task or not args.target):p.error('provide --task and --target, or --ready')
    parts=load(args.asset,args.asset_root)
    report=ready(parts) if args.ready else reset(parts,args.task,args.target)
    report=place(parts,args.placement,report)
    if args.save:
        args.save.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save.resolve()),compress=True)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


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
