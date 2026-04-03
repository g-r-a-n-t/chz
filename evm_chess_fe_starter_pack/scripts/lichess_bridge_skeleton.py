#!/usr/bin/env python3
"""
Lichess bridge skeleton.

Requirements:
    pip install berserk python-chess requests-oauthlib

This is a template. Fill in your own:
- token loading
- match selection
- contract client
- canonical hash logic
- retry / nonce management
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import chess


# Optional dependency; leave import lazy if you prefer.
try:
    import berserk
except ImportError:
    berserk = None


@dataclass
class ChainState:
    board_hash: str
    ply: int
    status: str


class ContractClient:
    """
    TODO: adapt to your chain stack.
    """

    def fetch_match_state(self, match_id: int) -> ChainState:
        raise NotImplementedError

    def submit_move(self, match_id: int, compact_move: int, claim_flags: int = 0) -> str:
        raise NotImplementedError


def load_lichess_client(token: str):
    if berserk is None:
        raise RuntimeError("Install berserk first")
    session = berserk.TokenSession(token)
    return berserk.Client(session=session)


def uci_to_compact_move(board: chess.Board, uci: str) -> int:
    move = chess.Move.from_uci(uci)
    from_sq = move.from_square
    to_sq = move.to_square

    promo = 0
    if move.promotion == chess.KNIGHT:
        promo = 1
    elif move.promotion == chess.BISHOP:
        promo = 2
    elif move.promotion == chess.ROOK:
        promo = 3
    elif move.promotion == chess.QUEEN:
        promo = 4

    return from_sq | (to_sq << 6) | (promo << 12)


def canonical_repetition_hash(board: chess.Board) -> str:
    """
    TODO:
      - match the contract's exact canonical repetition-state hashing
      - include legal ep normalization if your contract does
    """
    # Placeholder: use EPD/FEN-like normalized text only for local testing,
    # not as a production replacement for the contract's exact hash.
    epd = board.epd(en_passant="legal")
    return epd


def bridge_game(token: str, game_id: str, match_id: int, contract: ContractClient) -> None:
    client = load_lichess_client(token)

    # Bot example flow. For board/non-bot endpoints, adapt accordingly.
    stream = client.bots.stream_game_state(game_id)
    full = next(stream)

    board = chess.Board()
    seen_moves = []

    # If the stream already includes moves, replay them.
    moves_field = full.get("state", {}).get("moves") or full.get("moves") or ""
    if moves_field:
        for uci in moves_field.split():
            board.push(chess.Move.from_uci(uci))
            seen_moves.append(uci)

    while True:
        for event in stream:
            if event.get("type") != "gameState":
                continue

            moves_str = event.get("moves", "")
            moves = moves_str.split() if moves_str else []
            if len(moves) <= len(seen_moves):
                continue

            new_moves = moves[len(seen_moves):]
            for uci in new_moves:
                # Local oracle step
                move = chess.Move.from_uci(uci)
                if move not in board.legal_moves:
                    raise RuntimeError(f"Local board says illegal move from stream: {uci}")

                compact = uci_to_compact_move(board, uci)

                # Optional: use claim flags for draw-by-move semantics
                tx_hash = contract.submit_move(match_id, compact, claim_flags=0)

                board.push(move)
                seen_moves.append(uci)

                chain_state = contract.fetch_match_state(match_id)
                local_hash = canonical_repetition_hash(board)

                if str(chain_state.board_hash) != str(local_hash):
                    raise RuntimeError(
                        "Desync detected\n"
                        f"UCI: {uci}\n"
                        f"Local hash: {local_hash}\n"
                        f"Chain hash: {chain_state.board_hash}\n"
                        f"TX: {tx_hash}"
                    )

            if event.get("status") in {"mate", "stalemate", "resign", "draw", "timeout", "aborted"}:
                return

        time.sleep(1)


def main() -> None:
    print("Fill in token loading, match/game selection, and contract client wiring.")


if __name__ == "__main__":
    main()
