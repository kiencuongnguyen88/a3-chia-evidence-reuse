#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="${A3_CHIA_PUBLIC_ROOT:-$(cd "$HERE/.." && pwd)}"
export A3_CHIA_PUBLIC_ROOT="$ROOT"
mkdir -p "$ROOT/results/champion_verify"
if [ "$#" -eq 0 ]; then
  set -- --output "$ROOT/results/champion_verify/verify_$(date -u +%Y%m%dT%H%M%SZ).json" --dry-run
fi
exec "${A3_CHIA_PYTHON:-python3}" "$HERE/verify_chia.py" "$@"
