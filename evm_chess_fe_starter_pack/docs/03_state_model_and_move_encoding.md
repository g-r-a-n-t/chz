# State model and move encoding

## 1. Design goal

On EVM, **persistent storage writes are expensive**. That pushes you toward a representation that minimizes the number of written slots, even if the in-transaction computation is more arithmetic-heavy.

That strongly favors:

- compact packed storage
- small external move encoding
- recomputing simple attack relations on demand
- not storing presentation-friendly data on-chain

## 2. Representation options

### Option A — 12 piece bitboards
Store a bitboard for each piece type/color.

**Pros**
- excellent for engine-style move generation
- familiar to chess programmers

**Cons**
- many slots if persisted directly
- multiple bitboards update on every move
- less attractive for gas-sensitive persistence

This is better off-chain than on-chain.

### Option B — 64-square mailbox / array
Store a piece code for each square.

**Pros**
- easy to reason about
- natural for rule correctness

**Cons**
- naive array storage is bad on-chain if not packed

### Option C — packed nibbleboard (**recommended**)
Use one 256-bit word, 4 bits per square.

**Pros**
- 1 slot for the board
- deterministic and compact
- updates can be implemented with masks and shifts
- enough states for empty + 12 piece types with room to spare

**Cons**
- requires careful bit manipulation
- attack scans are more manual

For EVM settlement this is usually the best persistence format.

## 3. Suggested piece codes

One practical scheme:

- `0x0` empty
- `0x1` white pawn
- `0x2` white knight
- `0x3` white bishop
- `0x4` white rook
- `0x5` white queen
- `0x6` white king
- `0x9` black pawn
- `0xA` black knight
- `0xB` black bishop
- `0xC` black rook
- `0xD` black queen
- `0xE` black king

Why this is nice:
- 4 bits are enough
- top color bit can be inferred (`>= 8`)
- lower bits still encode the piece family cleanly

## 4. Square indexing

Pick one square index convention and never cheat on it.

Recommended:

- `0 = a1`
- `1 = b1`
- ...
- `7 = h1`
- `8 = a2`
- ...
- `63 = h8`

That makes:
- file = `sq & 7`
- rank = `sq >> 3`
- white north = `+8`
- black south = `-8`

It also keeps UCI/FEN conversions straightforward.

## 5. Packed board helpers

Core helpers:

- `piece_at(board, sq) -> piece`
- `set_piece(board, sq, piece) -> board`
- `clear_piece(board, sq) -> board`
- `move_piece(board, from, to) -> board`

Because the board is one packed word, all of these should operate via:
- shift by `sq * 4`
- mask nibble
- insert replacement nibble

## 6. Meta word

Keep non-board game state in a second packed word.

Suggested fields:

- side to move: 1 bit
- castling rights: 4 bits (`WK, WQ, BK, BQ`)
- en passant file or sentinel: 4 bits
- halfmove clock: 8 bits
- fullmove number: 16 bits
- white king square: 6 bits
- black king square: 6 bits
- status / result flags: a few bits
- optional repetition ring head / length: a few bits

You do not need a perfect layout now; you need a stable one.

## 7. Cache king squares

Always store the white and black king squares explicitly.

Reason:
- king lookup becomes O(1)
- every legality check needs it
- the storage cost is tiny
- it prevents repeated full-board scans

## 8. External move encoding

Use a compact integer, not a string.

Recommended minimal move encoding:

- bits `0..5`   = from square
- bits `6..11`  = to square
- bits `12..14` = promotion kind
  - `0` none
  - `1` knight
  - `2` bishop
  - `3` rook
  - `4` queen

Store it as `u16` or `u32`.

### Why not encode capture / castle / en passant flags?
Because the contract can derive them from the current state:
- if king moves two squares, it is castling
- if a pawn moves diagonally to empty en-passant target, it is en passant
- if destination had enemy piece, it is a normal capture
- if pawn reaches back rank, promotion kind decides the piece

Derivation removes a large class of malformed-input bugs.

## 9. UCI boundary

Use UCI only at the bridge/API boundary.

Examples:
- `e2e4`
- `e7e8q`
- `a7a8n`

Translate immediately into the compact internal move encoding.

Do **not** parse strings on-chain.

## 10. Repetition hashing

You need a canonical “position identity” for repetition logic.

It must include only what matters to repetition:
- board placement
- side to move
- castling rights
- legal en passant availability when it changes legal moves

It must **not** depend on:
- halfmove clock
- fullmove number
- wager, players, deadlines, or other settlement fields

## 11. Keccak vs Zobrist

### Zobrist
Classic engine choice:
- incremental XOR updates
- excellent off-chain
- tiny hash width if 64-bit

Problems on-chain:
- you need a large constant table
- table access and code size are not free
- truncated collisions may matter more when money is involved

### Keccak of canonical packed state
Very attractive on-chain:
- cryptographic collision resistance
- available as an EVM intrinsic
- no giant random constant table
- simpler to audit

Default recommendation for an on-chain arbiter:
- **use keccak of canonical repetition-relevant state**
- use Zobrist only in off-chain tools if you want engine-style speed

## 12. En passant hashing nuance

This is one of the easiest places to get repetition wrong.

Two positions are different only if en passant changes the set of legal moves. So the repetition hash should include the en-passant field only when a legal en-passant capture is available from the current state.

That is stricter than simply “the last move was a double pawn push”.

## 13. Repetition storage options

### A. Bounded ring buffer
Store recent repetition hashes since the last irreversible move.

Good because:
- bounded size
- overwrite in a circle
- claims scan a bounded list

### B. Epoch-tagged count map
Store `hash -> (epoch, count)`.

Good because:
- O(1) repetition count lookup

Bad because:
- persistent mapping growth
- more storage writes
- worse mainnet economics

### Recommended default
Use a **ring buffer** if you want bounded storage and can tolerate rare scan logic during claims or end-of-move auto-draw checks.

## 14. Irreversibility tracking

Repetition history can reset on more than pawn moves and captures.

A move is “repetition-irreversible” if it:
- moves a pawn
- captures
- changes castling rights
- creates/removes a legally relevant en-passant possibility

So keep:
- halfmove clock for 50/75 rule
- a separate repetition-segment notion for repetition accounting

Do not assume those are the same thing.

## 15. Events vs storage

Not everything belongs in persistent storage.

Good event data:
- accepted move
- compact move encoding
- resulting repetition hash
- status/result transitions

Good persistent data:
- current board
- current meta
- stake and players
- deadline / status

Do not persist SAN or PGN.

## 16. Suggested persistent shape for a single match

Minimal single-match storage:
- `board_word: u256`
- `meta_word: u256`
- `white: Address`
- `black: Address`
- `wager: u256`
- `status: u8`
- `deadline: u64`

Optional:
- repetition ring storage
- transcript root / transcript hash
- payout flags
