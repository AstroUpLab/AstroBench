# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""MELFI quarter/half-box mixed tray reconstruction from NASA SSP 57000 R and ESA photographs.

Metres; local X is box width, +Y runs from the tray front to the rear, Z is up.
This is an authored reconstruction, not manufacturer CAD.  Box envelope and
lid dimensions follow SSP H-30--H-32; detailed hardware dimensions, tray,
foam, card thickness, hole pitch, and finishes are reconstruction parameters.
"""
import math
import json
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

P = 'MELFI_'
WIDTH=.220
BOTTOM_WIDTH=.075
HEIGHT=.143
SHOULDER=.105
LENGTH=.270
QUARTER_LENGTH=.130
LID_WIDTH=.185
LID_LENGTH=.260
QUARTER_LID_LENGTH=.119
WALL=.001
# Digitized H-31 outline, calibrated to the authoritative H-32 dimensions.
# The 105 mm annotation is not the height of either maximum-width corner.
PROFILE=json.loads(Path(__file__).with_name('reference_profile.json').read_text())
SECTION=[tuple(v/1000 for v in p) for p in PROFILE['section_xz_mm']]
CROWN=[tuple(v/1000 for v in p) for p in PROFILE['crown_outer_xz_mm']]
LID_LEFT=PROFILE['lid']['free_edge_x_mm']/1000
LID_RIGHT=LID_LEFT+LID_WIDTH
DRAWING_AXIS_CANDIDATE=tuple(v/1000 for v in PROFILE['lid']['hinge_axis_xz_candidate_mm'])
# The circular mark in H31 is not dimensioned as the pin axis. Put the working
# pin at the outer lid edge with 3 mm assembly allowance; otherwise the 4.2 mm
# overhang about that mark sweeps downward through the stationary wall.
HINGE_X=LID_RIGHT+.003
HINGE_Z=DRAWING_AXIS_CANDIDATE[1]
LEFT_X=SECTION[-1][0];RIGHT_X=SECTION[2][0]
CROWN=[(LID_LEFT,CROWN[0][1])]+CROWN+[(LID_RIGHT,HINGE_Z)]


def _empty(name, parent=None, loc=(0,0,0)):
    o=bpy.data.objects.new(P+name,None);bpy.context.collection.objects.link(o)
    o.parent=parent;o.location=loc
    return o


def _material(name, color, metallic=0, roughness=.4, finish=None):
    name=P+name
    if name in bpy.data.materials:return bpy.data.materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic;bs.inputs['Roughness'].default_value=roughness
    m.diffuse_color=(*color,1)
    if finish:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        tc=nodes.new('ShaderNodeTexCoord')
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1800
        noise.inputs['Detail'].default_value=2
        if finish=='brushed':
            stretch=nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(1,180,1)
            links.new(tc.outputs['Object'],stretch.inputs[0]);links.new(stretch.outputs[0],noise.inputs['Vector']);noise.inputs['Scale'].default_value=650
            distance=.000004
            if 'Anisotropic IOR Level' in bs.inputs:bs.inputs['Anisotropic IOR Level'].default_value=.32
        else:
            links.new(tc.outputs['Object'],noise.inputs['Vector'])
            distance={'rubber':.000025,'fabric':.00015,'foam':.0005}.get(finish,.000025)
            noise.inputs['Scale'].default_value={'rubber':1500,'fabric':1000,'foam':350}.get(finish,1500)
        bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=distance;bump.inputs['Strength'].default_value=.45
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
        if finish=='fabric':
            waves=[]
            for direction in ('X','Y'):
                wave=nodes.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction=direction;wave.wave_profile='SIN'
                wave.inputs['Scale'].default_value=420;wave.inputs['Distortion'].default_value=.35
                links.new(tc.outputs['Object'],wave.inputs['Vector']);waves.append(wave.outputs['Fac'])
            weave=nodes.new('ShaderNodeMath');weave.operation='MULTIPLY'
            links.new(waves[0],weave.inputs[0]);links.new(waves[1],weave.inputs[1]);links.new(weave.outputs[0],bump.inputs['Height'])
            bump.inputs['Distance'].default_value=.00012;bump.inputs['Strength'].default_value=.6
            if 'Sheen Weight' in bs.inputs:bs.inputs['Sheen Weight'].default_value=.15
        ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=max(.1,roughness-(.012 if finish=='brushed' else .035));ramp.inputs['To Max'].default_value=min(1,roughness+(.012 if finish=='brushed' else .035))
        links.new(noise.outputs['Fac'],ramp.inputs['Value']);links.new(ramp.outputs['Result'],bs.inputs['Roughness'])
    return m


def _mats():
    return dict(
        sheet=_material('perforated_metal_reconstructed',(.57,.60,.62),.87,.30,'brushed'),
        edge=_material('folded_metal_edges',(.64,.67,.69),.9,.27,'brushed'),
        steel=_material('hardware_stainless_finish',(.34,.37,.39),.92,.25,'brushed'),
        dark=_material('black_hook_loop',(.014,.018,.021),0,.85,'fabric'),
        elastic=_material('elastic_retention_webbing',(.49,.48,.40),0,.83,'fabric'),
        foam=_material('ivory_foam_reconstructed',(.72,.71,.63),0,.89,'foam'),
        ink=_material('printed_identification',(.035,.043,.048),0,.64),
        label=_material('identification_label',(.76,.78,.74),0,.65),
        blue=_material('vial_cap_blue',(.14,.27,.37),0,.44,'rubber'),
        glass=_material('clear_sample_vial',(.72,.83,.86),0,.14),
        card=_material('standard_aluminium_card',(.58,.63,.67),.85,.28,'brushed'))


def _mesh(name, verts, faces, mat, parent=None, thickness=0):
    me=bpy.data.meshes.new(P+name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(P+name,me);bpy.context.collection.objects.link(ob);ob.parent=parent
    if mat:me.materials.append(mat)
    if thickness:
        so=ob.modifiers.new('Sheet thickness, 1 mm' if abs(thickness-.001)<1e-7 else 'Sheet thickness','SOLIDIFY')
        so.thickness=thickness;so.offset=0;so.use_even_offset=True
    return ob


def _box(name,loc,size,mat,parent,bevel=.0003):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object;o.name=P+name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.parent=parent;o.location=loc;o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Manufactured corner radius','BEVEL');b.width=bevel;b.segments=3
        n=o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    return o


def _cylinder(name,a,b,radius,mat,parent,vertices=24):
    a=Vector(a);b=Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=(b-a).length)
    o=bpy.context.object;o.name=P+name;o.parent=parent;o.location=(a+b)/2
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    bevel=o.modifiers.new('Small machined edge','BEVEL');bevel.width=min(.00025,radius*.10);bevel.segments=2
    for p in o.data.polygons:p.use_smooth=True
    o.modifiers.new('Cylinder normals','WEIGHTED_NORMAL')
    return o


def _tube(name, points, radius, mat, parent, cyclic=False):
    cu=bpy.data.curves.new(P+name,'CURVE');cu.dimensions='3D';cu.bevel_depth=radius;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    sp.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(P+name,cu);bpy.context.collection.objects.link(ob);ob.parent=parent;cu.materials.append(mat)
    return ob


def _text(name,text,loc,size,mat,parent,rotation=(math.pi/2,0,0),align='CENTER'):
    cu=bpy.data.curves.new(P+name,'FONT');cu.body=text;cu.size=size;cu.align_x=align;cu.extrude=.000025
    ob=bpy.data.objects.new(P+name,cu);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.location=loc;ob.rotation_euler=rotation;cu.materials.append(mat)
    return ob


def _cross(a,b):return a[0]*b[1]-a[1]*b[0]


def _clip_polygon(points, boundary):
    """Clip a convex cell to the CCW convex end-panel boundary."""
    out=points
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        if not out:break
        previous=out[-1];out2=[];edge=(b[0]-a[0],b[1]-a[1])
        for current in out:
            cp=_cross(edge,(previous[0]-a[0],previous[1]-a[1]));cc=_cross(edge,(current[0]-a[0],current[1]-a[1]))
            pin=cp>=-1e-10;cin=cc>=-1e-10
            if cin!=pin:
                t=cp/(cp-cc);out2.append((previous[0]+t*(current[0]-previous[0]),previous[1]+t*(current[1]-previous[1])))
            if cin:out2.append(current)
            previous=current
        out=out2
    clean=[]
    for p in out:
        if not clean or math.dist(p,clean[-1])>1e-8:clean.append(p)
    if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-8:clean.pop()
    return clean


def _inside_margin(point, boundary, margin):
    # General point-in-polygon: H-31 has a re-entrant step at the latch edge.
    # Convex half-plane tests would silently clip that asymmetric shoulder.
    x,y=point;inside=False;nearest=float('inf')
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];dd=dx*dx+dy*dy
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/dd)) if dd else 0
        nearest=min(nearest,math.hypot(x-a[0]-t*dx,y-a[1]-t*dy))
        if (a[1]>y)!=(b[1]>y) and x < a[0]+(y-a[1])*dx/dy:inside=not inside
    return nearest>=margin-1e-10 and (inside or nearest<=max(1e-9,-margin))


def _perforated_sheet(name,boundary,mapper,mat,parent,pitch=(.012,.012),radius=.0036,hole_filter=None,thickness=.001,stagger=False):
    """Real through holes and welded sheet boundaries, including H-31 steps.

    Staggered perforations use a hexagonal tiling; ordinary rectangular cells
    retain the corrected corners needed by the solid top of the sample card.
    Hole size/pitch are reconstructed from the drawings, not OEM tolerances.
    """
    lo=[min(p[i] for p in boundary) for i in range(2)];hi=[max(p[i] for p in boundary) for i in range(2)]
    nx=math.ceil((hi[0]-lo[0])/pitch[0]);ny=math.ceil((hi[1]-lo[1])/pitch[1])
    sx=(lo[0]+hi[0]-nx*pitch[0])/2;sy=(lo[1]+hi[1]-ny*pitch[1])/2
    verts=[];faces=[];holes=0;n=24 if stagger else 16
    concave=any(_cross((b[0]-a[0],b[1]-a[1]),(c[0]-b[0],c[1]-b[1])) < -1e-12 for a,b,c in zip(boundary,boundary[1:]+boundary[:1],boundary[2:]+boundary[:2]))
    # Expanded staggered rows guarantee full coverage at clipped perimeter.
    for iy in range(-1 if stagger else 0,ny+int(stagger)):
        for ix in range(-1 if stagger else 0,nx+int(stagger)):
            cx=sx+(ix+.5+(.5*(iy%2) if stagger else 0))*pitch[0];cy=sy+(iy+.5)*pitch[1]
            outer=[]
            for k in range(n):
                a=2*math.pi*k/n;dx,dy=math.cos(a),math.sin(a)
                if stagger:
                    # Hexagon with vertical sides: corners at (+/-px/2,
                    # +/-py/3) and (0,+/-2py/3). Adjacent rows share edges.
                    t=1/max(abs(dx)/(pitch[0]/2),abs(dy)*1.5/pitch[1]+abs(dx)/pitch[0])
                    outer.append((cx+t*dx,cy+t*dy))
                else:
                    t=1/max(abs(dx),abs(dy))
                    outer.append((cx+t*dx*pitch[0]/2,cy+t*dy*pitch[1]/2))
            # Clip the possibly concave workpiece against the convex cell,
            # not the cell against the concave workpiece.
            clipped=_clip_polygon(boundary,outer) if concave else _clip_polygon(outer,boundary)
            if len(clipped)<3:continue
            hole=_inside_margin((cx,cy),boundary,radius+.0025) and (hole_filter is None or hole_filter(cx,cy))
            whole=all(_inside_margin(p,boundary,-1e-9) for p in outer)
            if hole and whole:
                start=len(verts);verts.extend(mapper(u,v) for u,v in outer)
                verts.extend(mapper(cx+radius*math.cos(2*math.pi*k/n),cy+radius*math.sin(2*math.pi*k/n)) for k in range(n))
                for k in range(n):
                    j=(k+1)%n;faces.append((start+k,start+j,start+n+j,start+n+k))
                holes+=1
            else:
                start=len(verts);verts.extend(mapper(u,v) for u,v in clipped);faces.append(tuple(range(start,start+len(clipped))))
    ob=_mesh(name,verts,faces,mat,parent,thickness)
    ob['true_perforations']=holes;ob['wall_thickness_m']=thickness;ob['hole_pitch_m']=pitch;ob['hole_radius_m']=radius
    ob['hole_pattern']='staggered rows' if stagger else 'rectangular rows'
    return ob


def _crown(x):
    """Piecewise interpolation of the asymmetric H-31 cap, in metres."""
    if x<=CROWN[0][0]:return CROWN[0][1]
    for a,b in zip(CROWN,CROWN[1:]):
        if x<=b[0]:
            t=(x-a[0])/(b[0]-a[0]);return a[1]+t*(b[1]-a[1])
    return CROWN[-1][1]


def _section():return list(SECTION)


def _extruded_polygon(name,polygon,y0,y1,mat,parent):
    n=len(polygon);verts=[(x,y,z) for y in (y0,y1) for x,z in polygon]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return _mesh(name,verts,faces,mat,parent)


def _rivet(name,center,normal,mat,parent,r=.0016):
    c=Vector(center);n=Vector(normal).normalized()
    return _cylinder(name,c-n*.00015,c+n*.00065,r,mat,parent,20)


def _profile_end(name,y,mat,parent):
    """44 real holes at the digitized H-31 centres, not generic triangles."""
    ob=_extruded_polygon(name,_section(),y-WALL/2,y+WALL/2,mat,parent)
    cutters=[]
    for x,z in PROFILE['perforations']['front_hole_centers_xz_mm']:
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.005,depth=.008,location=(x/1000,y,z/1000),rotation=(math.pi/2,0,0))
        cutters.append(bpy.context.object)
    bpy.ops.object.select_all(action='DESELECT')
    for c in cutters:c.select_set(True)
    bpy.context.view_layer.objects.active=cutters[0];bpy.ops.object.join();cut=cutters[0]
    # Work in the box local frame; its parent is not at the world origin.
    cut.parent=parent
    mod=ob.modifiers.new('44 digitized through holes','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut,do_unlink=True)
    ob['true_perforations']=44;ob['wall_thickness_m']=WALL;ob['hole_radius_m']=.005
    ob['hole_pattern']='44 H-31 digitized centres, two asymmetric clusters'
    return ob


def _ribbon(name,points,width,mat,parent):
    # The band runs in XZ; every cross-section lies along Y.
    vertices=[]
    for x,y,z in points:vertices.extend([(x,y-width/2,z),(x,y+width/2,z)])
    ob=_mesh(name,vertices,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],mat,parent,.00065)
    return ob


def _retention(name,root,m,released):
    """Photo-visible band arrangement; small edge mounts are reconstruction."""
    anchor_points=[(.105,0,.094),(LID_LEFT+.006,0,.114)]
    anchors=[]
    for i,(x,y,z) in enumerate(anchor_points):
        a=_empty(name+'_band_edge_anchor_'+str(i),root,(x,y,z));anchors.append(a)
        _box(name+'_band_anchor_backing',(0,0,-.002),(.009 if i==0 else .015,.024,.0012),m['steel'],a,.0003)
        if i==1:
            _box(name+'_band_anchor_mount_return',(-.007,0,-.0005),(.001,.024,.004),m['steel'],a,.00015)
        _tube(name+'_band_anchor_bridge',[(-.004,-.009,-.001),(-.004,-.009,.002),(-.004,.009,.002),(-.004,.009,-.001)],.0007,m['steel'],a)
        for yy in (-.009,.009):_rivet(name+'_band_anchor_rivet',(.002,yy,-.0014),(0,0,1),m['steel'],a,.0011)
        a['source_status']='Edge attachment region from ESA Fig7; small bracket shape and dimensions reconstructed'
    if released:
        # Attached at +X and laid against the inner sloping wall, then loosely
        # folded on the right side of the floor, leaving the card plane clear.
        pts=[(.101,0,.096),(.101,0,.088),(.099,0,.080),(.091,0,.070),(.082,0,.060),(.072,0,.049),(.062,0,.038),(.051,0,.026),(.041,0,.014),(.034,0,.006),(.023,0,.006),(.023,0,.009),(.034,0,.009),(.034,0,.012),(.023,0,.012),(.023,0,.015),(.034,0,.015)]
    else:
        pts=[]
        for i in range(41):
            t=i/40
            pts.append((.101+(LID_LEFT+.002-.101)*t,0,.096+.020*t-.003*math.sin(math.pi*t)))
    band=_ribbon(name+'_manual_card_retention_band',pts,.014,m['elastic'],root)
    # A stitched folded end with a small connector is visible when released.
    end=pts[-1]
    tab=_box(name+'_band_free_end_fold',(end[0]-.003,0,end[2]+.0008),(.010,.014,.0012),m['elastic'],root,.0005)
    connector=_tube(name+'_band_end_connector',[(end[0]+.002,-.005,end[2]+.0015),(end[0]+.007,-.005,end[2]+.0015),(end[0]+.007,.005,end[2]+.0015),(end[0]+.002,.005,end[2]+.0015)],.00065,m['steel'],root)
    for yy in (-.0055,.0055):_tube(name+'_band_end_seam',[(end[0]-.007,yy,end[2]+.0016),(end[0]+.001,yy,end[2]+.0016)],.00011,m['label'],root)
    band['state']='released' if released else 'secured_empty'
    band['operation_note']='Manual elastic band across X, as ESA Fig7. Visible edge mounts/connector are reconstructed; no automatic fastening is shown.'
    band['fixed_endpoint_local']=pts[0];band['free_endpoint_local']=pts[-1]
    return band,anchors,pts


def _sample_box(name,center,parent,m,open_angle,kind):
    if kind not in ('quarter','half'):raise ValueError("MELFI box kind must be quarter or half")
    body_length=QUARTER_LENGTH if kind=='quarter' else LENGTH
    lid_length=QUARTER_LID_LENGTH if kind=='quarter' else LID_LENGTH
    lid_lock_y=-.025 if kind=='quarter' else -.043
    tray_lock_y=.027 if kind=='quarter' else .055
    hinge_leaf_length=lid_length-.008
    root=_empty(name,parent,center);root['asset_basis']='NASA SSP 57000 Rev R H-30--H-32 raster traced outline and ESA Bulletin109 photographs'
    root['envelope_m']=(WIDTH,body_length,HEIGHT);root['wall_thickness_m']=WALL
    root['format']=kind;root['body_length_m']=body_length;root['lid_length_m']=lid_length
    root['hardware_scale']='Unscaled 1 mm sheet, 10 mm end holes and shared latch stock; hardware repetitions and positions depend on box length'
    root['section_xz_m']=[v for point in SECTION for v in point]
    root['profile_accuracy']='Raster reconstruction about 1.5 mm; envelope calibrated to official table'
    ends=[]
    for sign in (-1,1):
        y=sign*(body_length/2-WALL/2);ends.append(_profile_end(name+'_perforated_end_'+str(sign),y,m['sheet'],root))
        # H-31 shows a tall, plain identification area, not a horizontal logo.
        label_poly=[]
        for cx,cz,start in ((.012+.0245-.003,.076+.0595-.003,0),(.012-.0245+.003,.076+.0595-.003,90),(.012-.0245+.003,.076-.0595+.003,180),(.012+.0245-.003,.076-.0595+.003,270)):
            for i in range(9):
                a=math.radians(start+90*i/8);label_poly.append((cx+.003*math.cos(a),cz+.003*math.sin(a)))
        _extruded_polygon(name+'_end_identification_plate',label_poly,y+sign*.0006,y+sign*.0010,m['label'],root)
        for x in (-.033,-.021,.046):
            for z in (.024,.075,.130):_rivet(name+'_end_plate_fastener',(x,y+sign*.00065,z),(0,sign,0),m['steel'],root,.00065)
    _box(name+'_flat_bottom',(0,0,.0005),(BOTTOM_WIDTH,body_length,WALL),m['sheet'],root,.0001)
    # Separate lower slopes use the actual, unequal corner heights.
    for side,a,b in [('left',(-BOTTOM_WIDTH/2,0),(LEFT_X,.065275)),('right',(BOTTOM_WIDTH/2,0),(RIGHT_X,.083949))]:
        dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
        rect=[(-body_length/2,0),(body_length/2,0),(body_length/2,length),(-body_length/2,length)]
        ob=_perforated_sheet(name+'_sloping_side_'+side,rect,lambda y,t,a=a,dx=dx,dz=dz,length=length:(a[0]+dx*t/length,y,a[1]+dz*t/length),m['sheet'],root,pitch=(.011,.011),radius=.0037,hole_filter=lambda y,t:abs(y)<body_length/2-.011 and .009<t<length-.010)
        ob['source_status']='Perforated lower walls visible in H31 side view; repeat pitch extrapolated along the selected box depth'
    # Left vertical flank, then the broad sloping latch shoulder and its step.
    strips=[((LEFT_X,.065275),(LEFT_X,.098081)),((LEFT_X,.098081),(LID_LEFT,.115746)),((LID_LEFT+.0022,.114),(LID_LEFT+.0022,.1172)),((RIGHT_X,.083949),(.111592,.090342)),((.111592,.090342),(.110586,.093875)),((.110586,.093875),(.110586,.0975))]
    for i,(a,b) in enumerate(strips):
        _mesh(name+'_fixed_folded_wall_'+str(i),[(a[0],-body_length/2,a[1]),(b[0],-body_length/2,b[1]),(b[0],body_length/2,b[1]),(a[0],body_length/2,a[1])],[(0,1,2,3)],m['edge'],root,WALL)
    # Fixed cap strips close the official body/lid depth difference:
    # 5 mm per end for half, 5.5 mm per end for quarter. The cap, and its supporting ledge, share the traced curve.
    for sign in (-1,1):
        ys=(sign*lid_length/2,sign*body_length/2)
        verts=[(x,y,z) for x,z in CROWN for y in ys]
        _mesh(name+'_short_end_cap_'+str(sign),verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(CROWN)-1)],m['edge'],root,WALL)
        # Support strips sit inside the sheet normal and stop before the
        # hinge curl/free-edge return, so they cannot clip the rotating cap.
        support_x=[LID_LEFT+.006]+[x for x,z in CROWN if LID_LEFT+.006<x<LID_RIGHT-.014]+[LID_RIGHT-.014]
        verts=[]
        for x in support_x:
            z=_crown(x);eps=.0003;slope=(_crown(x+eps)-_crown(x-eps))/(2*eps)
            normal=Vector((-slope,0,1)).normalized()
            verts.extend((x-normal.x*.0025,y,z-normal.z*.0025) for y in (sign*(lid_length/2-.0025),sign*lid_length/2))
        _mesh(name+'_lid_end_support_ledge_'+str(sign),verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(support_x)-1)],m['edge'],root,WALL)
    for sign in (-1,1):
        _box(name+'_bottom_return_'+str(sign),(sign*(BOTTOM_WIDTH/2-.002),0,.0025),(.004,body_length,.001),m['edge'],root,.00015)
    for x in (-.020,.020):
        _box(name+'_inside_loop_strip',(x,0,.0020),(.015,body_length-.034,.0012),m['dark'],root,.00025)
        _box(name+'_outside_hook_strip',(x,0,-.0008),(.015,body_length-.034,.0010),m['dark'],root,.0002)
    band,anchors,band_points=_retention(name,root,m,open_angle>0)
    lid=_empty(name+'_lid_hinge',root,(HINGE_X,0,HINGE_Z))
    rect=[(LID_LEFT,-lid_length/2),(LID_RIGHT,-lid_length/2),(LID_RIGHT,lid_length/2),(LID_LEFT,lid_length/2)]
    lid_sheet=_perforated_sheet(name+'_curved_perforated_lid',rect,lambda x,y:(x-HINGE_X,y,_crown(x)-HINGE_Z),m['sheet'],lid,pitch=(.011,.011),radius=.0038,hole_filter=lambda x,y:abs(y)<lid_length/2-.012 and LID_LEFT+.010<x<LID_RIGHT-.014)
    # Explicit thickness and separate top/edge normals keep the thin curved
    # sheet smooth; Solidify averaged rim normals can imprint a false grid.
    old=lid_sheet.data;oldverts=[v.co.copy() for v in old.vertices]
    surface_normals=[]
    for v in oldverts:
        x=v.x+HINGE_X;lo=max(LID_LEFT,x-.001);hi=min(LID_RIGHT,x+.001)
        slope=(_crown(hi)-_crown(lo))/max(1e-8,hi-lo)
        surface_normals.append(Vector((-slope,0,1)).normalized())
    n=len(oldverts);basefaces=[tuple(p.vertices) for p in old.polygons]
    edge_count={};edge_direction={}
    for face in basefaces:
        for va,vb in zip(face,face[1:]+face[:1]):
            key=tuple(sorted((va,vb)));edge_count[key]=edge_count.get(key,0)+1;edge_direction[key]=(va,vb)
    faces=basefaces+[tuple(v+n for v in reversed(face)) for face in basefaces]
    for key,count in edge_count.items():
        if count==1:
            va,vb=edge_direction[key];faces.append((va,vb,vb+n,va+n))
    verts=[v+normal*WALL/2 for v,normal in zip(oldverts,surface_normals)]+[v-normal*WALL/2 for v,normal in zip(oldverts,surface_normals)]
    me=bpy.data.meshes.new(lid_sheet.name+'_constant_stock');me.from_pydata(verts,[],faces);me.update()
    me.materials.append(m['sheet']);lid_sheet.data=me
    for mod in list(lid_sheet.modifiers):lid_sheet.modifiers.remove(mod)
    loop_normals=[];count=len(basefaces)
    for i,face in enumerate(me.polygons):
        face.use_smooth=True
        for vertex in face.vertices:
            loop_normals.append(surface_normals[vertex] if i<count else -surface_normals[vertex-n] if i<2*count else face.normal.copy())
    me.normals_split_custom_set(loop_normals)
    lid_sheet['dimension_basis']=f'185 mm projected width, {lid_length*1000:.0f} mm length; asymmetric H31 crown'
    lid_sheet['nominal_length_m']=lid_length;lid_sheet['format']=kind
    # Downward free-edge return follows the left step, not a symmetric rim.
    _box(name+'_lid_free_edge_fold',(LID_LEFT-HINGE_X,0,(_crown(LID_LEFT)+.117)/2-HINGE_Z),(.001,lid_length,_crown(LID_LEFT)-.117),m['edge'],lid,.00015)
    # A piano hinge is visible across the long opposite edge in ESA Fig7.
    _box(name+'_fixed_hinge_leaf',(HINGE_X-.002,0,HINGE_Z-.005),(.010,hinge_leaf_length,.0012),m['steel'],root,.00015)
    # Folded moving leaf follows the underside of the curved sheet. Short
    # rolled tongues connect only its alternating barrels; they are not a
    # floating flat plate or a continuous strip crossing the other barrels.
    moving_a=(-.0045,.0063);moving_b=(-.008,_crown(HINGE_X-.008)-HINGE_Z-.0009)
    _mesh(name+'_moving_hinge_leaf',[(moving_a[0],-hinge_leaf_length/2,moving_a[1]),(moving_b[0],-hinge_leaf_length/2,moving_b[1]),(moving_b[0],hinge_leaf_length/2,moving_b[1]),(moving_a[0],hinge_leaf_length/2,moving_a[1])],[(0,1,2,3)],m['steel'],lid,.0008)
    knuckle_count=math.floor((lid_length-.012)/.008+1e-9)
    knuckle_start=-(knuckle_count*.008-.0006)/2
    for i in range(knuckle_count):
        ya=knuckle_start+i*.008;par=lid if i%2 else root
        xx=0 if par==lid else HINGE_X;zz=0 if par==lid else HINGE_Z
        _cylinder(name+'_hinge_knuckle',(xx,ya,zz),(xx,ya+.0074,zz),.0023,m['steel'],par)
        if par==lid:
            a=(-.00163,.00163);b=moving_a
            verts=[(a[0],ya,a[1]),(b[0],ya,b[1]),(b[0],ya+.0074,b[1]),(a[0],ya+.0074,a[1])]
        else:
            a=(HINGE_X-.00163,HINGE_Z-.00163);b=(HINGE_X-.004,HINGE_Z-.005)
            verts=[(a[0],ya,a[1]),(b[0],ya,b[1]),(b[0],ya+.0074,b[1]),(a[0],ya+.0074,a[1])]
        _mesh(name+'_hinge_leaf_rolled_neck',verts,[(0,1,2,3)],m['steel'],par,.0007)
    _cylinder(name+'_hinge_pin',(HINGE_X,-lid_length/2+.002,HINGE_Z),(HINGE_X,lid_length/2-.002,HINGE_Z),.00085,m['steel'],root)
    rivet_steps=math.floor((hinge_leaf_length/2-.010)/.036+1e-9)
    for yy in [i*.036 for i in range(-rivet_steps,rivet_steps+1)]:_rivet(name+'_hinge_leaf_rivet',(HINGE_X-.005,yy,HINGE_Z-.0043),(0,0,1),m['steel'],root,.0011)
    # Independent lid latch and tray latch stay on the broad -X shoulder.
    # Visible external form is reconstructed; hidden springs/catches are absent.
    lid_lock=_empty(name+'_lid_lock_external',root,(-.091,lid_lock_y,.108))
    lid_lock.rotation_euler.y=-math.atan2(.017665,.028987)
    _box(name+'_lid_latch_backplate',(0,0,0),(.028,.040,.0013),m['steel'],lid_lock,.0005)
    for yy in (-.015,.015):
        _box(name+'_lid_latch_side_cheek',(-.004,yy,.013),(.006,.0014,.006),m['steel'],lid_lock,.0003)
        _cylinder(name+'_lid_latch_short_link',(-.004,yy,.001),(-.004,yy,.013),.0009,m['steel'],lid_lock,16)
        _rivet(name+'_lid_latch_mount',(0,yy,.001),(0,0,1),m['steel'],lid_lock,.0013)
    _cylinder(name+'_lid_latch_lever_pin',(-.004,-.017,.014),(-.004,.017,.014),.0016,m['steel'],lid_lock)
    paddle=_empty(name+'_lid_latch_lift_paddle',lid_lock,(-.004,0,.014))
    paddle['rotation_axis']='Y (local)';paddle['closed_rotation_y_rad']=0.;paddle['open_rotation_y_rad']=math.radians(28)
    paddle.rotation_euler.y=paddle['open_rotation_y_rad'] if open_angle else 0
    lid['latch_paddle_object']=paddle.name
    _box(name+'_lid_latch_lift_plate',(-.006,0,.003),(.023,.029,.0015),m['edge'],paddle,.0012)
    _box(name+'_lid_latch_finger_return',(-.016,0,.006),(.003,.029,.006),m['edge'],paddle,.0005)
    _tube(name+'_lid_latch_bail',[(.002,-.012,.004),(.018,-.012,.006),(.018,.012,.006),(.002,.012,.004)],.001,m['steel'],lid_lock)
    # Keeper follows the moving lid, so the open state has no floating catch.
    _box(name+'_moving_lid_latch_keeper',(LID_LEFT-HINGE_X-.001,lid_lock_y,.120-HINGE_Z),(.005,.021,.002),m['steel'],lid,.0004)
    lid_lock['detail_status']='Lid lever/bail external silhouette from H30/H31 and ESA; internals unmeasured'
    tray_lock=_empty(name+'_tray_lock_external',root,(-.108,tray_lock_y,.093))
    _box(name+'_tray_lock_mount',(.006,0,.002),(.015,.026,.0015),m['steel'],tray_lock,.0005)
    _cylinder(name+'_tray_lock_pivot',(0,-.014,0),(0,.014,0),.0016,m['steel'],tray_lock)
    _mesh(name+'_tray_lock_lower_clip',[(-.012,-.011,-.007),(-.002,-.011,.006),(.007,-.011,.008),(-.012,.011,-.007),(-.002,.011,.006),(.007,.011,.008)],[(0,1,4,3),(1,2,5,4)],m['edge'],tray_lock,.0012)
    _box(name+'_tray_lock_finger_tab',(-.012,0,-.006),(.010,.022,.0015),m['steel'],tray_lock,.0007)
    tray_lock['detail_status']='Separate lower clip at -X, H31 silhouette; format-specific Y location reconstructed'
    # Small plain label stock seen near the lid margin; no invented serial/barcode.
    _box(name+'_lid_small_label',(LID_LEFT+.025-HINGE_X,lid_length/2-.026,_crown(LID_LEFT+.025)-HINGE_Z+.0008),(.021,.009,.00025),m['label'],lid,.0007)
    lid.rotation_euler.y=math.radians(open_angle)
    lid['closed_rotation_y_rad']=0.;lid['open_rotation_y_rad']=math.radians(open_angle if open_angle else 85);lid['hinge_axis']='+Y; lid opens toward +X'
    return dict(root=root,format=kind,body_length_m=body_length,lid_length_m=lid_length,center_local=tuple(center),lid_root=lid,lid_sheet=lid_sheet,lid_lock=lid_lock,tray_lock=tray_lock,
                manual_retention_band=band,perforated_ends=ends,retention_anchors=anchors,lid_latch_paddle=paddle,
                retention_endpoints_local=[band_points[0],band_points[-1]],retention_state=band['state'],
                lid_closed_x_limits=[LID_LEFT,LID_RIGHT],hinge_axis_local=[HINGE_X,0,HINGE_Z])


def set_lid_pose(box_or_lid,angle_degrees):
    """Set an authored visible pose, including the corresponding latch state.

    Accept a returned quarter/half-box dictionary or the saved lid pivot object. This
    is not a solved latch kinematic mechanism; its internals are unmeasured.
    """
    lid=box_or_lid['lid_root'] if isinstance(box_or_lid,dict) else box_or_lid
    lid.rotation_euler.y=math.radians(angle_degrees)
    name=lid.get('latch_paddle_object')
    if name and name in bpy.data.objects:
        paddle=bpy.data.objects[name]
        paddle.rotation_euler.y=paddle['closed_rotation_y_rad'] if abs(angle_degrees)<1e-6 else paddle['open_rotation_y_rad']
    bpy.context.view_layer.update()


def create_vial_card(origin=(0,0,0),name='VialCard'):
    """100 x 110 mm aluminium card, XZ plane, with a bare upper grasp area.

    Plate thickness 2 mm and its partial four-vial layout are reconstruction
    parameters. The official source specifies the 100 x 110 mm card size and
    elastic vial loops, not thickness or this deliberately sparse arrangement.
    """
    m=_mats();root=_empty(name,loc=origin)
    # Only lower attachment rows are perforated. The top 25 mm remains bare.
    rect=[(-.050,-.055),(.050,-.055),(.050,.055),(-.050,.055)]
    plate=_perforated_sheet(name+'_aluminium_plate',rect,lambda x,z:(x,0,z),m['card'],root,pitch=(.020,.026),radius=.0013,hole_filter=lambda x,z:-.030<z<.005,thickness=.002)
    for i,x in enumerate((-.030,-.010,.010,.030)):
        # Small 2--10 ml class vials; chosen dimensions are reconstructed.
        _cylinder(name+'_vial_body_'+str(i),(x,-.008,-.039),(x,-.008,.007),.006,m['glass'],root,40)
        _cylinder(name+'_vial_bottom_'+str(i),(x,-.008,-.040),(x,-.008,-.037),.0056,m['glass'],root,32)
        _cylinder(name+'_vial_cap_'+str(i),(x,-.008,.006),(x,-.008,.016),.0066,m['blue'],root,32)
        # Cap grip ridges are actual narrow relief.
        for k in range(18):
            angle=2*math.pi*k/18
            _cylinder(name+'_cap_rib',(x+.0066*math.cos(angle),-.008+.0066*math.sin(angle),.007),(x+.0066*math.cos(angle),-.008+.0066*math.sin(angle),.015),.00022,m['blue'],root,8)
        for z in (-.026,0):
            points=[]
            for k in range(41):
                a=math.pi*k/40
                points.append((x-.010*math.cos(a),-.001-.0145*math.sin(a),z))
            _tube(name+'_elastic_vial_loop',points,.00065,m['elastic'],root)
        _box(name+'_vial_white_id',(x,-.0141,-.021),(.008,.0003,.017),m['label'],root,.0003)
        _text(name+'_vial_number',str(i+1),(x,-.0145,-.022),.004,m['ink'],root)
    _text(name+'_card_id','MELFI  /  SAMPLE CARD',(0,-.0011,-.050),.0033,m['ink'],root)
    root['source_card_size_m']=(.100,.110)
    root['thickness_m']=.002;root['thickness_basis']='Reconstruction parameter; source does not specify card thickness.'
    root['vial_count']=4;root['upper_unloaded_grasp_zone_m']=.025
    root['retention']='Vials attached to aluminium card by elastic loops; no invented robotic handle.'
    root['source']='ESA Bulletin 109 February 2002 p40, standard vial card 10 x 11 cm'
    return {'root':root,'plate':plate,'grasp_local':(0,0,.060),'plate_name':plate.name,'thickness_m':.002,'width_m':.100,'height_m':.110,'grasp_zone_m':.025}


def _tray_carrier_lattice(tray,m):
    """Paired triangular lightening openings visible in the H-29 empty tray.

    Their existence/layout is photographic; pitch, fillets and stock are not
    dimensioned. Panels support the two lower slopes without filling the mouth.
    """
    out=[]
    for side,a,b in [('left',(-.038,.006),(LEFT_X-.002,.073)),('right',(.038,.006),(RIGHT_X+.002,.091))]:
        delta=Vector((b[0]-a[0],0,b[1]-a[1]));length=delta.length;axis=delta.normalized()
        normal=Vector((axis.z,0,-axis.x));normal*=(-1 if side=='left' else 1)
        def co(y,t,d=0):return Vector((a[0],y,a[1]))+axis*t+normal*d
        host=_mesh('Tray_'+side+'_triangular_carrier',[co(-.024,0),co(.570,0),co(.570,length),co(-.024,length)],[(0,1,2,3)],m['steel'],tray,.0015)
        bpy.context.view_layer.objects.active=host
        bpy.ops.object.modifier_apply(modifier=host.modifiers[0].name)
        cutters=[]
        for i in range(8):
            ya=-.012+i*.070;yb=ya+.063
            tri=[(ya,.009),(yb,.009),((ya+yb)/2,length-.009)] if i%2==0 else [(ya,length-.009),(yb,length-.009),((ya+yb)/2,.009)]
            verts=[co(y,t,d) for d in (-.006,.006) for y,t in tri]
            cutters.append(_mesh('temporary_lattice_triangle',verts,[(2,1,0),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],None,tray))
        bpy.ops.object.select_all(action='DESELECT')
        for ob in cutters:ob.select_set(True)
        bpy.context.view_layer.objects.active=cutters[0];bpy.ops.object.join();cut=cutters[0]
        mod=host.modifiers.new('Eight triangular weight relief openings','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
        bpy.context.view_layer.objects.active=host;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
        host['triangular_openings']=8;host['source_status']='SSP H29 visible paired rows of triangular openings; exact pitch and stock estimated'
        out.append(host)
    return out


def build(origin=(0,0,0),box_angles=(0,0,85)):
    """Two 130 mm quarter boxes and one 270 mm half box on one tray.

    The format order is quarter, quarter, half along local +Y; box centres are
    70, 210, 420 mm. Each adjacent pair has a nominal 10 mm assembly gap.
    No part is non-uniformly scaled: stock, hole diameters and latch hardware
    retain the real size while longitudinal panels and repeats are rebuilt.
    All parts descend from a single root, so the carrier can be mounted with
    its long axis parallel to a wall. Angles are individual lid poses.
    """
    if len(box_angles)!=3:raise ValueError('Exactly three lid angles are required')
    m=_mats();root=_empty('Assembly',loc=origin);tray=_empty('Tray',root)
    root['asset_status']='Dimensioned photographic reconstruction, not OEM CAD or a scanned asset'
    root['source']='NASA SSP 57000 Rev R 2015 H-30--H-32; ESA Bulletin 109 2002 pp40--41'
    root['official_shared_dimensions_m']=(WIDTH,BOTTOM_WIDTH,HEIGHT,SHOULDER,LID_WIDTH,WALL)
    root['official_quarter_body_lid_length_m']=(QUARTER_LENGTH,QUARTER_LID_LENGTH)
    root['official_half_body_lid_length_m']=(LENGTH,LID_LENGTH)
    root['box_format_order']='quarter, quarter, half';root['box_lid_angles_deg']=list(box_angles)
    root['tray_and_foam_dimensions']='Photograph-based estimates; no source dimension claim'
    # Narrow bottom and folded longitudinal carrier rails follow box section.
    _box('Tray_bottom',(0,.272,-.0015),(.082,.594,.003),m['edge'],tray,.0003)
    for sign in (-1,1):
        _box('Tray_folded_floor_rail',(sign*.040,.272,.003),(.003,.594,.008),m['steel'],tray,.0003)
        _box('Tray_slide_runner',(sign*.047,.272,-.003),(.008,.594,.007),m['steel'],tray,.0003)
    carrier_lattice=_tray_carrier_lattice(tray,m)
    for y in (-.018,.140,.280,.564):
        verts=[(-.043,y,0),(LEFT_X-.004,y,.072),(RIGHT_X+.004,y,.091),(.043,y,0)]
        # Discrete U-shaped cradle straps, not solid plates closing access.
        _tube('Tray_cradle_strap',[verts[0],verts[1]],.002,m['steel'],tray)
        _tube('Tray_cradle_strap',[verts[2],verts[3]],.002,m['steel'],tray)
    centres=[(0,.070,.010),(0,.210,.010),(0,.420,.010)]
    formats=['quarter','quarter','half']
    names=['Front_quarter_box','Middle_quarter_box','Rear_half_box']
    boxes=[_sample_box(name,center,tray,m,angle,kind) for name,center,angle,kind in zip(names,centres,box_angles,formats)]
    front,middle,rear=boxes
    # Compatibility aliases denote physical near/far boxes; use active_box
    # for the open half box when constructing robot approach paths.
    near=front;far=rear
    # Front block: the photographs show a solid insulation face and small
    # fittings, not the large through hand-hole/U-handle used in the v3 sketch.
    # A convex envelope removes the box's metal latch step from the soft shell.
    points=sorted(set(_section()))
    lower=[];upper=[]
    for point in points:
        while len(lower)>=2 and _cross((lower[-1][0]-lower[-2][0],lower[-1][1]-lower[-2][1]),(point[0]-lower[-1][0],point[1]-lower[-1][1]))<=0:lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper)>=2 and _cross((upper[-1][0]-upper[-2][0],upper[-1][1]-upper[-2][1]),(point[0]-upper[-1][0],point[1]-upper[-1][1]))<=0:upper.pop()
        upper.append(point)
    foam_poly=lower[:-1]+upper[:-1]
    # ESA Fig6 shows a continuous insulation-to-first-box joint. Align the
    # block with the sample-box section (+10 mm in Z) and extend only its
    # reconstructed rear portion; the published quarter/half boxes stay fixed.
    # Rear edge +3.7 mm leaves 0.5 mm to the nearest front fastener (+4.2 mm).
    foam_root=_empty('Front_insulation_assembly',tray,(0,0,centres[0][2]))
    foam_rear_y=.0037
    foam=_extruded_polygon('Front_insulation_foam',foam_poly,-.082,foam_rear_y,m['foam'],foam_root)
    foam['dimensions_basis']='ESA Fig6 continuous end-block joint; 85.7 mm depth is reconstructed, not an official manufacturing dimension'
    foam['joint_rear_y_in_tray_m']=foam_rear_y
    foam['section_z_offset_m']=centres[0][2]
    # Integral, concealed lower seat bears directly on the tray floor. Its
    # narrow 70 mm width clears the existing rails; no carrier is penetrated.
    foam_foot=_box('Front_insulation_lower_seat',(0,(-.023+foam_rear_y)/2,.005),
                   (.070,foam_rear_y+.023,.010),m['foam'],tray,.0003)
    foam_foot['source_status']='Concealed mounting seat reconstructed to join insulation to existing tray floor; not exposed source hardware'
    foam_foot['bearing_surface_z_in_tray_m']=0.
    foam_foot['upper_surface_z_in_tray_m']=.010
    # The dark hairline visible in Fig6 is represented only as a joint edge;
    # its material or hidden sealing mechanism is not specified in the source.
    rear_seam=_tube('Insulation_rear_joint_edge',[(x,.0041,z) for x,z in foam_poly],.0004,m['dark'],foam_root,True)
    rear_seam['source_status']='Thin visible Fig6 joint line; nominal 0.5 mm box clearance, material reconstructed'
    skin=_material('insulation_thin_outer_skin',(.76,.75,.68),0,.60,'rubber')
    _extruded_polygon('Front_insulation_face_skin',foam_poly,-.083,-.0822,skin,foam_root)
    _tube('Insulation_skin_seam',[(x,-.0833,z) for x,z in foam_poly],.00045,m['elastic'],foam_root,True)
    for x,z in ((-.058,.104),(.060,.030)):
        _cylinder('Insulation_round_plug_seat',(x,-.0839,z),(x,-.0847,z),.0085,m['foam'],foam_root,36)
        _cylinder('Insulation_round_plug',(x,-.0848,z),(x,-.0862,z),.0068,skin,foam_root,36)
    brass=_material('front_small_fitting_finish',(.36,.29,.14),.75,.34,'brushed')
    handle=_empty('Tray_front_pull_handle',foam_root,(.004,-.084,.067))
    _box('Front_small_fitting_mount',(0,0,0),(.018,.0015,.021),brass,handle,.001)
    _box('Front_small_pull_tab',(0,-.004,.001),(.009,.0015,.013),m['steel'],handle,.001)
    for zz in (-.006,.006):_rivet('Front_small_fitting_screw',(0,-.001,zz),(0,-1,0),m['steel'],handle,.0013)
    handle['dimension_basis']='Small visible front fitting reconstructed from ESA Fig6; no large hand aperture or robotic interface'
    dims={'box_length_m':LENGTH,'box_lengths_m':[QUARTER_LENGTH,QUARTER_LENGTH,LENGTH],'lid_lengths_m':[QUARTER_LID_LENGTH,QUARTER_LID_LENGTH,LID_LENGTH],'quarter_box_length_m':QUARTER_LENGTH,'quarter_lid_length_m':QUARTER_LID_LENGTH,'nominal_inter_box_gap_m':.010,'tray_floor_length_m':.594,'insulation_rear_y_m':foam_rear_y,'insulation_depth_m':.082+foam_rear_y,'insulation_section_z_offset_m':.010,'insulation_nominal_joint_clearance_m':.0005,'box_max_width_m':WIDTH,'box_bottom_width_m':BOTTOM_WIDTH,'box_max_height_m':HEIGHT,'box_d_height_annotation_m':SHOULDER,'lid_width_m':LID_WIDTH,'lid_length_m':LID_LENGTH,'wall_approx_m':WALL}
    source={'envelope_and_lid':'NASA SSP 57000 Rev R H-30--H-32, official quarter and half-box dimensions',
            'shape_and_hardware':'SSP H31 raster trace and ESA Bulletin109 native photos; visible-part reconstruction with right hinge, left two distinct locks',
            'not_dimensioned':['tray overall size','foam depth and handle details','hinge and latch internals','perforation pitch','metal alloy/finish'],
            'crown':'Digitized asymmetric H31 profile, calibrated to 220 x 143 mm; raster uncertainty about 1.5 mm',
            'sample_card':'100x110 mm from ESA; 2 mm thickness and partial loading reconstructed',
            'band':'ESA Fig7 across-X band; open box released with fixed attachment, free connector on floor; small mounts reconstructed',
            'label':'Plain tall end-panel identification stock; no invented serial number or OEM logo',
            'profile_file':'reference_profile.json',
            'insulation_joint':'ESA Fig6 continuous white end-block to first box; reconstructed depth extended85.7mm, section raised10mm to match boxes; thin joint edge and hidden tray seat are reconstruction details',
            'working_hinge':'Axis placed 3mm outside right lid edge for assembled rotation; H31 circular mark is retained separately as an unconfirmed axis candidate'}
    bpy.context.view_layer.update()
    return {'root':root,'tray_root':tray,'box_root':near['root'],'lid_root':near['lid_root'],
            'box_center_local':centres[0],'box_opening_top_local':(0,centres[0][1],.010+HEIGHT),
            'boxes':boxes,'front_box':front,'middle_box':middle,'rear_box':rear,'active_box':rear,'active_box_center_local':centres[2],
            'box_formats':formats,'box_lengths_m':[b['body_length_m'] for b in boxes],'lid_lengths_m':[b['lid_length_m'] for b in boxes],
            'near_box':near,'far_box':far,'near_lid_root':near['lid_root'],'far_lid_root':far['lid_root'],
            'tray_handle':handle,'insulation_foam':foam,'insulation_root':foam_root,'insulation_lower_seat':foam_foot,'insulation_rear_joint_edge':rear_seam,'carrier_lattice':carrier_lattice,'dimensions':dims,'source_report':source,
            'box_centres_local':centres,'tray_axis':'+Y',
            'lid_open_direction':'+X, rotation about local +Y; individual box_angles in degrees',
            'profile':PROFILE,'drawing_axis_candidate_local':[DRAWING_AXIS_CANDIDATE[0],0,DRAWING_AXIS_CANDIDATE[1]],'lid_closed_x_limits':[LID_LEFT,LID_RIGHT],'hinge_axis_local':[HINGE_X,0,HINGE_Z]}
