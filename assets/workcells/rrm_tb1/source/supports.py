# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Original wall mount and floor plate; no cabin or robot mesh dependency."""
import json
import math
from pathlib import Path
import numpy as np

CONFIG=json.loads(Path(__file__).with_name('layout_config.json').read_text())
WALL_Y=CONFIG['wall']['plane_y_m']
FLOOR_Z=CONFIG['floor']['plane_z_m']
FLOOR_PLATE_THICKNESS=CONFIG['floor_plate']['dimensions_m'][2]
BASE=tuple(row[3] for row in CONFIG['robot_base_world'][:3])
BASE_YAW=math.pi/2

def panel_matrix():
    return np.asarray(CONFIG['world_from_asset'],dtype=float)

def local_to_world(point,matrix):
    return (np.asarray(matrix) @ np.r_[point,1.])[:3]

def make_supports(base=BASE, matrix=None, yaw=BASE_YAW):
    """Return actual mounts plus two hidden wall/floor collision proxies.

    Wall contact is explicit: backplate rear face equals WALL_Y. Four panel
    standoffs end at the original board rear surface (local Z=-6 mm).
    Stowage feet retain their measured panel-local position and get separate
    short mounting blocks connecting them to the same wall backplate.
    """
    import bpy
    from mathutils import Matrix, Vector
    pm = panel_matrix() if matrix is None else np.asarray(matrix)
    objects, mats = [], {}
    for key, color, metallic, roughness in (
        ('Silver', (.34, .39, .42, 1), .75, .39),
        ('White', (.64, .68, .69, 1), .20, .52),
        ('Dark', (.025, .032, .041, 1), .60, .40),
        ('Cable', (.020, .024, .028, 1), .0, .68),
    ):
        m = bpy.data.materials.new('RRM cabin '+key);m.use_nodes = True
        sh = m.node_tree.nodes['Principled BSDF']
        sh.inputs['Base Color'].default_value = color
        sh.inputs['Metallic'].default_value = metallic
        sh.inputs['Roughness'].default_value = roughness
        # Fine manufacturing variation rather than perfectly uniform surfaces.
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 260.
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .12
        bump.inputs['Distance'].default_value = .00012
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], sh.inputs['Normal'])
        mats[key] = m

    def box(name, pos, size, material='Silver', local=False, bevel=.001):
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
        ob = bpy.context.object;ob.name='RRM cabin '+name;ob.dimensions=size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if local: ob.matrix_world=Matrix(pm.tolist())@ob.matrix_world
        ob.data.materials.append(mats[material])
        if bevel:
            b=ob.modifiers.new('Machined edges','BEVEL');b.width=bevel;b.segments=3
        objects.append(ob)
        return ob

    def cylinder(name, pos, radius, depth, material='Silver', axis='Z'):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=pos)
        ob=bpy.context.object;ob.name='RRM cabin '+name
        if axis=='Y':ob.rotation_euler.x=math.pi/2
        ob.data.materials.append(mats[material]);objects.append(ob)
        b=ob.modifiers.new('Edge radius','BEVEL');b.width=.0006;b.segments=2
        return ob

    def cable(name, points, radius=.008):
        cv=bpy.data.curves.new(name,'CURVE');cv.dimensions='3D';cv.resolution_u=1
        sp=cv.splines.new('POLY');sp.points.add(len(points)-1)
        for p,xyz in zip(sp.points,points):p.co=(*xyz,1.)
        cv.bevel_depth=radius;cv.bevel_resolution=3
        ob=bpy.data.objects.new('RRM cabin '+name,cv);bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mats['Cable']);objects.append(ob);return ob

    wall_front=WALL_Y-.016
    box('wall load-spreading backplate', (.035,WALL_Y-.008,pm[2,3]-.065),
        (.66,.016,.87),'White',bevel=.003)
    panel_rear_y=float(local_to_world((0,0,-.006),pm)[1])
    post_len=wall_front-panel_rear_y
    if post_len<=0:raise ValueError('Panel rear intersects wall backplate')
    for x in (-.175,.175):
        for zlocal in (-.235,.235):
            p=local_to_world((x,zlocal,-.006),pm)
            box('panel standoff', (p[0],(panel_rear_y+wall_front)/2,p[2]),
                (.028,post_len,.028),bevel=.001)
            cylinder('panel mount washer',(p[0],panel_rear_y-.001,p[2]),.009,.002,'Dark','Y')
    # Existing stowage foot rear face is at panel-local Z=-80 mm.
    foot_back_y=float(local_to_world((0,0,-.080),pm)[1])
    for x in (.06,.23):
        p=local_to_world((x,-.36,-.080),pm)
        depth=wall_front-foot_back_y
        if depth<=0:raise ValueError('Stowage foot intersects backplate')
        box('stowage wall spacer',(p[0],(foot_back_y+wall_front)/2,p[2]),
            (.100,depth,.094),'Silver')
    for x in (-.255,.325):
        for z in (pm[2,3]-.45,pm[2,3]+.32):
            cylinder('wall anchor washer',(x,wall_front-.001,z),.011,.002,'Silver','Y')
            cylinder('wall anchor bolt',(x,wall_front-.004,z),.006,.006,'Dark','Y')

    bx,by,bz=base
    # The configured mounting plate centre is 40 mm behind the robot flange origin.
    cx,cy=bx-.04*math.cos(yaw),by-.04*math.sin(yaw)
    if abs(bz-(FLOOR_Z+FLOOR_PLATE_THICKNESS))>1e-6:
        raise ValueError('Robot base must meet the top of the thin floor plate')
    box('floor foundation plate',(cx,cy,FLOOR_Z+FLOOR_PLATE_THICKNESS/2),
        (.28,.28,FLOOR_PLATE_THICKNESS),'Silver',bevel=.003)
    for dx in (-.117,.117):
        for dy in (-.117,.117):
            cylinder('recessed floor anchor',(cx+dx,cy+dy,bz-.002),.006,.004,'Dark')
    # Supply exits a recessed passage in the thin adapter, lies on the floor,
    # then rises against the wall. There is no remaining pedestal or flange.
    cable_x=cx-.18
    cable('floor supply loom',[(cx-.137,cy,FLOOR_Z+.014),
        (cable_x,cy,FLOOR_Z+.0085),(cable_x,WALL_Y-.034,FLOOR_Z+.0085),
        (cable_x,WALL_Y-.034,pm[2,3]-.20),(-.295,WALL_Y-.034,pm[2,3]-.20)])
    for z in np.linspace(FLOOR_Z+.12,pm[2,3]-.20,3):
        box('wall cable clip',(cable_x,WALL_Y-.031,z),(.028,.025,.014),'Silver')

    wall=box('collision wall',(-.05,WALL_Y+.025,1.15),(2.6,.05,2.20),'White',bevel=0)
    floor=box('collision floor',(-.05,-.9,FLOOR_Z-.025),(2.6,2.0,.05),'White',bevel=0)
    for ob in (wall,floor):
        ob.hide_render=True;ob.display_type='WIRE';ob['collision_only']=True
    bpy.context.view_layer.update()
    return objects
