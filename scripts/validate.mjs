import fs from 'node:fs';
import validator from 'gltf-validator';
const bytes = fs.readFileSync('assets/escudo.glb');
const result = await validator.validateBytes(new Uint8Array(bytes),{uri:'escudo.glb',maxIssues:100});
fs.writeFileSync('validation-gltf.json',JSON.stringify(result,null,2));
const length = bytes.readUInt32LE(12);
const gltf = JSON.parse(bytes.subarray(20,20+length).toString());
const triangles = gltf.meshes.flatMap(m=>m.primitives).reduce((sum,p)=>sum+gltf.accessors[p.indices].count/3,0);
const names=gltf.materials.map(m=>m.name).sort();
const primitives=gltf.meshes.flatMap(m=>m.primitives);
const checks={
  gltf_errors:result.issues.numErrors,
  triangles,
  below_8000_triangles:triangles<8000,
  below_10MiB:bytes.length<10*1048576,
  materials:names,
  three_materials:names.join(',')==='Acero,Bronce,Madera',
  all_primitives_have_UVs:primitives.every(p=>p.attributes.TEXCOORD_0!==undefined),
  all_primitives_have_tangents:primitives.every(p=>p.attributes.TANGENT!==undefined),
  all_materials_have_PBR_maps:gltf.materials.every(m=>m.pbrMetallicRoughness.baseColorTexture && m.pbrMetallicRoughness.metallicRoughnessTexture && m.normalTexture),
  exactly_three_buttons:(fs.readFileSync('index.html','utf8').match(/<button /g)||[]).length===3
};
fs.writeFileSync('validation-summary.json',JSON.stringify(checks,null,2));
console.log(JSON.stringify(checks,null,2));
if(result.issues.numErrors || Object.values(checks).includes(false)) process.exitCode=1;
