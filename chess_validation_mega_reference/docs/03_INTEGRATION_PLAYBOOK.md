# Integration Playbook

This section turns the invariant catalog into an engine-integration plan.

## 1. Give validation a real API, not scattered asserts

Recommended core surface:

```text
ValidationReport validate_position(Position pos, ValidationMode mode, string stage);
ValidationReport validate_transition(Position before, Move mv, Position after, ValidationMode mode);
Position normalize_imported_position(Position pos, PolicySet policy);
```

This avoids three common failure modes:

- hidden policy differences between import and internal state,
- rule checks that only exist in unit tests and never run in-engine,
- silent disagreement between move application, search, and serializers.

## 2. Recommended hook points

### `parse_fen`

Purpose: validate imported state before it touches search.

Run:

- representation checks,
- local legality checks that make sense on static state,
- external-policy EP and castling checks,
- validity-level classification.

### `canonicalize`

Purpose: convert external state into your preferred internal canonical form.

Use this to:

- optionally collapse `spec_fen` EP to `strict_captureable`,
- normalize internal castling-right representation,
- record normalization in the validation report.

### `after_make`

Purpose: catch bugs at the exact point they are introduced.

This is the single most important hook for:

- structural coherence,
- side-not-to-move not in check,
- castling / EP / promotion correctness,
- clock and rights updates,
- incremental hash / cache correctness.

### `after_unmake`

Purpose: prove reversibility.

This hook should be brutal. If `make` followed by `unmake` does not return the engine to an identical state, treat that as a release-blocking bug.

### `after_null`

Purpose: validate search-only null move semantics.

This is optional, but if null move exists, validate it explicitly.

### `after_movegen`

Purpose: compare move sets to rule expectations.

Use this for:

- legal ⊆ pseudo-legal
- legal = pseudo-legal minus self-checks
- castling and EP edge-case coverage
- full move-set recomputation in FULL mode

### `search_root`

Purpose: protect the public state boundary.

At minimum:

- validate before search,
- validate after search,
- assert root non-mutation,
- replay PV legally.

### `periodic_deep_check`

Purpose: sampled heavyweight validation inside search or fuzzing.

Suggested use:

- every N nodes in debug builds,
- every node in small perft tests,
- every move in random-walk harnesses.

## 3. Modes and when to use them

### OFF

Release fast path if desired.

### LIGHT

Cheap assertions only. Recommended for every `make` / `unmake` in debug builds.

### FULL

All recomputation-heavy checks. Recommended in:

- fuzzing,
- perft,
- random walks,
- CI,
- targeted bug hunts.

### IMPORT_BASIC

External FEN validator that preserves exact external semantics.

### IMPORT_STRICT

External validator plus heuristics and normalization.

### ORACLE

Harness mode for perft, differential testing, and tablebases.

## 4. Recommended engine workflow

```text
External FEN
  -> parse_fen
  -> validate_position(IMPORT_BASIC, "parse_fen")
  -> normalize_imported_position(policy)
  -> optional validate_position(IMPORT_STRICT, "canonicalize")
  -> assign validity level
  -> engine state
```

```text
make_move
  -> apply move
  -> validate_position(LIGHT, "after_make")
  -> optional validate_position(FULL, "after_make")
```

```text
unmake_move
  -> restore prior state
  -> validate_position(LIGHT, "after_unmake")
  -> optional validate_transition(before, mv, after, FULL)
```

```text
search
  -> validate_position(LIGHT/FULL, "search_root")
  -> run search
  -> validate_position(LIGHT/FULL, "search_root")
  -> replay PV
```

## 5. Exactness requirements for undo

Your undo frame should be able to restore at least:

- moved piece and captured piece,
- from / to squares,
- promotion piece,
- castling-right state,
- EP square,
- halfmove clock,
- fullmove number or equivalent ply context,
- hash keys and any incremental caches if they are not recomputed.

If any of these are reconstructed loosely rather than restored exactly, make/unmake drift becomes much more likely.

## 6. Suggested compile-time / runtime behavior

### Debug local development

- LIGHT after every make / unmake
- FULL on demand or sampled every N nodes

### CI / nightly

- FULL in perft and random-walk harnesses
- differential checks
- oracle checks where available

### Release builds

- optional OFF or import-only BASIC validation
- keep the validation API available even if most checks are compiled out

## 7. What not to do

- do not run reachability heuristics on every internal node
- do not normalize away external FEN semantics without documenting it
- do not let serializer logic invent castling / EP fields that the engine state does not actually support
- do not bury validation failures in generic assertions with no invariant IDs

The point of this architecture is not merely to crash fast; it is to crash **diagnostically**.
