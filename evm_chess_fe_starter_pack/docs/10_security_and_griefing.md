# Security and griefing

A chess contract is adversarial software, not just a rules engine.

## 1. Threat model

Adversaries may try to:
- submit moves out of turn
- replay old signed moves
- force state desync through bad encoding
- grief by never moving
- spam false draw claims
- exploit payout logic
- exploit bridge trust assumptions
- exploit code-size / gas limits indirectly by pushing worst-case paths

## 2. Authorization

Every move submission must be bound to the correct side.

Depending on architecture:
- direct caller check (`msg.sender == side_to_move_player`)
- signed move with relayer
- hybrid

Never allow “anyone can submit a move” unless the move is cryptographically bound to the correct player and correct turn.

## 3. Replay protection

If using signatures or relayers, bind signed data to:
- chain ID
- contract address
- match ID
- ply number / nonce
- move payload
- claim flags
- deadline if relevant

Otherwise, valid old signatures may be reusable in the wrong context.

## 4. Turn griefing

A player can always grief by not moving unless the protocol has deadlines.

Recommended policy:
- per-move deadline or correspondence window
- `claim_timeout` after expiry
- explicit result semantics if the opponent cannot mate

## 5. False claims

False claims should revert:
- false threefold
- false fifty-move
- premature timeout
- duplicate payout
- draw claim after game already ended

A state machine should never silently mutate on a false claim.

## 6. Front-running and public mempools

Chess is turn-based, so generic mempool front-running is less dangerous than in DeFi, but there are still concerns:
- if move submission is not tied to the correct player, a third party might race the move in
- if a relayer is used, stale state / wrong-ply races can happen
- if your product supports premoves or hidden moves, public mempools are a poor fit

Defenses:
- bind move to side and ply
- reject stale moves
- keep move ABI minimal and deterministic

## 7. Payout safety

If money moves, use standard contract hygiene:
- checks-effects-interactions discipline
- consider pull-based withdrawals if that fits the UX
- mark game ended before external transfers
- prevent double settlement

## 8. Storage griefing

If your architecture allows unbounded match creation or unbounded history growth, someone can turn your system into a storage sink.

Mitigations:
- bounded per-match history
- per-match creation fees if appropriate
- archival via logs rather than unbounded storage
- manager contracts that keep only essential indexes

## 9. Hash collisions

If you use truncated position hashes for repetition:
- understand the collision risk
- decide whether the risk is acceptable given the stakes

If money is involved and you want the cleanest story, prefer a cryptographic hash of canonical state instead of a short ad-hoc hash.

## 10. Bridge trust minimization

The bridge should not be a trusted legality oracle.

Ideal property:
- a malicious or buggy bridge can fail to submit, delay, or spam invalid transitions
- but it cannot force the contract into an illegal chess state

This means the contract itself must validate moves.

## 11. Timestamp manipulation

`block.timestamp` is usable for coarse deadlines, not precise chess clocks.

Design accordingly:
- generous time windows
- no sub-second assumptions
- avoid “blitz parity with Lichess” promises on L1

## 12. Upgrade and governance risk

If you use upgradeability:
- you are adding a second trust model on top of chess correctness
- document who can change rules
- isolate escrow balances carefully

If you can keep the core immutable and move only orchestration around it, that is cleaner.

## 13. Illegal state injection

If the protocol allows:
- arbitrary FEN starts
- externally supplied challenge states
- transcript checkpoints

then validate those aggressively. Otherwise the attacker will try to smuggle in a state your move validator never expected.

## 14. Reentrancy and callbacks

A plain chess contract often does not need external calls during move validation. Keep it that way.

If external calls exist:
- do them after state is finalized
- separate settlement from validation where possible

## 15. Operational security for the bridge

Off-chain concerns matter too:
- rotate tokens if leaked
- store API credentials securely
- treat chain and Lichess rate limits as first-class operational constraints
- monitor for desync
- wait reasonable confirmations if reorg sensitivity matters

## 16. Security summary

The safest shape is:
- deterministic validator
- minimal persistent state
- strong turn/nonce binding
- deadlines
- revert on false claims
- payout discipline
- bridge as convenience, not authority
