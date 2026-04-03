# Executive Summary

This pack is built around one pragmatic claim:

> For a chess engine that evolves positions from the standard initial state using its own legal move function, broad invariants plus exact make/unmake checks plus perft plus differential testing can deliver extremely strong practical confidence.

It is **not** built around the stronger and false claim that one giant invariant suite proves every arbitrary imported FEN is a truly reachable legal chess position.

That distinction matters for two reasons:

1. A chess **state** is more than piece placement. FIDE and FEN include side to move, castling rights, en-passant target, halfmove clock, and fullmove number. Repetition identity also depends on these fields. See [FIDE](https://handbook.fide.com/chapter/E012023) and [FEN/PGN](https://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm).
2. Mature tooling distinguishes **basic validity** from **reachability**. [python-chess docs](https://python-chess.readthedocs.io/en/latest/core.html) explicitly warn that a position can pass validity checks without being reachable from the initial position, and the reachability literature treats the retrograde question as substantially harder; see [Gourion](https://arxiv.org/pdf/2112.09386) and [Brunner et al.](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ISAAC.2020.17).

## What this package gives you

- a catalog of **111 invariants**
- a stage-aware checkpoint map
- an explicit EP / castling / import policy model
- a standard perft corpus
- synthetic test vectors
- metamorphic and differential relations
- pseudocode for engine integration

## The strongest engineering recommendation

Use **two distinct notions of correctness** in the engine:

### 1. Engine-generated trust

States produced by your own move engine from the initial position are tagged `TRUSTED_GENERATED`.

This is the cleanest path for internal play, search, and analysis. Once move application is trusted, you do not need to re-solve retrograde reachability on every node.

### 2. External import trust

Imported FENs should be classified explicitly:

- `BASIC_VALID`
- `HEURISTIC_REACHABILITY_PASS`
- `HEURISTIC_REACHABILITY_FAIL`
- `INVALID`

That prevents a major category error: pretending that a position with structurally sound pieces and legal king safety must also be reachable from the start of a real game.

## Why the pack separates EP policies

The original FEN specification records an EP target square after any double pawn push, even when no legal EP capture exists. Production engines such as Stockfish often sanitize EP more strictly for internal use. That means you want two modes:

- external compatibility mode: `spec_fen`
- internal canonical mode: `strict_captureable`

See [FEN/PGN](https://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm), [python-chess source](https://github.com/niklasf/python-chess/blob/master/chess/__init__.py), and [Stockfish position.cpp](https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/position.cpp).

## What should be always-on vs occasional

### Always-on in debug builds

- cheap representation invariants
- cheap local-legality invariants
- core history invariants
- make/unmake exactness at key checkpoints

### Sampled / CI / nightly

- full cache recomputation
- full move-set recomputation
- perft / divide
- differential testing
- tablebase oracles
- reachability heuristics on imported positions

## Final judgment

If your goal is “can I trust the engine to behave like chess when playing from the normal start position?”, this package is enough to support a very strong answer.

If your goal is “can I prove that every arbitrary imported position my engine accepts is reachable from the initial state by legal play?”, this package gets you most of the way toward a disciplined import policy, but the literature says that full reachability is its own harder problem and should be treated that way.
