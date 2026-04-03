# chz contract API (current v0 + draft notes)

This is a draft ABI for the on-chain “match” layer.

Design goals
- small, deterministic surface
- explicit revert behavior for false claims
- events sufficient for off-chain reconstruction and reconciliation

## Current v0 shape

v0 is **one-contract-per-match**: deploy `ChzGame` for each game.

Constructor (payable)
- `init(white: Address, black: Address, wager: u256)`
- requires `msg.value == 2*wager` (full escrow up-front)

Core on-chain state
- packed `board_word` (`u256`)
- packed `meta_word` (`u256`)
- player addresses
- wager + terminal status/reason
- payout balances (pull-based withdrawals)

## Messages (implemented in v0)

### `submitMove(mv, claim_flags) -> bool`

Inputs
- `mv: u32` (compact encoding)
- `claim_flags: u8` (bitfield; see below)

Checks (v0 behavior)
- game is ongoing
- caller is correct side to move (or signature authorizes it)
- move is legal
- if claim flag is set, claim must be valid

Post-state
- board/meta advanced
- terminal result evaluated
- events emitted

### `claimDrawNow(reason) -> bool`

Reasons (draft)
- `1`: threefold (implemented)
- `2`: fifty-move (implemented)

Behavior
- if claim is false => returns `false`
- if true => end game and settle

### `resign() -> bool`

Behavior
- caller must be a player
- game must be ongoing
- ends game and settles

### `withdrawTo(to) -> bool`

Behavior
- caller must be a player with a non-zero payout balance
- sets payout to zero then transfers ETH to `to` (reverts on send failure)

## Claim flags

We want “claim by move” semantics without requiring extra txs.

Meaning
- **Claim-now**: `claimDrawNow(...)` ends the game immediately if true.
- **Claim-by-move**: `submitMove(..., claim_flags=...)` returns `false` unless the submitted move both:
  1) is legal, and
  2) results in the claimed draw condition being satisfied.

Bitfield proposal
- `0x01`: claim threefold (implemented)
- `0x02`: claim fifty-move (implemented)

Notes
- keep this small; flags expand ABI surface fast
- do **not** allow the caller to claim “castle/en-passant/capture” flags; infer them

## Events (implemented in v0)

### `MatchCreated`
- `white`, `black`, `wager`, `initial_hash`

### `MoveAccepted`
- mv
- pos_hash
- status
- end_reason

### `Withdrawal`
- player
- to
- amount

## Errors (notes)

Revert categories worth modeling explicitly:
- v0 mostly returns `false` on failure (except constructor escrow mismatch and failed ETH send).

## Open decisions (still true)

1. Manager-with-map vs one-contract-per-match.
2. Timeout semantics (FIDE “no mate => draw” vs simpler product rule).
3. Whether to store `position_hash` in storage (cheap reconciliation) or compute/log only.
