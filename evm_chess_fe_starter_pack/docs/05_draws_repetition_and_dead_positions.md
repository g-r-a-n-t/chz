# Draws, repetition, and dead positions

This is the most under-specified part of many chess backends. It deserves its own file.

## 1. Distinct draw/end concepts

Do not collapse these into one bucket.

- stalemate
- dead position
- claimable threefold repetition
- automatic fivefold repetition
- claimable fifty-move rule
- automatic seventy-five-move rule
- timeout where opponent cannot mate
- agreed draw / resignation / settlement-specific outcomes

Each has different triggers.

## 2. Repetition equality

Two positions count as the same repetition state only if:

- same side to move
- same piece placement
- same castling rights
- same legal move set with respect to en passant

So:
- fullmove number is irrelevant
- halfmove clock is irrelevant
- “same-looking board” is not enough

## 3. En-passant nuance in repetition hashing

This is the single most important subtlety in repetition logic.

The repetition identity should include en-passant state **only if it changes legal moves**.

That means:
- a raw FEN ep square after a double push is not automatically relevant
- if no legal en-passant capture exists, the repetition state should usually behave as though there is no ep opportunity

This is why raw FEN equality is not repetition equality.

## 4. Threefold repetition

Threefold is claimable, not automatic.

The claim may be based on:
- the current position already having occurred three times
- the intended move producing the third occurrence

That means your ABI should consider both:
- a “claim now” function
- a move submission with draw-claim flags

### Practical ABI shape
Examples:
- `claim_draw_now(reason=threefold)`
- `submit_move(move, claim_flags=THREEFOLD_IF_RESULTING_POSITION_QUALIFIES)`

If a claim flag is set and the condition is false, reverting is clearer than silently ignoring the claim.

## 5. Fivefold repetition

Fivefold is automatic unless the last move checkmated.

That implies evaluation order after a submitted move should be roughly:

1. apply move
2. if opponent is checkmated, end by checkmate
3. else test automatic draw conditions such as fivefold / seventy-five-move
4. else expose claimable conditions such as threefold / fifty-move

## 6. Fifty-move rule

Claimable after fifty moves by each player without:
- any pawn move
- any capture

Implementation:
- keep `halfmove_clock`
- reset on pawn moves and captures
- claimable when `halfmove_clock >= 100`

## 7. Seventy-five-move rule

Automatic after seventy-five moves by each player without:
- any pawn move
- any capture

Implementation:
- automatic when `halfmove_clock >= 150`
- but if the just-played move checkmated, checkmate takes precedence

## 8. Irreversibility is not identical to halfmove reset

For repetition tracking, a move is effectively irreversible if it:
- moves a pawn
- captures
- changes castling rights
- changes legal en-passant availability

That is broader than the halfmove rule.

So keep two concepts separate:

### A. halfmove clock
Used for 50/75-move rules

### B. repetition segment
Used for repetition accounting

## 9. Repetition storage strategies

### Strategy A — ring buffer (recommended default)
Store repetition hashes since the last repetition-irreversible move.

Why it works:
- the game cannot continue indefinitely without pawn moves/captures because 75-move auto-draw exists
- the repetition-relevant segment is therefore bounded in practical rules space
- scanning a bounded ring for claims is acceptable

You can store:
- hash values
- ring head
- ring length

### Strategy B — epoch + count map
Keep `current_epoch` and `hash -> (epoch, count)`.

Pros:
- O(1) repetition count lookup
- easy auto-fivefold detection

Cons:
- map growth
- more writes
- worse storage economics

## 10. What should the repetition hash include?

Include:
- packed board
- side to move
- castling rights
- legal ep state relevant to legal moves

Exclude:
- halfmove clock
- fullmove number
- player addresses
- wagers
- deadlines
- settlement status

## 11. Suggested repetition hash pipeline

A canonical approach:

1. normalize legal ep relevance
2. pack:
   - board word
   - side to move
   - castling rights
   - normalized ep info
3. `position_hash = keccak256(...)`

This avoids giant Zobrist tables in runtime code.

## 12. Dead position

Dead position is stronger than insufficient-material heuristics.

### Safe trivial cases
These are good candidates for exact on-chain handling:
- king vs king
- king + bishop vs king
- king + knight vs king

Potentially also some other minimal classes are safe, but be conservative. The critical thing is to avoid claiming completeness you do not actually have.

### Recommended policy
Implement:
- exact trivial dead positions
- maybe a few additional clearly safe material classes after careful proof
- explicit documentation that the helper is not a universal dead-position oracle unless you prove it is

If product requirements demand exact rare-case compliance, let a dispute path or external proof handle those rare cases.

## 13. Timeout and inability to mate

If you model move deadlines, decide explicitly whether timeout follows the FIDE-style rule:
- if a player fails to complete moves in time, the opponent wins
- **unless the opponent cannot possibly checkmate by any series of legal moves**, in which case it is a draw

That policy interacts directly with your dead-position/insufficient-material logic.

If you do not want that complexity, declare a product-specific timeout rule and document that it is not full FIDE parity.

## 14. Suggested contract semantics

### Claim-now paths
- `claim_draw_now(threefold)`
- `claim_draw_now(fifty_move)`

### Claim-by-move paths
- `submit_move(move, claim_flags)`

### Automatic result checks after every accepted move
- checkmate
- stalemate
- dead position
- fivefold repetition
- seventy-five-move

### Optional manual outcomes
- resign
- agreed draw

## 15. Edge-case tests that belong here

- same board, castling rights differ => not same repetition
- same board, raw ep square differs but no legal ep capture => same repetition
- same board, legal ep capture exists in one state but not the other => not same repetition
- threefold claim on current position
- threefold claim by intended move
- 50-move claim
- 75-move automatic draw
- checkmate on move that would otherwise trip automatic draw
- timeout with opponent unable to mate
