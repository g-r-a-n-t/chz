#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import chz_words
from hevm_backend import HevmChzRules
from movegen import generate_pseudo_legal_moves


ROOT = Path(__file__).resolve().parent.parent
PERFT_PATH = ROOT / "data" / "perft_positions.json"
MEGA_PERFT_PATH = ROOT / "chess_validation_mega_reference" / "machine" / "perft_reference.json"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


@dataclass(frozen=True)
class Position:
    id: str
    name: str
    fen: str
    depth_nodes: Dict[int, int]


def load_positions() -> List[Position]:
    raw = json.loads(PERFT_PATH.read_text())
    out: List[Position] = []
    for item in raw:
        depth_nodes = {int(k): int(v) for k, v in (item.get("depth_nodes") or {}).items()}
        out.append(Position(id=item["id"], name=item.get("name", item["id"]), fen=item["fen"], depth_nodes=depth_nodes))
    return out


def legal_next_states(backend: HevmChzRules, board_word: int, meta_word: int) -> List[Tuple[int, int]]:
    next_states: List[Tuple[int, int]] = []
    for cand in generate_pseudo_legal_moves(board_word, meta_word):
        res = backend.apply_move(board_word, meta_word, cand.mv_word)
        if res.ok == 1:
            next_states.append((res.board2, res.meta2))
    return next_states


def mirror_ranks_swap_colors_board(board_word: int) -> int:
    out = 0
    for sq in range(64):
        piece = (board_word >> (sq * 4)) & 0xF
        f = sq & 7
        r = sq >> 3
        sq2 = f + ((7 - r) * 8)

        # Swap colors while preserving kind: 0x1..0x6 <-> 0x9..0xE
        if piece == 0:
            piece2 = 0
        else:
            piece2 = piece ^ 0x8

        out = chz_words.set_piece(out, sq2, piece2)
    return out


def _meta_get(meta: int, shift: int, mask: int) -> int:
    return (meta >> shift) & mask


def _meta_set(meta: int, shift: int, mask: int, value: int) -> int:
    meta &= ~(mask << shift)
    meta |= (value & mask) << shift
    return meta


def mirror_ranks_swap_colors_meta(meta_word: int) -> int:
    white_to_move = _meta_get(meta_word, chz_words.STM_SHIFT, 0x1)
    rights = _meta_get(meta_word, chz_words.CASTLE_SHIFT, 0xF)
    ep_file = _meta_get(meta_word, chz_words.EP_SHIFT, 0xF)
    halfmove = _meta_get(meta_word, chz_words.HALF_SHIFT, 0xFF)
    fullmove = _meta_get(meta_word, chz_words.FULL_SHIFT, 0xFFFF)
    wk_sq = _meta_get(meta_word, chz_words.WK_SHIFT, 0x3F)
    bk_sq = _meta_get(meta_word, chz_words.BK_SHIFT, 0x3F)

    def refl_sq(sq: int) -> int:
        f = sq & 7
        r = sq >> 3
        return f + ((7 - r) * 8)

    # After mirroring ranks and swapping colors, the original white king becomes
    # the new black king (and vice versa), so swap the cached king squares.
    wk_sq2 = refl_sq(bk_sq)
    bk_sq2 = refl_sq(wk_sq)

    # EP is stored as file-only; the rank is implied by side-to-move. Since we
    # swap side-to-move, keeping the same file mirrors the EP square correctly.
    ep_file2 = ep_file

    # Swap side-to-move when swapping colors.
    stm2 = 0 if white_to_move else 1

    # Swap castling rights across colors (files unchanged under rank mirror).
    new_rights = 0
    if rights & chz_words.CASTLE_BK:
        new_rights |= chz_words.CASTLE_WK
    if rights & chz_words.CASTLE_BQ:
        new_rights |= chz_words.CASTLE_WQ
    if rights & chz_words.CASTLE_WK:
        new_rights |= chz_words.CASTLE_BK
    if rights & chz_words.CASTLE_WQ:
        new_rights |= chz_words.CASTLE_BQ

    meta2 = 0
    meta2 = _meta_set(meta2, chz_words.STM_SHIFT, 0x1, stm2)
    meta2 = _meta_set(meta2, chz_words.CASTLE_SHIFT, 0xF, new_rights)
    meta2 = _meta_set(meta2, chz_words.EP_SHIFT, 0xF, ep_file2)
    meta2 = _meta_set(meta2, chz_words.HALF_SHIFT, 0xFF, halfmove)
    meta2 = _meta_set(meta2, chz_words.FULL_SHIFT, 0xFFFF, fullmove)
    meta2 = _meta_set(meta2, chz_words.WK_SHIFT, 0x3F, wk_sq2)
    meta2 = _meta_set(meta2, chz_words.BK_SHIFT, 0x3F, bk_sq2)
    return meta2


def mirror_ranks_swap_colors_words(board_word: int, meta_word: int) -> Tuple[int, int]:
    return mirror_ranks_swap_colors_board(board_word), mirror_ranks_swap_colors_meta(meta_word)


def normalize_fen_6_fields(fen: str) -> str:
    fields = fen.split()
    if len(fields) == 6:
        return fen
    if len(fields) == 4:
        # Some reference corpora omit halfmove/fullmove; default to 0 1.
        return fen + " 0 1"
    raise ValueError(f"unexpected FEN fields ({len(fields)}): {fen!r}")


def load_mega_mirrors() -> Dict[str, List[str]]:
    if not MEGA_PERFT_PATH.exists():
        return {}
    raw = json.loads(MEGA_PERFT_PATH.read_text())
    out: Dict[str, List[str]] = {}
    for pos in raw.get("positions") or []:
        fen = pos.get("fen")
        mirrors = pos.get("mirrors") or []
        if mirrors:
            if not isinstance(fen, str):
                continue
            key = normalize_fen_6_fields(fen)
            out[key] = [normalize_fen_6_fields(m) for m in mirrors]
    return out


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Metamorphic perft checks (symmetry/invariance) via hevm+ChzRules.")
    ap.add_argument("--depth", type=int, default=2, help="Perft depth to compute (default 2).")
    ap.add_argument("--id", dest="only_id", default=None, help="Run only a specific perft position id.")
    args = ap.parse_args(argv)

    if not PERFT_PATH.exists():
        die(f"missing {PERFT_PATH}")

    backend = HevmChzRules()
    positions = load_positions()
    if args.only_id is not None:
        positions = [p for p in positions if p.id == args.only_id]
        if not positions:
            die(f"unknown perft id: {args.only_id!r}")

    mega_mirrors = load_mega_mirrors()

    @lru_cache(maxsize=None)
    def perft(board_word: int, meta_word: int, depth: int) -> int:
        if depth == 0:
            return 1
        nxt = legal_next_states(backend, board_word, meta_word)
        if depth == 1:
            return len(nxt)
        total = 0
        for b2, m2 in nxt:
            total += perft(b2, m2, depth - 1)
        return total

    failures = 0
    for pos in positions:
        board, meta = chz_words.fen_to_words(pos.fen)
        got = perft(board, meta, args.depth)
        exp = pos.depth_nodes.get(args.depth)
        if exp is not None and got != exp:
            failures += 1
            print(f"[FAIL] perft mismatch {pos.id} depth={args.depth} expected={exp} got={got}", file=sys.stderr)
            continue

        b_ref, m_ref = mirror_ranks_swap_colors_words(board, meta)
        got_ref = perft(b_ref, m_ref, args.depth)
        if got_ref != got:
            failures += 1
            print(
                f"[FAIL] mirror+swap mismatch {pos.id} depth={args.depth} original={got} mirrored={got_ref}",
                file=sys.stderr,
            )
            continue

        print(f"[ok] mirror+swap {pos.id} depth={args.depth} nodes={got}")

        # Also check any explicit mirror FENs from the mega reference corpus.
        for mirror_fen in mega_mirrors.get(pos.fen, []):
            try:
                b_m, m_m = chz_words.fen_to_words(mirror_fen)
            except Exception as e:
                failures += 1
                print(f"[FAIL] mega mirror parse {pos.id}: {e}", file=sys.stderr)
                continue
            got_m = perft(b_m, m_m, args.depth)
            if got_m != got:
                failures += 1
                print(
                    f"[FAIL] mega mirror perft mismatch {pos.id} depth={args.depth} original={got} mirror={got_m}",
                    file=sys.stderr,
                )
            else:
                print(f"[ok] mega_mirror {pos.id} depth={args.depth} nodes={got_m}")

    if failures:
        print(f"{failures} metamorphic perft check(s) failed.", file=sys.stderr)
        return 1

    print("Metamorphic perft checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
