# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Export TB1 task and tool contact geometry without filling hollow parts.

Run in Blender:
  blender -b -P assets/workcells/rrm_tb1/source/export_collision.py -- \
    --output collision.json

Static geometry retains concave triangle surfaces. Moving hollow shells carry
explicit meridional profiles and are split into convex section/azimuth pieces.
All original evaluated surfaces are retained alongside their convex pieces.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))


def rows(matrix):
    return [[float(v) for v in row] for row in matrix]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonable(value):
    if isinstance(value, bpy.types.Object):
        return value.name
    if isinstance(value, Matrix):
        return rows(value)
    if isinstance(value, Vector):
        return list(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def prop_json(obj, key, default=None):
    value = obj.get(key, default)
    return json.loads(value) if isinstance(value, str) else value


def geometry(obj, body_frame, graph):
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    try:
        if mesh is None or not mesh.vertices:
            return None
        mesh.calc_loop_triangles()
        transform = body_frame.inverted() @ obj.matrix_world
        points = [transform @ v.co for v in mesh.vertices]
        triangles = []
        for t in mesh.loop_triangles:
            a, b, c = t.vertices
            if (points[b]-points[a]).cross(points[c]-points[a]).length_squared > 1e-22:
                triangles.append([int(a), int(b), int(c)])
        if not triangles:
            return None
        if not all(math.isfinite(x) for p in points for x in p):
            raise ValueError(f"Non-finite vertex: {obj.name}")
        return {"name": obj.name, "vertices": [list(p) for p in points],
                "triangles": triangles, "coordinate_frame": "body_local"}
    finally:
        evaluated.to_mesh_clear()


def hull(points):
    """Small local convex hull; never called on a complete hollow object."""
    bm = bmesh.new()
    try:
        for p in points:
            bm.verts.new(p)
        bm.verts.ensure_lookup_table()
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-9)
        result = bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
        discard = set(result.get("geom_interior", [])) | set(result.get("geom_unused", []))
        unused = [g for g in discard if isinstance(g, bmesh.types.BMVert) and g.is_valid]
        if unused:
            bmesh.ops.delete(bm, geom=unused, context="VERTS")
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.verts.index_update()
        vertices = [list(v.co) for v in bm.verts]
        triangles = [[v.index for v in f.verts] for f in bm.faces]
        volume = abs(bm.calc_volume(signed=True))
        if volume < 1e-17:
            return None
        return vertices, triangles, volume
    finally:
        bm.free()


def cross2(a, b, c):
    return (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])


def convex_profile_parts(profile):
    """Triangulate the *material* cross-section, then merge convex neighbors."""
    points = [(float(p[0]), float(p[1])) for p in profile]
    polygon = [Vector((r, z, 0)) for r, z in points]
    lookup = {(round(v.x, 10), round(v.y, 10)): i for i, v in enumerate(polygon)}
    parts = []
    for tri in tessellate_polygon([polygon]):
        indices = [int(v) if isinstance(v, int)
                   else lookup[(round(v.x, 10), round(v.y, 10))] for v in tri]
        if cross2(*(points[i] for i in indices)) < 0:
            indices.reverse()
        parts.append(indices)
    if not parts:
        raise ValueError("Empty meridional material cross-section")

    def combine(a, b):
        edges = [(v[i], v[(i+1) % len(v)]) for v in (a, b) for i in range(len(v))]
        common = [edge for edge in edges if (edge[1], edge[0]) in edges]
        if len(common) != 2:
            return None
        boundary = [edge for edge in edges if edge not in common]
        out = [boundary[0][0]]
        while len(out) < len(boundary):
            nxt = [q for p, q in boundary if p == out[-1]]
            if len(nxt) != 1 or nxt[0] in out:
                return None
            out.append(nxt[0])
        if (out[-1], out[0]) not in boundary:
            return None
        if all(cross2(points[out[i-1]], points[out[i]], points[out[(i+1) % len(out)]]) >= -1e-12
               for i in range(len(out))):
            return out
        return None

    changed = True
    while changed:
        changed = False
        for i in range(len(parts)):
            for j in range(i+1, len(parts)):
                merged = combine(parts[i], parts[j])
                if merged:
                    parts = [v for k, v in enumerate(parts) if k not in (i, j)] + [merged]
                    changed = True
                    break
            if changed:
                break
    return parts


def shaped_radius(radius, angle, shape):
    if shape == "circle":
        return radius
    if shape == "hex":
        # Radius is the hexagon circumradius; a vertex lies on local +X.
        local = angle % (math.pi/3) - math.pi/6
        return radius * math.cos(math.pi/6) / math.cos(local)
    raise ValueError(f"Unknown collision profile radial shape: {shape}")


def profile_parts(obj, body_frame, segments):
    profile = prop_json(obj, "collision_profile_json")
    if profile is None:
        return None
    if obj.get("collision_axis", "Z") != "Z":
        raise ValueError(f"Only authored local Z profiles are supported: {obj.name}")
    center = prop_json(obj, "collision_center_json", [0, 0, 0])
    shapes = prop_json(obj, "collision_profile_vertex_shape_json",
                       ["circle"] * len(profile))
    if len(shapes) != len(profile):
        raise ValueError(f"Profile shape count mismatch: {obj.name}")
    if any(float(p[0]) < 0 for p in profile):
        raise ValueError(f"Negative profile radius: {obj.name}")
    sector = prop_json(obj, "collision_sector_degrees", [-180, 180])
    lo, hi = map(math.radians, sector)
    count = max(1, math.ceil((hi-lo) / (2*math.pi) * segments))
    boundaries = [lo+(hi-lo)*i/count for i in range(count+1)]
    if "hex" in shapes:
        # Exact hexagon corner angles also appear in the sector boundaries.
        boundaries += [k*math.pi/3 for k in range(-6, 7) if lo < k*math.pi/3 < hi]
        boundaries = sorted(set(round(a, 12) for a in boundaries))
    transform = body_frame.inverted() @ obj.matrix_world
    sections = convex_profile_parts(profile)
    output = []
    for section_index, section in enumerate(sections):
        for angle_index, (a, b) in enumerate(zip(boundaries, boundaries[1:])):
            points = []
            for theta in (a, b):
                for i in section:
                    radius, z = profile[i][:2]
                    r = shaped_radius(float(radius), theta, shapes[i])
                    points.append(transform @ Vector((center[0]+r*math.cos(theta),
                                                       center[1]+r*math.sin(theta),
                                                       center[2]+float(z))))
            item = hull(points)
            if item is None:
                continue
            vertices, triangles, volume = item
            output.append({"name": f"{obj.name}__section{section_index:02d}_sector{angle_index:03d}",
                           "vertices": vertices, "triangles": triangles, "volume_m3": volume,
                           "source_object": obj.name,
                           "method": "convex meridional material section swept over one azimuth sector",
                           "profile_section_indices": section,
                           "azimuth_radians": [a, b]})
    if not output:
        raise ValueError(f"Profile produced no volume: {obj.name}")
    return output


def convex_surface(record, tolerance=5e-6):
    """Check each nondegenerate face support plane before accepting one hull."""
    verts = [Vector(v) for v in record["vertices"]]
    center = sum(verts, Vector()) / len(verts)
    for tri in record["triangles"]:
        a, b, c = (verts[i] for i in tri)
        normal = (b-a).cross(c-a)
        if normal.length < 1e-12:
            continue
        normal.normalize()
        if normal.dot(center-a) > 0:
            normal.negate()
        if any(normal.dot(v-a) > tolerance for v in verts):
            return False
    return True


def clipped_polygon(polygon, axis, threshold, keep_greater):
    result = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        da, db = a[axis]-threshold, b[axis]-threshold
        ina = da >= -1e-12 if keep_greater else da <= 1e-12
        inb = db >= -1e-12 if keep_greater else db <= 1e-12
        if ina:
            result.append(a)
        if ina != inb:
            t = da/(da-db)
            result.append([a[k]+t*(b[k]-a[k]) for k in range(2)])
    return result


def slot_parts(obj, body_frame):
    slot = prop_json(obj, "collision_slot_json")
    if slot is None:
        return None
    coordinates = obj.get("collision_slot_coordinates", "parent")
    frame = obj.parent.matrix_world if coordinates == "parent" else obj.matrix_world
    transform = body_frame.inverted() @ frame
    radius, floor = float(slot["radius"]), float(slot["floor_z"])
    half_width, half_length = float(slot["width"])/2, float(slot["length"])/2
    # Keep the authored cylinder's polygonal outline instead of replacing it
    # with a larger circumscribed primitive.
    local_transform = frame.inverted() @ obj.matrix_world
    outline_points = [local_transform @ v.co for v in obj.data.vertices]
    outline = {(round(v.x, 10), round(v.y, 10)) for v in outline_points
               if abs(math.hypot(v.x, v.y)-radius) < 1e-7}
    outline = sorted([list(p) for p in outline], key=lambda p: math.atan2(p[1], p[0]))
    if len(outline) < 12:
        raise ValueError(f"Cannot recover slotted head outline: {obj.name}")
    pieces = [("bottom", outline, float(slot["head_z_min"]), floor)]
    for name, greater in (("shoulder_pos", True), ("shoulder_neg", False)):
        polygon = clipped_polygon(outline, 1, half_width if greater else -half_width, greater)
        pieces.append((name, polygon, floor, float(slot["head_z_max"])))
    strip = clipped_polygon(clipped_polygon(outline, 1, -half_width, True), 1, half_width, False)
    for name, greater in (("end_pos", True), ("end_neg", False)):
        polygon = clipped_polygon(strip, 0, half_length if greater else -half_length, greater)
        pieces.append((name, polygon, floor, float(slot["head_z_max"])))
    result = []
    for name, polygon, low, high in pieces:
        if len(polygon) < 3:
            continue
        item = hull([transform @ Vector((x, y, z)) for z in (low, high) for x, y in polygon])
        if item:
            vertices, triangles, volume = item
            result.append({"name": obj.name+"__"+name, "vertices": vertices,
                           "triangles": triangles, "volume_m3": volume,
                           "source_object": obj.name,
                           "method": "finite driver slot preserved as bottom disk, two shoulders and two end bridges"})
    return result


def recess_parts(obj, body_frame):
    """Preserve an offset four-wing cavity using nonoverlapping planar cells."""
    recess = prop_json(obj, "collision_recess_json")
    if recess is None:
        return None
    frame = obj.parent.matrix_world if obj.get("collision_recess_coordinates") == "parent" else obj.matrix_world
    transform = body_frame.inverted() @ frame
    radius, floor = float(recess["radius"]), float(recess["floor_z"])
    local = frame.inverted() @ obj.matrix_world
    points = [local @ v.co for v in obj.data.vertices]
    outline = {(round(v.x, 10), round(v.y, 10)) for v in points
               if abs(math.hypot(v.x, v.y)-radius) < 1e-7}
    outline = sorted([list(p) for p in outline], key=lambda p: math.atan2(p[1], p[0]))
    if len(outline) < 12:
        raise ValueError("Cannot recover recessed head outline: " + obj.name)
    rectangles = recess["rectangles"]
    xs = sorted({-radius, radius, *(v for r in rectangles for v in r[:2])})
    ys = sorted({-radius, radius, *(v for r in rectangles for v in r[2:])})
    pieces = [("bottom", outline, float(recess["head_z_min"]), floor)]
    for ix, (x0, x1) in enumerate(zip(xs, xs[1:])):
        for iy, (y0, y1) in enumerate(zip(ys, ys[1:])):
            cx, cy = (x0+x1)/2, (y0+y1)/2
            if any(a <= cx <= b and c <= cy <= d for a, b, c, d in rectangles):
                continue
            polygon = clipped_polygon(outline, 0, x0, True)
            polygon = clipped_polygon(polygon, 0, x1, False)
            polygon = clipped_polygon(polygon, 1, y0, True)
            polygon = clipped_polygon(polygon, 1, y1, False)
            pieces.append((f"cell_{ix}_{iy}", polygon, floor, float(recess["head_z_max"])))
    result = []
    for name, polygon, low, high in pieces:
        if len(polygon) < 3:
            continue
        item = hull([transform @ Vector((x, y, z)) for z in (low, high) for x, y in polygon])
        if item:
            vertices, triangles, volume = item
            result.append({"name": obj.name+"__"+name, "vertices": vertices,
                           "triangles": triangles, "volume_m3": volume,
                           "source_object": obj.name,
                           "method": "Offset cruciform preserved as lower disk and nonoverlapping convex planar cells"})
    return result


def obj_file(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for v in record["vertices"]:
            f.write("v " + " ".join(f"{c:.10g}" for c in v) + "\n")
        for tri in record["triangles"]:
            f.write("f " + " ".join(str(i+1) for i in tri) + "\n")
    return str(path.resolve().relative_to(EXPORT_ROOT))


def family(root):
    return {root, *root.children_recursive}


def selected_meshes(objects):
    return [o for o in sorted(objects, key=lambda v: v.name)
            if o.type in {"MESH", "CURVE"}]


def export_body(body_id, root, objects, graph, directory, segments, parent_id=None,
                parent_root=None):
    body = {"root_object": root.name, "initial_transform": rows(root.matrix_world),
            "parent_body": parent_id,
            "transform_in_parent": rows(parent_root.matrix_world.inverted() @ root.matrix_world)
            if parent_root else rows(root.matrix_world),
            "meshes": [], "convex_parts": [], "excluded": []}
    safe_id = body_id.replace("/", "__")
    for index, obj in enumerate(selected_meshes(objects)):
        reason = obj.get("collision_exclude_reason") or (
            "authored visual_detail marking" if obj.get("collision_role") == "visual_detail" else None)
        if reason:
            body["excluded"].append({"name": obj.name, "reason": str(reason)})
            continue
        record = geometry(obj, root.matrix_world, graph)
        if not record:
            continue
        body["meshes"].append(record)
        parts = profile_parts(obj, root.matrix_world, segments)
        if parts is None:
            parts = slot_parts(obj, root.matrix_world)
        if parts is None:
            parts = recess_parts(obj, root.matrix_world)
        if parts is None:
            explicit = prop_json(obj, "collision_convex_parts_json")
            if explicit is not None:
                transform = root.matrix_world.inverted() @ obj.matrix_world
                parts = []
                for n, vertices in enumerate(explicit):
                    result = hull([transform @ Vector(p) for p in vertices])
                    if result:
                        vertices, triangles, volume = result
                        parts.append({"name": f"{obj.name}__explicit{n}",
                                      "vertices": vertices, "triangles": triangles,
                                      "volume_m3": volume, "source_object": obj.name,
                                      "method": "author-provided explicit convex material piece"})
            else:
                if not convex_surface(record):
                    raise ValueError(f"Dynamic concave mesh has no material profile or explicit convex pieces: {obj.name}")
                result = hull(record["vertices"])
                if not result:
                    raise ValueError(f"Dynamic surface has no solid volume: {obj.name}")
                vertices, triangles, volume = result
                parts = [{"name": obj.name, "vertices": vertices, "triangles": triangles,
                          "volume_m3": volume, "source_object": obj.name,
                          "method": "original surface support planes checked before hull triangulation",
                          "support_plane_tolerance_m": 5e-6}]
        for n, part in enumerate(parts):
            part["obj_path"] = obj_file(directory/safe_id/f"{index:03d}_{n:03d}.obj", part)
            body["convex_parts"].append(part)
    return body


def export(output, segments, sma_row=2, sma_col=2, captive_index=1):
    global EXPORT_ROOT
    EXPORT_ROOT = output.parent.resolve()
    import task_panel
    import tools as task_tools

    source_before = {name: digest(HERE/name) for name in ("task_panel.py", "tools.py")}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = task_panel.build(sma_index=(sma_row, sma_col), captive_index=captive_index)
    tool_data = {kind: task_tools.build(kind) for kind in ("fdv1", "sma", "captive")}
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    directory = output.parent/(output.stem + "_meshes")
    bodies, task_records, tool_records = {}, {}, {}
    excluded = []
    for kind, task in data["tasks"].items():
        target_id = "target/"+kind
        target = task["moving_root"]
        bodies[target_id] = export_body(target_id, target, family(target), graph, directory, segments)
        task_records[kind] = {k: jsonable(v) for k, v in task.items()
                              if k not in {"moving_root", "fixed_root"}}
        task_records[kind].update(target_body=target_id, fixed_root=task["fixed_root"].name)
    static_meshes = []
    for index, obj in enumerate(selected_meshes(data["fixed_objects"])):
        reason = obj.get("collision_exclude_reason") or (
            "authored visual_detail marking" if obj.get("collision_role") == "visual_detail" else None)
        if reason:
            excluded.append({"name": obj.name, "reason": str(reason)})
            continue
        record = geometry(obj, Matrix.Identity(4), graph)
        if record:
            record["coordinate_frame"] = "world"
            record["obj_path"] = obj_file(directory/"static"/f"{index:04d}.obj", record)
            static_meshes.append(record)
    for kind, tool in tool_data.items():
        roots = [("base", tool["root"]), ("spindle", tool["spindle_root"])]
        roots += [(f"jaw_{i}", r) for i, r in enumerate(tool.get("jaw_roots", []))]
        roots += [(f"retention_{i}", r) for i, r in enumerate(tool.get("retention_roots", []))]
        roots = [(name, obj) for name, obj in roots if obj is not None]
        distinct = {obj for _, obj in roots}
        if len(distinct) != len(roots):
            raise ValueError(f"Duplicate tool body roots: {kind}")
        for name, root in roots:
            body_id = f"tool/{kind}/{name}"
            members = family(root)
            for _, child_root in roots:
                if child_root != root and child_root in members:
                    members -= family(child_root)
            ancestor = root.parent
            while ancestor and ancestor not in distinct:
                ancestor = ancestor.parent
            parent_name = next((n for n, obj in roots if obj == ancestor), None)
            parent_id = f"tool/{kind}/{parent_name}" if parent_name else None
            bodies[body_id] = export_body(body_id, root, members, graph, directory, segments,
                                         parent_id, ancestor)
        tool_records[kind] = {k: jsonable(v) for k, v in tool.items()
                              if k not in {"root", "spindle_root", "jaw_roots",
                                           "retention_roots", "mesh_objects"}}
        tool_records[kind]["body_ids"] = {name: f"tool/{kind}/{name}" for name, _ in roots}
    for kind, dock in data.get("stowage", {}).items():
        ids = []
        for i, latch in enumerate(dock["latch_roots"]):
            body_id = f"dock/{kind}/latch_{i}"
            bodies[body_id] = export_body(body_id, latch, family(latch), graph, directory, segments)
            ids.append(body_id)
        task_records[kind]["stowage"].update(
            latch_body_ids=ids,
            latch_radial_directions=dock["latch_radial_directions"])
    sources = {name: {"path": "source/" + name, "sha256": digest(HERE/name)}
               for name in ("task_panel.py", "tools.py", "export_collision.py")}
    if any(sources[name]["sha256"] != value for name, value in source_before.items()):
        raise RuntimeError("Task or tool source changed during geometry export")
    report = {
        "format_version": 1, "units": "m",
        "matrix_convention": "row-listed 4x4 matrices, column vectors: world = initial_transform @ local",
        "static_rule": "Static triangle meshes preserve authored cavities; load as static concave meshes.",
        "dynamic_rule": "Use convex_parts only for dynamic collision; original meshes remain for reference.",
        "angular_segments_per_circle": segments,
        "selected_sma_index": [sma_row, sma_col], "selected_captive_index": captive_index,
        "hollow_part_rule": "Convex decomposition acts on the material cross-section before azimuth subdivision; no whole-shell convex hull.",
        "sources": sources, "tasks": task_records, "tools": tool_records,
        "bodies": bodies, "static_meshes": static_meshes, "excluded": excluded,
        "summary": {"dynamic_body_count": len(bodies), "static_mesh_count": len(static_meshes),
                    "convex_part_count": sum(len(b["convex_parts"]) for b in bodies.values()),
                    "original_dynamic_mesh_count": sum(len(b["meshes"]) for b in bodies.values())}
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, separators=(",", ":"), ensure_ascii=False)+"\n")
    print(json.dumps({"output": str(output), **report["summary"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="collision.json")
    parser.add_argument("--segments", type=int, default=72)
    parser.add_argument("--sma-row", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--sma-col", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--captive-index", type=int, default=1, choices=(1, 2))
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    try:
        if args.segments < 24:
            raise ValueError("Use at least 24 azimuth sectors for contact shells.")
        export(ROOT/args.output, args.segments, args.sma_row, args.sma_col, args.captive_index)
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
