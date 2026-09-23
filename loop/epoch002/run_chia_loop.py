"""PUBLIC PORTABILITY DERIVATIVE — not byte-identical to the measured private wrapper.

Default behavior is DRY RUN. `--live` dispatches the existing GPU worker through
CHIA/Ray and writes a new artifact. Frozen G2/G3 results are never overwritten.
"""
from __future__ import annotations
import argparse, json, os, pathlib, subprocess
import ray
from chia.base.ChiaFunction import ChiaFunction, get

ROOT = pathlib.Path(os.environ.get(
    "A3_CHIA_PUBLIC_ROOT", pathlib.Path(__file__).resolve().parents[2]))
LOOP = ROOT / "loop" / "epoch002"

@ChiaFunction(num_cpus=1, num_gpus=1, max_retries=0)
def hardware_cell(path, implementation, n, output, gpu_python, batch):
    worker = LOOP / "gpu_worker.py"
    cmd = [gpu_python, str(worker), "--path", path, "--implementation", implementation,
           "--n", str(n), "--variant", "candidate", "--samples", "61",
           "--batch", str(batch), "--output", output]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    pathlib.Path(output + ".log").write_text(p.stdout + p.stderr)
    if p.returncode:
        raise RuntimeError("hardware cell failed; see " + output + ".log")
    return json.loads(pathlib.Path(output).read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--path", choices=["affine","reduction"], default="affine")
    ap.add_argument("--implementation", default="v1")
    ap.add_argument("--n", type=int, default=1048576)
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--output", default="results/public_portability_cell.json")
    ap.add_argument("--live", action="store_true")
    args=ap.parse_args()

    if not args.live:
        print(json.dumps({
            "status":"DRY_RUN",
            "root":str(ROOT),
            "chia_node":"hardware_cell",
            "worker":str(LOOP/"gpu_worker.py"),
            "path":args.path,
            "implementation":args.implementation,
            "n":args.n,
            "frozen_results_mutated":False,
            "public_portability_derivative":True
        },indent=2))
        return

    gpu_python=os.environ.get("A3_GPU_PYTHON")
    if not gpu_python:
        raise SystemExit("A3_GPU_PYTHON is required for --live")
    out=str((ROOT/args.output).resolve())
    pathlib.Path(out).parent.mkdir(parents=True,exist_ok=True)

    ray.init(address=os.environ.get("RAY_ADDRESS", None),
             include_dashboard=False, logging_level="ERROR")
    try:
        result=get(hardware_cell.chia_remote(
            args.path,args.implementation,args.n,out,gpu_python,args.batch))
        if result.get("status")!="PASS":
            raise RuntimeError("non-PASS result")
        print(json.dumps({
            "status":"PASS","artifact":out,"speedup":result.get("speedup"),
            "public_portability_derivative":True
        },indent=2))
    finally:
        ray.shutdown()

if __name__=="__main__":
    main()
