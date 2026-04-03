# External Position Policy

If your engine accepts arbitrary FENs, this file matters more than any single invariant list.

## The core problem

Imported positions sit at the intersection of three different notions:

1. **syntactically parseable**
2. **basic-valid**
3. **reachable from the initial position by legal play**

Those notions are not identical.

## Recommended public stance

Expose the distinction in your API and user-facing diagnostics.

Do **not** say:

- “legal” for every imported position that merely passes local checks.

Prefer:

- `BASIC_VALID`
- `HEURISTIC_REACHABILITY_PASS`
- `HEURISTIC_REACHABILITY_FAIL`
- `INVALID`

That matches both engine practice and the research literature more honestly.

## EP policy: external compatibility vs internal canonicalization

### `spec_fen`

Use when:

- parsing user-provided FEN
- exporting FEN
- round-tripping test fixtures
- preserving external compatibility

Definition:

- keep the EP target square after any double pawn push exactly as the FEN spec defines it.

### `strict_captureable`

Use when:

- you want a stricter internal invariant set
- you want to eliminate non-captureable EP squares from canonical internal state
- you want tighter debug checks

Definition:

- keep the EP square only if at least one legal EP capture exists and the capture is king-safe.

## Castling policy: rights vs immediate legality

Castling has two separate questions:

1. **Does the side still have the historical right?**
2. **Is castling legal on this move?**

Never merge them.

Correct decomposition:

- rights encode history,
- move legality adds geometry and attack-map checks.

## Reachability heuristics: what they are for

The `RCH-*` invariants are **not** a complete proof system for legal reachability.

They are useful for:

- rejecting obviously impossible imported positions,
- quarantining suspicious positions,
- making import APIs more honest,
- reducing garbage passed into analysis tools.

They are not enough to justify a claim such as “every FEN we accept is reachable from the initial position.”

## Recommended engine behavior by product type

### Engine used only for normal play / search from the standard start

- rely primarily on `TRUSTED_GENERATED`
- use import validation only for tooling surfaces

### Analysis tool that accepts arbitrary FENs

- implement BASIC_VALID
- implement explicit validity levels
- consider IMPORT_STRICT heuristics
- document that strict reachability is still a stronger question

### Rules server / validator for external clients

- expose policy mode explicitly
- return structured reasons
- preserve FEN I/O semantics exactly
- do not surprise clients by silently “fixing” their position unless normalization is opt-in

## Best practice

Treat external positions as an import problem first, a search problem second, and a reachability problem only where your product truly needs it.
