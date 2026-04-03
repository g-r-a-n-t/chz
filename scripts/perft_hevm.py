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
        out.append(
            Position(
                id=item["id"],
                name=item.get("name", item["id"]),
                fen=item["fen"],
                depth_nodes=depth_nodes,
            )
        )
    return out


def legal_next_states(backend: HevmChzRules, board_word: int, meta_word: int) -> List[Tuple[int, int]]:
    next_states: List[Tuple[int, int]] = []
    for cand in generate_pseudo_legal_moves(board_word, meta_word):
        res = backend.apply_move(board_word, meta_word, cand.mv_word)
        if res.ok == 1:
            next_states.append((res.board2, res.meta2))
    return next_states


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Perft via hevm+ChzRules.applyMove (slow; use small depths).")
    ap.add_argument("--id", dest="only_id", default=None, help="Run only a specific perft position id.")
    ap.add_argument("--depth", type=int, default=2, help="Depth to compute (default 2).")
    ap.add_argument("--max-positions", type=int, default=0, help="Limit number of positions (0 = all).")
    args = ap.parse_args(argv)

    if not PERFT_PATH.exists():
        die(f"missing {PERFT_PATH}")

    backend = HevmChzRules()
    positions = load_positions()

    if args.only_id is not None:
        positions = [p for p in positions if p.id == args.only_id]
        if not positions:
            die(f"unknown perft id: {args.only_id!r}")

    if args.max_positions and args.max_positions > 0:
        positions = positions[: args.max_positions]

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
        board_word, meta_word = chz_words.fen_to_words(pos.fen)
        got = perft(board_word, meta_word, args.depth)
        exp = pos.depth_nodes.get(args.depth)
        if exp is None:
            print(f"[skip] {pos.id}: no expected count for depth={args.depth}")
            continue
        ok = got == exp
        if ok:
            print(f"[ok] {pos.id} depth={args.depth} nodes={got}")
        else:
            failures += 1
            print(f"[FAIL] {pos.id} depth={args.depth} expected={exp} got={got}", file=sys.stderr)

    if failures:
        print(f"{failures} perft position(s) failed.", file=sys.stderr)
        return 1

    print("Perft checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
