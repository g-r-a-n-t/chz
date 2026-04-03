from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set, Tuple

import chz_words


@dataclass(frozen=True)
class MoveCandidate:
    uci: str
    mv_word: int
    from_sq: int
    to_sq: int
    promo: int


def _unpack_board(board_word: int) -> List[int]:
    board = [0] * 64
    for sq in range(64):
        board[sq] = (board_word >> (sq * 4)) & 0xF
    return board


def _is_white(piece: int) -> bool:
    return 0 < piece < 8


def _is_black(piece: int) -> bool:
    return piece >= 8


def _is_friendly(piece: int, white_to_move: bool) -> bool:
    return _is_white(piece) if white_to_move else _is_black(piece)


def _is_enemy(piece: int, white_to_move: bool) -> bool:
    return _is_black(piece) if white_to_move else _is_white(piece)


def _sq_to_alg(sq: int) -> str:
    file = sq & 7
    rank = sq >> 3
    return f"{chr(ord('a') + file)}{rank + 1}"


def _mk_uci(from_sq: int, to_sq: int, promo: int) -> str:
    s = _sq_to_alg(from_sq) + _sq_to_alg(to_sq)
    if promo:
        # 1 n, 2 b, 3 r, 4 q
        s += {1: "n", 2: "b", 3: "r", 4: "q"}[promo]
    return s


def _add(moves: Set[MoveCandidate], from_sq: int, to_sq: int, promo: int) -> None:
    mv_word = chz_words.encode_move(from_sq, to_sq, promo)
    moves.add(MoveCandidate(_mk_uci(from_sq, to_sq, promo), mv_word, from_sq, to_sq, promo))


def generate_pseudo_legal_moves(board_word: int, meta_word: int) -> List[MoveCandidate]:
    """
    Generate a superset of legal moves for the given packed board/meta.
    Intended for off-chain tooling; filter candidates by calling the backend.
    """
    board = _unpack_board(board_word)

    white_to_move = ((meta_word >> chz_words.STM_SHIFT) & 1) == 1
    rights = (meta_word >> chz_words.CASTLE_SHIFT) & 0xF
    ep_file = (meta_word >> chz_words.EP_SHIFT) & 0xF

    moves: Set[MoveCandidate] = set()

    for from_sq, piece in enumerate(board):
        if not _is_friendly(piece, white_to_move):
            continue

        kind = piece & 0x7  # 1 pawn .. 6 king
        f = from_sq & 7
        r = from_sq >> 3

        if kind == 1:
            # Pawn
            if white_to_move:
                # forward
                if r < 7:
                    one = from_sq + 8
                    if board[one] == 0:
                        if r == 6:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, one, promo)
                        else:
                            _add(moves, from_sq, one, 0)
                            if r == 1 and board[from_sq + 16] == 0:
                                _add(moves, from_sq, from_sq + 16, 0)
                # captures
                if r < 7 and f > 0:
                    to = from_sq + 7
                    if _is_enemy(board[to], white_to_move):
                        if r == 6:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, to, promo)
                        else:
                            _add(moves, from_sq, to, 0)
                if r < 7 and f < 7:
                    to = from_sq + 9
                    if _is_enemy(board[to], white_to_move):
                        if r == 6:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, to, promo)
                        else:
                            _add(moves, from_sq, to, 0)
            else:
                # forward
                if r > 0:
                    one = from_sq - 8
                    if board[one] == 0:
                        if r == 1:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, one, promo)
                        else:
                            _add(moves, from_sq, one, 0)
                            if r == 6 and board[from_sq - 16] == 0:
                                _add(moves, from_sq, from_sq - 16, 0)
                # captures
                if r > 0 and f > 0:
                    to = from_sq - 9
                    if _is_enemy(board[to], white_to_move):
                        if r == 1:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, to, promo)
                        else:
                            _add(moves, from_sq, to, 0)
                if r > 0 and f < 7:
                    to = from_sq - 7
                    if _is_enemy(board[to], white_to_move):
                        if r == 1:
                            for promo in (1, 2, 3, 4):
                                _add(moves, from_sq, to, promo)
                        else:
                            _add(moves, from_sq, to, 0)

        elif kind == 2:
            # Knight
            for df, dr in (
                (-2, -1),
                (-2, 1),
                (-1, -2),
                (-1, 2),
                (1, -2),
                (1, 2),
                (2, -1),
                (2, 1),
            ):
                tf, tr = f + df, r + dr
                if 0 <= tf < 8 and 0 <= tr < 8:
                    to = tf + tr * 8
                    if not _is_friendly(board[to], white_to_move):
                        _add(moves, from_sq, to, 0)

        elif kind in (3, 4, 5):
            # Sliding pieces
            if kind == 3:
                dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif kind == 4:
                dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            else:
                dirs = [
                    (-1, -1),
                    (-1, 1),
                    (1, -1),
                    (1, 1),
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ]

            for df, dr in dirs:
                tf, tr = f + df, r + dr
                while 0 <= tf < 8 and 0 <= tr < 8:
                    to = tf + tr * 8
                    if _is_friendly(board[to], white_to_move):
                        break
                    _add(moves, from_sq, to, 0)
                    if _is_enemy(board[to], white_to_move):
                        break
                    tf += df
                    tr += dr

        elif kind == 6:
            # King
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    tf, tr = f + df, r + dr
                    if 0 <= tf < 8 and 0 <= tr < 8:
                        to = tf + tr * 8
                        if not _is_friendly(board[to], white_to_move):
                            _add(moves, from_sq, to, 0)

    # En passant (meta stores file only; rank implied by side to move).
    if ep_file != chz_words.EP_NONE and 0 <= ep_file < 8:
        if white_to_move:
            ep_sq = int(ep_file) + 5 * 8  # rank 6
            for from_sq in (ep_sq - 9, ep_sq - 7):
                if 0 <= from_sq < 64 and board[from_sq] == chz_words.PIECE_WP:
                    _add(moves, from_sq, ep_sq, 0)
        else:
            ep_sq = int(ep_file) + 2 * 8  # rank 3
            for from_sq in (ep_sq + 7, ep_sq + 9):
                if 0 <= from_sq < 64 and board[from_sq] == chz_words.PIECE_BP:
                    _add(moves, from_sq, ep_sq, 0)

    # Castling (only generate when the basic piece placement is plausible).
    if white_to_move:
        if board[4] == chz_words.PIECE_WK:
            if (rights & chz_words.CASTLE_WK) and board[5] == 0 and board[6] == 0 and board[7] == chz_words.PIECE_WR:
                _add(moves, 4, 6, 0)  # e1g1
            if (
                (rights & chz_words.CASTLE_WQ)
                and board[1] == 0
                and board[2] == 0
                and board[3] == 0
                and board[0] == chz_words.PIECE_WR
            ):
                _add(moves, 4, 2, 0)  # e1c1
    else:
        if board[60] == chz_words.PIECE_BK:
            if (
                (rights & chz_words.CASTLE_BK)
                and board[61] == 0
                and board[62] == 0
                and board[63] == chz_words.PIECE_BR
            ):
                _add(moves, 60, 62, 0)  # e8g8
            if (
                (rights & chz_words.CASTLE_BQ)
                and board[57] == 0
                and board[58] == 0
                and board[59] == 0
                and board[56] == chz_words.PIECE_BR
            ):
                _add(moves, 60, 58, 0)  # e8c8

    return sorted(moves, key=lambda m: m.uci)
