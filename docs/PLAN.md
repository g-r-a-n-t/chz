# chz plan

This is the execution plan for implementing an **EVM chess backend in Fe**.

The high-signal reference pack is in `evm_chess_fe_starter_pack/`. This plan intentionally mirrors its roadmap, but pins *chz-specific* decisions and deliverables.

## Guiding principles

- Contract is a **deterministic arbiter**, not an engine.
- **Storage writes are the enemy**; spend computation to save writes.
- Treat **testing as the project** (perft + differential testing).
- Keep the **rules core as pure as possible**, then wrap settlement around it.

## Phase 0 — settle scope + model (decision gate)

We must pick a “deployment model” early because it changes the contract surface:

- **Model A**: every move posted on-chain and validated (simplest trust model; expensive)
- **Model B**: off-chain play, on-chain settlement with dispute (best UX/cost; more protocol design)

Current default for chz:
- implement **Model A first** (because the dispute path still needs the same validator)
- design the state / ABI so **Model B can be added later** without rewriting the core rules

Deliverables
- `docs/DESIGN.md` locked enough to start coding
- `docs/API.md` with a narrow, stable ABI
- explicit notes on what’s postponed to “Model B”

Exit criteria
- agreement on: start position only vs FEN import, timeout semantics, dead-position policy

## Phase 1 — packed state + helpers (pure core)

Deliverables
- square indexing helpers (`a1=0 .. h8=63`)
- packed nibbleboard helpers (`piece_at`, `set_piece`, `clear_piece`, `move_piece`)
- packed meta helpers (side, castling, EP, clocks, king squares)
- move encode/decode (`from`, `to`, `promo`)

Exit criteria
- helper invariants unit tests pass (round-trips, masks, king-cache consistency)

## Phase 2 — attack detection

Deliverables
- `is_square_attacked(board, meta, sq, by_white)`
- `in_check(board, meta, side)`

Exit criteria
- pinned-attacker semantics correct
- castling-path attack checks (king path only) validated via fixtures

## Phase 3 — move legality + transition (validator)

Deliverables
- piece geometry checks + ray blocking
- castling legality + rook movement
- en passant legality (including discovered-check trap)
- promotion (explicit choice required)
- “make move then test” self-check rejection
- metadata updates (rights, EP, clocks, king squares)

Exit criteria
- `data/edge_cases.json` passes (run: `make fe-build && scripts/run_edge_cases.py`; mirrors starter pack corpus)
- curated legal/illegal fixtures for each rule bucket

## Phase 4 — terminal state classification

Deliverables
- `has_any_legal_move(side)` (boolean probe, not full list)
- checkmate / stalemate classification
- halfmove clock enforcement (50/75 move thresholds)
- claimable vs automatic draw semantics
- repetition identity normalization + ring-buffer tracking
- dead-position detection (target: strict/complete; likely staged)

Exit criteria
- terminal fixtures pass (mate/stalemate, repetition claims, 50/75 move, dead positions)

Update (2026-03-31)
- `src/chess/terminal.fe` now implements:
  - checkmate / stalemate probing (`has_any_legal_move`)
  - dead-position detection (insufficient material subset)
  - 75-move automatic draw
- `ChzGame` now implements:
  - repetition hashing (legal-EP normalization) + threefold/fivefold handling
  - fifty-move claim (claim-now + claim-by-move)
- Sonatina still panics on the naive early-return move-probing formulation; the failing attempt is preserved at `docs/archive/terminal_attempt_20260331.fe`.
- Workaround used: avoid early returns inside the move-probing scan (track `found: bool` and exit loops via the condition).

## Phase 5 — contract wrapper (“match”)

Deliverables
- match storage struct (board/meta + players + wager + deadlines + status)
- `submit_move` with strict turn auth and deadline checks
- `claim_draw_now`, `resign`, payout discipline
- `claim_timeout` + strict timeout semantics are **deprioritized** until later (see `docs/DECISIONS.md`)

Decision update (2026-03-31)
- v0 has **no deadlines/timeouts**; deadline handling is deferred (see `docs/DECISIONS.md`).
- events designed for off-chain reconciliation (position hash after every accepted move)

Exit criteria
- contract-layer integration tests pass (auth, revert paths, single-settlement safety)

## Phase 6 — differential + perft validation

Deliverables
- differential harness:
  - replays random legal games from `python-chess`
  - checks legal-move set equality and per-move state transitions via `ChzRules` bytecode
  - script: `scripts/diff_vs_python_chess.py` (requires `python-chess`)
- perft driver (regression; small depths only due to cost of `hevm exec`)
  - script: `scripts/perft_hevm.py`

Exit criteria
- perft matches canonical counts to the chosen depth targets
- long random playouts show no state desync

## Phase 7 — benchmarks + hardening

Deliverables
- gas/codesize measurements for:
  - quiet move
  - capture
  - en passant
  - castling
  - promotion
  - checkmate/stalemate probes
  - repetition update + claim scan worst-case
- documented hotspots + refactors (only after correctness is stable)

Exit criteria
- benchmark report in `docs/BENCHMARKS.md`
- clear statement: “L2 required” vs “L1 acceptable” for the selected model

## Phase 8 — optional HEVM formalization

Deliverables
- focused hevm proofs on *bounded, high-value invariants* (not “prove all of chess”)
- evidence that proofs track the deployed bytecode, not just a model

Exit criteria
- a small set of meaningful properties proved and checked in CI (or documented as manual)
