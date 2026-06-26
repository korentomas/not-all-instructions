#!/usr/bin/env bash
# Re-score the canonical v2 logs with the v5 deterministic checkers (audit 2026-06-24
# construct-validity fixes). Deterministic channel only -> no candidate/judge API calls.
# Originals are left untouched; rescored copies land in OUT.
set -uo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-logs/rescored-v5}"
mkdir -p "$OUT"
skipped=0

# Canonical analysis set: logs/retention-v2 + logs/retention-v2-*  (per scripts/run_model.py)
LOGS=$(ls logs/retention-v2/*.eval logs/retention-v2-*/*.eval 2>/dev/null)
total=$(echo "$LOGS" | grep -c .)
echo "re-scoring $total logs -> $OUT"

i=0
for f in $LOGS; do
  i=$((i+1))
  base=$(basename "$f")
  printf "[%d/%d] %s\n" "$i" "$total" "$base"
  if ! inspect score "$f" \
        --scorer src/retention/scorer.py@deterministic_compliance \
        --action overwrite \
        --output-file "$OUT/$base" \
        --display none >/dev/null 2>&1; then
    echo "   ^ skipped (empty/error log)"
    skipped=$((skipped+1))
  fi
done
echo "done: $(ls "$OUT"/*.eval 2>/dev/null | wc -l | tr -d ' ') rescored logs in $OUT ($skipped skipped)"
