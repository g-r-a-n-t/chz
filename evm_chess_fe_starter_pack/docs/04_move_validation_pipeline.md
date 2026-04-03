# Move validation pipeline

## 1. Philosophy

You are not building a search engine. You only need to validate a submitted move and determine the resulting state.

That means the default strategy should be:

- cheap pseudo-legal geometry check
- apply to scratch state
- king-safety test
- minimal opponent reply search only when needed for termination

This is usually simpler and safer than trying to generate the full legal move list on every turn.

## 2. Core helper functions

Build these first:

- `piece_at(board, sq) -> u8`
- `set_piece(board, sq, piece) -> board`
- `clear_piece(board, sq) -> board`
- `is_square_attacked(board, meta, sq, by_white) -> bool`
- `in_check(board, meta, white_side) -> bool`
- `apply_unchecked(board, meta, move) -> (board, meta, aux)`
- `validate_move(board, meta, move) -> Result<(board, meta, aux), Error>`
- `has_any_legal_move(board, meta, side) -> bool`

Everything else composes from these.

## 3. `is_square_attacked`

This function is the center of correctness.

It should check attacks from:

- pawns
- knights
- kings
- bishops/queens on diagonals
- rooks/queens on files/ranks

### Important notes
- pinned pieces still count as attackers
- the function should be based on current occupancy
- do not mix “attacked” with “legally movable by that side” in a way that suppresses pinned attacks

## 4. Validation pipeline for one move

For a submitted compact move `(from, to, promo)`:

### Step 1 — decode
Reject obviously malformed ranges.

### Step 2 — source/ownership
- source must contain piece
- piece must belong to side to move

### Step 3 — destination ownership
- destination cannot contain friendly piece

### Step 4 — piece-specific pseudo-legal geometry
Examples:
- rook must share rank/file
- bishop must share diagonal
- knight must match L pattern
- pawn must match push/capture/promotion rules
- king must be one step or a castling attempt

### Step 5 — path clearance
For sliding pieces:
- scan ray until destination
- reject if blocked

### Step 6 — special move preconditions
Handle branches:
- castling
- en passant
- promotion

### Step 7 — apply to scratch state
Perform board mutation on temporary values:
- move piece
- remove captured piece
- move rook for castling
- remove en-passant victim
- replace pawn by promoted piece
- update king squares if needed

### Step 8 — king safety
Reject if mover’s king is attacked in resulting state.

This single step is what naturally catches:
- pinned pieces
- self-check
- illegal en-passant exposures
- discovered-check mistakes

### Step 9 — update metadata
- side to move flips
- fullmove increments after black move
- halfmove reset or increment
- castling rights updated
- en-passant target recomputed
- repetition data updated

### Step 10 — terminal-state detection
Assess the opponent:
- in check?
- any legal move?
- claimable or automatic draw?
- dead position?

### Step 11 — commit
Persist only once the transition is fully validated.

## 5. Castling branch

Recognize castling from king motion:
- white king `e1 -> g1` or `e1 -> c1`
- black king `e8 -> g8` or `e8 -> c8`

Checks:
1. current castling right exists
2. squares between king and rook are empty
3. king is not currently in check
4. transit square not attacked
5. destination square not attacked

Then:
- move king
- move rook
- clear both castling rights for that side
- clear en-passant
- increment halfmove (no capture, no pawn move)

## 6. En passant branch

Recognize from state, not caller flags:
- moving piece is pawn
- destination is the current legal en-passant capture square
- destination is empty
- source and destination differ diagonally by one file and one rank in the correct direction

Then:
- move capturing pawn
- remove captured pawn from the passed-over square, not the destination square
- test resulting king safety on the updated occupancy

This is mandatory because the disappearing pawn may open a rook/bishop line.

## 7. Promotion branch

Conditions:
- moving piece is pawn
- destination rank is back rank
- promotion kind is nonzero and valid

Then:
- remove pawn from source
- place promoted piece at destination

Do not auto-default silently on-chain. Make the input deterministic.

## 8. Updating castling rights

Rights change when:
- the king moves
- a rook moves from its home corner
- a rook is captured on its home corner

That last one is frequently forgotten.

## 9. Updating en-passant

After a double pawn push:
- there may be an en-passant target square for the opponent

For repetition hashing:
- only include it if it creates a legal en-passant possibility

For move legality:
- it exists only for the immediately following turn

## 10. Opponent reply existence

To detect mate/stalemate, you do not need a full generated move list if you only want a boolean.

### Efficient pattern
If side is in check:
- count checkers
- double check => test only king moves
- single check => test king moves, captures of checker, and blocks if checker slides

If side is not in check:
- it is enough to find one legal move anywhere

In many cases you can short-circuit quickly.

## 11. Pseudocode shape

```text
validate_move(state, move):
    decode(move)
    piece = piece_at(board, from)
    require(piece belongs to side_to_move)
    require(dest not friendly)

    require(piece-specific geometry satisfied)
    require(path clear when sliding)

    (board2, meta2) = apply_special_case_aware(board, meta, move)
    require(not in_check(board2, meta2, mover_side))

    meta3 = update_rights_clocks_ep(board, meta2, move)

    outcome = classify_terminal_state(board2, meta3, opponent_side)

    return (board2, meta3, outcome)
```

## 12. Why “make then test” is a good default here

It naturally handles:
- absolute pins
- discovered checks
- en-passant occupancy anomalies
- complex special-move interactions

For a settlement contract that validates one move at a time, that simplicity is usually worth more than advanced legal-generation cleverness.

## 13. Common bugs

- checking castling attacks on rook path instead of king path
- forgetting rook-capture castling-right updates
- allowing promotion without an explicit piece
- treating pseudo-legal en passant as legal without king-safety test
- comparing repetition states with raw FEN ep square instead of legal ep relevance
- generating only “movement-legal” king moves and forgetting attacked-square rejection
- forgetting that pinned attackers still attack

## 14. Suggested acceptance tests for this layer

A move validator is not “done” until it passes:
- initial-position legal move set spot checks
- en-passant pin case
- castling through attack case
- promotion to every allowed piece
- king adjacency / king into check rejection
- mate/stalemate classifier spot checks
- perft at least through standard benchmark positions
