const viewer = document.querySelector('#shield');
const status = document.querySelector('#status');
const buttons = [...document.querySelectorAll('.controls button')];
const state = {dark: false, worn: false, relief: true};
let materials;
const textures = new Map();
async function texture(path) {
  if (!textures.has(path)) textures.set(path, viewer.createTexture(path).catch(error => {textures.delete(path); throw error;}));
  return textures.get(path);
}
function announce() {
  status.textContent = `${state.worn ? 'Desgastado' : 'Limpio'} · Acero ${state.dark ? 'oscuro' : 'natural'} · Relieve ${state.relief ? 'activo' : 'inactivo'}`;
}
function syncButtons() {
  document.querySelector('#steel').setAttribute('aria-pressed', String(state.dark));
  document.querySelector('#wear').setAttribute('aria-pressed', String(state.worn));
  document.querySelector('#relief').setAttribute('aria-pressed', String(state.relief));
}
viewer.addEventListener('progress', event => {
  document.querySelector('#progress').style.width = `${event.detail.totalProgress * 100}%`;
  document.querySelector('.loading-track').hidden = event.detail.totalProgress === 1;
});
viewer.addEventListener('error', () => {
  status.textContent = 'No se pudo cargar el modelo. Revisa tu conexión y vuelve a cargar la página.';
  buttons.forEach(button => button.disabled = true);
});
viewer.addEventListener('load', () => {
  materials = Object.fromEntries(viewer.model.materials.map(material => [material.name, material]));
  if (!['Madera', 'Acero', 'Bronce'].every(name => materials[name])) {
    status.textContent = 'El modelo no contiene los tres materiales esperados.';
    return;
  }
  // Preserve the original embedded normal when toggling back to the clean version.
  textures.set('textures/Bronce_limpio_Normal.png', Promise.resolve(materials.Bronce.normalTexture.texture));
  buttons.forEach(button => button.disabled = false);
  announce();
});
document.querySelector('#steel').addEventListener('click', () => {
  state.dark = !state.dark;
  materials.Acero.pbrMetallicRoughness.setBaseColorFactor(state.dark ? '#596978' : '#ffffff');
  syncButtons(); announce();
});
document.querySelector('#relief').addEventListener('click', async () => {
  buttons.forEach(button => button.disabled = true);
  try {
    const next = !state.relief;
    const normal = next ? await texture(`textures/Bronce_${state.worn ? 'gastado' : 'limpio'}_Normal.png`) : null;
    materials.Bronce.normalTexture.setTexture(normal);
    state.relief = next; syncButtons(); announce();
  } catch {status.textContent = 'No se pudo cargar el relieve. Vuelve a intentarlo.';}
  finally {buttons.forEach(button => button.disabled = false);}
});
document.querySelector('#wear').addEventListener('click', async () => {
  buttons.forEach(button => button.disabled = true);
  status.textContent = 'Cargando el nuevo acabado…';
  const next = !state.worn;
  try {
    // Load all maps before changing anything so failures leave the current appearance intact.
    const loaded = await Promise.all(['Madera','Acero','Bronce'].map(async name => {
      const prefix = `textures/${name}_${next ? 'gastado' : 'limpio'}_`;
      return {name, maps: await Promise.all(['BaseColor','ORM','Normal'].map(map => texture(`${prefix}${map}.png`)))};
    }));
    for (const {name, maps} of loaded) {
      const mat = materials[name];
      mat.pbrMetallicRoughness.baseColorTexture.setTexture(maps[0]);
      mat.pbrMetallicRoughness.metallicRoughnessTexture.setTexture(maps[1]);
      mat.normalTexture.setTexture(name === 'Bronce' && !state.relief ? null : maps[2]);
    }
    state.worn = next; syncButtons(); announce();
  } catch {status.textContent = 'No se pudieron cargar las texturas. Se conserva el acabado anterior; vuelve a intentarlo.';}
  finally {buttons.forEach(button => button.disabled = false);}
});
fetch('assets/model-info.json').then(response => {
  if (!response.ok) throw Error('metadata'); return response.json();
}).then(info => {
  document.querySelector('#metrics').textContent = `${info.triangles.toLocaleString('es-MX')} triángulos · PBR 1K · ${(info.glb_bytes/1048576).toFixed(1)} MB`;
}).catch(() => {});
