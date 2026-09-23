# Public sanitization ledger

This release-ready tree is derived from `A3_CHIA_PUBLIC_RELEASE_CANDIDATE_R004_DAY2`.

- Removed Python `__pycache__` / `.pyc` build caches.
- Removed the obsolete `LICENSE_PENDING_HUMAN_SELECTION.md`.
- Activated project-level `BSD-3-Clause` license after explicit Human confirmation.
- Replaced the internal Drive pointer in `evidence/epoch002/acceptance.json` with a public redaction marker.
- Original internal `acceptance.json` SHA256 before that public projection: `b1e7a46351c4a520c4b432de90010f811ab8d4e213fc84ba28c39dffd58ba836`.
- Added exact parsed `FULL_LOOP_ACCEPTANCE.json` from the terminal machine readback.
- Added a public durability projection that preserves verdict/checksum/time/science boundaries while omitting private local/Drive paths.
- Machine readback source SHA256: `0178f13780bcaea79c242c40abfc26fc33b63b65c2c34c7894f32725810d9eb4`.

No scientific value, frozen decision, result number, C_128 / NO_PROMOTION / C_035 state, or G2/G3 evidence was changed by this sanitization.
