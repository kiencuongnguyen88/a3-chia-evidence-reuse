# ARCHIVE REFERENCE POLICY

The public candidate intentionally has two reference classes:

## Required runnable/public references
These must resolve inside the public tree:
- README entrypoints;
- public loop scripts;
- planner guard tests;
- champion verification entrypoints;
- public evidence replay;
- public result summaries.

## Archival provenance references
Some preserved development JSON files contain `raw_artifact` or `source` paths that point
into the exact private Epoch 001/002 closure archive. Those references are provenance pointers,
not required public runtime dependencies. The public CPU replay uses the summarized evidence
under `results/` and does not require the private archive.

Exact private closure SHA256 is bound in `provenance/MEASURED_SOURCE_HASH_MAP.json`.
