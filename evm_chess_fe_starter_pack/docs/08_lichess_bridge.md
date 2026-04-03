# Lichess bridge

## 1. What the bridge should do

The bridge exists to connect a user-facing chess surface to your settlement contract.

Typical responsibilities:

- authenticate to Lichess through official mechanisms
- stream events / game states
- translate UCI moves into your compact on-chain encoding
- optionally submit moves on-chain
- reconcile on-chain state against observed move stream
- export PGN after completion
- archive metadata and transaction hashes

## 2. What the bridge should not do

- no scraping
- no browser automation
- no unofficial APIs
- no hidden trust in the bridge for legality
- no chain-side SAN generation

The contract must remain the final arbiter of legality if that is your trust model.

## 3. API usage principles

Use the official Lichess API only.

There are two broad integration patterns:

### A. Board API / third-party client style
Good for:
- official account-backed third-party play
- eBoard-like integrations
- external clients acting as the player surface

### B. Bot API
Good for:
- bot accounts
- automated stream-and-respond workflows

The official ecosystem documentation and client libraries expose event streams, game-state streams, move submission, and game export.

## 4. Time-control caution

Live on-chain settlement and Lichess fast time controls are a rough fit.

Practical recommendation:
- prefer rapid / classical / correspondence bridges
- avoid assuming L1 can keep up with blitz/bullet clocks
- use off-chain move collection with on-chain settlement if you need lower latency

This lines up with both blockchain finality reality and the official Board API use constraints.

## 5. Suggested bridge architecture

### Component 1 — Lichess session
- API token or OAuth session
- scoped permissions only
- rate-limit aware request behavior

### Component 2 — local canonical board
Maintain a local reference board off-chain, preferably with python-chess.

Why:
- parse and validate incoming UCI cleanly
- derive promotion semantics
- compute FEN/PGN/SAN off-chain
- compare against expected on-chain hash

### Component 3 — encoder
Convert:
- UCI string
- current local board state

into:
- compact internal move integer

### Component 4 — chain submitter
Responsible for:
- gas policy
- retries
- nonce management
- confirmation handling
- optional access list generation

### Component 5 — reconciler
After move acceptance:
- compare expected position hash with on-chain emitted hash
- halt on divergence
- mark dispute/manual review if desynced

## 6. Recommended operational flow

1. subscribe to Lichess events
2. on new move, update local reference board
3. encode move compactly
4. submit on-chain or append to off-chain transcript
5. wait for acceptance / confirmation
6. compare resulting on-chain state hash
7. continue until game end
8. export PGN and archive final settlement record

## 7. Why use python-chess locally

It is extremely useful as a bridge-side oracle for:
- UCI parsing
- legal move checking
- resulting FEN
- game-over conditions
- PGN generation in surrounding tooling

But do not blindly inherit every helper as authoritative for rare dead-position semantics. Use it as a strong oracle, not as a substitute for understanding the rule edge cases you care about.

## 8. Rate limits and request discipline

The Lichess API expects polite behavior.

Bridge rules:
- do not burst parallel calls unnecessarily
- prefer streams over polling
- back off hard on 429
- keep one-request-at-a-time discipline where practical
- keep the bridge stateless enough to recover from disconnects

## 9. Account / permission hygiene

- use least-privilege scopes
- separate bot accounts from human accounts if needed
- keep tokens out of the contract layer
- never hardcode long-lived secrets into published artifacts

## 10. Reconciliation strategy

A good safety pattern is:

- local board tracks Lichess
- contract emits a canonical repetition-relevant position hash after every accepted move
- bridge recomputes the same canonical hash locally
- mismatch => stop auto-submission and flag

This catches:
- encoding bugs
- desync
- chain-side rules regressions
- bridge parser errors

## 11. PGN handling

Do PGN work off-chain.

Typical outputs:
- archived game PGN
- chain tx hashes per ply
- final result metadata
- optional move-to-tx mapping for audit

The chain does not need SAN/PGN to settle a game.

## 12. Failure modes to handle

- temporary API disconnect
- on-chain tx stuck or dropped
- chain reorg
- bridge restart mid-game
- Lichess game aborted/resigned/timeout
- local/oracle desync
- false draw claim attempt due to bridge bug

## 13. Bridge policy for settlement models

### If every move is posted on-chain
The bridge is mainly a transport/reconciliation component.

### If off-chain play with dispute
The bridge may instead:
- collect signed moves
- commit transcript roots
- submit only checkpoints or finalization data
- reveal transcript only on dispute

## 14. Minimal skeleton responsibilities

The provided script skeleton assumes:
- `berserk` or direct HTTP client
- `python-chess` for local state
- your contract wrapper for move submission and state fetches

Fill in:
- token loading
- game selection
- chain client
- move encoder
- canonical hash matcher
