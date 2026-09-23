# RUN THE PUBLIC CHIA LOOP

The package separates the exact measured execution from a public portability derivative.

- Measured-source hashes: `provenance/MEASURED_SOURCE_HASH_MAP.json`
- Public CHIA/Ray entrypoint: `loop/epoch002/run_chia_loop.py`

## Static / CPU-only review

```bash
python3 loop/epoch002/test_planner.py
python3 replay_public_evidence.py
sha256sum -c SHA256SUMS.txt
```

`loop/epoch002/run_chia_loop.py` imports CHIA/Ray even in its dry-run mode, so run that entrypoint inside the pinned CHIA/Ray environment described in `ENVIRONMENT.md`. The terminal H100 full-loop acceptance already exercised the CHIA/Ray portability path; absence of Ray in a generic CPU review shell is not an artifact failure.

## Live CHIA/H100 portability run

```bash
export A3_CHIA_PYTHON=/path/to/python-with-chia
export A3_GPU_PYTHON=/path/to/python-with-torch-triton
export A3_CHIA_PUBLIC_ROOT="$PWD"

"$A3_CHIA_PYTHON" loop/epoch002/run_chia_loop.py \
  --live --path affine --implementation v1 --n 1048576 \
  --output results/public_portability_cell.json
```

A portability run generates new exploratory evidence. It does not modify or replace
the frozen G2/G3 result.
