# Agent Brief: Integrate Chess Validation Aggressively

## Objective

Integrate a multi-layer validation system into the chess engine so that correctness checks can run in several modes:

- **LIGHT** for cheap invariants after every move / unmove in debug builds.
- **FULL** for recomputation-heavy checks in sampled debug runs, perft, fuzzing, and CI.
- **IMPORT_BASIC** for external FEN validation.
- **IMPORT_STRICT** for external FEN validation plus reachability-style heuristics.
- **ORACLE** for perft, differential, and tablebase-backed validation.

Use the files in `machine/` as the source of truth for invariant IDs, stage hooks, policy choices, and expected outputs.

## Non-negotiables

1. Do **not** conflate FEN state with board-only geometry.
2. Do **not** conflate:
   - castling rights with current castling legality,
   - FEN EP target-square semantics with “a legal EP capture definitely exists now,”
   - basic-valid import states with proven reachable legal positions.
3. Preserve a distinction between:
   - `TRUSTED_GENERATED`
   - `BASIC_VALID`
   - `HEURISTIC_REACHABILITY_PASS`
   - `HEURISTIC_REACHABILITY_FAIL`
   - `INVALID`

## Deliverables

### 1. Validation API

Implement something equivalent to:

```text
enum ValidationMode {
    OFF,
    LIGHT,
    FULL,
    IMPORT_BASIC,
    IMPORT_STRICT,
    ORACLE
}

enum ValidityLevel {
    TRUSTED_GENERATED,
    BASIC_VALID,
    HEURISTIC_REACHABILITY_PASS,
    HEURISTIC_REACHABILITY_FAIL,
    INVALID
}

struct ValidationReport {
    bool ok;
    ValidationMode mode;
    string stage;
    ValidityLevel validity_level;
    Failure[] failures;
    string[] warnings;
    string[] normalized_changes;
}
```

Required functions:

```text
ValidationReport validate_position(Position pos, ValidationMode mode, string stage);
ValidationReport validate_transition(Position before, Move mv, Position after, ValidationMode mode);
Position normalize_imported_position(Position pos, PolicySet policy);
```

### 2. Stage hooks

Wire validation into these checkpoints:

- import / parse_fen
- canonicalize
- after_make
- after_unmake
- after_null (if supported)
- after_movegen
- search_root
- periodic_deep_check
- perft
- differential
- oracle

Use `machine/checkpoints.json`.

### 3. Import policy

Implement explicit EP policy support:

- `spec_fen`
- `strict_captureable`

Implement explicit validity-level assignment. Imported FENs must **not** silently become `TRUSTED_GENERATED`.

### 4. Test harnesses

Implement:

- perft / divide harness using `machine/perft_reference.json`
- random reachable-state walk harness with make/unmake exactness
- differential harness against python-chess or another trusted reference
- optional Syzygy oracle harness for eligible endgames

### 5. Reporting

On failure, report:

- invariant ID
- severity
- short message
- state snapshot / FEN
- move being applied if in transition mode
- stage
- policy mode
- normalized changes if any

## Implementation order

### Phase 1 — high return, low ambiguity

- Implement validity levels and policies.
- Implement LIGHT invariants for representation, local legality, and history.
- Wire LIGHT checks after every make/unmake in debug builds.
- Implement exact make/unmake roundtrip checks.

### Phase 2 — import correctness

- Implement IMPORT_BASIC.
- Preserve exact external FEN semantics.
- Add explicit internal canonicalization.
- Implement IMPORT_STRICT heuristics from `RCH-*`.

### Phase 3 — oracles

- Add perft and divide corpus checks.
- Add random-walk stress with periodic FULL validation.
- Add differential testing.
- Add tablebase checks where supported.

### Phase 4 — search safety

- Assert root non-mutation.
- Assert PV replay legality.
- Assert TT move sanity in debug mode.
- Add null-move invariants if the engine supports null move.

## Acceptance criteria

The work is done when all of the following are true:

- `LIGHT` validation is integrated into move / unmove paths.
- `FULL` validation can be sampled or forced in debug mode.
- imported FENs receive explicit validity levels rather than a single opaque boolean.
- the standard perft corpus in `machine/perft_reference.json` passes at the chosen CI depths.
- start-position divide at depth 5 matches the included reference counts.
- random walk + make/unmake + full-state equality checks are green.
- differential legal move set tests are green on a representative sample of reachable positions.
- root search does not mutate the position.
- failures identify exact invariant IDs from the catalog.

## Pitfalls to avoid

- Treating castling-right flags as proof that castling is currently legal.
- Dropping the EP square during FEN import even in `spec_fen` compatibility mode.
- Assuming imported positions that pass local checks are therefore reachable from the initial position.
- Treating metamorphic evaluation differences as proof of a move-legality bug.
- Letting search-only structures mutate core game state.
