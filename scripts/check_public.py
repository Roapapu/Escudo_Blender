"""Verify published critical assets against this checkout (no credentials needed)."""
from pathlib import Path
import urllib.request, hashlib, json
root=Path(__file__).resolve().parent.parent
base='https://roapapu.github.io/Escudo_Blender/'
results=[]
for name in ['index.html','app.js','style.css','assets/escudo.glb','assets/model-info.json','vendor/model-viewer.min.js']:
    req=urllib.request.Request(base+name,headers={'User-Agent':'Escudo-Solar-QA','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as response:
        remote=response.read();local=(root/name).read_bytes()
        if name.endswith(('.html','.js','.css','.json')):
            remote=remote.replace(b'\r\n',b'\n');local=local.replace(b'\r\n',b'\n')
        results.append({'path':name,'http_status':response.status,'bytes':len(remote),'matches_local':hashlib.sha256(remote).digest()==hashlib.sha256(local).digest()})
print(json.dumps(results,indent=2))
if not all(r['matches_local'] for r in results):raise SystemExit(1)
