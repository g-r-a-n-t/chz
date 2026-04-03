#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEVM="${HEVM:-$ROOT/../hevm/local/bin/hevm}"
CODE_FILE="${CODE_FILE:-$ROOT/out/ChzRules.runtime.bin}"

die() {
  echo "error: $*" >&2
  exit 1
}

command -v cast >/dev/null 2>&1 || die "missing \`cast\` on PATH"
command -v jq >/dev/null 2>&1 || die "missing \`jq\` on PATH"
test -x "$HEVM" || die "missing hevm binary at \`$HEVM\` (set HEVM=... to override)"
test -f "$CODE_FILE" || die "missing \`$CODE_FILE\` (run: make fe-build)"
test -x "$ROOT/scripts/chz_words.py" || die "missing \`scripts/chz_words.py\`"

usage() {
  cat >&2 <<'USAGE'
Usage:
  scripts/hevm_play.sh [--start standard|promo] <uci-move> [<uci-move> ...]
  scripts/hevm_play.sh --fen "<FEN>" <uci-move> [<uci-move> ...]

Example:
  scripts/hevm_play.sh e2e4 e7e5 g1f3 b8c6
  scripts/hevm_play.sh --start promo a7a8q
  scripts/hevm_play.sh --fen "k7/8/8/4Pp2/8/8/8/7K w - f6 0 1" e5f6

Output columns:
  ply uci gasUsed ok status reason pos_hash
USAGE
}

start="standard"
fen=""
while [[ $# -ge 1 ]]; do
  case "${1:-}" in
    --start)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      start="$2"
      shift 2
      ;;
    --fen)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      fen="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ -n "$fen" && "$start" != "standard" ]]; then
  die "choose either --fen or --start (not both)"
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

init_desc="$start"
if [[ -n "$fen" ]]; then
  init_desc="fen"
  mapfile -t init_words < <("$ROOT/scripts/chz_words.py" fen "$fen")
else
  mapfile -t init_words < <("$ROOT/scripts/chz_words.py" "$start")
fi
[[ ${#init_words[@]} -ge 2 ]] || die "unexpected output from scripts/chz_words.py $init_desc"
board="${init_words[0]}"
meta="${init_words[1]}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "ply uci gasUsed ok status reason pos_hash"

ply=0
for uci in "$@"; do
  ply=$((ply + 1))
  mv="$("$ROOT/scripts/chz_words.py" uci "$uci")"
  calldata="$(cast calldata 'applyMove(uint256,uint256,uint256)' "$board" "$meta" "$mv")"

  (
    cd "$tmpdir"
    "$HEVM" exec --code-file "$CODE_FILE" --calldata "$calldata" --gas 0xffffffffffff --verb 0 --json-trace
  ) >"$tmpdir/out.txt"

  ret="$(sed -n 's/"Return: \(0x[0-9a-fA-F]*\)"/\1/p' "$tmpdir/out.txt")"
  gas_used="$(tail -n 1 "$tmpdir/hevm-trace.jsonl" | jq -r '.gasUsed')"

  decoded="$(cast decode-abi --json 'applyMove(uint256,uint256,uint256)(uint256,uint256,uint256,uint256,uint256,uint256)' "$ret")"

  ok="$(echo "$decoded" | jq -r '.[0]')"
  board2="$(echo "$decoded" | jq -r '.[1]')"
  meta2="$(echo "$decoded" | jq -r '.[2]')"
  status="$(echo "$decoded" | jq -r '.[3]')"
  reason="$(echo "$decoded" | jq -r '.[4]')"
  pos_hash="$(echo "$decoded" | jq -r '.[5]')"

  echo "$ply $uci $gas_used $ok $status $reason $pos_hash"

  if [[ "$ok" != "1" ]]; then
    die "move rejected at ply $ply ($uci)"
  fi

  board="$board2"
  meta="$meta2"

  if [[ "$status" != "0" ]]; then
    break
  fi
done
