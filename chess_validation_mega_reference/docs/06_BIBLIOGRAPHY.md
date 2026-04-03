# Bibliography

## SRC-001 — FIDE Laws of Chess (effective 1 January 2023)

- URL: https://handbook.fide.com/chapter/E012023
- Why it matters: Primary source for move legality, castling, en passant, repetition, checkmate, stalemate, dead position, and 75-move/fivefold rules.

## SRC-002 — Portable Game Notation Specification and Implementation Guide

- URL: https://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm
- Why it matters: Canonical specification for FEN/PGN field semantics: active color, castling availability, EP target square, halfmove clock, and fullmove number.

## SRC-003 — python-chess core documentation

- URL: https://python-chess.readthedocs.io/en/latest/core.html
- Why it matters: Clear reference implementation documentation for legal vs pseudo-legal moves, board validity, mirror transforms, and API semantics.

## SRC-004 — python-chess source (status()/is_valid())

- URL: https://github.com/niklasf/python-chess/blob/master/chess/__init__.py
- Why it matters: Concrete import-time status taxonomy: bad castling rights, invalid EP square, opposite check, too many checkers, impossible check, and more.

## SRC-005 — Stockfish position.cpp

- URL: https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/position.cpp
- Why it matters: Production-grade reference for internal state validation, EP sanitization, castling-right consistency, hash recomputation, and legal move edge cases.

## SRC-006 — Stockfish Docs: UCI & Commands

- URL: https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html
- Why it matters: Official divide/perft example and operational guidance useful for test harnesses.

## SRC-007 — Chessprogramming Wiki: Perft

- URL: https://www.chessprogramming.org/Perft
- Why it matters: Explains why perft/divide is the standard debugging oracle for move generation and make/unmake.

## SRC-008 — Chessprogramming Wiki: Perft Results

- URL: https://www.chessprogramming.org/Perft_Results
- Why it matters: Provides standard reference positions and node counts used across engine debugging.

## SRC-009 — Daniel Gourion, An upper bound for the number of chess diagrams without promotion

- URL: https://arxiv.org/pdf/2112.09386
- Why it matters: Useful for the legal-diagram/reachability distinction and for retrograde-style pawn/promotion reasoning.

## SRC-010 — Brunner et al., Complexity of Retrograde and Helpmate Chess Problems

- URL: https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ISAAC.2020.17
- Why it matters: Puts formal weight behind the claim that reachability is a genuinely harder problem than local move legality.

## SRC-011 — Méndez et al., Metamorphic testing of chess engines

- URL: https://www.sciencedirect.com/science/article/pii/S0950584923001179
- Why it matters: Introduces metamorphic relations as a practical testing aid in the oracle-poor parts of engine validation.

## SRC-012 — Martin et al., Re-evaluating metamorphic testing of chess engines: A replication study

- URL: https://www.sciencedirect.com/science/article/abs/pii/S0950584925000187
- Why it matters: Important caution: metamorphic evaluation discrepancies can come from implementation details rather than true bugs.

## SRC-013 — python-chess Syzygy endgame tablebase probing

- URL: https://python-chess.readthedocs.io/en/stable/syzygy.html
- Why it matters: Exact WDL/DTZ oracle for many small endgames, with the important caveat that castling-right positions are excluded.
