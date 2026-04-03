#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


_RETURN_RE = re.compile(r"0x[0-9a-fA-F]*")


def _u256_to_be32(x: int) -> bytes:
    if x < 0:
        raise ValueError("u256 cannot be negative")
    if x >= 1 << 256:
        raise ValueError("u256 too large")
    return x.to_bytes(32, "big")


def _words_from_abi(ret: bytes, n: int) -> Tuple[int, ...]:
    if len(ret) < 32 * n:
        raise ValueError(f"expected at least {32*n} bytes, got {len(ret)}")
    out = []
    for i in range(n):
        out.append(int.from_bytes(ret[i * 32 : (i + 1) * 32], "big"))
    return tuple(out)


def _extract_return_hex(output: str) -> str:
    # hevm prints lines like:
    #   "Return: 0x...."
    m = _RETURN_RE.search(output)
    if not m:
        raise RuntimeError(f"hevm output missing return data:\n{output}")
    return m.group(0)


@dataclass(frozen=True)
class ApplyMoveResult:
    ok: int
    board2: int
    meta2: int
    status: int
    reason: int
    pos_hash: int


class HevmChzRules:
    APPLY_MOVE_SELECTOR = bytes.fromhex("d2d9e25f")
    CLASSIFY_SELECTOR = bytes.fromhex("8c594653")
    POSITION_HASH_SELECTOR = bytes.fromhex("f2694688")

    def __init__(
        self,
        *,
        hevm: Optional[str] = None,
        code_file: Optional[str] = None,
    ) -> None:
        root = Path(__file__).resolve().parent.parent
        self.hevm = hevm or os.environ.get("HEVM") or str(root / "../hevm/local/bin/hevm")
        self.code_file = code_file or os.environ.get("CODE_FILE") or str(root / "out/ChzRules.runtime.bin")

        if not Path(self.hevm).exists():
            raise FileNotFoundError(f"missing hevm binary at {self.hevm!r} (set HEVM=... to override)")
        if not Path(self.code_file).exists():
            raise FileNotFoundError(f"missing code file at {self.code_file!r} (run: make fe-build-rules)")

    def _exec(self, calldata: bytes) -> bytes:
        calldata_hex = "0x" + calldata.hex()
        try:
            out = subprocess.check_output(
                [
                    self.hevm,
                    "exec",
                    "--code-file",
                    self.code_file,
                    "--calldata",
                    calldata_hex,
                    "--gas",
                    "0xffffffffffff",
                    "--verb",
                    "0",
                ],
                text=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"hevm exec failed:\n{e.output}") from e

        ret_hex = _extract_return_hex(out)
        if ret_hex == "0x":
            return b""
        return bytes.fromhex(ret_hex[2:])

    def apply_move(self, board_word: int, meta_word: int, mv_word: int) -> ApplyMoveResult:
        calldata = b"".join(
            [
                self.APPLY_MOVE_SELECTOR,
                _u256_to_be32(board_word),
                _u256_to_be32(meta_word),
                _u256_to_be32(mv_word),
            ]
        )
        ret = self._exec(calldata)
        ok, board2, meta2, status, reason, pos_hash = _words_from_abi(ret, 6)
        return ApplyMoveResult(ok, board2, meta2, status, reason, pos_hash)

    def classify(self, board_word: int, meta_word: int) -> Tuple[int, int]:
        calldata = b"".join([self.CLASSIFY_SELECTOR, _u256_to_be32(board_word), _u256_to_be32(meta_word)])
        ret = self._exec(calldata)
        status, reason = _words_from_abi(ret, 2)
        return int(status), int(reason)

    def position_hash(self, board_word: int, meta_word: int) -> int:
        calldata = b"".join([self.POSITION_HASH_SELECTOR, _u256_to_be32(board_word), _u256_to_be32(meta_word)])
        ret = self._exec(calldata)
        (h,) = _words_from_abi(ret, 1)
        return int(h)
