"""Configure and inspect Pages using the existing Git credential, without logging secrets."""
import subprocess, json, urllib.request, urllib.error, sys
repo='Roapapu/Escudo_Blender'
result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
credential=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
token=credential.get('password')
if not token:raise SystemExit('No GitHub credential available')
def api(path,method='GET',data=None):
    req=urllib.request.Request('https://api.github.com/repos/'+repo+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Escudo-Solar-build'})
    try:
        with urllib.request.urlopen(req,timeout=30) as res:return json.load(res) if res.status!=204 else {}
    except urllib.error.HTTPError as err:
        body=json.loads(err.read());return {'status':err.code,'message':body.get('message','API error')}
if 'enable' in sys.argv:
    current=api('/pages')
    if current.get('status')==404:current=api('/pages','POST',{'build_type':'workflow'})
    elif current.get('build_type')!='workflow' and not current.get('status'):current=api('/pages','PUT',{'build_type':'workflow'})
    print(json.dumps({'pages':current},indent=2))
else:
    pages=api('/pages'); runs=api('/actions/runs?per_page=3')
    print(json.dumps({'pages':{k:pages.get(k) for k in ['status','html_url','build_type','message']},'runs':[{k:r.get(k) for k in ['id','status','conclusion','html_url']} for r in runs.get('workflow_runs',[])]},indent=2))
