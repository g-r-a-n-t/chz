# chz

Deterministic chess rules + settlement backend for the EVM written in **Fe**.

This repo intentionally targets an **arbiter/state-machine**, not a chess engine:
- on-chain code validates *one submitted move* and advances state deterministically
- off-chain code handles UX (UCI/FEN/PGN/SAN), streaming, and integrations (ex: Lichess)

Planning date: 2026-03-30.

## Status

This is now in the **core rules implementation** stage (Phases 1–3 mostly complete). Start here:
- `docs/DECISIONS.md`
- `docs/PLAN.md`
- `docs/DESIGN.md`
- `docs/API.md`
- `docs/BENCHMARKS.md`
- `docs/VERIFICATION.md`
- `docs/OPEN_QUESTIONS.md`

Implemented (current):
- packed board/meta helpers + move encoding
- `is_square_attacked` / `in_check`
- `validate_move`: full orthodox legality (castling, en passant, promotion, self-check)
- `terminal.classify_terminal_state`: checkmate / stalemate / dead-position / 75-move draw
- repetition hashing (legal-EP normalization) + threefold/fivefold logic
- `ChzGame` match wrapper:
  - payable constructor escrow (`msg.value == 2*wager`)
  - `submitMove`: turn auth + `validate_move` + terminal classification + settlement
  - `claimDrawNow`: v0 supports threefold + fifty-move
  - `resign`
  - `withdrawTo`
- `ChzRules` stateless rules surface (for hevm / off-chain tooling)
- `ChzProofs` proof helper contract (for hevm symbolic checks)

Not yet implemented:
- agreed draw / timeout semantics (explicitly deferred)

The original research / reference pack is preserved at:
- `evm_chess_fe_starter_pack/`

## Core goals

- **Correct orthodox chess legality** (including castling, en passant, promotion)
- **Deterministic terminal-state detection** (mate/stalemate + draw machinery)
- **Gas-aware on-chain state** (minimize persistent writes; bounded history)
- **Auditable settlement wrapper** (wagers, deadlines, claims, payouts)
- **Strong testing** (fixtures + perft + differential vs `python-chess`)

## Non-goals

- no search/eval/engine logic
- no SAN/PGN generation on-chain
- no string parsing on-chain
- no chess variants (Chess960, crazyhouse, etc.)

## Tooling

### Fe compiler (adjacent repo)

The Fe compiler source is at `../fe`.

Typical dev commands:

```sh
cd ../fe

# Typecheck the chz ingot (once it exists)
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- check ../chz

# Run Fe tests (EVM backend)
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- test ../chz --backend sonatina

# Note: `--backend yul` currently fails to codegen the full validator test module.

# Build EVM artifacts (useful for code-size + gas work)
# Note: due to a Sonatina verifier issue when emitting multiple contracts,
# `make fe-build` builds each contract independently.
cd ../chz
make fe-build

# Run the current regression suite (edge cases + perft + hevm symbolic;
# differential vs python-chess is run if installed).
make verify

# (Alternative) build just the main match contract:
cd ../fe
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- build ../chz --backend sonatina --contract ChzGame
```

### UI demo (terminal)

This repo can run a simple terminal UI that uses `ChzRules` (via hevm) as the move validator/state transition.

```sh
make tui
```

### HEVM (optional; adjacent repo)

HEVM source is at `../hevm`. The verification plan is in `docs/VERIFICATION.md`.

## Design snapshot (current intended direction)

- **Board**: packed 256-bit “nibbleboard” (`4 bits * 64 squares = 256 bits`)
- **Meta**: packed `u256` (side-to-move, castling rights, EP, clocks, cached king squares)
- **Moves**: compact `u32` (`from:6 | to:6 | promo:3`)
- **Repetition**: `keccak256(canonical repetition state)` with legal-EP normalization
- **History**: bounded repetition ring buffer (scan on claim)

## Repo map (intended)

- `src/` — Fe ingot (rules core + contract wrapper)
- `docs/` — plan/spec/bench/verification notes
- `data/` — perft corpus + edge-case fixtures (mirrors starter pack)
- `scripts/` — differential harness + optional Lichess bridge (mirrors starter pack)
- `scripts/hevm_rules.sh` — hevm concrete execution helper for `ChzRules`
- `scripts/hevm_play.sh` — replay a UCI sequence against `ChzRules`
- `scripts/bench_rules.sh` — small gas corpus (capture/ep/castle/promo)
- `scripts/hevm_symbolic.sh` — runs the current hevm symbolic checks
- `scripts/chz_words.py` — compute packed words + move encoding for scripts
- `scripts/run_edge_cases.py` — run `data/edge_cases.json` against `ChzRules` bytecode (via hevm)
- `scripts/perft_hevm.py` — perft regression (slow; intended for small depths)
- `scripts/diff_vs_python_chess.py` — differential vs `python-chess` (move sets + transitions)
- `evm_chess_fe_starter_pack/` — reference material (do not edit lightly)
