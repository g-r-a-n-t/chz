# Roadmap

## Phase 1 — pure state core

### Deliverables
- square indexing helpers
- packed nibbleboard helpers
- packed meta helpers
- move encode/decode
- attack detector
- check detector

### Exit criteria
- helper invariants pass
- king attack logic spot tests pass

## Phase 2 — move legality

### Deliverables
- pseudo-legal geometry checks
- sliding path checks
- castling legality
- en passant legality
- promotion logic
- self-check rejection

### Exit criteria
- curated legal/illegal fixtures pass
- edge cases in `data/edge_cases.json` pass where applicable

## Phase 3 — terminal-state logic

### Deliverables
- mate/stalemate detection
- halfmove clock logic
- repetition identity logic
- draw claims
- auto-draw handling
- trivial dead-position detection

### Exit criteria
- draw and terminal fixtures pass
- claim-now and claim-by-move semantics work

## Phase 4 — perft and differential validation

### Deliverables
- perft driver
- perft corpus support
- python-chess differential harness integration

### Exit criteria
- canonical perft counts pass for major benchmark positions
- random playout differential tests show no desync

## Phase 5 — Fe contract shell

### Deliverables
- match storage
- submit_move
- claim_draw_now
- claim_timeout
- resign
- events
- deadline handling

### Exit criteria
- contract integration tests pass
- state transitions match pure-core expectations

## Phase 6 — bridge

### Deliverables
- Lichess stream client
- local canonical board mirror
- move encoder
- on-chain submitter
- reconciliation hash checks
- PGN archival

### Exit criteria
- one full bridged game works end to end
- desync is detected and halts automation

## Phase 7 — settlement architecture refinement

### Deliverables
Choose and finalize one model:
- every move on-chain
- off-chain transcript + dispute
- final-state notarization + challenge

### Exit criteria
- threat model documented
- cost profile understood
- false-claim and timeout rules finalized

## Suggested decision gates

### Before allowing arbitrary FEN on-chain
Ask:
- do you actually need it?
- are you prepared to validate malformed states?
- can you keep that feature strictly test-only instead?

### Before optimizing
Ask:
- did perft pass?
- did differential tests pass?
- is there actual profiling evidence?

### Before mainnet
Ask:
- why is L2 or optimistic settlement not sufficient?
- are stake amounts large enough to justify the added mainnet cost?
- are code-size and storage-growth assumptions fully measured?

## Minimum viable serious version

A serious MVP is:

- standard initial position only
- one match contract or manager-backed matches
- compact move integer ABI
- full legal move validation
- checkmate/stalemate
- threefold/fifty-move claims
- fivefold/seventy-five-move auto draws
- basic timeout and resignation
- perft + differential-tested
- L2 deployment
