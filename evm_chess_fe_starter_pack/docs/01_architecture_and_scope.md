# Architecture and scope

## 1. What you are really building

Do not think “on-chain chess engine”.

Think:

- **game state machine**
- **legal move validator**
- **escrow / payout arbiter**
- **dispute resolver**
- **optional bridge target for external UIs such as Lichess**

That mindset changes almost every design decision. The contract only needs to answer questions like:

- is this move legal from the current state?
- whose turn is it?
- has the game ended?
- who gets paid?
- has a deadline expired?
- is a draw claim valid?

It does **not** need:

- evaluation
- search
- opening theory
- SAN pretty-printing
- human-focused notation logic on-chain
- engine-grade move ordering
- permanent full-history storage if your settlement model does not require it

## 2. Deployment models

### Model A — fully on-chain validated moves

Every move is submitted to the contract and validated immediately.

**Pros**
- simplest trust model
- easiest to reason about
- strongest “chain is the arbiter” story

**Cons**
- expensive
- repetition/history logic is costly
- L1 latency is poor for live play
- code-size pressure is real
- bad fit for fast time controls

This model is acceptable for:
- experiments
- L2 deployments
- correspondence / slow games
- small wager environments

### Model B — off-chain play, on-chain settlement with dispute

Players exchange signed moves or a relayer mirrors moves. The contract stores enough state to finalize or, if disputed, replays a transcript or validates a disputed transition.

**Pros**
- much cheaper
- better UX
- easier Lichess/custom-client integration
- mainnet-realistic

**Cons**
- more moving parts
- dispute protocol design matters
- relayer/orchestrator complexity

This is the best practical model if the chain is a settlement layer.

### Model C — signed final result only

Players or an authorized arbiter submit a jointly signed result transcript or final state.

**Pros**
- cheapest normal-path execution
- simplest on-chain runtime

**Cons**
- disputes require a second protocol anyway
- weakest “contract as direct arbiter” story

This works if the product goal is mostly escrow + notarized result, not deep on-chain legality.

## 3. Recommended default

The best default stack is:

- **pure deterministic rules core**
- **compact contract state**
- **L2 deployment**
- **off-chain bridge / relayer**
- **optimistic normal path**
- **on-chain legality verification when challenged or when every move is posted**

## 4. Scope boundaries

### In scope
- orthodox chess
- normal initial position
- legal move validation
- terminal-state detection
- settlement, timeouts, resignations, draw claims
- optional live bridge from Lichess/custom UI

### Optional
- arbitrary FEN initialization
- imported studies
- tournament layer
- observer/event indexers
- typed-signature transcript finalization
- multiple simultaneous matches via a manager contract

### Out of scope
- Chess960
- variants
- engine search
- external engine assistance
- anti-cheat
- real-time blitz clocks with exact wall-clock fidelity on L1

## 5. Contract layering

A clean split is:

### A. Rules core
Pure or mostly pure code:
- board representation
- move validation
- attack detection
- terminal-state detection
- repetition logic
- canonical hashing

### B. Match contract
Stateful wrapper:
- players
- stake
- move deadlines
- move submission
- draw claims
- resign
- timeout claims
- payout

### C. Manager/factory (optional)
Creates matches and indexes them.

### D. Off-chain bridge
- converts UCI ↔ internal move encoding
- mirrors moves from Lichess or custom UI
- exports PGN
- handles retries, confirmations, and rate limits

## 6. ABI suggestions

A compact match interface could look like:

- `create_match(white, black, wager, time_policy, mode)`
- `submit_move(match_id, move, claim_flags)`
- `claim_draw_now(match_id, reason)`
- `claim_timeout(match_id)`
- `resign(match_id)`
- `accept_draw(match_id)`
- `finalize(match_id)` if delayed payout logic exists

Events:
- `MoveAccepted`
- `DrawClaimed`
- `GameEnded`
- `DeadlineExtended`
- `MatchCreated`

## 7. Time-control reality on-chain

A blockchain does not behave like a chess clock.

Practical lessons:
- use **move deadlines** or **correspondence-style windows**
- avoid bullet/blitz semantics on L1
- if mirroring Lichess, prefer slower formats
- specify whether timeout follows FIDE “cannot mate => draw” behavior or a simpler product rule

## 8. Initial-position policy

The safest contract policy is:
- only standard start position on-chain
- arbitrary FEN only in tests or off-chain harnesses

Why:
- arbitrary FEN imports introduce “illegal but FEN-shaped” states
- validating that a position is legally reachable is substantially harder than validating a move from a known-good state
- if every accepted move is validated from the initial position onward, you never need a full “reachability” solver in production

## 9. Architecture summary

The simplest serious design is:

1. start from standard initial position
2. accept compact moves
3. validate one move at a time
4. keep state compact
5. keep history only where rules require it
6. push notation and UX off-chain
7. use chain logic for arbitration, money, and finality
