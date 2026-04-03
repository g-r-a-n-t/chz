#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from typing import List, Tuple

import chz_words
from hevm_backend import HevmChzRules


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def require_python_chess():
    try:
        import chess  # type: ignore
    except ImportError:
        die("missing python-chess (expected in .venv); install via `pip install python-chess`")
    return chess


def kings_adjacent(chess, wk_sq: int, bk_sq: int) -> bool:
    wf, wr = chess.square_file(wk_sq), chess.square_rank(wk_sq)
    bf, br = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    return abs(wf - bf) <= 1 and abs(wr - br) <= 1


def random_minor_only_fen(chess, rng: random.Random, max_minors: int) -> str:
    # Generate a syntactically-valid FEN with only kings and (N/B) minors.
    # We filter by python-chess `is_valid()` rather than attempting to enforce all constraints upfront.
    while True:
        b = chess.Board(None)
        b.clear_board()
        b.turn = bool(rng.getrandbits(1))
        b.castling_rights = 0
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1

        # Kings first (must exist, and must not be adjacent).
        wk_sq = rng.randrange(64)
        bk_sq = rng.randrange(64)
        while bk_sq == wk_sq or kings_adjacent(chess, wk_sq, bk_sq):
            wk_sq = rng.randrange(64)
            bk_sq = rng.randrange(64)

        b.set_piece_at(wk_sq, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk_sq, chess.Piece(chess.KING, chess.BLACK))

        # Random minors.
        wn = rng.randrange(max_minors + 1)
        wb = rng.randrange(max_minors + 1)
        bn = rng.randrange(max_minors + 1)
        bb = rng.randrange(max_minors + 1)

        used = {wk_sq, bk_sq}
        for _ in range(wn):
            sq = rng.randrange(64)
            while sq in used:
                sq = rng.randrange(64)
            used.add(sq)
            b.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.WHITE))

        for _ in range(wb):
            sq = rng.randrange(64)
            while sq in used:
                sq = rng.randrange(64)
            used.add(sq)
            b.set_piece_at(sq, chess.Piece(chess.BISHOP, chess.WHITE))

        for _ in range(bn):
            sq = rng.randrange(64)
            while sq in used:
                sq = rng.randrange(64)
            used.add(sq)
            b.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.BLACK))

        for _ in range(bb):
            sq = rng.randrange(64)
            while sq in used:
                sq = rng.randrange(64)
            used.add(sq)
            b.set_piece_at(sq, chess.Piece(chess.BISHOP, chess.BLACK))

        if b.is_valid():
            return b.fen(en_passant="fen")


def expected_terminal(chess, board) -> Tuple[int, int]:
    # Status encoding in ChzRules:
    # 0 ongoing, 1 white won, 2 black won, 3 draw
    # Reason encoding:
    # 1 checkmate, 2 stalemate, 7 dead position
    if board.is_checkmate():
        status = 2 if board.turn == chess.WHITE else 1
        return status, 1
    if board.is_stalemate():
        return 3, 2
    if board.is_insufficient_material():
        return 3, 7
    return 0, 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Terminal diff: dead-position semantics vs python-chess on random minor-only positions.")
    ap.add_argument("--num-samples", type=int, default=2000)
    ap.add_argument("--max-minors", type=int, default=2, help="Max bishops/knights per side (0..N).")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    chess = require_python_chess()
    backend = HevmChzRules()

    failures = 0
    rng = random.Random(args.seed)
    for i in range(args.num_samples):
        fen = random_minor_only_fen(chess, rng, args.max_minors)
        ref_board = chess.Board(fen)
        exp_status, exp_reason = expected_terminal(chess, ref_board)

        board_word, meta_word = chz_words.fen_to_words(fen)
        got_status, got_reason = backend.classify(board_word, meta_word)
        if (got_status, got_reason) != (exp_status, exp_reason):
            failures += 1
            print(
                "[FAIL] terminal mismatch\n"
                f"fen={fen}\n"
                f"expected=(status={exp_status}, reason={exp_reason})\n"
                f"got=(status={got_status}, reason={got_reason})\n"
                f"ref_insufficient={ref_board.is_insufficient_material()} ref_checkmate={ref_board.is_checkmate()} ref_stalemate={ref_board.is_stalemate()}",
                file=sys.stderr,
            )
            break
        if (i + 1) % 250 == 0:
            print(f"[ok] {i + 1}/{args.num_samples}")

    if failures:
        return 1
    print("dead-position diff passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

