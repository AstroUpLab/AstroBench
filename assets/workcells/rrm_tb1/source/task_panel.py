# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Operable benchmark adaptation of the separate NASA TB1 visual reconstruction.

The original panel source is imported unchanged. External photo geometry is a
reconstruction; internal joints, thread pitches and retention details below are
explicit benchmark engineering parameters, not NASA manufacturing dimensions.
`specifications` and `write_spec` work in plain Python without Blender.
"""
import importlib.util
import json
import math
from pathlib import Path

SOURCE = Path(__file__).with_name("panel.py")
P = "RRM_TASK_"
THERMAL_REFERENCE = "https://ntrs.nasa.gov/api/citations/20110013452/downloads/20110013452.pdf"
TORQ_SET_REFERENCE = "https://www.phillips-screw.com/drive_systems/torq-set/"


def matrix_at(x, y, z):
    return [[1., 0., 0., x], [0., 1., 0., y], [0., 0., 1., z], [0., 0., 0., 1.]]


def stowage_specifications():
    """Measured poses are in the board frame; sockets stand on the tabletop."""
    result = {}
    for kind, x, y, flange_z, flange_r, bore_r in (
        ("fdv1", .06, -.36, .031, .029, .0252),
        ("sma", .23, -.36, .028, .0155, .0112),
    ):
        result[kind] = {
            "tool_pose_panel": matrix_at(x, y, .016),
            "xy_tolerance_m": .0015, "z_tolerance_m": .0015,
            "angle_tolerance_rad": .06, "approach_clearance_m": .06,
            "latch_support_names_prefix": "STOW_" + kind,
            "adapter_flange_bottom_tool_z_m": flange_z,
            "adapter_flange_thickness_m": .004,
            "adapter_flange_radius_m": flange_r,
            "support_top_panel_z_m": .016 + flange_z,
            "shoulder_top_z_m": .016 + flange_z,
            "flange_bottom_local_z_m": flange_z,
            "flange_radius_m": flange_r,
            "shoulder_contact_mesh_names": ["STOW_" + kind + "_open_guide_shoulder"],
            "bearing_support_names_prefix": "STOW_" + kind + "_open_guide_shoulder",
            "capture_latch_bottom_panel_z_m": .016 + flange_z + .0042,
            "capture_latch_inner_radius_m": flange_r - .0015,
            "capture_latch_outer_radius_m": flange_r + .0035,
            "guide_bore_radius_m": bore_r,
            "tabletop_panel_z_m": -.080,
            "latch_open_offset_m": .004, "latch_closed_offset_m": 0.,
            "latch_clearance_above_flange_m": .0002,
            "provenance": (
                "Bench-mounted receptacle implementing adapter-plus-cap stowage; "
                "guide dimensions, sliding locks and bench supports are engineering adaptations, "
                "not measured NASA hardware dimensions."
            ),
        }
    return result


def offset_cruciform_rectangles(clearance=0.):
    """Offset four-wing engineering recess; four rectangles meet centrally.

    NASA calls the RRM fastener '#10 Torque Set'; the available RRM images do
    not resolve its bit profile. This demonstrator uses the documented
    aerospace TORQ-SET geometry family, without claiming a verified RRM
    manufacturing drawing or its #10 dimensions.
    """
    length, width = .0031, .001
    c = clearance
    return [(c, length-c, c, width-c),
            (-width+c, -c, c, length-c),
            (-length+c, -c, -width+c, -c),
            (c, width-c, -length+c, -c)]


def specifications(sma_index=(2, 2), captive_index=1):
    row, col = sma_index
    if row not in (1, 2, 3) or col not in (1, 2, 3) or captive_index not in (1, 2):
        raise ValueError("SMA indices are 1..3; captive index is 1 or 2")
    sx, sy = -.012 + (col - 2) * .022, -.2014 + (row - 2) * .022
    cy = .0901 + (-.073 if captive_index == 1 else -.108)
    common = {"axis_local": [0, 0, 1], "parameter_provenance": "benchmark engineering adaptation, not NASA manufacturing data"}
    specs = {
        "fdv1": dict(common, seat_matrix_panel=matrix_at(-.154, -.02915, .012),
                     prototype_interface="MFT + Tertiary Cap Adapter (TCA)",
                     seat_position_parent=[0, 0, .012],
                     tool_contact_matrix_panel=matrix_at(-.154, -.02915, .042),
                     dimensions={"body_radius_m": .0145, "rim_max_radius_m": .0154,
                                 "inner_radius_m": .0127, "height_m": .055,
                                 "fixed_socket_radius_m": .011, "cap_top_panel_z_m": .067},
                     benchmark_parameters={"thread_pitch_m": .001, "unlock_turns": 2,
                                           "thread_release_travel_m": .002, "withdrawal_m": .065}),
        "sma": dict(common, selected_index=[row, col], seat_matrix_panel=matrix_at(sx, sy, .010),
                    prototype_interface="Safety Cap Tool (SCT) + SMA Adapter",
                    seat_position_parent=[(col - 2) * .022, (row - 2) * .022, .010],
                    tool_contact_matrix_panel=matrix_at(sx, sy, .0125),
                    dimensions={"hex_circumradius_m": .0048, "hex_across_flats_m": .0048 * math.sqrt(3),
                                "inner_radius_m": .00315, "height_m": .0109,
                                "fixed_stem_radius_m": .0028, "cap_top_panel_z_m": .0209},
                    benchmark_parameters={"thread_pitch_m": .000706, "unlock_turns": 2,
                                          "thread_release_travel_m": .001412, "withdrawal_m": .040}),
        "captive": dict(common, selected_index=captive_index, seat_matrix_panel=matrix_at(-.066, cy, .024),
                        prototype_interface="Safety Cap Tool (SCT) + #10 Torque Set Adapter",
                        seat_position_parent=[0, 0, 0],
                        tool_contact_matrix_panel=matrix_at(-.066, cy, .0321),
                        dimensions={"head_radius_m": .0047, "head_bottom_m": .0035,
                                    "head_top_m": .0095, "head_top_panel_z_m": .0335,
                                    "slot_floor_m": .008, "slot_floor_panel_z_m": .032,
                                    "recess_family": "offset four-wing cruciform engineering profile",
                                    "recess_rectangles_m": offset_cruciform_rectangles(),
                                    "recess_profile_source": TORQ_SET_REFERENCE,
                                    "recess_provenance": "Engineering adaptation; RRM specific recess not resolved in source photographs",
                                    "slot_length_m": .0062, "slot_width_m": .001,
                                    "slot_depth_m": .0015, "shank_radius_m": .0021,
                                    "guide_bore_radius_m": .0024, "retention_stop_radius_m": .0036},
                        benchmark_parameters={"thread_pitch_m": .0007, "turns": 3,
                                              "loosening_travel_m": .0021, "max_travel_m": .003}),
    }
    for kind, stow in stowage_specifications().items():
        specs[kind]["stowage"] = stow
    return {"schema": "astrobench.rrm.task-panel.v2", "units": "meters_radians",
            "plate_dimensions_m": [.400, .530, .006], "tasks": specs}


def write_spec(path, **kwargs):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(specifications(**kwargs), indent=2))
    return target


def _panel():
    module_spec = importlib.util.spec_from_file_location("rrm_visual_panel_reference", SOURCE)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def descendants(root):
    return [root, *root.children_recursive]


def profile_metadata(ob, profile, shapes=None, sector=None, center=(0, 0, 0)):
    ob["collision_profile_json"] = json.dumps(profile)
    ob["collision_profile_vertex_shape_json"] = json.dumps(shapes or ["circle"] * len(profile))
    ob["collision_axis"] = "Z"
    ob["collision_center_json"] = json.dumps(center)
    ob["collision_role"] = "hollow_profile"
    if sector is not None:
        ob["collision_sector_degrees"] = list(sector)


def profiled_shell(name, profile, shapes, material, parent, n=72, sector=None):
    """Closed radial section, optionally polygonal; hex radii are circumradii."""
    import bpy
    p = _panel()
    start, end = (-180, 180) if sector is None else sector
    full = abs(end - start - 360) < 1e-8
    count = n if full else n + 1
    vertices, rings = [], []
    for index, (radius, z) in enumerate(profile):
        shape = shapes[index]
        if radius == 0:
            rings.append([len(vertices)])
            vertices.append((0, 0, z))
            continue
        rings.append(list(range(len(vertices), len(vertices) + count)))
        for j in range(count):
            theta = math.radians(start + (end - start) * j / n)
            r = radius
            if shape == "hex":
                r *= math.cos(math.pi / 6) / math.cos(theta % (math.pi / 3) - math.pi / 6)
            vertices.append((r * math.cos(theta), r * math.sin(theta), z))
    faces = []
    for i in range(len(profile)):
        a, b = rings[i], rings[(i + 1) % len(profile)]
        if len(a) == len(b) == 1:
            continue
        for j in range(n):
            k = (j + 1) % count
            faces.append((a[0], b[k], b[j]) if len(a) == 1 else
                         (a[j], a[k], b[0]) if len(b) == 1 else
                         (a[j], a[k], b[k], b[j]))
    if not full:
        faces += [tuple(rings[i][0] for i in range(len(profile) - 1, -1, -1)),
                  tuple(ring[-1] for ring in rings)]
    ob = p.mesh(name, vertices, faces, material, parent)
    profile_metadata(ob, profile, shapes, sector)
    return ob


def _remove_children(root):
    import bpy
    for ob in list(root.children_recursive):
        bpy.data.objects.remove(ob, do_unlink=True)


def _subtract(target, cutter, name):
    import bpy
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(name, "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def build_stowage(parent):
    """Open-through guide seats and two independently movable radial locks."""
    p, output = _panel(), {}
    m = p.materials()
    for kind, spec in stowage_specifications().items():
        x, y = (spec["tool_pose_panel"][i][3] for i in range(2))
        root = p.empty("STOW_" + kind, parent, (x, y, 0.))
        root["provenance"] = spec["provenance"]
        top, bore = spec["support_top_panel_z_m"], spec["guide_bore_radius_m"]
        flange = spec["adapter_flange_radius_m"]
        outer, entry = flange + .009, bore + .0022
        p.box(f"STOW_{kind}_table_foot", (0, 0, -.077),
              (.100, .094, .006), m["dark"], root, .0015)
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.box(f"STOW_{kind}_support_post_{sx}_{sy}",
                      (sx*(outer-.005), sy*(outer-.005), -.037),
                      (.010, .010, .074), m["silver"], root, .0005)
                p.cylinder(f"STOW_{kind}_foot_bolt_{sx}_{sy}",
                           (sx*.043, sy*.040, -.073), .003, .002,
                           m["steel"], root, 6, .0001)
        # The opening remains a real through-bore. The cap never rests on a
        # painted disk, and the seated flange bears on the top annulus.
        shell_mat = p.material("TCR_warm_metal_shell", (.50, .44, .31), .75, .31, "brushed")
        blue = p.material("TCR_blue_flange", (.025, .070, .14), .8, .27, "brushed")
        profiled_shell(f"STOW_{kind}_open_guide_shoulder",
                       [(outer, -.005), (outer, top), (entry, top),
                        (bore, top-.006), (bore, -.005)],
                       ["circle"]*5, shell_mat, root)
        profiled_shell(f"STOW_{kind}_blue_mounting_flange",
                       [(outer+.006, -.005), (outer+.006, -.001),
                        (outer, -.001), (outer, -.005)],
                       ["circle"]*4, blue, root)
        for j in range(6):
            theta = j*math.pi/3
            p.cylinder(f"STOW_{kind}_mounting_flange_bolt_{j}",
                       ((outer+.003)*math.cos(theta), (outer+.003)*math.sin(theta), 0.),
                       .0017, .002, m["bright"], root, 6, .00005)
        # The visible TCR photo supplies the flange, cylindrical shell and
        # triangular alignment marking. Hidden lock details remain our design.
        mark = p.mesh(f"STOW_{kind}_alignment_triangle",
                      [(-.006, -outer-.0001, top*.22),
                       (.006, -outer-.0001, top*.22),
                       (0, -outer-.0001, top*.65)],
                      [(0, 1, 2)], m["ink"], root)
        mark["collision_role"] = "visual_detail"
        latches = []
        for i, angle in enumerate((0., math.pi)):
            latch = p.empty(f"STOW_{kind}_radial_lock_{i}", root)
            latch.rotation_euler.z = angle
            direction = [math.cos(angle), math.sin(angle), 0.]
            latch["radial_direction_parent"] = direction
            latch["closed_offset_m"] = 0.
            latch["open_offset_m"] = spec["latch_open_offset_m"]
            hook_bottom = top + spec["adapter_flange_thickness_m"] + .0002
            # Upright clears the flange; the top dog holds its rim after the
            # two sliders close. All entry-path geometry is retractable.
            p.box(f"STOW_{kind}_lock_{i}_upright",
                  (flange+.002, 0, top+.0023),
                  (.0028, .008, .0046), m["steel"], latch, .00015)
            p.box(f"STOW_{kind}_lock_{i}_dog",
                  (flange+.001, 0, hook_bottom+.0012),
                  (.0050, .008, .0024), m["steel"], latch, .00015)
            p.box(f"STOW_{kind}_lock_{i}_slider",
                  (flange+.008, 0, top+.0013),
                  (.010, .009, .0026), m["dark"], latch, .00015)
            p.box(f"STOW_{kind}_lock_{i}_guide",
                  ((flange+.012)*math.cos(angle), (flange+.012)*math.sin(angle), top-.002),
                  (.014, .014, .004), m["dark"], root, .0002)
            latches.append(latch)
        name = p.text(f"STOW_{kind}_label",
                      "TCA + CAP" if kind == "fdv1" else "SMA-A + CAP",
                      (0, -.036, -.0738), .0045, m["white"], root)
        name["collision_role"] = "visual_detail"
        for ob in descendants(root):
            idx = ob.name.find("STOW_")
            if idx >= 0:
                ob.name = ob.name[idx:]
        output[kind] = dict(spec, root=root, latch_roots=latches,
                            latch_radial_directions=[[1., 0., 0.], [-1., 0., 0.]])
    return output


def build(origin=(0, 0, 0), sma_index=(2, 2), captive_index=1):
    import bpy
    p = _panel()
    spec = specifications(sma_index, captive_index)
    result = p.build(origin=origin)
    mat = p.materials()
    tasks = {}

    fdv = result["components"]["FDV1"]
    fdv_profile = [(.0145, 0), (.0145, .049), (.0141, .052), (.0125, .054),
                   (.009, .055), (0, .055), (0, .0532), (.0085, .0532),
                   (.0117, .052), (.0127, .049), (.0127, .003), (.0127, 0)]
    profile_metadata(fdv["hollow_shell"], fdv_profile)
    for ob in fdv["cap_root"].children:
        if "fine_grip_mark" in ob.name:
            ob["collision_role"] = "visual_detail"
        elif "cap_base_rim" in ob.name:
            profile_metadata(ob, [(.0154, .0015), (.0154, .0045), (.014, .0045), (.014, .0015)])
        elif "cap_top_rim" in ob.name:
            profile_metadata(ob, [(.0147, .0514), (.0147, .0526), (.0139, .0526), (.0139, .0514)])
    tasks["fdv1"] = dict(spec["tasks"]["fdv1"], moving_root=fdv["cap_root"], fixed_root=fdv["root"])

    array = result["components"]["SMA_array"]
    row, col = sma_index
    cap = array["caps"][(row - 1) * 3 + col - 1]
    _remove_children(cap)
    # A complete closed wall section: lower opening is genuine; top is sealed.
    sma_profile = [(.0048, 0), (.0048, .0095), (.0035, .0109), (0, .0109),
                   (0, .0084), (.00315, .0084), (.00315, 0)]
    shapes = ["hex", "hex", "circle", "circle", "circle", "circle", "circle"]
    sma_shell = profiled_shell("TASK_SMA_selected_hollow_cap", sma_profile, shapes, mat["gold"], cap)
    sma_shell["inner_radius_m"] = .00315
    x, y = cap.location.x, cap.location.y
    fixed = p.empty("TASK_SMA_selected_fixed_connector", array["root"], (x, y, 0))
    p.cylinder("TASK_SMA_selected_stem", (0, 0, .01265), .0028, .0077, mat["bright"], fixed, 48, .0001)
    p.ring("TASK_SMA_selected_contact_ring", (0, 0, .0165), .0028, .0017, .0005, mat["gold"], fixed)
    p.cylinder("TASK_SMA_selected_dielectric", (0, 0, .0164), .0016, .0004, mat["white"], fixed, 40, .00005)
    cap["task_role"] = "Selected hollow removable SMA protective cap"
    cap["benchmark_thread_pitch_m"] = .000706
    tasks["sma"] = dict(spec["tasks"]["sma"], moving_root=cap, fixed_root=fixed, hollow_shell=sma_shell)

    fasteners = result["components"]["fastener_block"]
    anchor = fasteners["captive"][captive_index - 1]
    _remove_children(anchor)
    moving = p.empty("TASK_captive_moving_screw", anchor)
    guide = p.ring("TASK_captive_seat_washer", (0, 0, .00175), .007, .0024, .0035, mat["silver"], anchor)
    profile_metadata(guide, [(.007, 0), (.007, .0035), (.0024, .0035), (.0024, 0)])
    head = p.cylinder("TASK_captive_head", (0, 0, .0065), .0047, .006, mat["bright"], moving, 72, 0)
    # True offset four-wing recess. All four material removals are exported
    # exactly as planar cell pieces, not filled by a convex whole-head hull.
    for index, (x0, x1, y0, y1) in enumerate(offset_cruciform_rectangles()):
        cutter = p.box("TASK_temporary_offset_driver_wing",
                       ((x0+x1)/2, (y0+y1)/2, .0095),
                       (x1-x0, y1-y0, .003), mat["dark"], moving, 0)
        _subtract(head, cutter, "Offset four-wing recess " + str(index))
    head["collision_role"] = "offset_cruciform_head"
    head["collision_recess_coordinates"] = "parent"
    head["collision_recess_json"] = json.dumps({
        "rectangles": offset_cruciform_rectangles(), "floor_z": .008,
        "head_z_min": .0035, "head_z_max": .0095, "radius": .0047,
        "provenance": spec["tasks"]["captive"]["dimensions"]["recess_provenance"]})
    p.cylinder("TASK_captive_shank", (0, 0, -.00625), .0021, .0195, mat["steel"], moving, 40, .00005)
    stop = p.ring("TASK_captive_lower_stop", (0, 0, -.0084), .0036, .00205, .0012, mat["steel"], moving)
    profile_metadata(stop, [(.0036, -.009), (.0036, -.0078), (.00205, -.0078), (.00205, -.009)])
    # Drill a shaft passage and internal retaining pocket only in this new
    # task scene. The original panel source and its saved blend stay untouched.
    for ob in list(fasteners["root"].children):
        if ob.type != "MESH" or not any(s in ob.name for s in ("Fastener_block_back", "Fastener_block_front_sheet")):
            continue
        for kind, radius, low, high in (("guide", .0024, -.020, .001), ("stop_pocket", .0042, -.0165, -.0025)):
            cutter = p.cylinder("TASK_temporary_" + kind, (0, 0, (low + high) / 2), radius,
                                high - low, mat["steel"], anchor, 64, 0)
            _subtract(ob, cutter, "Captive screw " + kind)
    moving["task_role"] = "Captive screw: head, shaft and lower retaining stop move together"
    moving["travel_limit_m"] = .003
    tasks["captive"] = dict(spec["tasks"]["captive"], moving_root=moving, fixed_root=anchor, slotted_head=head)

    for key, task in tasks.items():
        task["moving_root"]["task_id"] = key
        task["moving_root"]["parameter_provenance"] = spec["tasks"][key]["parameter_provenance"]
        task["moving_objects"] = [o for o in descendants(task["moving_root"]) if o.type in ("MESH", "CURVE")]
        task["moving_root"]["seat_position_parent"] = task["seat_position_parent"]
    moving_set = {o for t in tasks.values() for o in descendants(t["moving_root"])}
    result["tasks"] = tasks
    stowage = build_stowage(result["root"])
    latch_set = {o for dock in stowage.values() for latch in dock["latch_roots"]
                 for o in descendants(latch)}
    result["stowage"] = stowage
    result["fixed_objects"] = [o for o in result["root"].children_recursive
                               if o not in moving_set | latch_set and o.type in ("MESH", "CURVE")]
    result["specifications"] = spec
    result["adaptation_source"] = str(SOURCE)
    bpy.context.view_layer.update()
    return result


def set_state(task, angle_rad=0., axial_m=0.):
    if task["moving_root"].get("task_id") == "captive" and not 0 <= axial_m <= .003 + 1e-9:
        raise ValueError("Captive travel is limited to 0..3 mm")
    task["moving_root"].location = task["seat_position_parent"]
    task["moving_root"].location.z += axial_m
    task["moving_root"].rotation_euler.z = angle_rad


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    write_spec(args.spec)
