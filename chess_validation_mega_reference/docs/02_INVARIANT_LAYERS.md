# Invariant Layers

The catalog is easiest to use if you treat the invariants as five layers, not one undifferentiated list.

## Layer 1 — Representation

Count: **32**

These invariants verify that your internal state representation is self-consistent.

Typical examples:

- exactly one king per side,
- no pawns on rank 1 / 8,
- color occupancies disjoint,
- board array and bitboards agree,
- hash / material / attack caches match recomputation,
- castling-right field and EP field are structurally sane.

**Where to run:** always after make / unmake in debug builds, and on every import.

**Why it matters:** these are the fastest checks and they catch a huge fraction of real engine bugs.

## Layer 2 — Local legality

Count: **32**

These invariants verify that a position and move set obey chess rules locally.

Typical examples:

- side not to move is not in check,
- kings are not adjacent,
- legal moves are pseudo-legal plus king-safe,
- castling path and attack constraints hold,
- EP legality is history-sensitive and king-safe,
- promotion semantics are exact,
- checkmate / stalemate classification is exact.

**Where to run:** after move generation, after make, in perft, and in deep debug sampling.

**Why it matters:** this is the rule core.

## Layer 3 — History / transition

Count: **25**

These invariants verify that state fields tied to previous play are maintained exactly.

Typical examples:

- castling rights are monotone,
- EP expires after one reply,
- halfmove clock and fullmove number update correctly,
- make/unmake roundtrips exactly,
- repetition keys include side to move, castling rights, and relevant EP state,
- search does not mutate the root state.

**Where to run:** after make / unmake, at search boundaries, in random-walk stress tests.

**Why it matters:** many engines get board geometry right while still getting history wrong.

## Layer 4 — Reachability / import heuristics

Count: **10**

These are deliberately separated from local validity.

Typical examples:

- promotion budgets,
- pawn-capture budgets,
- pawn-origin plausibility,
- bishop color-complex plausibility,
- explicit validity levels for imported positions.

**Where to run:** imported FENs only.

**Why it matters:** an imported FEN can be locally valid but not actually reachable from the start of a legal game.

## Layer 5 — Metamorphic / oracle

Count: **12**

These are not “always-on” assertions. They are test harness relations.

Typical examples:

- FEN roundtrip,
- make/unmake involution,
- reflection / mirror symmetries,
- perft corpus agreement,
- differential legal move set agreement,
- Syzygy agreement.

**Where to run:** CI, debug harnesses, nightly stress, research validation.

**Why it matters:** these checks catch the bugs that local assertions sometimes miss.

## Recommended runtime split

### LIGHT

Run only cheap fatal / strict checks:

- core representation
- core local legality
- core history

### FULL

Add expensive recomputation:

- full move-set recomputation
- cache / hash refresh checks
- attack-map recomputation
- rebuild-from-history checks

### IMPORT_BASIC

Run structural and local validity while preserving external notation semantics.

### IMPORT_STRICT

Run IMPORT_BASIC plus reachability-style heuristics and optional internal canonicalization.

### ORACLE

Use perft, divide, differential testing, and tablebases.

## Practical rule

The more often a check runs, the more it should focus on cheap structural and transition correctness. The more expensive and semantic the check is, the more it belongs in import validation, perft, differential testing, and CI rather than in every search node.
