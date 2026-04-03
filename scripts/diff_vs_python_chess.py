#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from typing import List, Set

import chz_words
from hevm_backend import HevmChzRules
from movegen import generate_pseudo_legal_moves


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def require_python_chess():
    try:
        import chess  # type: ignore
    except ImportError:
        die("missing python-chess; install via `apt install python3-chess` or `pip install python-chess`")
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


def random_playout(chess, seed: int, max_plies: int) -> List[str]:
    rng = random.Random(seed)
    b = chess.Board()
    fens = [b.fen(en_passant="fen")]
    for _ in range(max_plies):
        if b.is_game_over(claim_draw=True):
            break
        moves = list(b.legal_moves)
        if not moves:
            break
        mv = rng.choice(moves)
        b.push(mv)
        fens.append(b.fen(en_passant="fen"))
    return fens


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Differential check: ChzRules (via hevm) vs python-chess.")
    ap.add_argument("--num-games", type=int, default=20)
    ap.add_argument("--max-plies", type=int, default=80)
    ap.add_argument("--sample-moves", type=int, default=8, help="How many random legal moves to spot-check per position.")
    ap.add_argument("--skip-random", action="store_true")
    args = ap.parse_args(argv)

    chess = require_python_chess()
    backend = HevmChzRules()

    curated = [
        # start
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        # kiwipete
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        # EP discovered check (from edge cases)
        "k7/8/8/4KPpr/8/8/8/8 w - g6 0 1",
        # promotion required
        "4k3/P7/8/8/8/8/8/4K3 w - - 0 1",
    ]

    for fen in curated:
        compare_one_position(chess, backend, fen, sample_moves=args.sample_moves)
        print(f"[ok] curated {fen}")

    if not args.skip_random:
        for seed in range(args.num_games):
            for fen in random_playout(chess, seed, args.max_plies):
                compare_one_position(chess, backend, fen, sample_moves=args.sample_moves)
            print(f"[ok] random seed={seed}")

    print("Differential checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
