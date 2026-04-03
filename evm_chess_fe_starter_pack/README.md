# EVM Chess + Fe starter pack

Prepared on 2026-03-30.

This pack is aimed at a coder agent building a **deterministic chess arbiter** for the EVM in **Fe**. The intended mindset is:

- the **contract is not a chess engine**
- the **contract is a settlement / arbitration state machine**
- off-chain components can do UX, streaming, PGN/SAN, and API bridging
- on-chain code should only do the minimum required for correctness, settlement, and dispute resolution

## What this pack emphasizes

1. **Orthodox chess rules coverage**
   - move legality
   - check / checkmate / stalemate
   - castling, en passant, promotion
   - threefold / fivefold repetition
   - fifty-move / seventy-five-move rules
   - dead-position nuance
   - illegal move and illegal position handling

2. **Gas-oriented design**
   - storage packing
   - move encoding
   - repetition tracking tradeoffs
   - code-size pressure
   - when to prefer L2 or optimistic settlement over per-move mainnet validation

3. **Fe-specific implementation notes**
   - current language ergonomics
   - storage and testing patterns
   - why the core rules engine should remain as pure and isolated as possible

4. **Lichess integration**
   - official API usage only
   - bridge architecture
   - bot/board streaming patterns
   - rate-limit considerations
   - how to keep Lichess as UX while the chain remains the settlement layer

## Recommended default architecture

If your end goal is a serious deployable product, the best default is:

- **off-chain move stream**
- **on-chain escrow + deterministic validator + dispute path**
- **Lichess or a custom client as UX**
- **L2 before mainnet**
- **compact on-chain state, compact move encoding**
- **PGN/SAN generation off-chain**

If you insist on validating every move fully on-chain, do it on an L2 first and treat mainnet as the final settlement / dispute domain.

## File map

- `AGENT_BRIEF.md` — the quickest high-signal overview for a coder agent
- `docs/01_architecture_and_scope.md` — system shape and deployment models
- `docs/02_rules_matrix.md` — complete rule coverage and implementation traps
- `docs/03_state_model_and_move_encoding.md` — packed state design and encodings
- `docs/04_move_validation_pipeline.md` — legality pipeline and algorithms
- `docs/05_draws_repetition_and_dead_positions.md` — repetition, fifty/75-move, dead positions
- `docs/06_gas_and_evm_constraints.md` — EVM cost model and code-size constraints
- `docs/07_fe_language_notes.md` — practical Fe notes
- `docs/08_lichess_bridge.md` — bridge architecture and operational cautions
- `docs/09_testing_oracles_and_perft.md` — perft, differential testing, fuzzing
- `docs/10_security_and_griefing.md` — adversarial considerations
- `docs/11_notation_and_io.md` — UCI/FEN/PGN boundaries
- `docs/12_fe_pseudocode_sketch.md` — Fe-shaped pseudocode skeleton
- `docs/13_roadmap.md` — pragmatic build order
- `data/perft_positions.json` — standard perft corpus
- `data/edge_cases.json` — hand-picked rule traps
- `scripts/differential_test_harness.py` — python-chess comparison harness template
- `scripts/lichess_bridge_skeleton.py` — bridge template
- `SOURCES.md` — bibliography

## Strong recommendations

- Use **compact binary move encoding on-chain**, not strings.
- Use **UCI at the bridge boundary** and convert immediately.
- Treat **SAN and PGN as off-chain presentation / archival concerns**.
- Keep **repetition equality** separate from FEN equality.
- Be very careful with **en passant** in repetition hashing.
- Cache **king squares** explicitly.
- Derive special move meaning from state; **do not trust caller-supplied move flags**.
- Prefer **apply-move + king-safety test** over “pure legal move generation” when validating one submitted move.
- For **mate/stalemate**, only generate enough replies to find one legal move.
- Keep the contract ABI small and deterministic.

## Scope assumptions

This pack assumes **standard orthodox chess from the normal initial position** unless a section explicitly discusses arbitrary FEN import. Variants such as Chess960, crazyhouse, atomic, antichess, or custom board sizes are out of scope.

## Quick implementation order

1. Board encoding + square helpers
2. `piece_at`, `set_piece`, `move_piece`, `remove_piece`
3. `is_square_attacked`
4. `in_check`
5. `apply_unchecked_move`
6. `validate_move`
7. terminal-state detection
8. repetition / draw logic
9. contract wrapper
10. bridge and settlement logic
