#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

import chz_words
from hevm_backend import HevmChzRules
from movegen import generate_pseudo_legal_moves


UNICODE_PIECE: Dict[int, str] = {
    chz_words.PIECE_WP: "♙",
    chz_words.PIECE_WN: "♘",
    chz_words.PIECE_WB: "♗",
    chz_words.PIECE_WR: "♖",
    chz_words.PIECE_WQ: "♕",
    chz_words.PIECE_WK: "♔",
    chz_words.PIECE_BP: "♟",
    chz_words.PIECE_BN: "♞",
    chz_words.PIECE_BB: "♝",
    chz_words.PIECE_BR: "♜",
    chz_words.PIECE_BQ: "♛",
    chz_words.PIECE_BK: "♚",
    0: ".",
}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


def stm(meta_word: int) -> str:
    white = ((meta_word >> chz_words.STM_SHIFT) & 1) == 1
    return "white" if white else "black"


def _unpack_board(board_word: int) -> List[int]:
    out: List[int] = [0] * 64
    for sq in range(64):
        out[sq] = (board_word >> (sq * 4)) & 0xF
    return out


def render_board(board_word: int) -> str:
    board = _unpack_board(board_word)
    lines: List[str] = []
    for rank in range(7, -1, -1):
        row: List[str] = []
        for file in range(8):
            sq = file + rank * 8
            row.append(UNICODE_PIECE.get(board[sq], "?"))
        lines.append(f"{rank + 1}  " + " ".join(row))
    lines.append("")
    lines.append("   a b c d e f g h")
    return "\n".join(lines)


def legal_moves(backend: HevmChzRules, board_word: int, meta_word: int) -> List[str]:
    out: List[str] = []
    for cand in generate_pseudo_legal_moves(board_word, meta_word):
        res = backend.apply_move(board_word, meta_word, cand.mv_word)
        if res.ok == 1:
            out.append(cand.uci)
    return sorted(out)


def print_status(res_status: int, res_reason: int) -> None:
    if res_status == 0 and res_reason == 0:
        return

    # ChzRules encoding:
    # status: 0 ongoing, 1 white won, 2 black won, 3 draw
    # reason: 1 checkmate, 2 stalemate, 6 75-move, 7 dead position, 3/4/5 are repetition/50-move (match-layer)
    status_s = {0: "ongoing", 1: "white_won", 2: "black_won", 3: "draw"}.get(res_status, f"status_{res_status}")
    reason_s = {
        0: "none",
        1: "checkmate",
        2: "stalemate",
        3: "threefold",
        4: "fivefold",
        5: "fifty_move",
        6: "seventy_five_move",
        7: "dead_position",
        8: "resignation",
        9: "timeout",
        10: "timeout_no_mate",
        11: "agreed_draw",
    }.get(res_reason, f"reason_{res_reason}")
    print(f"status={status_s} reason={reason_s}")


HELP = """Commands:
  <uci>              Apply a move, e.g. e2e4, e7e8q
  moves              List legal moves (UCI)
  fen                Print current FEN
  hash               Print repetition hash (positionHash)
  status             Print terminal classification (classify)
  reset              Reset to standard initial position
  load <FEN...>      Load an exact FEN (6 fields; strict)
  undo               Undo one ply
  help               Show this help
  quit               Exit
"""


def main(argv: Sequence[str]) -> int:
    ap = argparse.ArgumentParser(description="Terminal UI demo for ChzRules (via hevm).")
    ap.add_argument("--fen", type=str, default=None, help="Start from a FEN instead of the standard initial position.")
    args = ap.parse_args(list(argv))

    backend = HevmChzRules()

    if args.fen:
        board_word, meta_word = chz_words.fen_to_words(args.fen)
    else:
        board_word, meta_word = chz_words.board_init_standard(), chz_words.meta_init_standard()

    history: List[Tuple[int, int]] = [(board_word, meta_word)]

    print(HELP.strip())
    while True:
        board_word, meta_word = history[-1]
        print()
        print(render_board(board_word))
        print(f"turn={stm(meta_word)}")

        status, reason = backend.classify(board_word, meta_word)
        print_status(status, reason)

        try:
            line = input("> ").strip()
        except EOFError:
            print()
            return 0

        if not line:
            continue

        if line in {"q", "quit", "exit"}:
            return 0
        if line in {"h", "help", "?"}:
            print(HELP.strip())
            continue
        if line == "fen":
            print(chz_words.words_to_fen(board_word, meta_word))
            continue
        if line == "hash":
            h = backend.position_hash(board_word, meta_word)
            print(hex(h))
            continue
        if line == "status":
            s, r = backend.classify(board_word, meta_word)
            print_status(s, r)
            continue
        if line == "reset":
            history = [(chz_words.board_init_standard(), chz_words.meta_init_standard())]
            continue
        if line == "undo":
            if len(history) <= 1:
                print("cannot undo")
            else:
                history.pop()
            continue
        if line.startswith("load "):
            fen = line[len("load ") :].strip()
            if not fen:
                print("usage: load <FEN...>")
                continue
            try:
                b, m = chz_words.fen_to_words(fen)
            except Exception as e:
                print(f"invalid fen: {e}")
                continue
            history = [(b, m)]
            continue
        if line == "moves":
            ms = legal_moves(backend, board_word, meta_word)
            print(f"{len(ms)} legal move(s)")
            if ms:
                print(" ".join(ms))
            continue

        # Assume a UCI move.
        uci = line.replace(" ", "")
        try:
            mv_word = chz_words.move_from_uci(uci)
        except Exception as e:
            print(f"invalid input: {e}")
            continue

        res = backend.apply_move(board_word, meta_word, mv_word)
        if res.ok != 1:
            print(f"illegal move: {uci}")
            continue

        history.append((res.board2, res.meta2))

    # unreachable


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

