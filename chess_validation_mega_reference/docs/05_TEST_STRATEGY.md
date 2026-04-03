# Test Strategy

The invariant catalog is necessary but not sufficient. This package assumes you will combine invariants with several orthogonal test families.

## 1. Unit tests for primitive rules

These should directly test:

- piece movement geometry,
- attack detection,
- check detection,
- castling preconditions,
- EP capture application,
- promotion application,
- terminal-state classification.

Unit tests are best for precise edge cases but are too brittle and incomplete to carry the whole burden alone.

## 2. Perft and divide

Use the reference corpus in `machine/perft_reference.json`.

Perft is the canonical oracle for:

- move-generation completeness,
- make/unmake exactness,
- castling edge cases,
- EP edge cases,
- promotion edge cases.

Use divide when a count fails. Divide localizes the bug to one root move immediately.

Important limitation from [Chessprogramming Perft](https://www.chessprogramming.org/Perft): perft is not a full substitute for search correctness or all draw-rule semantics.

## 3. Random reachable-state walks

Recommended pattern:

- start from the standard initial position,
- choose random legal moves,
- validate after every make,
- occasionally validate after every unmake,
- compare current state to a replay-from-root reconstruction,
- serialize / parse roundtrip periodically.

This is one of the best ways to catch incremental drift.

## 4. Differential testing

Compare against a trusted reference implementation on **reachable** positions.

Good targets:

- legal move sets,
- in-check flags,
- checkmate / stalemate classification,
- FEN roundtrip semantics under the same policy,
- perft on the same positions.

Differential testing is especially valuable because two independent implementations tend to disagree loudly on rule bugs.

## 5. Metamorphic tests

Useful exact relations:

- clone equality,
- FEN roundtrip,
- make/unmake involution,
- mirror / reflection perft symmetry,
- search non-mutation.

Use caution for evaluation-level metamorphic relations. The 2025 replication study shows that some apparent evaluation inconsistencies can come from implementation details rather than rule bugs.

## 6. Tablebase oracles

Where supported:

- probe Syzygy on eligible positions,
- compare WDL / DTZ,
- validate terminal-state logic in the endgame band.

This is the cleanest exact oracle beyond perft.

## 7. Search safety tests

Search integration needs its own tests:

- root state unchanged after search,
- PV replay legal,
- TT move sane,
- null move semantics correct if used,
- no hidden mutation from evaluation or search helpers.

## 8. Suggested CI lanes

### Fast lane (every PR)

- unit tests
- start-position perft through depth 5
- one or two special perft positions at moderate depth
- short random-walk stress
- a small differential sample
- root non-mutation test

### Deeper lane (nightly)

- broader perft corpus
- deeper perft on bug-prone positions
- long random walks
- full differential batches
- FULL validation sampling
- tablebase checks

### Fuzz lane

- fuzz imported FENs
- classify them with IMPORT_BASIC / IMPORT_STRICT
- ensure no crashes
- ensure structured reasons on rejection

## 9. What to trust most

If forced to rank the highest-value validation activities:

1. make/unmake exactness
2. perft / divide
3. differential legal move set testing
4. random reachable-state walks
5. imported-position policy with explicit validity levels
6. tablebases
7. metamorphic evaluation checks

This ordering is pragmatic: it prioritizes the tests most likely to find real engine bugs with clear diagnostics.
