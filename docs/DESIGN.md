# chz design (working spec)

This document pins the initial design for the chz implementation.

The baseline ideas are adapted from `evm_chess_fe_starter_pack/docs/*`, but this file is the *chz-specific* “single source of truth”.

## System shape

- **Rules core** (pure-ish): packed board/meta, move legality, state transition, terminal classification
- **Match wrapper** (stateful): players, wager, deadlines, claims, payout, event log
- **Off-chain tools**: encoding, differential oracle, perft driver, (optional) Lichess bridge

Implementation note
- In Fe code, the rules core module is named `chess` (not `core`) to avoid colliding with Fe’s standard `core` ingot.

## Chess scope

In scope (v0)
- orthodox chess from the standard initial position
- full move legality (incl. castling/en-passant/promotion)
- terminal state detection (mate/stalemate)
- repetition and 50/75-move machinery
- **dead position** handling (goal: strict/complete FIDE dead-position semantics; see `docs/DECISIONS.md`)

Out of scope (v0)
- chess variants (Chess960, etc.)
- arbitrary on-chain FEN import (dev tooling may still parse FEN off-chain)
- on-chain SAN/PGN

## Packed board (“nibbleboard”)

One `u256` stores the entire board:
- 64 squares
- 4 bits per square
- square `sq` lives at bits `[sq*4 .. sq*4+3]`

Square indexing (fixed):
- `0 = a1`, `1 = b1`, …, `7 = h1`
- `8 = a2`, …, `63 = h8`

Helpers required
- `piece_at(board, sq) -> u8`
- `set_piece(board, sq, piece) -> u256`
- `clear_piece(board, sq) -> u256`
- `move_piece(board, from, to) -> u256`

### Piece codes (4-bit)

Working encoding:
- `0x0` empty
- `0x1..0x6` white: pawn, knight, bishop, rook, queen, king
- `0x9..0xE` black: pawn, knight, bishop, rook, queen, king

Color test:
- `piece >= 8` => black
- `piece != 0 && piece < 8` => white

## Packed meta word

Second `u256` stores *chess-relevant* metadata.

Working fields (tentative bit layout)

| Field | Bits | Notes |
|---|---:|---|
| side to move | 1 | `1 = white`, `0 = black` (tentative) |
| castling rights | 4 | `WK,WQ,BK,BQ` |
| EP file | 4 | `0..7`, `0xF = none` |
| halfmove clock | 8 | increments on reversible moves; resets on pawn move/capture |
| fullmove number | 16 | increments after black moves |
| white king square | 6 | cached for O(1) check tests |
| black king square | 6 | cached for O(1) check tests |

Notes
- **Do not** store settlement-only fields (players, wager, deadlines) in this word.
- Repetition hashing must **ignore** halfmove/fullmove.
- EP field is stored as *file-only*; rank is implied by side-to-move.

## Compact move encoding

One `u32` (or `u16`) for on-chain move I/O:

- bits `0..5`: from square
- bits `6..11`: to square
- bits `12..14`: promotion kind (`0 none, 1 N, 2 B, 3 R, 4 Q`)

Do not encode “capture/castle/ep” flags in the external move:
- infer semantics from the state + geometry
- reject malformed promotion (promotion required on back-rank pawn moves)

## Legality strategy (core philosophy)

Validate a *single submitted move* via:
1. decode from/to/promo
2. source piece exists and belongs to side-to-move
3. destination is not friendly-occupied
4. pseudo-legal geometry + ray blocking
5. special-move preconditions (castle/ep/promo)
6. apply to scratch state
7. reject if mover king is attacked in resulting state
8. update meta (rights/ep/clocks/king sq)
9. classify terminal conditions (mate/stalemate/draw)
10. commit once

This keeps pins and discovered-check interactions correct without needing “full legal generation” for normal moves.

## `is_square_attacked` (center of correctness)

Must consider attackers from:
- pawns
- knights
- kings
- bishops/queens on diagonals
- rooks/queens on ranks/files

Important: **pinned pieces still attack** squares for king-safety and castling-through-check logic.

## Terminal state classification

After an accepted move, evaluate the opponent:
- if in check and no legal reply => checkmate
- if not in check and no legal reply => stalemate

Draw machinery
- automatic: fivefold, seventy-five-move (unless the last move is checkmate)
- claimable: threefold, fifty-move (ABI must allow “claim now” and/or “claim by move”)

Dead position (policy)
- target strict/complete FIDE dead-position semantics (acknowledged hard)
- likely needs a staged implementation plan and/or a dispute/proof path for rare edge cases
- see `docs/DECISIONS.md`
- v0 implementation note: current on-chain detection is a **conservative insufficient-material subset**:
  - K vs K
  - K+N vs K
  - bishops-only positions where **all bishops are on the same color squares**
    - includes: K+B vs K, K+B vs K+B (same-colored bishops), and promoted-bishop edge cases
  - notably **not** treated as dead: K+2N vs K (checkmate positions exist)

## Repetition identity + storage

Repetition equality depends on:
- board placement
- side to move
- castling rights
- **legal EP availability only when it changes legal moves**

Default approach
- compute `pos_hash = keccak256(canonical_repetition_state)`
- store `pos_hash` into a **bounded ring buffer** since last repetition-irreversible move
- on claim, scan the ring buffer to count occurrences

Why ring buffer
- bounded storage (no unbounded map growth)
- claim-time scanning is acceptable because bounds are small under 75-move rules

## Contract architecture (two viable shapes)

### Option 1: “all-in-one” manager
One contract stores many matches in a map.

Pros
- simpler deployment/story
- easy indexing by `match_id`

Cons
- risk of hitting **EIP-170 code size** once the rules core is fully implemented

### Option 2: rules contract + thin match contract(s)
Deploy a single **stateless rules contract** and have match(s) call it.

Pros
- isolates big rules code into one place
- match contract stays small
- rules contract is an ideal target for HEVM properties

Cons
- cross-contract call overhead
- slightly more moving parts

Decision gate
- after Phase 3, measure bytecode size and decide.
