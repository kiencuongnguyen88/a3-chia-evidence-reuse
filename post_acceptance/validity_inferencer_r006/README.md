# Post-acceptance bounded validity inferencer — R006 / R008 repair

This folder is an **additive post-acceptance research derivative** of the frozen R1 artifact. It does not modify the accepted R1 planner, champion, evidence, frozen G2/G3, or scientific promotion state.

## Claim ceiling

Validated only for the two bounded R1 consumers (`affine`, `reduction`) using source/replay semantics. It is deliberately conservative and may over-invalidate. It does not claim arbitrary Python/CUDA semantic analysis, dynamic alias resolution, hidden JIT dependency completeness, fresh GPU performance, or R2 superiority.

## R008 safety repairs

R008 closes four false-reuse counterexamples found by adversarial BBR against R007: comparator baseline changes, affine import retargeting, reduction dispatch/setup changes, and reduction baseline changes. It also binds dtype/layout and makes the CPU acceptance runner read-only.

## CPU acceptance

From repository root:

```bash
python -B post_acceptance/validity_inferencer_r006/run_cpu_acceptance.py
```

The runner first verifies the exact frozen R1 anchor hashes, then executes the existing planner guards and the repaired inferencer tests with bytecode writes disabled. It prints the receipt to stdout and intentionally writes no result file. No GPU/H100 is required.

## Infrastructure note

The event-provided H100 allocation has expired. This derivative remains CPU/source-replay only until a future independent scientific reason and infrastructure exist.
