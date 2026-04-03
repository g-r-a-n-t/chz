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

usage() {
  cat >&2 <<'USAGE'
Usage:
  scripts/hevm_rules.sh hash <board_word> <meta_word>
  scripts/hevm_rules.sh classify <board_word> <meta_word>
  scripts/hevm_rules.sh apply <board_word> <meta_word> <mv_word>

Notes:
  - All values can be decimal or 0x-prefixed hex.
  - Standard initial words:
      # portable across sh/bash/zsh (avoids bash-only `mapfile`)
      set -- $(scripts/chz_words.py standard); BOARD=$1; META=$2
  - `apply` prints gas used (via hevm json trace) and decodes the 6-word tuple:
      (ok, board2, meta2, status, reason, pos_hash)
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

cmd="$1"
shift

case "$cmd" in
  hash)
    [[ $# -eq 2 ]] || { usage; exit 2; }
    board="$1"
    meta="$2"
    calldata="$(cast calldata 'positionHash(uint256,uint256)' "$board" "$meta")"
    out="$("$HEVM" exec --code-file "$CODE_FILE" --calldata "$calldata" --gas 0xffffffffffff --verb 0)"
    echo "$out" | sed -n 's/"Return: \(0x[0-9a-fA-F]*\)"/\1/p'
    ;;

  classify)
    [[ $# -eq 2 ]] || { usage; exit 2; }
    board="$1"
    meta="$2"
    calldata="$(cast calldata 'classify(uint256,uint256)' "$board" "$meta")"
    out="$("$HEVM" exec --code-file "$CODE_FILE" --calldata "$calldata" --gas 0xffffffffffff --verb 0)"
    ret="$(echo "$out" | sed -n 's/"Return: \(0x[0-9a-fA-F]*\)"/\1/p')"
    cast abi-decode 'classify(uint256,uint256)(uint256,uint256)' "$ret"
    ;;

  apply)
    [[ $# -eq 3 ]] || { usage; exit 2; }
    board="$1"
    meta="$2"
    mv="$3"

    calldata="$(cast calldata 'applyMove(uint256,uint256,uint256)' "$board" "$meta" "$mv")"

    tmpdir="$(mktemp -d)"
    trap 'rm -rf "$tmpdir"' EXIT
    (
      cd "$tmpdir"
      "$HEVM" exec --code-file "$CODE_FILE" --calldata "$calldata" --gas 0xffffffffffff --verb 0 --json-trace
    ) >"$tmpdir/out.txt"

    ret="$(sed -n 's/"Return: \(0x[0-9a-fA-F]*\)"/\1/p' "$tmpdir/out.txt")"
    gas_used="$(tail -n 1 "$tmpdir/hevm-trace.jsonl" | jq -r '.gasUsed')"

    echo "gasUsed=$gas_used"
    cast abi-decode 'applyMove(uint256,uint256,uint256)(uint256,uint256,uint256,uint256,uint256,uint256)' "$ret"
    ;;

  *)
    usage
    exit 2
    ;;
esac
