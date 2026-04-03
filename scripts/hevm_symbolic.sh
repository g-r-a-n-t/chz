#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEVM="${HEVM:-$ROOT/../hevm/local/bin/hevm}"

die() {
  echo "error: $*" >&2
  exit 1
}

test -x "$HEVM" || die "missing hevm binary at \`$HEVM\` (set HEVM=... to override)"
test -f "$ROOT/out/ChzProofs.runtime.bin" || die "missing out/ChzProofs.runtime.bin (run: make fe-build-rules)"

# hevm shells out to `z3`, so ensure it's on PATH (repo-local install lives next to hevm here).
export PATH="$ROOT/../hevm/local/bin:$PATH"

SYMBOLIC_TIMEOUT_SECS="${SYMBOLIC_TIMEOUT_SECS:-120}"
HEAVY_SYMBOLIC_TIMEOUT_SECS="${HEAVY_SYMBOLIC_TIMEOUT_SECS:-600}"

run_symbolic() {
  local sig="$1"
  local timeout_secs="$2"

  local cmd=(
    "$HEVM" symbolic
    --code-file "$ROOT/out/ChzProofs.runtime.bin"
    --sig "$sig"
    --assertions 0x01
    --initial-storage Empty
    --smttimeout 10000
  )

  if command -v stdbuf >/dev/null 2>&1; then
    cmd=(stdbuf -oL -eL "${cmd[@]}")
  fi

  if command -v timeout >/dev/null 2>&1; then
    cmd=(timeout "$timeout_secs" "${cmd[@]}")
  fi

  "${cmd[@]}"
}

echo "== hevm symbolic: provePieceAtSetPiece =="
run_symbolic "provePieceAtSetPiece(uint256,uint256,uint256)" "$SYMBOLIC_TIMEOUT_SECS"

echo
echo "== hevm symbolic: provePieceAtClearPiece =="
run_symbolic "provePieceAtClearPiece(uint256,uint256)" "$SYMBOLIC_TIMEOUT_SECS"

echo
echo "== hevm symbolic: proveMovePieceEquiv =="
run_symbolic "proveMovePieceEquiv(uint256,uint256,uint256)" "$SYMBOLIC_TIMEOUT_SECS"

echo
echo "== hevm symbolic: proveSetPiecePreservesOtherSquare =="
run_symbolic "proveSetPiecePreservesOtherSquare(uint256,uint256,uint256,uint256)" "$SYMBOLIC_TIMEOUT_SECS"

if [[ "${HEAVY_SYMBOLIC:-0}" == "1" ]]; then
  echo
  echo "== hevm symbolic (heavy): proveCanonicalEpNoAdjPawn =="
  run_symbolic "proveCanonicalEpNoAdjPawn(uint256,uint256)" "$HEAVY_SYMBOLIC_TIMEOUT_SECS"
fi

if [[ "${HEAVY_SYMBOLIC:-0}" == "1" ]]; then
  echo
  echo "== hevm symbolic (heavy): proveRepetitionHashIgnoresHalfFullNoEp =="
  run_symbolic "proveRepetitionHashIgnoresHalfFullNoEp(uint256,uint256,uint256,uint256)" "$HEAVY_SYMBOLIC_TIMEOUT_SECS"
fi
