# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Original MELFI wall mount and floor pedestal geometry, in metres."""
import math
from geometry_supports import box, bolt, cylinder, material, label, tube
BASE=(-.25,-.60,.85)
WALL_Y=-.029108
FLOOR_Z=.11655

def mounting_frame():
    """Benchmark mounting adapter, visibly separate from referenced payload."""
    metal = material("Adapter brushed structural metal", (.32, .38, .43), .75, .36)
    white = material("Adapter off white powder coat", (.6, .64, .65), .2, .5)
    dark = material("Adapter fasteners", (.04, .045, .05), .5, .4)
    box("Benchmark tray adapter wall plate", (-.05, WALL_Y-.006, .98),
        (.69, .012, .24), white, .003)
    for x in (-.27, .17):
        box("Benchmark tray adapter short bracket", (x, -.1935, 1.001),
            (.030, .305, .026), metal, .003)
        tube("Benchmark tray adapter diagonal brace",
             [(x, WALL_Y-.018, .88), (x, -.295, .984)], .009, metal)
        for z in (.90, 1.065):
            bolt("Benchmark tray adapter wall bolt", (x, WALL_Y-.014, z), dark)
    for y in (-.290, -.155):
        box("Benchmark tray adapter cross rail", (-.05, y, 1.016),
            (.60, .022, .012), metal, .002)
    label("Adapter label", "MELFI / MIXED SAMPLE TRAY",
          (-.21, WALL_Y-.014, .925), .010, dark)

def floor_pedestal():
    """Ground-supported robot mount. Plate bottom matches the imported cabin floor."""
    metal = material("Pedestal brushed aluminium", (.32, .37, .40), .8, .34)
    white = material("Pedestal powder coat", (.70, .73, .72), .2, .44)
    dark = material("Pedestal hardware", (.035, .04, .045), .5, .38)
    x, y, z = BASE
    box("Floor pedestal base plate", (x, y, FLOOR_Z+.0125), (.30, .30, .025), metal, .006)
    bottom, top = FLOOR_Z+.025, z-.027
    cylinder("Floor pedestal support column", (x, y, (bottom+top)/2),
             .066, top-bottom, white, vertices=64)
    cylinder("Floor pedestal lower collar", (x, y, bottom+.015), .087, .030, metal)
    box("Floor pedestal upper mounting flange", (x, y, z-.0135),
        (.215, .21, .027), metal, .006)
    for dx in (-.114, .114):
        for dy in (-.114, .114):
            cylinder("Floor pedestal foundation washer", (x+dx,y+dy,FLOOR_Z+.026),
                     .010,.002,dark)
            bolt("Floor pedestal foundation screw", (x+dx,y+dy,FLOOR_Z+.0285),dark,axis="Z")
    for dx in (-.082, .082):
        for dy in (-.080, .080):
            bolt("Floor pedestal recessed top screw", (x+dx,y+dy,z-.002),dark,axis="Z")
    tube("Floor pedestal cable loom",
         [(x-.075,y,z-.025),(x-.079,y,.55),(x-.081,y,FLOOR_Z+.075),
          (x-.12,y-.045,FLOOR_Z+.035)], .009, dark)
    label("Floor pedestal identification", "ASTROBENCH\nFIXED BASE",
          (x-.038, y-.067, .48), .010, dark)

