"""Inspect the delivered native scene; save a readable starting viewport."""
import bpy, os, json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'source','Escudo_Solar.blend'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for name in os.listdir(os.path.join(root,'textures')):
    if name.endswith('.png'):
        image=bpy.data.images.get(name[:-4])
        if image is None:image=bpy.data.images.load(os.path.join(root,'textures',name))
        image.colorspace_settings.name='sRGB' if 'BaseColor' in name else 'Non-Color'
        image.use_fake_user=True;image.pack()
assert len(meshes)==58
assert all(o.data.uv_layers for o in meshes)
assert all(len(face.vertices)==3 for ob in meshes for face in ob.data.polygons)
report={'native_meshes':len(meshes),'all_native_pieces_have_UVs':True,'all_faces_triangulated':True,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'native_triangles':sum(len(o.data.polygons) for o in meshes)}
assert report['packed_images']>=30
for ob in bpy.context.selected_objects:ob.select_set(False)
active=bpy.data.objects.get('Tablon_04');active.select_set(True);bpy.context.view_layer.objects.active=active
rotation=(Vector((0,0,0))-Vector((1,-4,1))).to_track_quat('-Z','Y')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=3.2
            area.spaces.active.region_3d.view_location=(0,0,0)
            area.spaces.active.region_3d.view_rotation=rotation
            area.spaces.active.shading.type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'source','Escudo_Solar.blend'))
with open(os.path.join(root,'validation-native.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
