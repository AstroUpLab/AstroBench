# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Original geometric primitives for portable workcell supports."""
import math
import bpy
from mathutils import Vector

def material(name, color, metallic=0.0, roughness=0.4, emission=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=roughness
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1)
        bs.inputs['Emission Strength'].default_value=emission
    m.diffuse_color=(*color,1)
    return m

def box(name, loc, dims, mat, bevel=.004, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Machined edge radii','BEVEL');b.width=bevel;b.segments=3
        b=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    if parent:parent_keep(o,parent)
    return o

def cylinder(name, loc, radius, depth, mat, axis='Z', vertices=48, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object;o.name=name
    if axis=='Y':o.rotation_euler.x=math.pi/2
    if axis=='X':o.rotation_euler.y=math.pi/2
    o.data.materials.append(mat)
    b=o.modifiers.new('Turned edge radii','BEVEL');b.width=min(.0015,radius*.08);b.segments=3
    for p in o.data.polygons:p.use_smooth=True
    b=o.modifiers.new('Surface normals','WEIGHTED_NORMAL')
    if parent:parent_keep(o,parent)
    return o

def label(name,text,loc,size=.02,mat=None,parent=None,align='LEFT'):
    cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.size=size;cu.extrude=.0001
    cu.align_x=align;cu.space_character=1.12
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(math.pi/2,0,0)
    if mat:o.data.materials.append(mat)
    if parent:parent_keep(o,parent)
    return o

def parent_keep(o,parent):
    bpy.context.view_layer.update()
    matrix=o.matrix_world.copy();o.parent=parent;o.matrix_world=matrix

def empty(name,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc
    return o

def tube(name,points,radius,mat,parent=None):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12
    cu.bevel_depth=radius;cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for b,p in zip(sp.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
    if parent:parent_keep(o,parent)
    return o

def bolt(name,loc,mat,axis='Y'):
    o=cylinder(name,loc,.0055,.003,mat,axis,6)
    return o

