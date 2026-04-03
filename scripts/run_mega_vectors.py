#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import chz_words
from hevm_backend import HevmChzRules
from movegen import generate_pseudo_legal_moves


ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "chess_validation_mega_reference" / "machine" / "test_vectors.json"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def require_python_chess():
    try:
        import chess  # type: ignore
    except ImportError:
        die("missing python-chess (expected in .venv); install via `pip install python-chess`")
    return chess


def backend_legal_moves_from_fen(backend: HevmChzRules, fen: str) -> Set[str]:
    board_word, meta_word = chz_words.fen_to_words(fen)
    out: Set[str] = set()
    for cand in generate_pseudo_legal_moves(board_word, meta_word):
        res = backend.apply_move(board_word, meta_word, cand.mv_word)
        if res.ok == 1:
            out.add(cand.uci)
    return out


def backend_apply_uci_move(backend: HevmChzRules, fen: str, uci: str) -> str:
    board_word, meta_word = chz_words.fen_to_words(fen)
    mv_word = chz_words.move_from_uci(uci)
    res = backend.apply_move(board_word, meta_word, mv_word)
    if res.ok != 1:
        raise AssertionError(f"backend rejected move {uci} from {fen}")
    return chz_words.words_to_fen(res.board2, res.meta2)


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


def _kings_adjacent(chess, board) -> bool:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return False
    wf, wr = wk % 8, wk // 8
    bf, br = bk % 8, bk // 8
    return abs(wf - bf) <= 1 and abs(wr - br) <= 1


def failure_codes_from_python_chess_status(chess, board) -> Set[str]:
    st = board.status()
    out: Set[str] = set()

    if st & chess.STATUS_NO_WHITE_KING:
        out.add("no_white_king")
    if st & chess.STATUS_NO_BLACK_KING:
        out.add("no_black_king")
    if st & chess.STATUS_TOO_MANY_KINGS:
        out.add("too_many_kings")
    if st & chess.STATUS_BAD_CASTLING_RIGHTS:
        out.add("bad_castling_rights")
    if st & chess.STATUS_PAWNS_ON_BACKRANK:
        out.add("pawns_on_backrank")
    if st & chess.STATUS_TOO_MANY_WHITE_PAWNS:
        out.add("too_many_white_pawns")
    if st & chess.STATUS_TOO_MANY_BLACK_PAWNS:
        out.add("too_many_black_pawns")
    if st & chess.STATUS_TOO_MANY_WHITE_PIECES:
        out.add("too_many_white_pieces")
    if st & chess.STATUS_TOO_MANY_BLACK_PIECES:
        out.add("too_many_black_pieces")
    if st & chess.STATUS_INVALID_EP_SQUARE:
        out.add("invalid_ep_square")
    if st & chess.STATUS_OPPOSITE_CHECK:
        out.add("side_not_to_move_in_check")
    if st & chess.STATUS_IMPOSSIBLE_CHECK:
        out.add("impossible_check")
    if st & chess.STATUS_TOO_MANY_CHECKERS:
        out.add("too_many_checkers")

    if _kings_adjacent(chess, board):
        out.add("kings_adjacent")

    # python-chess status bits don't always surface "both kings in check" as a distinct
    # flag, but the mega reference expects it as a named failure mode.
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is not None and bk is not None:
        white_in_check = board.is_attacked_by(chess.BLACK, wk)
        black_in_check = board.is_attacked_by(chess.WHITE, bk)
        if white_in_check and black_in_check:
            out.add("impossible_check")

    return out


def assert_ep_hash_canonicalization(backend: HevmChzRules, fen: str) -> None:
    board_word, meta_word = chz_words.fen_to_words(fen)

    ep_file = (meta_word >> chz_words.EP_SHIFT) & 0xF
    if ep_file == chz_words.EP_NONE or ep_file >= 8:
        raise AssertionError("expected test vector to include a spec-fen EP square")

    h1 = backend.position_hash(board_word, meta_word)

    # Clear EP file in meta and ensure repetition hash is unchanged when no legal EP capture exists.
    cleared = meta_word & ~(0xF << chz_words.EP_SHIFT)
    meta_no_ep = cleared | (chz_words.EP_NONE << chz_words.EP_SHIFT)
    h2 = backend.position_hash(board_word, meta_no_ep)

    if h1 != h2:
        raise AssertionError("expected positionHash to ignore non-captureable EP, but hashes differed")


def compare_one_position(chess, backend: HevmChzRules, fen: str, *, sample_moves: int) -> None:
    ref_board = chess.Board(fen)
    ref_moves = {m.uci() for m in ref_board.legal_moves}
    got_moves = backend_legal_moves_from_fen(backend, fen)

    if ref_moves != got_moves:
        missing = sorted(ref_moves - got_moves)
        extra = sorted(got_moves - ref_moves)
        raise AssertionError(
            "Legal move mismatch\n"
            f"FEN: {fen}\n"
            f"Missing({len(missing)}): {missing[:50]}\n"
            f"Extra({len(extra)}): {extra[:50]}"
        )

    if not ref_moves:
        return

    rng = random.Random(0)
    k = min(sample_moves, len(ref_moves))
    for uci in rng.sample(sorted(ref_moves), k):
        # reference next FEN, keeping the *raw* ep square (to match chz meta).
        b2 = chess.Board(fen)
        b2.push(chess.Move.from_uci(uci))
        ref_next = b2.fen(en_passant="fen")

        got_next = backend_apply_uci_move(backend, fen, uci)
        if ref_next != got_next:
            raise AssertionError(
                "Resulting FEN mismatch\n"
                f"Before: {fen}\n"
                f"Move:   {uci}\n"
                f"Ref:    {ref_next}\n"
                f"Got:    {got_next}"
            )


def main(argv: List[str]) -> int:
    chess = require_python_chess()

    if not VECTORS_PATH.exists():
        die(f"missing {VECTORS_PATH}")

    raw = json.loads(VECTORS_PATH.read_text())
    vectors = raw.get("vectors") or []
    if not isinstance(vectors, list):
        die(f"expected 'vectors' to be a list in {VECTORS_PATH}")

    backend = HevmChzRules()

    failures = 0
    for vec in vectors:
        vec_id = (vec or {}).get("id", "<unknown>")
        name = (vec or {}).get("name", vec_id)
        fen = (vec or {}).get("fen")
        expected_validity = (vec or {}).get("expected_validity")
        expected_terminal_kind = (vec or {}).get("expected_terminal")
        expected_failures = set((vec or {}).get("expected_failures") or [])

        try:
            if not isinstance(fen, str):
                raise AssertionError("missing fen")
            if expected_validity not in {"BASIC_VALID", "INVALID"}:
                raise AssertionError(f"unknown expected_validity: {expected_validity!r}")

            ref_board = chess.Board(fen)
            got_codes = failure_codes_from_python_chess_status(chess, ref_board)
            is_valid = ref_board.is_valid()

            if expected_validity == "BASIC_VALID":
                if not is_valid:
                    raise AssertionError(f"python-chess says invalid: {sorted(got_codes)}")

                # Ensure chz parser can represent the position.
                board_word, meta_word = chz_words.fen_to_words(fen)
                _ = (board_word, meta_word)

                if expected_terminal_kind is not None:
                    stm_white = fen.split()[1] == "w"
                    exp_status, exp_reason = expected_terminal(stm_white, expected_terminal_kind)
                    got_status, got_reason = backend.classify(board_word, meta_word)
                    if got_status != exp_status or got_reason != exp_reason:
                        raise AssertionError(
                            f"terminal mismatch: expected {expected_terminal_kind} -> (status={exp_status}, reason={exp_reason}) "
                            f"got (status={got_status}, reason={got_reason})"
                        )

                # Run a full legal move-set check + a few transition spot checks.
                compare_one_position(chess, backend, fen, sample_moves=8)

                # Special policy vector: EP canonicalization for repetition.
                if vec_id == "TV-004":
                    # Ensure EP square matches spec-FEN encoding in our meta word.
                    ep_file = (meta_word >> chz_words.EP_SHIFT) & 0xF
                    if ep_file != 4:
                        raise AssertionError(f"expected ep_file=4 for e3, got {ep_file}")
                    assert_ep_hash_canonicalization(backend, fen)

            else:
                # INVALID
                if is_valid:
                    raise AssertionError("python-chess says valid, expected invalid")

                if expected_failures:
                    missing = sorted(expected_failures - got_codes)
                    if missing:
                        raise AssertionError(
                            f"expected failure codes missing from python-chess status: {missing}; got={sorted(got_codes)}"
                        )

            print(f"[ok] {vec_id} {name}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {vec_id} {name}: {e}", file=sys.stderr)

    if failures:
        print(f"{failures} mega vector(s) failed.", file=sys.stderr)
        return 1

    print("All mega vectors passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
