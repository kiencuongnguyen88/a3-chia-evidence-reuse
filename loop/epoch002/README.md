# Epoch 002 development planner

Run from the existing workspace with `loop/epoch002/run_public.sh --path affine`, then `--path reduction`. These commands launch real hardware work and write result artifacts; archived results should be preserved before rerunning. The reduction path requires the first affine comparison. Both paths use the same CHIA hardware node, GPU worker, sampler, planner and evidence types. No second runtime or dependency environment is introduced.

`python3 loop/epoch002/test_planner.py` runs CPU-only planner guard tests. After both live paths finish, use the existing CHIA Python to execute `loop/epoch002/ablations.py` for explicitly offline replay ablations.

The immutable development protocol and matrices are in `evidence/epoch002/`. B0/B1/B2/B3/Full A each start from an identical seed independently for each scenario. B0 is measured first but its results are never supplied to another live planner. B1 uses the actual pinned CHIA cache actor and bypass provider with the inherited caller-defined tag policy. CHIA itself does not prescribe semantic keys. B2 and B3 are workspace implementations, not claims about upstream CHIA functionality.

Full A's typed scope uses the resolved callable: changing the large-vector fused affine kernel does not invalidate measurements of the unchanged small-vector baseline. Its selector prioritizes decision sensitivity per measured cost, omits zero-weight cases, and stops on a proven regression or a fully known rejection. Unknown cases never authorize promotion. B3 orders largest weighted shapes first and uses the same sound rejection rule. Neither selector extrapolates unmeasured performance.

The C_035 champion is unchanged. Development `PROMOTE` means the scenario policy would select the challenger against its baseline; it is not authorization to replace the runnable champion.


Public portability instructions: see `../../RUN_CHIA_LOOP.md`.
