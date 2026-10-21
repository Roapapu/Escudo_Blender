"""Rebuild the original shield, PBR maps, GLB and presentation renders in Blender."""
import bpy, bmesh, math, os, json, tempfile
import numpy as np
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(ROOT,'.tmp'),exist_ok=True)
tempfile.tempdir=os.path.join(ROOT,'.tmp')
for d in ['assets','textures','source','renders']:
    os.makedirs(os.path.join(ROOT,d),exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
N=1024
v,u=np.mgrid[0:N,0:N].astype(np.float32)/(N-1)
rng=np.random.default_rng(31)
noise=(np.sin(u*173+np.sin(v*91))*np.sin(v*187+u*37)*.25+.5).astype(np.float32)
def save_map(name, data, color=False):
    a=np.ones((N,N,4),np.float32)
    a[:,:,:3]=data[:,:,None] if data.ndim==2 else data
    im=bpy.data.images.new(name,width=N,height=N,alpha=False)
    im.colorspace_settings.name='sRGB' if color else 'Non-Color'
    im.pixels.foreach_set(a.ravel()); im.filepath_raw=os.path.join(ROOT,'textures',name+'.png'); im.file_format='PNG'; im.save()
    return im
def texture_set(kind,worn):
    wear=1 if worn else 0
    if kind=='Madera':
        grain=np.sin(u*220+np.sin(v*14)*2+np.sin(v*39+u*13))*0.5+0.5
        fine=np.sin(u*950+np.sin(v*28)*4)*0.5+0.5
        h=.48+grain*.025+fine*.003+noise*.003
        t=.68+grain*.32+fine*.08+noise*.08
        base=np.stack([t*.29,t*.135,t*.055],axis=2)
        base=base*(1-wear*.13)+wear*.022
        rough=np.clip(.61+grain*.16+noise*.08+wear*.08,0,1); metal=np.zeros_like(u)
    else:
        brushed=np.sin(v*1750+np.sin(u*17))*.5+.5
        pits=np.maximum(0,np.sin(u*197+v*23)*np.sin(v*251-u*9)-.82)
        scratches=(np.sin(u*580+v*90)>.997).astype(np.float32)
        h=.5+brushed*.0007+noise*.001-wear*pits*.018-wear*scratches*.004
        t=.78+noise*.12+brushed*.06-wear*pits*1.6-wear*scratches*.18
        c=[.61,.66,.71] if kind=='Acero' else [.64,.38,.115]
        base=np.stack([t*x for x in c],axis=2)
        if kind=='Bronce':
            patina=np.clip((np.sin(u*30)*np.sin(v*25)+noise*.4-.65)*wear,0,.45)
            base=base*(1-patina[:,:,None])+patina[:,:,None]*np.array([.06,.22,.15])
        rough=np.clip(.30+noise*.12+wear*.20+wear*pits,0,1); metal=np.full_like(u,.98)
    # Bake sampled surface height into a tangent-space normal texture, +Y (glTF).
    dy,dx=np.gradient(h); normal=np.stack([-dx*30,-dy*30,np.ones_like(u)],axis=2)
    normal/=np.linalg.norm(normal,axis=2,keepdims=True)
    tag=kind+('_gastado' if worn else '_limpio')
    maps={
        'base':save_map(tag+'_BaseColor',np.clip(base,0,1),True),
        'rough':save_map(tag+'_Roughness',rough),
        'metal':save_map(tag+'_Metallic',metal),
        'normal':save_map(tag+'_Normal',normal*.5+.5),
        'orm':save_map(tag+'_ORM',np.stack([np.ones_like(u),rough,metal],axis=2))}
    return maps
sets={k:[texture_set(k,False),texture_set(k,True)] for k in ['Madera','Acero','Bronce']}
mats={}
for kind in sets:
    m=bpy.data.materials.new(kind);m.use_nodes=True
    ns=m.node_tree.nodes; lk=m.node_tree.links; p=ns.get('Principled BSDF')
    p.inputs['Metallic'].default_value=0 if kind=='Madera' else .98
    for key,socket in [('base','Base Color'),('rough','Roughness'),('metal','Metallic')]:
        tex=ns.new('ShaderNodeTexImage');tex.image=sets[kind][0][key];tex.label=key
        lk.new(tex.outputs['Color'],p.inputs[socket])
    tex=ns.new('ShaderNodeTexImage');tex.image=sets[kind][0]['normal']
    nm=ns.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1
    lk.new(tex.outputs['Color'],nm.inputs['Color']);lk.new(nm.outputs['Normal'],p.inputs['Normal'])
    mats[kind]=m
def mesh(name,verts,faces,kind):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(mats[kind])
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    # Pack all faces, including rims and back faces, with a real UV unwrap.
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
    return ob
def front(x,z):return -.09-.10*(1-(x/.65)**2)
def width(z):
    if z<-.36:return .10+(z+.96)/.60*.50
    if z>.65:return .60-(z-.65)*.18
    return .60
zs=[-.96,-.82,-.60,-.36,0,.35,.65,.88]
outline=[(-width(z),z) for z in zs]+[(width(z),z) for z in reversed(zs)]
def clip_x(poly,bound,keep_greater):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ai=a[0]>=bound if keep_greater else a[0]<=bound
        bi=b[0]>=bound if keep_greater else b[0]<=bound
        if ai:result.append(a)
        if ai!=bi:
            t=(bound-a[0])/(b[0]-a[0]);result.append((bound,a[1]+t*(b[1]-a[1])))
    return result
# Tapered planks follow the shield silhouette, with small visible joints.
for i in range(7):
    left=-.60+i*1.20/7+.003;right=-.60+(i+1)*1.20/7-.003
    poly=clip_x(clip_x(outline,left,True),right,False)
    count=len(poly)
    verts=[(x,front(x,z)+offset,z) for offset in [0,.095] for x,z in poly]
    faces=[tuple(range(count)),tuple(reversed(range(count,count*2)))]
    for j in range(count):
        k=(j+1)%count;faces.append((j,k,k+count,j+count))
    mesh('Tablon_%02d'%(i+1),verts,faces,'Madera')
verts=[]
for x,z in outline:
    for scale,yoff in [(1.055,-.025),(.925,-.027),(1.055,.105),(.925,.105)]:
        xx=x*scale;zz=z*scale;verts.append((xx,front(xx,zz)+yoff,zz))
faces=[]
for i in range(len(outline)):
    a=i*4;b=((i+1)%len(outline))*4
    faces.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
mesh('Cerco_de_acero',verts,faces,'Acero')
def sphere(name,loc,scale,kind,segments=12,rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(mats[kind])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in ob.data.polygons:p.use_smooth=True
    ob.select_set(False);return ob
for i,(x,z) in enumerate(outline):
    sphere('Remache_%02d'%i,(x*.99,front(x,z)-.04,z*.99),(.018,.012,.018),'Bronce')
# Sunburst emblem: shallow bronze rays and a convex central boss.
for i in range(12):
    a=i*math.tau/12
    coords=[]
    for rad,angle in [(.205,a-.14),(.36,a),(.205,a+.14)]:coords.append((math.sin(angle)*rad,math.cos(angle)*rad+.09))
    vs=[(x,front(x,z)-depth,z) for depth in [.025,.043] for x,z in coords]
    mesh('Rayo_%02d'%i,vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'Bronce')
sphere('Umbo_solar',(0,-.215,.09),(.215,.085,.215),'Bronce',32,12)
for i in range(16):
    a=i*math.tau/16
    sphere('Perla_%02d'%i,(math.sin(a)*.185,-.256,math.cos(a)*.185+.09),(.012,.012,.012),'Bronce',8,4)
def cube(name,loc,scale,kind,bevel=.012):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name;ob.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(mats[kind])
    mod=ob.modifiers.new('Cantos suaves','BEVEL');mod.width=bevel;mod.segments=2
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
for z in [-.28,.4]:cube('Travesano',(0,-.025,z),(1.03,.075,.09),'Acero')
for z in [-.16,.28]:cube('Soporte_del_agarre',(0,.035,z),(.14,.16,.07),'Bronce')
cube('Empunadura',(0,.115,.06),(.085,.075,.47),'Madera',.025)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:
    if not o.data.uv_layers:raise RuntimeError('Missing UV: '+o.name)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    o.select_set(True)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)
# Export three meshes (one draw group per material); keep native pieces editable.
bpy.ops.object.select_all(action='DESELECT')
web_objects=[]
for kind in mats:
    copies=[]
    for ob in objects:
        if ob.data.materials[0].name==kind:
            dup=ob.copy();dup.data=ob.data.copy();bpy.context.collection.objects.link(dup);dup.select_set(True);copies.append(dup)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
    joined=bpy.context.object;joined.name='WEB_'+kind;web_objects.append(joined);joined.select_set(False)
for ob in web_objects:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'assets','escudo.glb'),export_format='GLB',use_selection=True,export_yup=True,export_tangents=True)
for ob in web_objects:bpy.data.objects.remove(ob,do_unlink=True)
# Pack editable assets into the native Blender file.
for im in bpy.data.images:
    if im.source=='FILE' or im.filepath:im.pack()
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.16,.16,.16)
def aim(ob,point):ob.rotation_euler=(Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((-3,-4,5),650,4),((3,-2,1),450,3),((0,3,4),800,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;aim(l,(0,0,0))
bpy.ops.object.camera_add(location=(2.1,-4.7,1.45));cam=bpy.context.object;aim(cam,(0,0,-.02));cam.data.type='ORTHO';cam.data.ortho_scale=2.55;scene.camera=cam
scene.render.film_transparent=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'source','Escudo_Solar.blend'))
scene.render.filepath=os.path.join(ROOT,'renders','escudo-frente.png');bpy.ops.render.render(write_still=True)
cam.location=(-1.9,4.7,1.2);aim(cam,(0,0,-.02));scene.render.filepath=os.path.join(ROOT,'renders','escudo-reverso.png');bpy.ops.render.render(write_still=True)
with open(os.path.join(ROOT,'assets','model-info.json'),'w',encoding='utf-8') as f:json.dump({'triangles':tris,'mesh_objects':len(objects),'materials':list(mats),'texture_resolution':N,'glb_bytes':os.path.getsize(os.path.join(ROOT,'assets','escudo.glb'))},f,indent=2)
print('SHIELD_COMPLETE',tris)
