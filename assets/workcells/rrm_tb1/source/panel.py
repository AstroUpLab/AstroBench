# Copyright 2026 AstroUpLab. SPDX-License-Identifier: Apache-2.0
"""Editable RRM Task Board 1 reconstruction in the portrait reference orientation.

Local XY is the plate plane; +Y is the top, +Z faces the operator. The front
plate is at Z=0 and the rear at -plate_thickness. 400x530x6 mm are configurable
reconstruction estimates, not NASA drawing dimensions. No hidden thread pitch,
release mechanism, or operational success criteria are asserted here.
"""
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

P='RRM_TB1_'


def empty(name,parent=None,loc=(0,0,0)):
 o=bpy.data.objects.new(P+name,None);bpy.context.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def material(name,color,metal=0,rough=.4,finish=None):
 key=P+name
 if key in bpy.data.materials:return bpy.data.materials[key]
 m=bpy.data.materials.new(key);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;m.diffuse_color=(*color,1)
 if finish:
  tex=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=550;noise.inputs['Detail'].default_value=2
  if finish=='brushed':
   stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(1,65,1);l.new(tex.outputs['Object'],stretch.inputs[0]);l.new(stretch.outputs[0],noise.inputs['Vector'])
   if 'Anisotropic IOR Level' in bs.inputs:bs.inputs['Anisotropic IOR Level'].default_value=.35
  else:l.new(tex.outputs['Object'],noise.inputs['Vector'])
  bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value={'brushed':.000004,'foil':.00007,'paint':.000015}.get(finish,.000006);bump.inputs['Strength'].default_value=.32;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
  if finish=='foil':
   # Thin amber film: small wrinkles change the reflected light, not a
   # painted mottled colour. Keep the effect below the machining scale.
   noise.inputs['Scale'].default_value=22;noise.inputs['Roughness'].default_value=.7
   wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='DIAGONAL';wave.inputs['Scale'].default_value=70;wave.inputs['Distortion'].default_value=7;wave.inputs['Detail'].default_value=2;l.new(tex.outputs['Object'],wave.inputs['Vector'])
   mix=n.new('ShaderNodeMath');mix.operation='MULTIPLY';l.new(wave.outputs['Color'],mix.inputs[0]);l.new(noise.outputs['Fac'],mix.inputs[1]);l.new(mix.outputs[0],bump.inputs['Height'])
   bump.inputs['Distance'].default_value=.000055;bump.inputs['Strength'].default_value=.38
   sheen=n.new('ShaderNodeValToRGB');sheen.color_ramp.elements[0].position=.15;sheen.color_ramp.elements[0].color=(.095,.095,.095,1);sheen.color_ramp.elements[1].position=.85;sheen.color_ramp.elements[1].color=(.24,.24,.24,1);l.new(noise.outputs['Fac'],sheen.inputs['Fac']);l.new(sheen.outputs['Color'],bs.inputs['Roughness'])
   bs.inputs['Coat Weight'].default_value=.25;bs.inputs['Coat Roughness'].default_value=.12
 if name in ('black_label_ink','black_thermal_coating'):
  bs.inputs['Specular IOR Level'].default_value=.12
 return m

def materials():
 return {'plate':material('warm_anodized_plate',(.53,.54,.50),.70,.34,'brushed'),
  'silver':material('machined_aluminium',(.55,.58,.60),.90,.28,'brushed'),
  'bright':material('nickel_connector_finish',(.66,.68,.70),.95,.20,'brushed'),
  'steel':material('stainless_fastener',(.34,.36,.38),.92,.25,'brushed'),
  'dark':material('black_anodized_adapter',(.022,.026,.028),.65,.36,'brushed'),
  'black':material('black_thermal_coating',(.003,.004,.005),.03,.72,'paint'),
  'kapton':material('amber_polyimide_film',(.42,.17,.025),.65,.17,'foil'),
  'gold':material('gold_SMA_plating',(.67,.46,.14),.87,.23,'brushed'),
  'white':material('white_identification_stock',(.82,.83,.78),0,.63),
  'ink':material('black_label_ink',(.001,.001,.001),0,.85),
  'gasket':material('dark_interface_ring',(.028,.031,.033),0,.78),
  'grey':material('grey_placeholder_coupon',(.18,.19,.18),.65,.44,'brushed')}

def mesh(name,verts,faces,mat,parent=None):
 me=bpy.data.meshes.new(P+name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(P+name,me);bpy.context.collection.objects.link(o);o.parent=parent
 if mat:me.materials.append(mat)
 return o

def bevel(o,r=.0005,segments=3):
 if r:
  b=o.modifiers.new('Machined edge radius','BEVEL');b.width=r;b.segments=segments
  o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
 return o

def box(name,loc,size,mat,parent=None,r=.0004):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=P+name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.parent=parent;o.location=loc;o.data.materials.append(mat);return bevel(o,r)

def rounded_plate(name,w,h,z0,z1,r,mat,parent,center=(0,0)):
 points=[]
 for cx,cy,start in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
  for i in range(9):
   a=math.radians(start+90*i/8);points.append((center[0]+cx+r*math.cos(a),center[1]+cy+r*math.sin(a)))
 n=len(points);v=[(x,y,z) for z in (z0,z1) for x,y in points];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return bevel(mesh(name,v,f,mat,parent),min(.0004,(z1-z0)/4))

def cylinder(name,loc,radius,depth,mat,parent=None,vertices=48,edge=.0003):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth);o=bpy.context.object;o.name=P+name;o.parent=parent;o.location=loc;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return bevel(o,edge)

def ring(name,loc,outer,inner,depth,mat,parent=None,n=64):
 verts=[(loc[0]+r*math.cos(2*math.pi*i/n),loc[1]+r*math.sin(2*math.pi*i/n),loc[2]+z) for z in (-depth/2,depth/2) for r in (outer,inner) for i in range(n)]
 faces=[]
 for i in range(n):
  j=(i+1)%n;faces.extend([(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),(i,n+i,n+j,j),(2*n+j,3*n+j,3*n+i,2*n+i)])
 o=mesh(name,verts,faces,mat,parent)
 for p in o.data.polygons:p.use_smooth=p.index%4<2
 return bevel(o,min(.00015,depth/5))

def lathe_shell(name,profile,mat,parent,n=64):
 # A closed radial cross-section makes a true open-bottom cup. Axis points
 # are single vertices; no coincident triangles or fake black cavity disk.
 verts=[];rings=[]
 for r,z in profile:
  if abs(r)<1e-9:rings.append([len(verts)]);verts.append((0,0,z))
  else:
   rings.append(list(range(len(verts),len(verts)+n)))
   verts.extend((r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n))
 faces=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(n):
   j=(i+1)%n
   faces.append((a[0],b[j],b[i]) if len(a)==1 else (a[i],a[j],b[0]) if len(b)==1 else (a[i],a[j],b[j],b[i]))
 ob=mesh(name,verts,faces,mat,parent)
 for poly in ob.data.polygons:poly.use_smooth=True
 return ob

def tube(name,pts,radius,mat,parent):
 cu=bpy.data.curves.new(P+name,'CURVE');cu.dimensions='3D';cu.bevel_depth=radius;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 ob=bpy.data.objects.new(P+name,cu);bpy.context.collection.objects.link(ob);ob.parent=parent;cu.materials.append(mat);return ob

def text(name,value,loc,size,mat,parent,angle=0,align='CENTER'):
 cu=bpy.data.curves.new(P+name,'FONT');cu.body=value;cu.size=size;cu.align_x=align;cu.align_y='CENTER';cu.extrude=.000015;ob=bpy.data.objects.new(P+name,cu);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.location=loc;ob.rotation_euler.z=angle;cu.materials.append(mat);return ob

def label(name,value,xy,w,h,size,m,parent,angle=0):
 root=empty(name,parent,(*xy,.0004));root.rotation_euler.z=angle
 rounded_plate(name+'_stock',w,h,-.00015,.00015,.001,m['white'],root)
 text(name+'_print',value,(0,0,.00018),size,m['ink'],root)
 return root

def screw(name,xy,z,m,parent,r=.0025,slot=False):
 ring(name+'_washer',(*xy,z+.0004),r*1.30,r*.55,.0007,m['steel'],parent)
 head=cylinder(name+'_head',(*xy,z+.0015),r,.0024,m['steel'],parent,32,.00025)
 if slot:box(name+'_driver_slot',(*xy,z+.00275),(r*1.6,.00055,.00015),m['dark'],parent,.0001)
 else:
  cylinder(name+'_hex_socket_shadow',(*xy,z+.00272),r*.48,.00018,m['dark'],parent,6,.00005)
 return head

def mount(name,xy,m,parent):
 root=empty(name,parent,(*xy,0))
 cylinder(name+'_base',(0,0,.0025),.027,.005,m['steel'],root)
 ring(name+'_flange',(0,0,.008),.025,.011,.009,m['silver'],root)
 cylinder(name+'_stepped_hub',(0,0,.016),.016,.012,m['silver'],root)
 ring(name+'_socket_collar',(0,0,.024),.012,.0075,.007,m['bright'],root)
 cylinder(name+'_socket_dark',(0,0,.022),.0072,.005,m['dark'],root,6,.00005)
 for a in (45,135,225,315):
  q=math.radians(a);screw(name+'_mount_screw',(.020*math.cos(q),.020*math.sin(q)),.0125,m,root,.0024)
 root['source_status']='Visible stepped board mounting head reconstructed from NASA TB1 figures; hidden latch unmodelled'
 return root

def safety_cap(name,xy,tall,m,parent):
 root=empty(name+'_fixed',parent,(*xy,0))
 base=rounded_plate(name+'_square_flange',.043,.043,0,.004,.004,m['steel'],root)
 for x in (-.016,.016):
  for y in (-.016,.016):screw(name+'_flange_screw',(x,y),.004,m,root,.0025)
 cylinder(name+'_mounting_neck',(0,0,.0075),.017,.007,m['dark'],root)
 cylinder(name+'_fixed_socket',(0,0,.016),.011,.013,m['bright'],root)
 ring(name+'_socket_top_land',(0,0,.0226),.0105,.004,.0008,m['bright'],root)
 cylinder(name+'_socket_recess',(0,0,.0227),.0038,.0003,m['dark'],root,32,.00005)
 ring(name+'_seal_visible',(0,0,.0114),.0145,.0106,.0012,m['gasket'],root)
 cap=empty(name+'_removable_cap',root,(0,0,.012))
 height=.055 if tall else .026
 profile=[(.0145,0),(.0145,height-.006),(.0141,height-.003),(.0125,height-.001),(.009,height),(0,height),(0,height-.0018),(.0085,height-.0018),(.0117,height-.003),(.0127,height-.006),(.0127,.003),(.0127,0)]
 shell=lathe_shell(name+'_hollow_cap_shell',profile,m['silver'],cap)
 shell['open_bottom_inner_radius_m']=.0127;shell['nominal_radial_wall_m']=.0018
 shell['source_status']='Photo-visible outer cap; hidden cavity reconstructed with clearance around fixed socket, no invented helical threads'
 # Two separate machined rims and fine axial grip marks visible near the base.
 ring(name+'_cap_base_rim',(0,0,.003),.0154,.014,.003,m['bright'],cap)
 ring(name+'_cap_top_rim',(0,0,height-.003),.0147,.0139,.0012,m['silver'],cap)
 if not tall:
  cylinder(name+'_hex_drive',(0,0,height+.002),.0078,.006,m['steel'],cap,6,.0006)
 for k in range(24):
  a=2*math.pi*k/24
  tube(name+'_fine_grip_mark',[(.01465*math.cos(a),.01465*math.sin(a),.004),(.01465*math.cos(a),.01465*math.sin(a),.008)],.00012,m['steel'],cap)
 cap['rotation_axis_local']=(0,0,1);cap['translation_axis_local']=(0,0,1);cap['closed_position_local']=(0,0,.012)
 cap['thread_pitch']='Not specified by the available source; no helical constraint authored'
 cap['task_role']='Independent removable protective cap, no safety wire in this TB1 location'
 root['component_label']=name
 return {'root':root,'fixed_socket':bpy.data.objects[P+name+'_fixed_socket'],'cap_root':cap,'axis_local':(0,0,1),'closed_position_local':(0,0,.012),'visual_cap_height_m':height,'hollow_shell':shell,'inner_radius_m':.0127,'fixed_socket_radius_m':.011}

def stowage_adapter(name,xy,m,parent):
 root=empty(name,parent,(*xy,0))
 cylinder(name+'_flange',(0,0,.004),.025,.008,m['steel'],root)
 for a in (45,135,225,315):
  q=math.radians(a);screw(name+'_flange_screw',(.018*math.cos(q),.018*math.sin(q)),.008,m,root,.0024)
 cylinder(name+'_dark_shaft',(0,0,.032),.013,.048,m['dark'],root)
 ring(name+'_lower_band',(0,0,.013),.014,.0125,.0025,m['bright'],root)
 cylinder(name+'_stepped_tip',(0,0,.062),.0085,.012,m['bright'],root)
 for z in (.059,.062,.065):ring(name+'_tip_turned_groove',(0,0,z),.0089,.0081,.00065,m['steel'],root)
 cylinder(name+'_tip_face',(0,0,.070),.0068,.004,m['steel'],root,12,.00035)
 return root

def fiducial(name,xy,m,parent):
 root=empty(name,parent,(*xy,0))
 rounded_plate(name+'_support',.052,.0636,0,.007,.0025,m['silver'],root)
 rounded_plate(name+'_black_target',.045,.056,.007,.0074,.001,m['ink'],root)
 ring(name+'_outer_ring',(0,0,.00765),.0125,.011,.0002,m['white'],root)
 ring(name+'_inner_ring',(0,0,.00765),.0048,.0039,.0002,m['white'],root)
 for axis in (0,1):
  size=(.031,.0007,.00018) if axis==0 else (.0007,.035,.00018)
  box(name+'_crosshair',(0,0,.00765),size,m['white'],root,.00005)
 for x in (-.0185,.0185):
  for y in (-.023,.023):
   cylinder(name+'_white_corner',(x,y,.00765),.0032,.0002,m['white'],root,24,.00005)
   screw(name+'_corner_screw',(x,y),.008,m,root,.0012)
 root['source_status']='NASA hardware optical target geometry; unreadable RTP numbers deliberately omitted'
 return root

def sma_array(xy,m,parent):
 root=empty('SMA_nine_cap_array',parent,(*xy,0))
 frame=rounded_plate('SMA_array_housing',.124,.1166,0,.036,.006,m['silver'],root)
 cutter=rounded_plate('temporary_array_well',.098,.0906,.004,.050,.005,m['silver'],root)
 bpy.context.view_layer.objects.active=frame
 mod=frame.modifiers.new('Actual recessed connector well','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 for x in (-.054,.054):
  for y in (-.050,.050):screw('SMA_array_corner_screw',(x,y),.036,m,root,.0017)
 caps=[]
 for row in range(3):
  for col in range(3):
   x=(col-1)*.022;y=(row-1)*.022
   cylinder('SMA_connector_base',(x,y,.0065),.0055,.005,m['gold'],root,32,.0003)
   ring('SMA_connector_washer',(x,y,.008),.0058,.003,.0012,m['bright'],root)
   c=empty(f'SMA_cap_{row+1}_{col+1}',root,(x,y,.010))
   cylinder('SMA_cap_hex',(0,0,.005),.0048,.010,m['gold'],c,6,.0004)
   cylinder('SMA_cap_top',(0,0,.0103),.0035,.0012,m['gold'],c,32,.0002)
   for z in (.002,.004):ring('SMA_cap_machined_ring',(0,0,z),.0042,.0038,.00035,m['gold'],c)
   caps.append(c)
 root['connector_count']=9;root['layout']='3 by 3';root['source_status']='Nine SMA protective caps on NASA TB1, retained as separate component roots'
 return {'root':root,'caps':caps}

def fastener_block(xy,m,parent):
 root=empty('Fastener_block',parent,(*xy,0))
 rounded_plate('Fastener_block_back',.080,.265,0,.022,.002,m['silver'],root)
 rounded_plate('Fastener_block_front_sheet',.080,.265,.022,.024,.001,m['silver'],root)
 # Four cages in one black guide channel; two separate captive screws below.
 box('Four_cage_black_channel',(0,.038,.025),(.024,.165,.002),m['dark'],root,.001)
 cages=[]
 for i,y in enumerate((.100,.060,.020,-.020)):
  cage=empty(f'Caged_fastener_{i+1}',root,(0,y,.025));cages.append(cage)
  cylinder('Cage_screw_shank',(0,0,.007),.0021,.014,m['steel'],cage,24,.0001)
  cylinder('Cage_screw_head',(0,0,.012),.0055,.004,m['bright'],cage,40,.0005)
  cylinder('Cage_screw_hex_socket',(0,0,.0142),.0023,.0003,m['dark'],cage,6,.00005)
  for x in (-.010,.010):
   box('Cage_side_upright',(x,0,.009),(.0014,.022,.018),m['silver'],cage,.0002)
  # Slotted top retainer surrounds the head and prevents free escape.
  for yy in (-.010,.010):box('Cage_end_bridge',(0,yy,.017),(.021,.002,.0014),m['silver'],cage,.00025)
  for x in (-.0075,.0075):box('Cage_top_slot_rail',(x,0,.017),(.005,.020,.0014),m['silver'],cage,.00025)
  for yy in (-.008,.008):box('Cage_front_fold',(0,yy,.002),(.018,.003,.001),m['silver'],cage,.0002)
 captive=[]
 for i,y in enumerate((-.073,-.108)):
  r=empty(f'Captive_fastener_{i+1}',root,(0,y,.024));captive.append(r)
  ring('Captive_annular_retainer',(0,0,.002),.007,.0048,.003,m['silver'],r)
  cylinder('Captive_head',(0,0,.005),.0047,.007,m['bright'],r,40,.0005)
  box('Captive_screw_slot',(0,0,.0087),(.006,.0008,.0002),m['dark'],r,.0001)
 # Tiny drilled dimples/fasteners and bent cover tabs follow the photograph.
 for x in (-.025,.025):
  for y in (-.118,-.061,.119):screw('Fastener_plate_mount',(x,y),.024,m,root,.0014)
 for x in (-.018,-.009,0,.009,.018):
  for y in (-.050,-.042):cylinder('Fastener_reference_dimple',(x,y,.0242),.0008,.0003,m['steel'],root,16,.00005)
 for y in (.103,.063,.023,-.017):
  tab=box('Cage_cover_diagonal_tab',(.022,y,.026),(.011,.0012,.004),m['silver'],root,.0002);tab.rotation_euler.z=-.45
 root['caged_fasteners']=4;root['captive_fasteners']=2
 return {'root':root,'caged':cages,'captive':captive}

def marman_strip(xy,m,parent,length=.330):
 root=empty('Marman_ring_section',parent,(*xy,0));points=[]
 for i in range(65):
  y=-length/2+length*i/64;x=.016-.90*(y-.10)**2;points.append((x,y))
 # An extruded curved M-profile: two narrow rail channels, not a flat ribbon.
 profile=[(-.025,0),(-.025,.006),(-.018,.009),(-.013,.009),(-.013,.003),(-.006,.003),(-.006,.009),(.006,.009),(.006,.003),(.013,.003),(.013,.009),(.018,.009),(.025,.006),(.025,0)]
 verts=[]
 for i,(x,y) in enumerate(points):
  dxdy=-1.8*(y-.10);normal=Vector((1,-dxdy,0)).normalized()
  for u,z in profile:verts.append((x+u*normal.x,y+u*normal.y,.003+z))
 n=len(profile);faces=[]
 for i in range(len(points)-1):
  for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 faces.extend([tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+j for j in range(n))])
 beam=bevel(mesh('Marman_curved_double_channel',verts,faces,m['silver'],root),.00035,3)
 for side in (-1,1):
  trace=[]
  for x,y in points:
   normal=Vector((1,1.8*(y-.10),0)).normalized();trace.append((x+side*.018*normal.x,y+side*.018*normal.y,.0124))
  tube('Marman_fine_edge_score',trace,.00011,m['steel'],root)
 root['source_status']='Curved Marman-ring section and open longitudinal channel profile reconstructed from TB1 CAD and hardware photograph'
 return root

def build(origin=(0,0,0),width_m=.400,height_m=.530,plate_thickness_m=.006):
 if width_m<=0 or height_m<=0 or plate_thickness_m<=0:raise ValueError('Positive reconstruction dimensions required')
 m=materials();root=empty('Assembly',loc=origin)
 root['source']='NASA RRM thermal-design paper Fig5 Task Board1 CAD and Fig7 Flight Task Boards; NASA hardware photograph5912199964'
 root['scale_status']='400x530x6mm reference reconstruction estimate; no official single-board dimensions found'
 root['estimated_plate_dimensions_m']=(width_m,height_m,plate_thickness_m)
 root['front_normal_local']=(0,0,1)
 def at(x,y):return (x*width_m/.400,y*height_m/.530)
 plate=rounded_plate('Base_plate',width_m,height_m,-plate_thickness_m,0,.012,m['plate'],root)
 # In the selected NASA hardware photograph these round upper features
 # contain diagonal slotted metal faces; the CAD's white circles alone are
 # insufficient evidence for empty holes. Reconstruct only the visible locks.
 upper_slotted=[]
 for i,x in enumerate((-.078,.094)):
  xy=at(x,.23055)
  cutter=cylinder('temporary_through_hole',(*xy,0),.0085,.030,m['silver'],root,64,0)
  bpy.context.view_layer.objects.active=plate;mod=plate.modifiers.new('Visible circular clearance around flush lock','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
  lock=empty(f'Upper_slotted_lock_{i+1}',root,(*xy,0));lock.rotation_euler.z=math.pi/4
  head=cylinder('Upper_round_slotted_face',(0,0,-.00025),.00825,.002,m['bright'],lock,64,.00015)
  cut=box('temporary_diagonal_slot',(0,0,.0016),(.013,.0012,.003),m['dark'],lock,0)
  bpy.context.view_layer.objects.active=head;bo=head.modifiers.new('Physical diagonal driver slot','BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cut;bpy.ops.object.modifier_apply(modifier=bo.name);bpy.data.objects.remove(cut,do_unlink=True)
  box('Upper_lock_slot_floor',(0,0,.00005),(.0125,.0011,.00008),m['dark'],lock,.00005)
  lock['source_status']='Silver circular face and diagonal slot from NASA hardware photograph; hidden locking mechanism unspecified'
  upper_slotted.append(lock)
 # Left and right black/amber thermal surface coupons are deliberately flat.
 patches=[]
 for name,xy,w,h,mat in [('Left_black',at(.0275,.0848),.095,.2226,m['black']),('Left_amber',at(.0275,-.0848),.095,.1166,m['kapton']),('Right_black',at(.1335,.14045),.117,.1113,m['black']),('Right_amber',at(.1335,-.02915),.117,.2279,m['kapton'])]:
  p=rounded_plate(name+'_thermal_surface',w*width_m/.4,h*height_m/.53,.0002,.0006,.001,mat,root,xy);patches.append(p)
  if 'black' in name:
   cx,cy=xy
   for xx in (cx-w*width_m/.4/2+.0012,cx+w*width_m/.4/2-.0012):tube(name+'_fine_white_edge',[(xx,cy-h*height_m/.53/2+.001,.00075),(xx,cy+h*height_m/.53/2-.001,.00075)],.00013,m['white'],root)
 mounts=[mount('M1',at(.008,.22525),m,root),mount('Lower_left_mount',at(-.174,-.2279),m,root),mount('Lower_right_mount',at(.150,-.2279),m,root)]
 grey=box('TB2_MLI_magnet_catch_plate',(*at(-.164,.23585),.009),(.048,.0424,.018),m['grey'],root,.0008)
 grey['source_status']='Magnet Catch Plate for TB2 MLI, named in NASA Fig5; TB1 carries the catch, not the TB2 blanket'
 fdv3=safety_cap('FDV3',at(-.154,.06095),False,m,root)
 fdv1=safety_cap('FDV1',at(-.154,-.02915),True,m,root)
 smaa=stowage_adapter('SMA_A',at(-.154,-.12985),m,root)
 tsa=stowage_adapter('TSA',at(.156,.23055),m,root)
 fasteners=fastener_block(at(-.066,.0901),m,root)
 ring_section=marman_strip(at(.076,.0318),m,root,.330*height_m/.53)
 array=sma_array(at(-.012,-.2014),m,root)
 targets=[fiducial('Lower_left_target',at(-.110,-.212),m,root),fiducial('Lower_right_target',at(.094,-.212),m,root)]
 # The hardware photograph and the independent flight-board view both
 # show a third target immediately above M1 on a separate projecting bracket.
 bracket=rounded_plate('Upper_target_separate_back_bracket',.056,.092,-.008,-.006,.003,m['silver'],root,at(.008,.277))
 for dx in (-.019,.019):
  box('Upper_target_rear_spacer',(*at(.008+dx,.296),-.003),(.009,.032,.006),m['silver'],root,.0003)
  screw('Upper_target_bracket_attachment',at(.008+dx,.256),0,m,root,.0015)
 upper_target=fiducial('Upper_M1_target',at(.008,.294),m,root);targets.append(upper_target)
 bracket['source_status']='Separate upward target support visible in NASA hardware photograph and Fig7 flight view; rear attachment details reconstructed'
 labels=[label('TB1_label','TB1',at(-.047,.247),.037,.015,.010,m,root),label('M1_label','M1',at(.039,.233),.013,.009,.0055,m,root)]
 for name,value,xy in [('FDV3_label','FDV3',at(-.184,.06095)),('FDV1_label','FDV1',at(-.184,-.02915)),('SMA_A_label','SMA-A',at(-.184,-.12985)),('TSA_label','TSA',at(.119,.228))]:labels.append(label(name,value,xy,.052,.015,.009,m,root,math.pi/2))
 for x,y in ((-.185,.250),(.185,.250),(-.185,-.250),(.185,-.250),(-.185,-.170),(.185,-.150)):
  screw('Base_plate_perimeter_fastener',at(x,y),0,m,root,.0015)
 components={'FDV3':fdv3,'FDV1':fdv1,'SMA_A':smaa,'TSA':tsa,'fastener_block':fasteners,'Marman_section':ring_section,'SMA_array':array,'mounts':mounts,'fiducials':targets,'thermal_patches':patches,'labels':labels,'magnet_catch':grey,'upper_target_bracket':bracket,'upper_slotted_locks':upper_slotted}
 bpy.context.view_layer.update()
 return {'root':root,'plate':plate,'components':components,'removable_cap':fdv1['cap_root'],'cap_fixed_interface':fdv1['fixed_socket'],
  'cap_axis_local':(0,0,1),'cap_closed_position_local':(0,0,.012),
  'estimated_dimensions':{'width_m':width_m,'height_m':height_m,'plate_thickness_m':plate_thickness_m},
  'source_report':{'configuration':'RRM Task Board1 only, portrait review orientation',
   'layout':'NASA20110013452 Fig5 TB1 CAD; Fig7 flight boards used as configuration evidence; positions follow TB1_layout_estimate.json visually estimated portrait layout',
   'finish':'NASA hardware image5912199964; caption has mixed mockup/flight wording. Fig7 explicitly supplies flight-board configuration evidence',
   'not_dimensioned':['overall single-board dimensions','plate thickness','component dimensions','thread pitch','internal retention mechanisms'],
   'independent_cap':'FDV1 separate removable root; local+Z axis, no invented helical/thread constraint',
   'labels':'TB1, M1, TSA, FDV3, FDV1, SMA-A; unreadable RTP identifiers omitted',
   'photo_state_details':'Three optical targets, including separate upward M1 bracket; two round upper diagonal-slotted metal faces. Both details follow the hardware photo over the simplified CAD view',
   'no_safety_wire':'The two TB1 dummy fill/drain valve locations shown here have no safety wire; no TB2 red door or insulation blanket has been mixed into the board'}}
