#!/usr/bin/env python3
"""
Public full-loop acceptance harness.

This is orchestration glue only. It imports the existing public planner and invokes the
existing public CHIA/H100 portability entrypoint. It does not modify planner/oracle rules.
"""
from __future__ import annotations
import argparse, dataclasses, hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOOP = ROOT / "loop" / "epoch002"
sys.path.insert(0, str(LOOP))
from planner import Scope, cache_key, choose, evaluate, can_stop  # noqa: E402

def sha256(p: pathlib.Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def read_json(p): return json.loads(pathlib.Path(p).read_text())

def env_fingerprint(chia_python: str, gpu_python: str) -> tuple[str,dict]:
    commands = {
      "chia":[chia_python,"-c","import sys,ray; import chia; print(sys.version); print(getattr(chia,'__file__',None)); print(ray.__version__)"],
      "gpu":[gpu_python,"-c","import sys,torch,triton; print(sys.version); print(torch.__version__); print(torch.version.cuda); print(triton.__version__); print(torch.cuda.get_device_name() if torch.cuda.is_available() else 'NO_CUDA')"],
      "nvidia":["nvidia-smi","--query-gpu=name,driver_version,memory.total","--format=csv,noheader,nounits"],
    }
    out={}
    for k,cmd in commands.items():
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        out[k]={"rc":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()}
        if p.returncode: raise RuntimeError(f"environment probe failed: {k}: {p.stderr}")
    files={}
    for rel in ["baseline.py","challenger.py","challenger_v2.py","operations.py","planner.py","gpu_worker.py","run_chia_loop.py"]:
        files[rel]=sha256(LOOP/rel)
    payload={"commands":out,"public_code_hashes":files}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(), payload

def invoke_live(chia_python, gpu_python, n, output_rel, implementation="v1"):
    out=(ROOT/output_rel).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env["A3_CHIA_PYTHON"]=chia_python
    env["A3_GPU_PYTHON"]=gpu_python
    env["A3_CHIA_PUBLIC_ROOT"]=str(ROOT)
    cmd=[chia_python,str(LOOP/"run_chia_loop.py"),"--live","--path","affine",
         "--implementation",implementation,"--n",str(n),"--output",str(pathlib.Path(output_rel))]
    p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=600)
    log=out.with_suffix(out.suffix+".acceptance.log")
    log.write_text(p.stdout+p.stderr)
    if p.returncode:
        raise RuntimeError(f"live run failed n={n}; see {log}")
    d=read_json(out)
    if d.get("status")!="PASS":
        raise RuntimeError(f"non-PASS live artifact n={n}: {d.get('status')}")
    if d.get("oracle",{}).get("status")!="PASS" or d.get("baseline_oracle",{}).get("status")!="PASS":
        raise RuntimeError(f"oracle failure n={n}")
    return d, out, log, cmd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--chia-python")
    ap.add_argument("--gpu-python")
    ap.add_argument("--output-dir",default="results/public_full_loop_acceptance")
    ap.add_argument("--offline-selftest",action="store_true")
    args=ap.parse_args()
    outdir=(ROOT/args.output_dir).resolve()
    outdir.mkdir(parents=True,exist_ok=True)

    seed=read_json(ROOT/"evidence/epoch002/affine_typed_seed_public.json")
    protocol=read_json(ROOT/"evidence/epoch002/protocol.json")
    weights={int(k):1 for k in seed}
    values={int(k):v["speedup"] for k,v in seed.items()}

    # Case A: valid reuse. Presentation-only changes do not alter typed scope.
    reuse=[]
    for ks,e in seed.items():
        n=int(ks)
        s=Scope(**e["scope"])
        key_old=cache_key("FULL_A",s,e["candidate_bundle"],protocol)
        key_new=cache_key("FULL_A",s,e["candidate_bundle"],{"presentation":"renamed only"})
        reuse.append({"n":n,"cache_key_equal":key_old==key_new,"source_sha256":e["raw_sha256"],"speedup":e["speedup"]})
    reuse_decision=evaluate(values,weights)
    reuse_pass=all(x["cache_key_equal"] for x in reuse) and reuse_decision in ("PROMOTE","REJECT")

    if args.offline_selftest:
        result={
          "state":"OFFLINE_SELFTEST_PASS" if reuse_pass else "OFFLINE_SELFTEST_FAIL",
          "valid_reuse":{"pass":reuse_pass,"decision":reuse_decision,"events":reuse},
          "live_cases":"NOT_RUN"
        }
        (outdir/"OFFLINE_SELFTEST.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        raise SystemExit(0 if reuse_pass else 2)

    if not args.chia_python or not args.gpu_python:
        raise SystemExit("--chia-python and --gpu-python are required for live acceptance")

    current_env, env_payload=env_fingerprint(args.chia_python,args.gpu_python)
    (outdir/"CURRENT_ENVIRONMENT.json").write_text(json.dumps({"environment_sha256":current_env,**env_payload},indent=2)+"\n")

    # Case B: a current-environment scope must not reuse historical-environment evidence.
    hist=seed["1048576"]
    hist_scope=Scope(**hist["scope"])
    current_scope=dataclasses.replace(hist_scope,environment=current_env)
    hist_key=cache_key("FULL_A",hist_scope,hist["candidate_bundle"],protocol)
    current_bundle=hashlib.sha256(
        "".join(sha256(LOOP/x) for x in ["baseline.py","challenger.py","operations.py","planner.py"]).encode()
    ).hexdigest()
    current_key=cache_key("FULL_A",current_scope,current_bundle,protocol)
    invalidation_pass = hist_key != current_key

    # The first live cell is both the public GPU smoke and the required measurement after invalidation.
    live1048,p1048,l1048,cmd1048=invoke_live(
        args.chia_python,args.gpu_python,1048576,
        "results/public_full_loop_acceptance/live_n1048576.json","v1")
    invalid_values={1048576:live1048["speedup"]}
    invalid_weights={1048576:1}
    invalid_decision=evaluate(invalid_values,invalid_weights)

    # Case C: no compatible prior. Compare B3 and FULL_A action order under empty prior.
    pending={262144,1048576}
    empty_prior={}
    b3_order=[]; fa_order=[]
    p1=set(pending); p2=set(pending)
    while p1:
        n=choose("B3",p1,{x:1 for x in p1},empty_prior); b3_order.append(n); p1.remove(n)
    while p2:
        n=choose("FULL_A",p2,{x:1 for x in p2},empty_prior); fa_order.append(n); p2.remove(n)
    order_equal=b3_order==fa_order

    live_by_n={1048576:live1048}
    live_artifacts={1048576:{"artifact":str(p1048.relative_to(ROOT)),"sha256":sha256(p1048),"log":str(l1048.relative_to(ROOT))}}
    observed={}
    executed=[]
    for n in fa_order:
        if n not in live_by_n:
            d,p,l,cmd=invoke_live(args.chia_python,args.gpu_python,n,
                 f"results/public_full_loop_acceptance/live_n{n}.json","v1")
            live_by_n[n]=d
            live_artifacts[n]={"artifact":str(p.relative_to(ROOT)),"sha256":sha256(p),"log":str(l.relative_to(ROOT))}
        observed[n]=live_by_n[n]["speedup"]; executed.append(n)
        if can_stop("FULL_A",observed,{262144:1,1048576:1}):
            break

    b3_decision=evaluate(observed,{262144:1,1048576:1})
    fa_decision=evaluate(observed,{262144:1,1048576:1})
    collapse_pass = order_equal and b3_decision==fa_decision and b3_decision != "UNRESOLVED"

    result={
      "state":"PASS_PUBLIC_FULL_LOOP_ACCEPTANCE" if (reuse_pass and invalidation_pass and collapse_pass) else "FAIL_PUBLIC_FULL_LOOP_ACCEPTANCE",
      "claim_ceiling":"artifact_portability_and_orchestration_only",
      "scientific_promotion":False,
      "frozen_G2_G3_mutated":False,
      "valid_reuse":{
        "pass":reuse_pass,"decision":reuse_decision,"events":reuse,
        "new_H100_measurements":0
      },
      "invalidated_evidence":{
        "pass":invalidation_pass,
        "historical_environment":hist_scope.environment,
        "current_environment":current_env,
        "historical_cache_key":hist_key,
        "current_cache_key":current_key,
        "forced_live_measurement":1048576,
        "live_speedup":live1048["speedup"],
        "decision":invalid_decision,
        "live_artifact":live_artifacts[1048576]
      },
      "no_compatible_prior_collapse":{
        "pass":collapse_pass,
        "B3_order":b3_order,
        "FULL_A_order":fa_order,
        "executed_order":executed,
        "observed_speedups":observed,
        "B3_decision":b3_decision,
        "FULL_A_decision":fa_decision,
        "live_artifacts":live_artifacts
      }
    }
    out=(outdir/"FULL_LOOP_ACCEPTANCE.json")
    out.write_text(json.dumps(result,indent=2)+"\n")
    md=[
      "# PUBLIC FULL-LOOP ACCEPTANCE",
      "",
      f"Verdict: **{result['state']}**",
      "",
      "This acceptance proves bounded public artifact behavior only. It does not promote FULL_A or modify frozen G2/G3.",
      "",
      f"- Valid evidence reuse: {'PASS' if reuse_pass else 'FAIL'}; decision `{reuse_decision}`; 0 new H100 cells.",
      f"- Scope invalidation → live measurement: {'PASS' if invalidation_pass else 'FAIL'}; decision `{invalid_decision}`.",
      f"- No-compatible-prior collapse B3↔FULL_A: {'PASS' if collapse_pass else 'FAIL'}; order `{fa_order}`; decision `{fa_decision}`.",
    ]
    (outdir/"FULL_LOOP_ACCEPTANCE.md").write_text("\n".join(md)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["state"]=="PASS_PUBLIC_FULL_LOOP_ACCEPTANCE" else 3)

if __name__=="__main__":
    main()
