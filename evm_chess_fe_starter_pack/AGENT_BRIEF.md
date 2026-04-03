# Agent brief

This file is the fastest possible brief for a coder agent.

## Primary objective

Build a **deterministic, auditable chess rules core** suitable for EVM settlement. The output is not an engine and not a searcher. It is a legality checker + state transition machine + settlement wrapper.

## Non-goals

- no search / evaluation / opening book
- no SAN generation on-chain
- no PGN generation on-chain
- no need for bitboard-level engine speed if it costs storage writes
- no browser automation against Lichess
- no reliance on “common online shortcuts” where FIDE distinctions matter

## Critical invariants

1. Exactly one white king and one black king.
2. A move is only accepted if the mover’s king is not left in check.
3. Castling rights are lost permanently once the king moves or the corresponding rook moves.
4. Castling rights also disappear if a rook is captured on its original corner square.
5. En passant is legal only on the immediately following move.
6. En passant must be tested on the resulting occupancy, because both pawns disappear from their original rank/file relationship.
7. Promotion requires an explicit piece choice and the promoted piece acts immediately.
8. Repetition equality depends on:
   - side to move
   - piece placement
   - castling rights
   - en passant availability if it changes the legal move set
9. Threefold and fifty-move are claimable; fivefold and seventy-five-move are automatic.
10. Dead position is stricter than “insufficient material” shortcuts.
11. Pinned pieces still attack squares for king-safety purposes.
12. Do not trust move flags supplied by the caller; infer semantics from state.

## Best default on-chain representation

Use a **nibbleboard** in one 256-bit word:

- 64 squares
- 4 bits per square
- exactly 256 bits

Then keep a second meta word for:

- side to move
- castling rights
- en passant file / none
- halfmove clock
- fullmove number
- king squares
- optional result / status flags

Why this is attractive:

- one board slot
- one meta slot
- updates are local and deterministic
- computation is cheaper than extra persistent storage writes on EVM

## Best default move encoding

Use a compact integer, for example:

- 6 bits: from square
- 6 bits: to square
- 3 bits: promotion piece kind (0 none, 1 knight, 2 bishop, 3 rook, 4 queen)
- spare bits reserved

Do **not** store capture / castle / en-passant flags in the external encoding unless you absolutely need them. Derive them.

## Recommended legality strategy

For a submitted move, do this:

1. Decode from/to/promo.
2. Check source square, ownership, target-ownership conflict.
3. Check pseudo-legal geometry.
4. Check special-rule preconditions for castle / en passant / promotion.
5. Apply move to a scratch state.
6. Reject if own king is attacked in result.
7. Update clocks, rights, ep square, king squares.
8. Determine terminal result by probing for at least one opponent legal reply.
9. Commit.

This catches pins and self-check cheaply and robustly.

## Repetition strategy options

### Option A — bounded ring buffer
Store a bounded ring of recent repetition hashes since the last irreversible move.

Pros:
- bounded storage
- easier to reason about
- no permanent count map growth

Cons:
- draw claims require scanning

### Option B — epoch-tagged count map
Use `hash -> (epoch, count)`.

Pros:
- O(1) count lookup

Cons:
- more map writes
- more persistent growth
- less attractive on mainnet

Default recommendation: **ring buffer on-chain**, especially if you care about bounded storage.

## Dead-position policy

For strict FIDE compliance, dead-position detection is subtle. Recommended practical policy:

- implement exact trivial dead positions on-chain
- document the distinction from material-only heuristics
- if you need absolute completeness for rare cases, route those through an explicit dispute / proof path rather than pretending the heuristic is complete

## Best deployment model

If the goal is real users and cost discipline:

- escrow and result settlement on-chain
- moves off-chain
- challenge / fraud proof on-chain
- L2 first
- Lichess or custom UI for user experience

## Files to read next

1. `docs/01_architecture_and_scope.md`
2. `docs/03_state_model_and_move_encoding.md`
3. `docs/04_move_validation_pipeline.md`
4. `docs/05_draws_repetition_and_dead_positions.md`
5. `docs/06_gas_and_evm_constraints.md`
