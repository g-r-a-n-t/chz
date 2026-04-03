# Notation and I/O boundaries

## 1. Keep formats in the right layer

### On-chain
Use:
- compact move encoding
- compact state encoding
- canonical repetition hash inputs

### Off-chain
Use:
- UCI for move interchange
- FEN for debugging and test fixtures
- PGN / SAN for archival and presentation

This boundary keeps the contract small and deterministic.

## 2. UCI as the bridge format

Lichess and many chess tools work naturally with UCI-like move strings:
- `e2e4`
- `g1f3`
- `e7e8q`

Use UCI at the bridge boundary because:
- it is simple
- it captures promotion cleanly
- it maps directly to `from`, `to`, `promotion`

## 3. Internal compact move

Recommended conversion:

- parse UCI off-chain
- compute `from_sq`
- compute `to_sq`
- compute promotion kind
- pack into a small integer
- send that integer on-chain

This avoids string parsing and presentation concerns in the contract.

## 4. SAN is not a contract concern

SAN requires:
- disambiguation
- check/checkmate suffixes
- move-sequence awareness for formatting

That is UI/archival logic. Keep it off-chain.

## 5. FEN uses

FEN is useful for:
- test fixtures
- perft corpus
- debugging mismatches
- importing challenge states in a dev harness

Be careful:
- raw FEN ep fields are not the same as normalized repetition equality
- if you support FEN import on-chain, validate aggressively

## 6. Canonical state serialization for hashing

For repetition hashing, serialize only:
- packed board
- side to move
- castling rights
- normalized legal ep state

Do not include:
- halfmove clock
- fullmove number
- wager
- deadlines
- player addresses

You may still serialize those other fields for UI or debugging, but not for repetition identity.

## 7. PGN handling

PGN belongs off-chain.

Use it to:
- archive a completed match
- compare with Lichess exports
- expose human-readable audit trails
- publish settled games

A useful off-chain archive entry might contain:
- PGN
- chain transaction hashes per move
- final settlement transaction hash
- final result code

## 8. Result codes

Internally, define a compact result enum, for example:
- ongoing
- white win by checkmate
- black win by checkmate
- white win by resignation
- black win by resignation
- draw by stalemate
- draw by repetition
- draw by fifty move
- draw by seventy-five move
- draw by dead position
- draw by timeout-no-mate
- white win by timeout
- black win by timeout

Then map these to PGN/Lichess-style result strings off-chain:
- `1-0`
- `0-1`
- `1/2-1/2`

## 9. Recommended debug payloads

When logging or emitting diagnostic info off-chain, capture:
- FEN before move
- UCI move
- compact move integer
- board word
- meta word
- canonical repetition hash
- reason if rejected

This makes cross-system reconciliation much easier.

## 10. Parsing policy

Parsing should happen at the bridge or dev-tool layer, not in the contract.

The contract should expect:
- already-normalized compact moves
- explicit promotion piece codes
- optional explicit claim flags

That keeps the runtime surface tight and auditable.
