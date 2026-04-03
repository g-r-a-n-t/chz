#!/usr/bin/env python3
"""
Differential testing harness template.

Requirements:
    pip install python-chess

How to use:
    1. Implement the TODO functions that call your backend.
    2. Run this script to compare your backend against python-chess.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple

import chess


# ---------------------------------------------------------------------------
# TODO: adapt these hooks to your backend
# ---------------------------------------------------------------------------

def backend_legal_moves_from_fen(fen: str) -> Set[str]:
    """
    Return the set of legal moves from the given FEN as UCI strings.
    Example return: {"e2e4", "g1f3", ...}
    """
    raise NotImplementedError("Hook this up to your backend")


def backend_apply_uci_move(fen: str, uci: str) -> str:
    """
    Apply one legal move and return the resulting FEN from your backend.
    Prefer a FEN form that includes side to move, castling rights, ep field,
    halfmove clock, and fullmove number.
    """
    raise NotImplementedError("Hook this up to your backend")


def backend_game_flags_from_fen(fen: str) -> dict:
    """
    Return a dict with any game-state flags your backend exposes.
    Suggested keys:
        in_check
        is_checkmate
        is_stalemate
        can_claim_threefold
        can_claim_fifty_moves
        is_seventyfive_moves
        is_fivefold_repetition
    """
    raise NotImplementedError("Hook this up to your backend")


# ---------------------------------------------------------------------------
# Reference logic using python-chess
# ---------------------------------------------------------------------------

def reference_legal_moves_from_fen(fen: str) -> Set[str]:
    board = chess.Board(fen)
    return {move.uci() for move in board.legal_moves}


def reference_apply_uci_move(fen: str, uci: str) -> str:
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        raise ValueError(f"Reference says move is illegal: {uci} in {fen}")
    board.push(move)
    return board.fen(en_passant="legal")


def reference_game_flags_from_fen(fen: str) -> dict:
    board = chess.Board(fen)
    return {
        "in_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "can_claim_threefold": board.can_claim_threefold_repetition(),
        "can_claim_fifty_moves": board.can_claim_fifty_moves(),
        "is_seventyfive_moves": board.is_seventyfive_moves(),
        "is_fivefold_repetition": board.is_fivefold_repetition(),
    }


def compare_one_position(fen: str) -> None:
    ref_moves = reference_legal_moves_from_fen(fen)
    got_moves = backend_legal_moves_from_fen(fen)

    if ref_moves != got_moves:
        missing = sorted(ref_moves - got_moves)
        extra = sorted(got_moves - ref_moves)
        raise AssertionError(
            "Legal move mismatch\n"
            f"FEN: {fen}\n"
            f"Missing: {missing[:20]}\n"
            f"Extra: {extra[:20]}"
        )

    for uci in sorted(random.sample(list(ref_moves), min(10, len(ref_moves)))):
        ref_next = reference_apply_uci_move(fen, uci)
        got_next = backend_apply_uci_move(fen, uci)
        if ref_next != got_next:
            raise AssertionError(
                "Resulting FEN mismatch\n"
                f"Before: {fen}\n"
                f"Move:   {uci}\n"
                f"Ref:    {ref_next}\n"
                f"Got:    {got_next}"
            )

    ref_flags = reference_game_flags_from_fen(fen)
    got_flags = backend_game_flags_from_fen(fen)
    for key, ref_val in ref_flags.items():
        got_val = got_flags.get(key)
        if got_val != ref_val:
            raise AssertionError(
                "Flag mismatch\n"
                f"FEN: {fen}\n"
                f"Key: {key}\n"
                f"Ref: {ref_val}\n"
                f"Got: {got_val}"
            )


def random_playout(seed: int, max_plies: int = 200) -> List[str]:
    rng = random.Random(seed)
    board = chess.Board()
    fens = [board.fen(en_passant="legal")]

    for _ in range(max_plies):
        if board.is_game_over(claim_draw=True):
            break
        moves = list(board.legal_moves)
        if not moves:
            break
        move = rng.choice(moves)
        board.push(move)
        fens.append(board.fen(en_passant="legal"))
    return fens


def run_random_regression(num_games: int = 100, max_plies: int = 200) -> None:
    for seed in range(num_games):
        fens = random_playout(seed, max_plies=max_plies)
        for fen in fens:
            compare_one_position(fen)


def main() -> None:
    curated = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "k7/8/8/4KPpr/8/8/8/8 w - g6 0 1",
        "r3k2r/8/8/8/2b5/8/8/R3K2R w KQkq - 0 1",
        "4k3/P7/8/8/8/8/8/4K3 w - - 0 1",
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
    ]

    for fen in curated:
        compare_one_position(fen)

    run_random_regression(num_games=50, max_plies=150)
    print("Differential tests passed.")


if __name__ == "__main__":
    main()
