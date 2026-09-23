#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="${A3_CHIA_PUBLIC_ROOT:-$(cd "$HERE/../.." && pwd)}"
export A3_CHIA_PUBLIC_ROOT="$ROOT"
exec "${A3_CHIA_PYTHON:-python3}" "$HERE/run_chia_loop.py" "$@"
