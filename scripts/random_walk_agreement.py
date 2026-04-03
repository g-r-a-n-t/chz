#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from typing import List, Set, Tuple

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
        die("missing python-chess; install via `pip install python-chess`")
    return chess


def backend_legal_moves_from_words(backend: HevmChzRules, board_word: int, meta_word: int) -> Set[str]:
    out: Set[str] = set()
    for cand in generate_pseudo_legal_moves(board_word, meta_word):
        res = backend.apply_move(board_word, meta_word, cand.mv_word)
        if res.ok == 1:
            out.add(cand.uci)
    return out


def check_move_set(chess, backend: HevmChzRules, board_word: int, meta_word: int, ref_board) -> None:
    ref_moves = {m.uci() for m in ref_board.legal_moves}
    got_moves = backend_legal_moves_from_words(backend, board_word, meta_word)
    if ref_moves != got_moves:
        missing = sorted(ref_moves - got_moves)
        extra = sorted(got_moves - ref_moves)
        raise AssertionError(
            "Legal move mismatch\n"
            f"FEN: {ref_board.fen(en_passant='fen')}\n"
            f"Missing({len(missing)}): {missing[:50]}\n"
            f"Extra({len(extra)}): {extra[:50]}"
        )


def expected_auto_terminal(chess, board) -> Tuple[int, int]:
    # Status encoding in ChzRules:
    # 0 ongoing, 1 white won, 2 black won, 3 draw
    # Reason encoding:
    # 1 checkmate, 2 stalemate, 6 seventy-five move, 7 dead position
    if board.is_checkmate():
        status = 2 if board.turn == chess.WHITE else 1
        return status, 1
    if board.is_stalemate():
        return 3, 2
    if board.is_insufficient_material():
        return 3, 7
    if board.is_seventyfive_moves():
        return 3, 6
    return 0, 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Random-walk state agreement: ChzRules (hevm) vs python-chess.")
    ap.add_argument("--num-games", type=int, default=25)
    ap.add_argument("--max-plies", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--check-moves-every",
        type=int,
        default=10,
        help="Every N plies, compare full legal move sets (0 = never).",
    )
    args = ap.parse_args(argv)

    chess = require_python_chess()
    backend = HevmChzRules()

    failures = 0
    for game_idx in range(args.num_games):
        rng = random.Random(args.seed + game_idx)
        ref_board = chess.Board()

        board_word, meta_word = chz_words.board_init_standard(), chz_words.meta_init_standard()

        try:
            for ply in range(args.max_plies):
                # Stop only on automatic outcomes supported by `classify_terminal_state`.
                # (Repetition and 50-move claims live in the match contract, not in `ChzRules`.)
                if ref_board.is_checkmate() or ref_board.is_stalemate() or ref_board.is_insufficient_material() or ref_board.is_seventyfive_moves():
                    break

                if args.check_moves_every and args.check_moves_every > 0 and (ply % args.check_moves_every) == 0:
                    check_move_set(chess, backend, board_word, meta_word, ref_board)

                moves = list(ref_board.legal_moves)
                if not moves:
                    break
                mv = rng.choice(moves)
                uci = mv.uci()

                # Apply move in python-chess.
                ref_board.push(mv)
                ref_fen = ref_board.fen(en_passant="fen")

                # Apply same move through ChzRules.
                mv_word = chz_words.move_from_uci(uci)
                res = backend.apply_move(board_word, meta_word, mv_word)
                if res.ok != 1:
                    raise AssertionError(f"backend rejected move {uci} at ply={ply + 1}")

                board_word, meta_word = res.board2, res.meta2
                got_fen = chz_words.words_to_fen(board_word, meta_word)

                if ref_fen != got_fen:
                    raise AssertionError(
                        "FEN mismatch\n"
                        f"ply={ply + 1} uci={uci}\n"
                        f"ref={ref_fen}\n"
                        f"got={got_fen}"
                    )

                exp_status, exp_reason = expected_auto_terminal(chess, ref_board)
                if res.status != exp_status or res.reason != exp_reason:
                    raise AssertionError(
                        "Terminal mismatch\n"
                        f"ply={ply + 1} uci={uci}\n"
                        f"fen={ref_fen}\n"
                        f"expected=(status={exp_status}, reason={exp_reason})\n"
                        f"got=(status={res.status}, reason={res.reason})"
                    )

            print(f"[ok] random_walk game={game_idx} plies={ref_board.ply()}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] random_walk game={game_idx}: {e}", file=sys.stderr)

    if failures:
        print(f"{failures} random-walk game(s) failed.", file=sys.stderr)
        return 1

    print("Random-walk agreement passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
