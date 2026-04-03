# verification (HEVM + invariants plan)

chz can’t realistically be “fully formally verified” end-to-end. The target is:
- heavy differential testing for broad coverage
- **small, high-value formal properties** on the compiled EVM bytecode where feasible

## Why HEVM is interesting here

HEVM can:
- symbolically execute EVM bytecode
- search for counterexamples to asserted invariants
- help prove small functional properties of “pure-ish” routines

This aligns well with a design that isolates a stateless “rules” component.

## Candidate proof targets (high value, bounded)

### Packing helpers
- `piece_at(set_piece(board, sq, p), sq) == p`
- `clear_piece` removes exactly one nibble
- `move_piece` is equivalent to clear+set with correct ordering

### King safety
If `validate_move` returns `Ok`, then the mover’s king is not attacked in the resulting state.

### Castling-right monotonicity
Rights are only removed, never re-added.

### EP lifetime
EP is available for at most one ply after the enabling double-pawn push.

### Repetition canonicalization
- the canonical repetition-state hash includes EP information **only when legal EP changes the move set**

## Practical constraints

- Symbolic chess state space explodes quickly.
- Many useful properties require bounding the domain (ex: restrict squares/pieces).
- Proofs are easier if the rules component is exposed as pure entrypoints.

## Proposed strategy

1. Implement a small set of “proof-friendly” entrypoints (pure functions).
2. Add `assert(...)`-style checks for invariants in those entrypoints.
3. Use HEVM to search for counterexamples.
4. Keep the proven set small and meaningful; prefer proofs that catch catastrophic bugs.

## Current tooling hook (implemented)

`ChzRules` is a stateless contract intended for concrete/symbolic hevm runs:
- `applyMove(board_word, meta_word, mv_word) -> (ok, board2, meta2, status, reason, pos_hash)`
- `classify(board_word, meta_word) -> (status, reason)`
- `positionHash(board_word, meta_word) -> hash`

Concrete execution helper:
- `scripts/hevm_rules.sh` (uses `../hevm/local/bin/hevm` + `cast`)

### Symbolic checks (implemented)

`ChzProofs` is a small contract that exposes proof-friendly entrypoints and uses
Solidity-style `Panic(0x01)` reverts so `hevm symbolic` can search for violations.

Run:
```sh
make fe-build
scripts/hevm_symbolic.sh
```

Notes:
- `scripts/hevm_symbolic.sh` runs the cheap packing invariants by default.
- Set `HEAVY_SYMBOLIC=1` to also run heavier properties (may be slow).
- Use `SYMBOLIC_TIMEOUT_SECS` / `HEAVY_SYMBOLIC_TIMEOUT_SECS` to cap wall-clock time per proof.

### Mega reference vectors (import + oracle checks)

The repo includes `chess_validation_mega_reference/` (a validation “mega reference” pack with machine-readable vectors).

Run:
```sh
make fe-build
scripts/run_mega_vectors.py
```

This checks:
- python-chess validity status for the mega vectors
- `ChzRules` legal-move set agreement + transition spot-checks on BASIC_VALID vectors
- terminal classification for stalemate/checkmate/dead-position vectors
- EP canonicalization for repetition hashing on the spec-FEN EP vector

### Metamorphic perft checks

Run:
```sh
make fe-build
scripts/metamorphic_perft.py --depth 2
```

This applies the symmetry transform “mirror ranks + swap colors + swap stm/castling/king-cache” and checks perft invariance at the chosen depth.

### Random-walk agreement (reachable positions)

Run:
```sh
make fe-build
scripts/random_walk_agreement.py
```

This performs long reachable-state random walks driven by python-chess legal moves and asserts:
- exact FEN agreement (with periodic full legal-move-set checks), and
- terminal classification agreement for automatic outcomes (checkmate/stalemate/dead-position/75-move).

### Dead-position differential (minor-only positions)

Run:
```sh
make dead-diff
```

This generates random positions with only kings and minor pieces and checks that `ChzRules.classify` matches `python-chess` for dead-position semantics (plus mate/stalemate/75-move).

## Open question

Do we want verification to target:
- the **rules core bytecode** (preferred), or
- the full match/escrow contract bytecode (harder due to storage + time)?

See also: `docs/VALIDATION_GAPS.md`.
