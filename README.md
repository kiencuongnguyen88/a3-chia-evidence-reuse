# Change-Aware Evidence Reuse and Sufficient Experiment Planning in CHIA — Public Release Ready R005

**State:** publicly released, BSD-3-Clause licensed; scientific claim ceiling unchanged.

Public artifact URL: `https://github.com/kiencuongnguyen88/a3-chia-evidence-reuse`  
Exact pre-publication R005 commit: `82532378ea04c5ffd0e2168f4ae00244dec837ee`.

This artifact supports the submission claim that evidence-scope-aware planning can reduce measurement demand under specific change/evidence conditions, while a frozen held-out evaluation shows that the richer planner collapses to a strong adaptive baseline when those enabling signals are absent.

## Claim ceiling

- Development: FULL_A used 11 live cells vs B3 14 with equal tested decision fidelity to B0.
- Frozen G2/G3: FULL_A and B3 both used five live cells; the preregistered 10% material advantage failed.
- Final held-out acceptance: **NO_PROMOTION**.
- The prior runnable champion remains preserved.
- No claim of general FULL_A superiority, external-canonical G2/G3 equivalence, or v2/slow generalization.

## Quick checks

```bash
python3 loop/epoch002/test_planner.py
python3 replay_public_evidence.py
sha256sum -c SHA256SUMS.txt
```

The quick checks do not require private Drive credentials or the original execution VM. Full H100 timing replay requires compatible CHIA/CUDA hardware infrastructure and is outside this prepublication build.


## CHIA-loop portability entrypoint

The measured execution used CHIA/Ray orchestration. This package now contains a
post-measurement portability derivative at `loop/epoch002/run_chia_loop.py` and
review instructions in `RUN_CHIA_LOOP.md`.

The portability derivative replaces machine-specific absolute paths with explicit
configuration. It is **not claimed byte-identical** to the measured wrapper.
Exact measured-source hashes are bound in `provenance/MEASURED_SOURCE_HASH_MAP.json`.


---

## Day-2 acceptance candidate

This R004-day2 candidate keeps the R003 scientific claim boundary unchanged and adds:

- public-safe post-heldout atlas and Phase-G summaries;
- exact typed affine seed metadata needed to demonstrate evidence-validity behavior;
- a bounded `acceptance/run_full_loop_acceptance.py` orchestration harness.

Artifact acceptance state: **PASS_PUBLIC_FULL_LOOP_ACCEPTANCE / PASS_CHECKSUM_READBACK**. Public GitHub release was Human-authorized and verified after the exact R005 publication commit.

A successful acceptance is an artifact-portability result only. It does not change `C_128`,
`NO_PROMOTION`, `C_035`, or frozen G2/G3.


## License and final artifact acceptance

- Project license: **BSD-3-Clause** (`LICENSE`).
- Third-party attribution: `THIRD_PARTY_NOTICES.md`.
- Full-loop acceptance: `results/public_ful_loop_acceptance/FULL_LOOP_ACCEPTANCE.json`.
- Public durability receipt: `results/public_full_loop_acceptance/ACCEPTANCE_DURABILITY_PUBLIC_RECEIPT.json`.
- Public-sanitization ledger: `provenance/PUBLIC_SANITIZATION_LEDGER.md`.

The artifact-acceptance claim ceiling remains **artifact portability and orchestration only**; it does not promote FULL_A or alter frozen G2/G3.
