# CHIA/H100 affine-ReLU development champion

This workspace-owned workload computes `max(0, x*0.5 + 0.25)` on contiguous FP32 CUDA vectors. The incumbent uses three preallocated PyTorch operations. The challenger uses one Triton kernel at 1,048,576 elements and above. The runner resolves the incumbent directly below that threshold, outside the timed region.

Run the packaged champion through an actual GPU-reserved CHIA node:

```bash
champion/verify.sh
```

Or give `--n 16777216 --output /absolute/path/to/new_result.json`. The output must be a new evidence path. The default output is timestamped. `CHIA_EPOCH_ROOT`, `CHIA_PYTHON` and `CHIA_GPU_PYTHON` can override the workspace and interpreter paths. The existing default interpreters are Python 3.10 with CHIA/Ray and Python 3.12 with PyTorch/Triton. Exact versions and installed-runtime/reference hashes are in `evidence/currentness`. CUDA requires the existing H100 and driver. No LLM is involved.

The external bundle includes the matching Ubuntu Python development-header package under `runtime/deps`. The verifier extracts this within the workspace if required. Other Python dependencies are supplied by the existing environments, with package inventories retained for reconstruction; the archive is not a complete VM image.

The public planning loop is under `loop/epoch002/`; see `RUN_CHIA_LOOP.md`. E0, FULL, B0 and B1 stage names refer to this development experiment only. Stage drivers write fixed evidence paths, so preserve the existing experiment before replaying them. Use `verify.sh` for ordinary runnable verification.

Correctness is exact against an independent CPU float64 expression, cast to FP32, for every measured element. Measured inputs are deterministic binary fractions in [-8, 8); extra seeded uniform inputs in [-16, 16] and boundary/tail sizes check the fused kernel. This is not an exhaustive IEEE-754 proof for arbitrary inputs, strides, dtypes or devices.

Timing uses synchronized CUDA events around batches of 100 eager submissions, with compilation, allocation and 30 warmups excluded. Raw samples preserve alternating paired order. Eager submission gaps may be included in event intervals; these are execution-path timings, not isolated device instruction timings. Foreign GPU PID detection quarantines the complete cell. Monitoring is sampled, so extremely short external interference between polls cannot be excluded.

The kernel change is accepted only if both changed cells exceed 1.15x speedup in selective and full-reference checks, exact correctness passes, and control ratios remain at least 0.95. B0 has 61 samples per pair; E0/FULL/B1 have 31. B1 uses CHIA's actual persistent cache and provider bypass with scope-aware tags, and is not intentionally given stale keys. The successful kernel change does not establish A3 novelty, planner superiority, held-out performance or generalization.
