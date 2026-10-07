from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[1]
anchors=json.loads((HERE/'R1_ANCHOR_SHA256.json').read_text())['files']
anchor_results=[]
for rel,expected in anchors.items():
 p=REPO/rel; actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
 anchor_results.append({'path':rel,'expected':expected,'actual':actual,'pass':actual==expected})
env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'
checks=[]
for cmd in ([sys.executable,'-B',str(REPO/'loop'/'epoch002'/'test_planner.py')],[sys.executable,'-B',str(HERE/'test_validity_inferencer.py')]):
 p=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True,env=env)
 checks.append({'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
state='PASS_CPU_INTEGRATION_ACCEPTANCE' if all(x['pass'] for x in anchor_results) and all(c['returncode']==0 for c in checks) else 'FAIL_CPU_INTEGRATION_ACCEPTANCE'
result={'state':state,'anchor_results':anchor_results,'checks':checks,'writes_performed':False}
print(json.dumps(result,indent=2))
raise SystemExit(0 if state.startswith('PASS') else 2)
