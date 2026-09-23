"""PUBLIC PORTABILITY DERIVATIVE for C_035 verification."""
import argparse,json,os,pathlib,subprocess
import ray
from chia.base.ChiaFunction import ChiaFunction,get

@ChiaFunction(num_cpus=1,num_gpus=1,max_retries=0)
def verify_node(worker,n,output,gpu_python):
    p=subprocess.run([gpu_python,worker,"--variant","candidate","--n",str(n),
                      "--samples","31","--output",output],
                     capture_output=True,text=True,timeout=240)
    pathlib.Path(output+".log").write_text(p.stdout+p.stderr)
    if p.returncode: raise RuntimeError("verification failed")
    return json.loads(pathlib.Path(output).read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=1048576)
    ap.add_argument("--output",required=True)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    worker=pathlib.Path(__file__).resolve().parent/"gpu_worker.py"
    if args.dry_run:
        print(json.dumps({"status":"DRY_RUN","worker":str(worker),"n":args.n,
                          "public_portability_derivative":True},indent=2))
        return
    gpu_python=os.environ.get("A3_GPU_PYTHON")
    if not gpu_python: raise SystemExit("A3_GPU_PYTHON is required")
    ray.init(address=os.environ.get("RAY_ADDRESS",None),
             include_dashboard=False,logging_level="ERROR")
    try:
        r=get(verify_node.chia_remote(str(worker),args.n,args.output,gpu_python))
        assert r["status"]=="PASS"
        print(json.dumps({"status":"PASS","speedup":r["speedup"],
                          "artifact":args.output},indent=2))
    finally: ray.shutdown()

if __name__=="__main__": main()
