# Research Synthesis

This note synthesizes the main source strata that matter for validation:

1. official rules,
2. official / de facto state formats,
3. production engine validation practice,
4. library status taxonomies,
5. standard rule oracles such as perft,
6. reachability / retrograde literature,
7. metamorphic testing literature.

## 1. FIDE defines legality at the move and game-state level

The [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023) are the primary source for:

- king safety and the rule that you may not make a move that leaves your own king in check,
- castling conditions,
- en passant timing,
- promotion choices,
- checkmate, stalemate, dead position,
- repetition identity,
- 50-move / 75-move rules.

Two implications matter immediately for engine validation:

### Legality is not only geometry

A move is legal only if it both obeys piece movement rules **and** leaves the mover's king safe.

### Terminal-state logic is not optional bookkeeping

Checkmate, stalemate, repetition, and move-count rules all depend on correct state fields, not just on the board.

## 2. FEN/PGN make clear that “board state” is larger than the board

The [Portable Game Notation specification](https://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm) defines FEN as six fields:

1. piece placement
2. active color
3. castling availability
4. en-passant target square
5. halfmove clock
6. fullmove number

That means a correct validator must reason over the full state, not only the 64 squares.

Two subtle but crucial consequences follow:

### Castling availability is historical entitlement, not current immediate legality

A side can keep castling rights even when castling is blocked right now or temporarily illegal because of attacks.

### The original FEN EP field is an external notation choice

The spec records an EP target square after a double pawn push even if no legal EP capture exists. That is a real compatibility concern for import / export code.

## 3. Stockfish shows what production-grade internal validation looks like

[Stockfish position.cpp](https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/position.cpp) is the most useful practical source for internal invariants.

Its validation logic checks or strongly implies checks for:

- structural agreement between board representations,
- king counts,
- pawn counts and back-rank pawn rejection,
- castling-right consistency,
- EP-square sanity,
- hash / material consistency,
- king-safety impossibilities,
- stricter internal EP normalization than raw FEN requires.

This gives a strong signal about what is worth asserting inside a serious engine:

- representation integrity,
- cache integrity,
- move-application exactness,
- state-field sanity,
- king-safety preservation.

## 4. python-chess is useful because it exposes a clean status taxonomy

[python-chess docs](https://python-chess.readthedocs.io/en/latest/core.html) and [python-chess source](https://github.com/niklasf/python-chess/blob/master/chess/__init__.py) make two points that are especially valuable for a validation design:

### Point A: basic validity is not reachability

The docs explicitly say that a board can pass `is_valid()` / `status()` without being reachable from the standard initial position.

### Point B: import validation benefits from named status bits

python-chess has statuses for conditions such as:

- missing kings,
- too many kings,
- too many pawns,
- pawns on the back rank,
- bad castling rights,
- invalid EP square,
- opposite check,
- too many checkers,
- impossible check.

That is a strong design cue: instead of returning one boolean, return a typed validation report with exact causes.

## 5. Perft remains the standard move-generation oracle

The [Chessprogramming Perft page](https://www.chessprogramming.org/Perft) and [Perft Results](https://www.chessprogramming.org/Perft_Results) are still the standard debugging references for move generation and make/unmake logic.

Perft is especially strong because it amplifies small move-legality bugs quickly.

The included corpus in this package contains the standard positions most commonly used to find errors involving:

- castling,
- en passant,
- promotions,
- checks,
- make/unmake drift,
- move-generation completeness.

One caution from [Chessprogramming Perft](https://www.chessprogramming.org/Perft): perft is not a complete model of the entire game tree with all draw-rule semantics. It is a rule-layer oracle, not a complete search oracle.

## 6. Reachability is a separate problem, not just “more invariants”

The distinction between local validity and true legal reachability is not a philosophical quibble.

[Gourion](https://arxiv.org/pdf/2112.09386) explicitly distinguishes diagrams from full positions and defines legality as reachability from the starting position. The paper also notes that there are many illegal diagrams / positions beyond the obvious ones and that they are not easy to characterize exhaustively.

[Brunner et al.](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ISAAC.2020.17) give the formal complexity backdrop: generalized retrograde reachability problems are PSPACE-complete. You do not need that result to write an engine, but it does justify a practical engineering stance:

- use local invariants aggressively,
- use import heuristics where useful,
- keep “reachable legality” as a stronger and separate concept.

## 7. Metamorphic testing is useful, but strongest on the rule layer

The 2023 paper [Metamorphic testing of chess engines](https://www.sciencedirect.com/science/article/pii/S0950584923001179) is useful because it frames testing chess software as an oracle problem and proposes transform-based checks.

The 2025 replication study [Re-evaluating metamorphic testing of chess engines](https://www.sciencedirect.com/science/article/abs/pii/S0950584925000187) is just as important because it warns that some evaluation discrepancies arise from implementation details such as move ordering and search depth, not from true logic bugs.

Practical conclusion:

- use metamorphic tests heavily for exact state transformations, rule-layer symmetries, and serialization,
- be more cautious when interpreting evaluation-level metamorphic failures.

## 8. Tablebases are exact oracles in the endgame band

[python-chess Syzygy docs](https://python-chess.readthedocs.io/en/stable/syzygy.html) are a good operational reference. Syzygy provides exact WDL / DTZ information for many small endgames, with the important caveat that positions with castling rights are excluded.

That makes Syzygy a powerful final-stage oracle for:

- terminal classification,
- move legality in small endgames,
- 50-move-rule-sensitive outcomes.

## Synthesis

The literature and production practice line up around one architecture:

- **representation invariants**
- **local-legality invariants**
- **history / transition invariants**
- **import-only reachability heuristics**
- **external oracles and differential testing**

That architecture is what the rest of this pack encodes.
