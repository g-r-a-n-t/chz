#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() {
  echo "error: $*" >&2
  exit 1
}

test -x "$ROOT/scripts/hevm_play.sh" || die "missing scripts/hevm_play.sh"
test -f "$ROOT/out/ChzRules.runtime.bin" || die "missing out/ChzRules.runtime.bin (run: make fe-build)"

run_case() {
  local name="$1"
  shift

  echo
  echo "== $name =="
  local out
  out="$("$ROOT/scripts/hevm_play.sh" "$@")"
  echo "$out"

  local total
  total="$(echo "$out" | awk 'NR>1 {sum+=$3} END {print sum+0}')"
  local plies
  plies="$(echo "$out" | awk 'NR>1 {n+=1} END {print n+0}')"

  echo "totalGasUsed=$total plies=$plies"
}

run_case "capture" e2e4 d7d5 e4d5
run_case "en_passant" e2e4 a7a6 e4e5 d7d5 e5d6
run_case "castling_kingside_white" e2e4 e7e5 g1f3 b8c6 f1e2 g8f6 e1g1
run_case "promotion_a7a8q" --start promo a7a8q
run_case "checkmate_fools_mate" f2f3 e7e5 g2g4 d8h4
