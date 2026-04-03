# Rules matrix

This file is the implementation checklist for orthodox chess legality and termination.

## 1. Legal move baseline

A move is legal only if all of the following hold:

1. the source square contains a piece of the side to move
2. the destination square is not occupied by a friendly piece
3. the piece’s movement pattern is satisfied
4. sliding paths are unobstructed where relevant
5. special-move preconditions are satisfied
6. after the move, the mover’s king is not in check

The last point is what kills most “almost correct” backends.

## 2. Piece movement rules

### King
- moves one square in any direction
- cannot move onto an attacked square
- may castle if all castling conditions are met

### Queen
- rook + bishop movement
- sliding; cannot jump

### Rook
- orthogonal sliding
- cannot jump

### Bishop
- diagonal sliding
- cannot jump

### Knight
- jumps in an L-shape
- ignores intervening pieces

### Pawn
White:
- single push: `+8`
- double push from rank 2 if both squares clear
- capture diagonally forward
- promote on rank 8
- en passant only immediately after the opponent’s two-square pawn advance

Black is symmetrical in the opposite direction.

## 3. Attack semantics that trip people up

### Pinned pieces still attack squares
This matters for king movement and castling-through-check logic.

If an enemy bishop is pinned to its own king, it still attacks along its line for purposes of “is my king moving into check?”

### King adjacency
Kings may never become adjacent because they attack each other’s neighboring squares.

### “Occupied by enemy” is not enough for legal capture
A move can geometrically capture an enemy piece and still be illegal if it leaves the moving side’s king in check.

## 4. Castling

Castling is legal only if:

1. the king has not moved
2. the relevant rook has not moved
3. the squares between king and rook are empty
4. the king is not in check
5. the square the king crosses is not attacked
6. the square the king lands on is not attacked

Important implementation notes:

- only the **king’s** path matters for attack checks
- the rook may move through attacked squares
- the rook square itself may be attacked; that does not matter
- if the rook on its home square is captured, the relevant castling right must be removed
- rights are permanent; if a rook moves away and comes back, rights do not return

## 5. En passant

En passant is legal only if:

1. the opponent’s previous move was a two-square pawn advance
2. your pawn is on an adjacent file and same rank
3. the capture is taken immediately on the next move
4. after performing the special capture, your king is not in check

The last condition is the famous trap. Because both pawns disappear from the rank/file relation, en passant can reveal a rook or bishop attack that was previously blocked.

This is one of the most common legality bugs.

## 6. Promotion

When a pawn reaches the back rank:

- promotion is mandatory
- the new piece must be explicitly chosen
- choice is limited to queen / rook / bishop / knight
- the effect of the promoted piece is immediate

Implications:
- a promoting move may give check immediately
- a promoting move may resolve check immediately
- `a7a8` without a promotion piece should be rejected by a backend that expects compact deterministic input

## 7. Check and self-check

A side is in check if its king’s square is attacked by any enemy piece.

No legal move may:
- expose the moving side’s king to check
- leave the moving side’s king in check

That means a validator should always have:
- `is_square_attacked`
- `in_check`
- a “make move then test” path

## 8. Checkmate

Checkmate means:

- side to move is in check
- side to move has no legal move

Implementation advice:
- first determine `in_check`
- if false, you are in stalemate territory instead
- if true, you only need to prove there is no legal reply

### Efficient reply logic
If in check:
- if there are 2+ checking pieces, only king moves can help
- if exactly 1 checker, legal replies are:
  - king move
  - capture the checker
  - interpose on the ray if the checker is sliding

This is important if you care about gas.

## 9. Stalemate

Stalemate means:

- side to move is **not** in check
- side to move has **no** legal move

Do not confuse stalemate with:
- dead position
- fifty-move draw
- insufficient-material heuristics

## 10. Dead position

Dead position means neither player can checkmate by **any** series of legal moves.

This is stricter than the common shortcut “insufficient material.”

Practical caution:
- many libraries expose helpers that only prove a material-based subset
- that is useful, but it is not the full FIDE concept

Recommended implementation policy:
- support exact trivial dead positions directly
- document clearly where you stop
- if strict completeness matters, handle rare non-trivial dead-position disputes via a challenge path rather than claiming a heuristic is exact

## 11. Repetition-related equality

For repetition, positions are the same only if:
- same side to move
- same pieces of the same kind on the same squares
- same castling rights
- same legal en passant availability where it changes the legal move set

This means:
- fullmove number does **not** matter
- halfmove clock does **not** matter
- a board that looks identical can still be a different repetition state

## 12. Fifty-move and seventy-five-move rules

### Claimable draw
- fifty-move rule is claimable

### Automatic draw
- seventy-five-move rule is automatic unless the last move checkmated

Keep a halfmove clock:
- reset on pawn moves
- reset on captures
- increment otherwise

## 13. Threefold and fivefold repetition

### Claimable
- threefold repetition

### Automatic
- fivefold repetition unless the last move checkmated

The contract interface should consider both:
- claim in the current position
- claim “this intended move will produce the draw condition”

## 14. Illegal moves vs illegal positions

### Illegal move
A proposed transition that violates movement or king-safety rules.

### Illegal position
A state that could not arise from legal play.

If production starts only from the standard initial position and every move is validated, you do not need a full illegal-position reachability checker in the contract.

If you allow arbitrary FEN imports, you do.

## 15. Structural validity checks for imported states

If you support arbitrary FEN initialization or challenge states, validate at least:

- exactly one white king
- exactly one black king
- kings not adjacent
- no pawn on rank 1 or rank 8
- side-to-move consistency
- castling rights only if relevant king/rook are on plausible home squares
- en passant field only if the previous move could plausibly have been a double push
- not both kings in check

A full reachability proof is much harder and usually not worth doing on-chain.

## 16. Rule traps your implementation must test

- pinned piece moves away and exposes own king
- en passant that reveals rook or bishop attack
- castling through attacked transit square
- king move onto a square attacked by a pinned enemy piece
- rook captured on corner removes castling right
- double check => only king moves
- promotion to knight/bishop/rook, not just queen
- same board, different castling rights => not same repetition state
- same board, different legal en passant availability => not same repetition state
- checkmate on a move that would otherwise trigger automatic repetition or 75-move draw
