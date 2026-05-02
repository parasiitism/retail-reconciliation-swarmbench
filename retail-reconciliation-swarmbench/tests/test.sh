#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_PATH="${1:-${REPORT_PATH:-/workspace/report.json}}"

python "$SCRIPT_DIR/verify.py" "$REPORT_PATH" --assert-full
