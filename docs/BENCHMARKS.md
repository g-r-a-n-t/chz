# benchmarks (plan)

chz correctness comes first; benchmarks begin once Phase 3 is stable.

## Current measurements (Sonatina backend)

Measured on 2026-04-01 from a local `fe build` of `ChzGame`:
- initcode size: **27168 bytes**
- runtime code size: **22968 bytes**

Notes
- Runtime size is under the **EIP-170** limit (24576 bytes), but the margin is now smaller (~1.5 KB).

Reproduce:
```sh
cd ../fe
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- build ../chz --backend sonatina --contract ChzGame --out-dir /tmp/chz-sonatina-out

# Bytes = hex_chars/2
python3 - <<'PY'
import pathlib
for name in ["ChzGame.bin", "ChzGame.runtime.bin"]:
    p = pathlib.Path("/tmp/chz-sonatina-out") / name
    hexstr = p.read_text().strip()
    print(name, len(hexstr)//2)
PY
```

## Pure rules gas (ChzRules + hevm)

Baseline (measured 2026-04-01):
- `ChzRules.applyMove` from the initial position with `e2e4`: **39923 gas**

Small corpus (measured 2026-04-01 via `scripts/bench_rules.sh`):

| Scenario | Start | Plies | Total gas |
|---|---|---:|---:|
| capture (`e2e4 d7d5 e4d5`) | standard | 3 | 111632 |
| en passant (`e2e4 a7a6 e4e5 d7d5 e5d6`) | standard | 5 | 184001 |
| castle (white O-O) (`e2e4 e7e5 g1f3 b8c6 f1e2 g8f6 e1g1`) | standard | 7 | 272248 |
| promotion (`a7a8q`) | promo | 1 | 42465 |
| checkmate (Fool’s mate) (`f2f3 e7e5 g2g4 d8h4`) | standard | 4 | 246484 |

Notes:
- This is a concrete `hevm exec` on `ChzRules.runtime.bin` (stateless rules surface).
- It excludes match/escrow storage writes (`ChzGame.submitMove` will be higher).
- Checkmate moves are expensive because terminal classification must exhaustively confirm “no legal replies”.

Reproduce:
```sh
make fe-build
# Standard initial words (portable across sh/bash/zsh):
set -- $(scripts/chz_words.py standard); BOARD=$1; META=$2
MV=$(scripts/chz_words.py uci e2e4)
scripts/hevm_rules.sh apply "$BOARD" "$META" "$MV"

# For multi-ply sequences (updates board/meta between moves):
scripts/hevm_play.sh e2e4 e7e5 g1f3 b8c6

# Run the full small corpus (capture/ep/castle/promo):
scripts/bench_rules.sh
```

## What we measure

### Bytecode size
- runtime code size (EIP-170 limit pressure)
- initcode size (EIP-3860 pressure)

### Gas per move class
Measure `submit_move` across:
- quiet move (non-capture, non-pawn)
- pawn move (halfmove reset)
- capture (halfmove reset)
- en passant (special capture)
- castling (attack checks on king path + rook move)
- promotion (each promo kind)
- moves that trigger terminal probing (mate/stalemate detection paths)
- repetition update + claim scan worst-case

### Storage footprint
- slots touched per move
- whether repetition ring uses bounded slots and overwrites cleanly

## Suggested benchmark corpus

Start with small, high-signal positions:
- initial position (baseline)
- Kiwipete (castling + tactical stress)
- curated edge cases from `data/edge_cases.json`

Then add worst-case style positions:
- dense piece boards that maximize ray scans
- positions where `has_any_legal_move` must scan many candidates before finding a legal reply

## Tooling options

### Option A: Fe test runner gas reporting
If Fe exposes per-test gas in the runner, prefer it for quick iteration.

### Option B: hevm execution
Compile bytecode, then run selected calls via hevm to gather gas and traces.

### Option C: Foundry integration
Use Foundry gas snapshots once build artifacts exist.

## “Attractive” benchmark output

Deliver `docs/BENCHMARKS.md` updates as tables:
- scenario
- gas used
- slots written
- notes on why it’s expensive
- link to the position fixture + move sequence

## Early warning checks

Run these as soon as the core validator exists:
- does the combined contract exceed code size?
- does `is_square_attacked` dominate runtime?
- is repetition storage doing >1 SSTORE per move?
