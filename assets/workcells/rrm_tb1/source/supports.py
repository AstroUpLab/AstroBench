# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Original RRM work table, corner standoffs and robot mount geometry."""
import math
import numpy as np
BASE=(-.43,-.35,.778)
BASE_YAW=0.
TABLE_TOP_Z=.750
def panel_matrix():
    m=np.eye(4);m[2,3]=.830;return m

def make_supports(base=BASE, matrix=None, yaw=BASE_YAW):
    """A 1.20 × 0.95 m table; four 74 mm spacers leave the board rear clear."""
    import bpy
    from mathutils import Matrix

    matrix = panel_matrix() if matrix is None else np.asarray(matrix)
    objects, materials = [], {}
    for name, color, metallic, roughness in (
        ("Brushed aluminium", (.26, .29, .32, 1), .7, .40),
        ("Dark frame", (.075, .09, .105, 1), .55, .38),
        ("Mount bolts", (.035, .04, .045, 1), .75, .30),
        ("Foot pads", (.025, .029, .033, 1), .05, .65),
    ):
        material = bpy.data.materials.new("RRM tabletop " + name)
        material.use_nodes = True
        shader = material.node_tree.nodes["Principled BSDF"]
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = roughness
        materials[name] = material

    def box(name, pos, size, material="Brushed aluminium", local=False,
            radius=.002):
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
        obj = bpy.context.object
        obj.name = "RRM tabletop " + name
        obj.dimensions = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if local:
            obj.matrix_world = Matrix(matrix.tolist()) @ obj.matrix_world
        obj.data.materials.append(materials[material])
        if radius:
            mod = obj.modifiers.new("Manufactured edge radius", "BEVEL")
            mod.width, mod.segments = radius, 3
        objects.append(obj)
        return obj

    box("work surface", (-.14, -.12, TABLE_TOP_Z-.015), (1.20, .95, .030),
        radius=.006)
    for x in (-.66, .38):
        for y in (-.515, .275):
            box("leg", (x, y, .37), (.055, .055, .700), "Dark frame")
            box("foot", (x, y, .010), (.075, .075, .020), "Foot pads")
    for y in (-.515, .275):
        box("long apron", (-.14, y, .690), (1.095, .040, .060), "Dark frame")
    for x in (-.66, .38):
        box("side apron", (x, -.12, .690), (.040, .830, .060), "Dark frame")

    # Source panel back is at local Z = -6 mm.  Each post stops at that surface.
    post_height = float(matrix[2, 3]-.006-TABLE_TOP_Z)
    if post_height <= 0:
        raise ValueError("The panel must leave positive space above the table")
    for x in (-.175, .175):
        for y in (-.235, .235):
            box("panel corner standoff", (x, y, -.006-post_height/2),
                (.028, .028, post_height), local=True)

    bx, by, bz = base
    fx, fy = bx-.04*math.cos(yaw), by-.04*math.sin(yaw)
    flange_height = bz-TABLE_TOP_Z
    if flange_height <= 0:
        raise ValueError("The robot base must be above the table top")
    box("robot mounting flange", (fx, fy, TABLE_TOP_Z+flange_height/2),
        (.280, .280, flange_height))
    for dx in (-.10, .10):
        for dy in (-.10, .10):
            box("robot flange bolt", (fx+dx, fy+dy, bz+.002),
                (.012, .012, .004), "Mount bolts", radius=.001)
    return objects
