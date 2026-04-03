#!/usr/bin/env python3
from __future__ import annotations

import sys


FILES = "abcdefgh"

PIECE_WP = 0x1
PIECE_WN = 0x2
PIECE_WB = 0x3
PIECE_WR = 0x4
PIECE_WQ = 0x5
PIECE_WK = 0x6

PIECE_BP = 0x9
PIECE_BN = 0xA
PIECE_BB = 0xB
PIECE_BR = 0xC
PIECE_BQ = 0xD
PIECE_BK = 0xE

CASTLE_WK = 0x1
CASTLE_WQ = 0x2
CASTLE_BK = 0x4
CASTLE_BQ = 0x8

EP_NONE = 0xF

STM_SHIFT = 0
CASTLE_SHIFT = 1
EP_SHIFT = 5
HALF_SHIFT = 9
FULL_SHIFT = 17
WK_SHIFT = 33
BK_SHIFT = 39

PIECE_FROM_FEN = {
    "P": PIECE_WP,
    "N": PIECE_WN,
    "B": PIECE_WB,
    "R": PIECE_WR,
    "Q": PIECE_WQ,
    "K": PIECE_WK,
    "p": PIECE_BP,
    "n": PIECE_BN,
    "b": PIECE_BB,
    "r": PIECE_BR,
    "q": PIECE_BQ,
    "k": PIECE_BK,
}

PIECE_TO_FEN = {v: k for k, v in PIECE_FROM_FEN.items()}


def set_piece(board: int, sq: int, piece: int) -> int:
    shift = sq * 4
    mask = 0xF << shift
    board &= ~mask
    board |= (piece & 0xF) << shift
    return board


def board_init_standard() -> int:
    board = 0

    white_back = [PIECE_WR, PIECE_WN, PIECE_WB, PIECE_WQ, PIECE_WK, PIECE_WB, PIECE_WN, PIECE_WR]
    for sq, piece in enumerate(white_back):
        board = set_piece(board, sq, piece)

    for sq in range(8, 16):
        board = set_piece(board, sq, PIECE_WP)

    for sq in range(48, 56):
        board = set_piece(board, sq, PIECE_BP)

    black_back = [PIECE_BR, PIECE_BN, PIECE_BB, PIECE_BQ, PIECE_BK, PIECE_BB, PIECE_BN, PIECE_BR]
    for i, piece in enumerate(black_back):
        board = set_piece(board, 56 + i, piece)

    return board


def meta_init_standard() -> int:
    def set_bits(meta: int, shift: int, mask: int, value: int) -> int:
        meta &= ~(mask << shift)
        meta |= (value & mask) << shift
        return meta

    meta = 0
    meta = set_bits(meta, STM_SHIFT, 0x1, 1)  # white to move
    meta = set_bits(meta, CASTLE_SHIFT, 0xF, CASTLE_WK | CASTLE_WQ | CASTLE_BK | CASTLE_BQ)
    meta = set_bits(meta, EP_SHIFT, 0xF, EP_NONE)
    meta = set_bits(meta, HALF_SHIFT, 0xFF, 0)
    meta = set_bits(meta, FULL_SHIFT, 0xFFFF, 1)
    meta = set_bits(meta, WK_SHIFT, 0x3F, 4)   # e1
    meta = set_bits(meta, BK_SHIFT, 0x3F, 60)  # e8
    return meta


def sq_from_algebraic(s: str) -> int:
    if len(s) != 2:
        raise ValueError(f"invalid square: {s!r}")
    file_ch = s[0]
    rank_ch = s[1]
    if file_ch < "a" or file_ch > "h":
        raise ValueError(f"invalid file: {file_ch!r}")
    if rank_ch < "1" or rank_ch > "8":
        raise ValueError(f"invalid rank: {rank_ch!r}")
    file_idx = ord(file_ch) - ord("a")
    rank_idx = int(rank_ch) - 1
    return file_idx + rank_idx * 8


def encode_move(from_sq: int, to_sq: int, promo: int) -> int:
    return from_sq | (to_sq << 6) | (promo << 12)


def promo_code(ch: str) -> int:
    ch = ch.lower()
    if ch == "n":
        return 1
    if ch == "b":
        return 2
    if ch == "r":
        return 3
    if ch == "q":
        return 4
    raise ValueError(f"invalid promotion: {ch!r}")

def move_from_uci(uci: str) -> int:
    if len(uci) not in (4, 5):
        raise ValueError(f"invalid uci: {uci!r}")
    from_sq = sq_from_algebraic(uci[0:2])
    to_sq = sq_from_algebraic(uci[2:4])
    promo = promo_code(uci[4]) if len(uci) == 5 else 0
    return encode_move(from_sq, to_sq, promo)


def cmd_standard() -> None:
    print(hex(board_init_standard()))
    print(hex(meta_init_standard()))

def cmd_promo() -> None:
    # Minimal promotion position:
    # - White: king e1, pawn a7
    # - Black: king e8
    board = 0
    board = set_piece(board, 4, PIECE_WK)    # e1
    board = set_piece(board, 48, PIECE_WP)   # a7
    board = set_piece(board, 60, PIECE_BK)   # e8

    # Same meta layout as src/chess/meta.fe but with no castling rights.
    def set_bits(meta: int, shift: int, mask: int, value: int) -> int:
        meta &= ~(mask << shift)
        meta |= (value & mask) << shift
        return meta

    meta = 0
    meta = set_bits(meta, STM_SHIFT, 0x1, 1)  # white to move
    meta = set_bits(meta, CASTLE_SHIFT, 0xF, 0)
    meta = set_bits(meta, EP_SHIFT, 0xF, EP_NONE)
    meta = set_bits(meta, HALF_SHIFT, 0xFF, 0)
    meta = set_bits(meta, FULL_SHIFT, 0xFFFF, 1)
    meta = set_bits(meta, WK_SHIFT, 0x3F, 4)   # e1
    meta = set_bits(meta, BK_SHIFT, 0x3F, 60)  # e8

    print(hex(board))
    print(hex(meta))


def cmd_uci(uci: str) -> None:
    print(move_from_uci(uci))


def _parse_int(s: str) -> int:
    return int(s, 0)


def _meta_set_bits(meta: int, shift: int, mask: int, value: int) -> int:
    meta &= ~(mask << shift)
    meta |= (value & mask) << shift
    return meta


def fen_to_words(fen: str) -> tuple[int, int]:
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f"invalid FEN (expected 6 fields): {fen!r}")

    board_field, stm_field, castle_field, ep_field, half_field, full_field = fields

    ranks = board_field.split("/")
    if len(ranks) != 8:
        raise ValueError(f"invalid FEN board field: {board_field!r}")

    board = 0
    wk_sq: int | None = None
    bk_sq: int | None = None

    for fen_rank_idx, rank_str in enumerate(ranks):
        rank = 7 - fen_rank_idx  # 7..0 (a8..h8 down to a1..h1)
        file = 0
        for ch in rank_str:
            if ch.isdigit():
                n = int(ch)
                if n <= 0 or n > 8:
                    raise ValueError(f"invalid empty count: {ch!r} in {rank_str!r}")
                file += n
                continue

            piece = PIECE_FROM_FEN.get(ch)
            if piece is None:
                raise ValueError(f"invalid piece: {ch!r} in {rank_str!r}")
            if file >= 8:
                raise ValueError(f"too many files in rank: {rank_str!r}")

            sq = file + rank * 8
            board = set_piece(board, sq, piece)
            if ch == "K":
                if wk_sq is not None:
                    raise ValueError("invalid FEN: multiple white kings")
                wk_sq = sq
            elif ch == "k":
                if bk_sq is not None:
                    raise ValueError("invalid FEN: multiple black kings")
                bk_sq = sq

            file += 1

        if file != 8:
            raise ValueError(f"rank does not sum to 8 files: {rank_str!r}")

    if wk_sq is None or bk_sq is None:
        raise ValueError("invalid FEN: missing king")

    wk_f, wk_r = wk_sq % 8, wk_sq // 8
    bk_f, bk_r = bk_sq % 8, bk_sq // 8
    if abs(wk_f - bk_f) <= 1 and abs(wk_r - bk_r) <= 1:
        raise ValueError("invalid FEN: kings are adjacent")

    if stm_field == "w":
        white_to_move = True
    elif stm_field == "b":
        white_to_move = False
    else:
        raise ValueError(f"invalid side-to-move field: {stm_field!r}")

    rights = 0
    if castle_field != "-":
        for ch in castle_field:
            if ch == "K":
                rights |= CASTLE_WK
            elif ch == "Q":
                rights |= CASTLE_WQ
            elif ch == "k":
                rights |= CASTLE_BK
            elif ch == "q":
                rights |= CASTLE_BQ
            else:
                raise ValueError(f"invalid castling char: {ch!r}")

    ep_file = EP_NONE
    if ep_field != "-":
        if len(ep_field) != 2:
            raise ValueError(f"invalid ep field: {ep_field!r}")
        fch, rch = ep_field[0], ep_field[1]
        if fch not in FILES:
            raise ValueError(f"invalid ep file: {fch!r}")
        if rch not in "12345678":
            raise ValueError(f"invalid ep rank: {rch!r}")
        expected_rank = "6" if white_to_move else "3"
        if rch != expected_rank:
            raise ValueError(f"invalid ep square for stm={stm_field!r}: {ep_field!r}")
        ep_file = ord(fch) - ord("a")

    halfmove = int(half_field)
    fullmove = int(full_field)
    if halfmove < 0 or halfmove > 0xFF:
        raise ValueError(f"invalid halfmove clock: {half_field!r}")
    if fullmove <= 0 or fullmove > 0xFFFF:
        raise ValueError(f"invalid fullmove number: {full_field!r}")

    meta = 0
    meta = _meta_set_bits(meta, STM_SHIFT, 0x1, 1 if white_to_move else 0)
    meta = _meta_set_bits(meta, CASTLE_SHIFT, 0xF, rights)
    meta = _meta_set_bits(meta, EP_SHIFT, 0xF, ep_file)
    meta = _meta_set_bits(meta, HALF_SHIFT, 0xFF, halfmove)
    meta = _meta_set_bits(meta, FULL_SHIFT, 0xFFFF, fullmove)
    meta = _meta_set_bits(meta, WK_SHIFT, 0x3F, wk_sq)
    meta = _meta_set_bits(meta, BK_SHIFT, 0x3F, bk_sq)

    return board, meta


def words_to_fen(board: int, meta: int) -> str:
    ranks = []
    for rank in range(7, -1, -1):
        out = []
        empty = 0
        for file in range(8):
            sq = file + rank * 8
            piece = (board >> (sq * 4)) & 0xF
            if piece == 0:
                empty += 1
                continue
            if empty:
                out.append(str(empty))
                empty = 0
            ch = PIECE_TO_FEN.get(piece)
            if ch is None:
                raise ValueError(f"unknown piece code: 0x{piece:x}")
            out.append(ch)
        if empty:
            out.append(str(empty))
        ranks.append("".join(out))

    board_field = "/".join(ranks)

    white_to_move = ((meta >> STM_SHIFT) & 0x1) == 1
    stm_field = "w" if white_to_move else "b"

    rights = (meta >> CASTLE_SHIFT) & 0xF
    castle = ""
    if rights & CASTLE_WK:
        castle += "K"
    if rights & CASTLE_WQ:
        castle += "Q"
    if rights & CASTLE_BK:
        castle += "k"
    if rights & CASTLE_BQ:
        castle += "q"
    if not castle:
        castle = "-"

    ep_file = (meta >> EP_SHIFT) & 0xF
    if ep_file == EP_NONE or ep_file >= 8:
        ep = "-"
    else:
        fch = chr(ord("a") + int(ep_file))
        rch = "6" if white_to_move else "3"
        ep = f"{fch}{rch}"

    halfmove = (meta >> HALF_SHIFT) & 0xFF
    fullmove = (meta >> FULL_SHIFT) & 0xFFFF

    return f"{board_field} {stm_field} {castle} {ep} {int(halfmove)} {int(fullmove)}"


def cmd_fen(fen: str) -> None:
    board, meta = fen_to_words(fen)
    print(hex(board))
    print(hex(meta))


def cmd_to_fen(board_word: str, meta_word: str) -> None:
    board = _parse_int(board_word)
    meta = _parse_int(meta_word)
    print(words_to_fen(board, meta))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: chz_words.py standard|promo | uci <e2e4|e7e8q> | fen <FEN...> | to_fen <board> <meta>", file=sys.stderr)
        return 2

    try:
        if argv[1] == "standard":
            cmd_standard()
            return 0

        if argv[1] == "promo":
            cmd_promo()
            return 0

        if argv[1] == "uci":
            if len(argv) != 3:
                print("usage: chz_words.py uci <e2e4|e7e8q>", file=sys.stderr)
                return 2
            cmd_uci(argv[2])
            return 0

        if argv[1] == "fen":
            if len(argv) < 3:
                print("usage: chz_words.py fen <FEN...>", file=sys.stderr)
                return 2
            cmd_fen(" ".join(argv[2:]))
            return 0

        if argv[1] == "to_fen":
            if len(argv) != 4:
                print("usage: chz_words.py to_fen <board_word> <meta_word>", file=sys.stderr)
                return 2
            cmd_to_fen(argv[2], argv[3])
            return 0

        print(f"unknown command: {argv[1]!r}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
