# Fe compiler feedback (from `chz`)

This doc captures concrete compiler/backend issues and ergonomics notes encountered while building `chz` (a chess rules + settlement backend) in Fe.

Last updated: 2026-04-01 (America/Denver).

## Environment / repro notes

- `chz` lives at `../chz` relative to the compiler repo `../fe`.
- Most commands set `CARGO_TARGET_DIR=/tmp/chz-fe-target` to avoid writing into `../fe/target`.

## Backend issues encountered

### 1) Yul backend: “assignment to immutable local”

Command:
```sh
cd ../fe
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- test ../chz --backend yul
```

Observed:
```
Failed to emit test Yul: assignment to immutable local
ERROR [165.31s] Failed to emit test Yul: assignment to immutable local
```

Notes:
- `--backend sonatina` can compile and run the same test suite successfully.
- This error currently blocks using the Yul backend for `chz` test codegen.

What would help:
- The error should ideally point to a source span (file/line) or at least the function name being emitted.
- A minimal-repro output mode would be useful (dump Yul around the failing construct, or a MIR snippet).

### 2) Sonatina backend panic on terminal move-probing loop

Context:
- Implementing checkmate/stalemate requires a “does side-to-move have *any* legal move?” probe.
- A first-pass implementation enumerated pseudo-legal targets and called `validate_move` until it found one legal move.
- That implementation is preserved at `docs/archive/terminal_attempt_20260331.fe`.

Repro (conceptual):
- Replace `src/chess/terminal.fe` with `docs/archive/terminal_attempt_20260331.fe` (or copy its contents), then run:

```sh
cd ../chz
make fe-test
```

Observed panic:
```
thread '<unnamed>' (...) panicked at .../sonatina.../crates/ir/src/dfg.rs:543:13:
cannot delete inst InstId(221) with live result users
...
Sonatina backend panicked while emitting test module: cannot delete inst InstId(221) with live result users
```

Notes:
- The panic happens during codegen, not at runtime.
- It appears correlated with loops + early returns + calling `validate_move` (which returns a `Result`) in the inner path.

What would help:
- A compiler-side “disable DCE / simplify passes” flag to bisect which optimization triggers `dfg.rs` deletion of live instructions.
- A smaller exported reproducer from Fe (dump Sonatina IR before/after the failing pass).

### 3) Sonatina backend verifier failure when emitting multiple contracts

Command:
```sh
cd ../fe
CARGO_TARGET_DIR=/tmp/chz-fe-target cargo run -q -p fe -- build ../chz --backend sonatina
```

Observed (when building all contracts in one run):
```
Error: Failed to compile Sonatina bytecode: internal error: VerifierFailed ...
CallArgTypeMismatch ... (%__ChzRules_recv_0_0) ... expected I256, found I32
```

Notes:
- Building individual contracts succeeds:
  - `--contract ChzGame`
  - `--contract PlayerProxy`
  - `--contract ChzRules`
- This blocks a simple “build all artifacts” workflow on Sonatina for multi-contract ingots.

Workaround used in `chz`:
- `Makefile` `fe-build` builds each contract independently via `--contract ...`.

## Language / stdlib ergonomics notes

These are not necessarily bugs, but things that were friction points for writing a rules-heavy validator.

### Project config ergonomics

- It would be useful if `fe.toml` could specify defaults like:
  - backend (`sonatina` vs `yul`)
  - output directory (for build artifacts)
  - optimizer level / size presets
- Rationale: `chz` currently uses Makefile/scripts to force `--backend sonatina` consistently.

### Better EVM primitives (stdlib)

For a settlement wrapper, it would be useful to have:
- A first-class, well-documented “send/transfer/call with value” helper (with clear revert/return semantics).
- Safer typed wrappers around logs/events (or at least stable patterns for emitting compact hashes).

### Control-flow / iteration ergonomics

- Terminal classification and perft-style code benefits from compact iteration constructs.
  - `while` works, but lack of `break`/`continue` (if currently absent) forces awkward loop exits and can bloat control-flow.

### Diagnostics / spans

- Backend failures should surface source spans whenever possible (file + line + function).
- Even when the failure is in a backend (Yul/Sonatina), reporting the Fe function being emitted helps dramatically.

## Workarounds used in `chz`

- Target `--backend sonatina` for now; document Yul backend limitations in `README.md`.
- For terminal probing, avoid early-return-heavy scans; `has_any_legal_move` is implemented using a `found: bool` scan pattern that compiles on Sonatina.
- Keep the panic-triggering formulation archived at `docs/archive/terminal_attempt_20260331.fe` for upstream repro.
