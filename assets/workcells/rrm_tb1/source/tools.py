# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""RRM tool/adapter families on a compact Franka-compatible drive carrier.

Tip/mouth is local origin; +Z points away from the board toward the robot.
The fixed grip handle centre is Z=115 mm; the carrier grasp frame is at
Z=120 mm to keep its fingertip geometry clear of the bearing. Working head and drive shaft belong
to an independent detachable spindle; the FDV jaws and SMA retaining leaves
are separate. Public NASA images support the TCA cage and replaceable
SMA-A/TSA architecture. Their hidden grip, coupling and stowage mechanisms
are documented engineering implementations, not NASA manufacturing geometry.
"""
import importlib.util
import json
import math
from pathlib import Path


def tool_specs():
    common = {"tip_to_tcp_m": [0, 0, .120], "handle_dimensions_m": [.020, .018, .040],
              "handle_center_m": [0, 0, .115], "grasp_center_m": [0, 0, .120], "axis_local": [0, 0, 1],
              "provenance": "NASA-referenced adapter architecture on AstroBench drive carrier; hidden mechanisms and dimensions are engineering adaptations",
              "drive_interface_local_z_m": .064,
              "adapter_body": "spindle_root including its jaw/retention descendants",
              "driver_withdrawal_axis_local": [0, 0, 1]}
    return {
        "fdv1": dict(common, prototype_family="MFT + Tertiary Cap Adapter (TCA)",
                     visual_reference="NASA 20110013452 Fig.10; NASA Goddard photo 8379611845",
                     grip_provenance="Three radial padded elements are an engineering retention implementation, not a verified TCA internal mechanism",
                     adapter_stowage_flange={"bottom_z_m": .031, "thickness_m": .004, "radius_m": .029},
                     jaw_closed_radius_m=.01455, jaw_contact_offset_m=-.00005,
                     jaw_open_offset_m=.003, jaw_outer_radius_m=.018,
                     mouth_to_cap_top_m=.025, rear_cavity_floor_m=.028,
                     jaw_radial_offset_range_m=[-.00005, .003]),
        "sma": dict(common, prototype_family="Safety Cap Tool (SCT) + SMA Adapter",
                    visual_reference="NASA NExIS ASTC 2022 hardware-development slide, SCT Adapter Suite",
                    adapter_stowage_flange={"bottom_z_m": .028, "thickness_m": .004, "radius_m": .0155},
                    outer_radius_m=.0063, inner_hex_across_flats_m=.00855,
                    socket_depth_m=.0108, retention="Three compliant bronze spring leaves; friction retention, no magnets",
                    retaining_leaf_radial_offset_range_m=[0., .0006]),
        "captive": dict(common, prototype_family="Safety Cap Tool (SCT) + #10 Torque Set Adapter",
                        driver_family="Offset four-wing cruciform engineering profile",
                        driver_profile_provenance="TORQ-SET geometry family per manufacturer; RRM-specific recess not resolved in available imagery",
                        driver_reference="https://www.phillips-screw.com/drive_systems/torq-set/",
                        driver_tip_height_m=.003),
    }


def _module(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("rrm_tasks_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(kind, parent=None):
    import bpy
    if kind not in tool_specs():
        raise ValueError("Tool kind must be fdv1, sma or captive")
    tp = _module("task_panel")
    p = tp._panel()
    m = p.materials()
    root = p.empty("TOOL_" + kind, parent)
    spindle = p.empty("TOOL_" + kind + "_spindle", root)
    root["provenance"] = tool_specs()[kind]["provenance"]
    root["tip_to_tcp_m"] = [0, 0, .120]
    root["handle_center_m"] = [0, 0, .115]
    root["grasp_center_m"] = [0, 0, .120]
    root["spindle_axis_local"] = [0, 0, 1]
    # Fixed shaft bearings have real bores; the moving shaft fits inside.
    housing = p.ring("TOOL_" + kind + "_bearing_housing", (0, 0, .0845), .014, .00425, .021, m["dark"], root)
    tp.profile_metadata(housing, [(.014, .074), (.014, .095), (.00425, .095), (.00425, .074)])
    for z in (.075, .093):
        rim = p.ring("TOOL_" + kind + "_bearing_rim", (0, 0, z), .0146, .00425, .002, m["bright"], root)
        tp.profile_metadata(rim, [(.0146, z-.001), (.0146, z+.001), (.00425, z+.001), (.00425, z-.001)])
    handle = p.box("TOOL_" + kind + "_parallel_jaw_handle", (0, 0, .115), (.020, .018, .040), m["dark"], root, .0006)
    # The captured adapter terminates inside a true driver socket.  No collar
    # crosses the withdrawal path: driver + bearing + handle can leave axially.
    p.cylinder("TOOL_" + kind + "_adapter_shaft", (0, 0, .0475), .004, .033, m["steel"], spindle, 64, .0001)
    p.cylinder("TOOL_" + kind + "_adapter_coupling_shaft", (0, 0, .0675), .004, .007, m["steel"], spindle, 64, 0)
    tp.profiled_shell("TOOL_" + kind + "_driver_coupling_socket",
                      [(.0075, .064), (.0075, .074), (.0042, .074), (.0042, .064)],
                      ["circle"]*4, m["bright"], root)
    p.cylinder("TOOL_" + kind + "_driver_shaft", (0, 0, .083), .004, .024,
               m["steel"], root, 64, .0001)
    release = p.empty("TOOL_" + kind + "_drive_release_indicator", root)
    # This indicator follows the measured release phase. The locking
    # constraint and detachable adapter state are handled in the trial.
    tp.profiled_shell("TOOL_" + kind + "_drive_lock_collar",
                      [(.010, .065), (.010, .069), (.0076, .069), (.0076, .065)],
                      ["circle"]*4, m["dark"], release)
    for ob in release.children:
        ob["collision_role"] = "visual_detail"
        ob["collision_exclude_reason"] = "Drive-release indication only; mechanical lock is represented by adapter constraint"
    marker = p.box("TOOL_" + kind + "_drive_lock_index", (.0098, 0, .067),
                   (.0005, .003, .002), m["white"], release, .00005)
    marker["collision_role"] = "visual_detail"
    jaws, retainers = [], []
    if kind == "fdv1":
        # Three separately actuated collet fingers. Their curved pads close to
        # a 29 mm cap; -50 microns radial travel removes the setup clearance.
        for i in range(3):
            jaw = p.empty("TOOL_fdv1_jaw_" + str(i+1), spindle)
            jaw.rotation_euler.z = 2 * math.pi * i / 3
            jaw["radial_direction_parent"] = [math.cos(jaw.rotation_euler.z), math.sin(jaw.rotation_euler.z), 0]
            tp.profiled_shell("TOOL_fdv1_jaw_body_" + str(i+1),
                              [(.0156, 0), (.018, 0), (.018, .023), (.0156, .023)],
                              ["circle"]*4, m["silver"], jaw, n=32, sector=(-48, 48))
            tp.profiled_shell("TOOL_fdv1_contact_pad_" + str(i+1),
                              [(.01455, .005), (.01565, .005), (.01565, .014), (.01455, .014)],
                              ["circle"]*4, m["gasket"], jaw, n=24, sector=(-25, 25))
            jaws.append(jaw)
        # Crown holds the jaw rails; the centre remains a real cavity to 28 mm.
        crown_profile = [(.018, .023), (.024, .023), (.024, .031),
                         (0, .031), (0, .028), (.018, .028)]
        tp.profiled_shell("TOOL_fdv1_rear_crown", crown_profile, ["circle"]*6, m["dark"], spindle)
        for i in range(3):
            angle = 2 * math.pi * i / 3
            xy = (.021*math.cos(angle), .021*math.sin(angle))
            old_children = set(spindle.children)
            p.screw("TOOL_fdv1_adjustment", xy, .031, m, spindle, .0018)
            for ob in set(spindle.children) - old_children:
                if "washer" in ob.name:
                    tp.profile_metadata(ob, [(.00234, .03105), (.00234, .03175),
                                             (.00099, .03175), (.00099, .03105)], center=(*xy, 0))
                elif "hex_socket_shadow" in ob.name:
                    ob["collision_role"] = "visual_detail"
                    ob["collision_exclude_reason"] = "Thin driver socket colour marking on adjustment screw"
        # NASA Fig.10 and the on-orbit TCA/TCR photo show a cylindrical cage
        # with longitudinal windows, bright guide members and a rear ring.
        blue = p.material("TCA_blue_anodized_rings", (.035, .090, .16), .78, .29, "brushed")
        tp.profiled_shell("TOOL_fdv1_TCA_front_cage_ring",
                          [(.0243, 0), (.0243, .003), (.0217, .003), (.0217, 0)],
                          ["circle"]*4, m["dark"], spindle)
        for i in range(6):
            angle = math.pi/6 + i*math.pi/3
            a0, a1 = math.degrees(angle)-5, math.degrees(angle)+5
            tp.profiled_shell("TOOL_fdv1_TCA_window_rail_" + str(i),
                              [(.0217, .003), (.0243, .003), (.0243, .023), (.0217, .023)],
                              ["circle"]*4, m["bright"] if i % 2 == 0 else blue,
                              spindle, n=6, sector=(a0, a1))
        tp.profiled_shell("TOOL_fdv1_TCA_stowage_flange",
                          [(.029, .031), (.029, .035), (.0042, .035), (.0042, .031)],
                          ["circle"]*4, m["bright"], spindle)
        tp.profiled_shell("TOOL_fdv1_TCA_rear_band",
                          [(.0238, .023), (.0238, .027), (.018, .027), (.018, .023)],
                          ["circle"]*4, blue, spindle)
        label = p.text("TOOL_fdv1_TCA_id", "TCA", (0, -.019, .03515), .004, m["ink"], spindle)
        label["collision_role"] = "visual_detail"
    elif kind == "sma":
        inner = .00855 / math.sqrt(3)
        # Three true axial relief slots accommodate the compliant leaves.
        # Alternating hex flats remain solid torque-bearing socket surfaces.
        profile = [(.0063, 0), (.0063, .0108), (inner, .0108), (inner, 0)]
        for i in range(3):
            tp.profiled_shell("TOOL_sma_hex_socket_sector_" + str(i+1), profile,
                              ["circle", "circle", "hex", "hex"], m["steel"], spindle,
                              n=32, sector=(44 + i*120, 136 + i*120))
        p.cylinder("TOOL_sma_socket_back", (0, 0, .0119), .0063, .0022, m["steel"], spindle, 72, 0)
        p.cylinder("TOOL_sma_extension", (0, 0, .022), .0036, .018, m["steel"], spindle, 48, .0001)
        # Thin bronze leaves contact alternate hex flats and retain the cap
        # after unthreading. These are compliant benchmark elements, not magnets.
        bronze = p.material("tool_spring_bronze", (.36, .19, .055), .8, .28)
        for i in range(3):
            leaf = p.empty("TOOL_sma_retaining_leaf_" + str(i+1), spindle)
            leaf.rotation_euler.z = math.pi/6 + 2*math.pi*i/3
            leaf["radial_direction_parent"] = [math.cos(leaf.rotation_euler.z), math.sin(leaf.rotation_euler.z), 0]
            # In its fitted state the inner face touches the target flat;
            # root may open it radially by 0.6 mm for the unretained control.
            p.box("TOOL_sma_spring_leaf_" + str(i+1), (.00431, 0, .0059),
                  (.00030, .0018, .0098), bronze, leaf, .00004)
            retainers.append(leaf)
        p.cylinder("TOOL_sma_adapter_rear_body", (0, 0, .047), .009,
                   .034, m["silver"], spindle, 64, .0003)
        tp.profiled_shell("TOOL_sma_stowage_flange",
                          [(.0155, .028), (.0155, .032), (.0036, .032), (.0036, .028)],
                          ["circle"]*4, m["bright"], spindle)
        label = p.text("TOOL_sma_adapter_id", "SMA", (0, -.0116, .03215),
                       .0025, m["ink"], spindle)
        label["collision_role"] = "visual_detail"
    else:
        for i, (x0, x1, y0, y1) in enumerate(tp.offset_cruciform_rectangles(.0001)):
            p.box("TOOL_captive_offset_wing_" + str(i),
                  ((x0+x1)/2, (y0+y1)/2, .0015),
                  (x1-x0, y1-y0, .003), m["steel"], spindle, 0)
        # Center joins all four offset wings while remaining within the recess.
        p.box("TOOL_captive_offset_tip_core", (0, 0, .0015),
              (.0016, .0016, .003), m["steel"], spindle, 0)
        p.cylinder("TOOL_captive_driver_stem", (0, 0, .017), .0025, .028, m["steel"], spindle, 40, .0001)
        p.cylinder("TOOL_captive_TSA_rear_body", (0, 0, .047), .009,
                   .034, m["silver"], spindle, 64, .0003)
        tp.profiled_shell("TOOL_captive_TSA_identification_ring",
                          [(.010, .058), (.010, .061), (.009, .061), (.009, .058)],
                          ["circle"]*4, m["dark"], spindle)
    result = {"root": root, "spindle_root": spindle, "jaw_roots": jaws, "retention_roots": retainers,
              "handle": handle, "drive_release_root": release,
              "handle_pose_local": tp.matrix_at(0, 0, .115),
              "grasp_pose_local": tp.matrix_at(0, 0, .120), "tip_to_tcp": (0, 0, .120),
              "tip_relative_tcp": (0, 0, -.120), "specifications": tool_specs()[kind],
              "mesh_objects": [o for o in root.children_recursive if o.type in ("MESH", "CURVE")]}
    bpy.context.view_layer.update()
    return result


def set_jaw_offset(tool, radial_m):
    if not -.00005 <= radial_m <= .003:
        raise ValueError("FDV jaw radial offset must be between -0.05 and +3 mm")
    for jaw in tool["jaw_roots"]:
        direction = jaw["radial_direction_parent"]
        jaw.location = [v * radial_m for v in direction]


def set_retention(tool, engaged=True):
    for leaf in tool["retention_roots"]:
        direction = leaf["radial_direction_parent"]
        leaf.location = [v * (0. if engaged else .0006) for v in direction]
