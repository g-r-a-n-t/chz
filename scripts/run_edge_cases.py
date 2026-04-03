#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import chz_words


ROOT = Path(__file__).resolve().parent.parent
EDGE_CASES_PATH = ROOT / "data" / "edge_cases.json"
HEVM_RULES = ROOT / "scripts" / "hevm_rules.sh"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def run(cmd: List[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{e.output}") from e


def _parse_abi_word_line(line: str) -> int:
    # `cast abi-decode` prints:
    #   <decimal> [<sci>]
    # or just `<decimal>` for small values.
    tok = line.strip().split()[0]
    return int(tok, 0)


def hevm_apply_move(board_word: int, meta_word: int, mv_word: int) -> Dict[str, int]:
    out = run(
        [
            str(HEVM_RULES),
            "apply",
            hex(board_word),
            hex(meta_word),
            str(mv_word),
        ]
    )
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if len(lines) < 7:
        raise RuntimeError(f"unexpected hevm_rules apply output:\n{out}")

    gas_line = lines[0].strip()
    if not gas_line.startswith("gasUsed="):
        raise RuntimeError(f"unexpected hevm_rules apply output:\n{out}")
    gas_used = int(gas_line.split("=", 1)[1])

    vals = [_parse_abi_word_line(ln) for ln in lines[1:7]]
    ok, board2, meta2, status, reason, pos_hash = vals
    return {
        "gas_used": gas_used,
        "ok": ok,
        "board2": board2,
        "meta2": meta2,
        "status": status,
        "reason": reason,
        "pos_hash": pos_hash,
    }


def hevm_classify(board_word: int, meta_word: int) -> Tuple[int, int]:
    out = run([str(HEVM_RULES), "classify", hex(board_word), hex(meta_word)])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"unexpected hevm_rules classify output:\n{out}")
    status = _parse_abi_word_line(lines[0])
    reason = _parse_abi_word_line(lines[1])
    return status, reason


def hevm_position_hash(board_word: int, meta_word: int) -> int:
    out = run([str(HEVM_RULES), "hash", hex(board_word), hex(meta_word)])
    s = out.strip().splitlines()[-1].strip()
    if not s.startswith("0x"):
        raise RuntimeError(f"unexpected hevm_rules hash output:\n{out}")
    return int(s, 16)


def check_move_ok(case_id: str, board_word: int, meta_word: int, uci: str, want_ok: bool) -> None:
    mv_word = chz_words.move_from_uci(uci)
    res = hevm_apply_move(board_word, meta_word, mv_word)
    ok = res["ok"] == 1
    if ok != want_ok:
        raise AssertionError(
            f"{case_id}: move {uci} expected ok={want_ok} got ok={ok} "
            f"(status={res['status']} reason={res['reason']} gasUsed={res['gas_used']})"
        )


def expected_terminal(stm_white: bool, terminal: str) -> Tuple[int, int]:
    # Status encoding in ChzRules:
    # 0 ongoing, 1 white won, 2 black won, 3 draw
    # Reason encoding:
    # 1 checkmate, 2 stalemate, 7 dead position
    if terminal == "checkmate":
        status = 2 if stm_white else 1
        return status, 1
    if terminal == "stalemate":
        return 3, 2
    if terminal == "dead_position":
        return 3, 7
    raise ValueError(f"unknown terminal kind: {terminal!r}")


def run_case(case: Dict[str, Any]) -> None:
    kind = case.get("kind")
    case_id = case.get("id", "<unknown>")

    if kind == "single_position":
        fen = case.get("fen")
        if not isinstance(fen, str):
            raise AssertionError(f"{case_id}: missing fen")

        if case.get("valid_position") is False:
            try:
                chz_words.fen_to_words(fen)
            except Exception:
                return
            raise AssertionError(f"{case_id}: expected invalid position but fen_to_words succeeded")

        board_word, meta_word = chz_words.fen_to_words(fen)

        moves = case.get("candidate_moves") or {}
        for uci in moves.get("legal_uci", []):
            check_move_ok(case_id, board_word, meta_word, uci, want_ok=True)
        for uci in moves.get("illegal_uci", []):
            check_move_ok(case_id, board_word, meta_word, uci, want_ok=False)
        for uci in moves.get("illegal_like_uci", []):
            check_move_ok(case_id, board_word, meta_word, uci, want_ok=False)

        terminal = case.get("terminal")
        if terminal is not None:
            stm_field = fen.split()[1]
            stm_white = stm_field == "w"
            exp_status, exp_reason = expected_terminal(stm_white, terminal)
            got_status, got_reason = hevm_classify(board_word, meta_word)
            if got_status != exp_status or got_reason != exp_reason:
                raise AssertionError(
                    f"{case_id}: expected terminal {terminal} -> (status={exp_status}, reason={exp_reason}) "
                    f"got (status={got_status}, reason={got_reason})"
                )
        return

    if kind == "position_pair":
        fen_a = case.get("fen_a")
        fen_b = case.get("fen_b")
        if not isinstance(fen_a, str) or not isinstance(fen_b, str):
            raise AssertionError(f"{case_id}: missing fen_a/fen_b")

        board_a, meta_a = chz_words.fen_to_words(fen_a)
        board_b, meta_b = chz_words.fen_to_words(fen_b)

        want_same = case.get("same_position_for_repetition")
        if want_same is None:
            raise AssertionError(f"{case_id}: missing same_position_for_repetition")
        if not isinstance(want_same, bool):
            raise AssertionError(f"{case_id}: same_position_for_repetition must be bool")

        h_a = hevm_position_hash(board_a, meta_a)
        h_b = hevm_position_hash(board_b, meta_b)
        got_same = h_a == h_b
        if got_same != want_same:
            raise AssertionError(f"{case_id}: expected same={want_same} got same={got_same}")
        return

    raise AssertionError(f"{case_id}: unknown kind {kind!r}")


def main(argv: List[str]) -> int:
    if not HEVM_RULES.exists():
        die(f"missing {HEVM_RULES}")

    if not EDGE_CASES_PATH.exists():
        die(f"missing {EDGE_CASES_PATH}")

    try:
        cases = json.loads(EDGE_CASES_PATH.read_text())
    except Exception as e:
        die(f"failed to parse {EDGE_CASES_PATH}: {e}")

    if not isinstance(cases, list):
        die(f"expected a JSON list in {EDGE_CASES_PATH}")

    failures = 0
    for case in cases:
        case_id = (case or {}).get("id", "<unknown>")
        try:
            run_case(case)
            print(f"[ok] {case_id}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {case_id}: {e}", file=sys.stderr)

    if failures:
        print(f"{failures} edge case(s) failed.", file=sys.stderr)
        return 1

    print("All edge cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
