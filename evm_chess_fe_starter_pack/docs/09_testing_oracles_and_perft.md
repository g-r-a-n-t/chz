# Testing, oracles, and perft

## 1. Why testing dominates this project

Chess rules are a dense edge-case surface. A backend can feel correct for dozens of casual games and still be catastrophically wrong on:
- en passant under pin
- castling through attack
- repetition equality
- dead-position semantics
- claimable-vs-automatic draw timing

So your test plan is the project.

## 2. Testing pyramid

### Layer 1 — helper invariants
Examples:
- `piece_at(set_piece(board, sq, p), sq) == p`
- clearing then reading yields empty
- king square cache remains consistent after king moves
- encode/decode round-trips for moves

### Layer 2 — rule spot tests
Examples:
- legal / illegal move fixtures
- terminal-state fixtures
- draw-claim fixtures

### Layer 3 — perft
Perft verifies move-generation correctness against canonical node counts.

### Layer 4 — differential testing
Compare your backend against python-chess for large numbers of legal positions and move sequences.

### Layer 5 — contract integration tests
Check:
- authorization
- deadlines
- payouts
- revert paths
- event emission

## 3. Perft

Perft is the gold standard for move-generation regressions.

Use the standard corpus in `data/perft_positions.json`.

At minimum, your implementation should hit the canonical counts for:
- initial position
- Kiwipete
- standard ep/castling stress positions
- deeper reference positions once performance allows

Perft catches:
- missing moves
- illegal moves accepted
- castling bugs
- en-passant bugs
- promotion bugs
- check evasions mishandled

## 4. Differential testing with python-chess

A very strong workflow is:

1. start from the standard initial position
2. generate random legal games with python-chess
3. after every move:
   - feed the same move into your backend
   - compare resulting legality, side-to-move, terminal flags, and canonical state
4. stop and dump the transcript on mismatch

Also test from curated edge-case FENs.

## 5. What to compare in differential tests

Good comparison targets:
- whether a candidate move is legal
- resulting board placement
- side to move
- castling rights
- legal ep availability
- check / checkmate / stalemate flags
- claimable draw flags
- halfmove clock
- canonical repetition hash normalization inputs

Be cautious comparing:
- dead-position helpers if one side uses only material heuristics
- representation-specific details that are not semantically meaningful

## 6. Randomized test generation

Useful generators:
- random legal move playout from initial position
- biased playouts that preserve castling rights longer
- positions with many promotions
- reversible move loops for repetition logic
- imported edge-case FEN corpus

## 7. Fuzz targets

### Fuzz the move decoder
Reject malformed bit patterns gracefully.

### Fuzz the board/meta packer
No out-of-range square arithmetic.

### Fuzz imported states if supported
Expect many malformed states.

### Fuzz claim flags
False claims must revert cleanly.

## 8. Contract tests

Contract-layer scenarios:
- only correct side can move
- wrong turn reverts
- move after game end reverts
- timeout before deadline reverts
- payout happens once
- false draw claim reverts
- state/event hashes match expected transition

## 9. Test oracles

### Primary oracle
`python-chess`

### Secondary oracle
standard perft counts and curated rule fixtures

### Human references
FIDE Laws of Chess and Chessprogramming Wiki notes

## 10. Known oracle caveat

`python-chess` is excellent for move legality, attack generation, repetition helpers, and standard game-end logic, but its insufficient-material helper is material-based and should not be mistaken for a universal dead-position oracle.

That is still useful:
- it is safe as a lower-bound style sanity aid
- it is not the final word on every rare dead-position case

## 11. Suggested acceptance milestones

### Milestone A
- all helper invariants pass
- initial position move legality spot checks pass

### Milestone B
- standard edge-case fixtures pass
- castling / ep / promotion spot tests pass

### Milestone C
- perft for initial position and Kiwipete passes through reasonable depth

### Milestone D
- long differential random playouts pass with no desync

### Milestone E
- settlement wrapper integration tests pass

## 12. Debugging advice

On mismatch, always dump:
- FEN before move
- compact move encoding
- UCI move
- side to move
- castling rights
- ep state
- halfmove/fullmove
- your canonical repetition hash inputs

That makes reproduction and minimization dramatically easier.
