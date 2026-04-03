# Chess Engine Validation Mega Reference

This package is a handoff kit for integrating aggressive validation into an orthodox chess engine.

The central design decision is **not** to collapse all position notions into one boolean. A position can be:

- **trusted-generated**: produced from the initial position by your own legal move engine or a fully trusted replay pipeline,
- **basic-valid**: structurally and locally legal under the chosen FEN / EP / castling policy,
- **heuristic-reachability-pass**: basic-valid plus additional retrograde-style sanity checks,
- **invalid**: fails one or more hard invariants.

That split matters because the standards and the literature distinguish full state semantics from mere board geometry, and they also distinguish local validity from genuine reachability from the initial position. See [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023), the [FEN/PGN specification](https://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm), [python-chess docs](https://python-chess.readthedocs.io/en/latest/core.html), [python-chess source](https://github.com/niklasf/python-chess/blob/master/chess/__init__.py), and [Brunner et al. on retrograde complexity](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ISAAC.2020.17).

## Package contents

- `AGENT_BRIEF.md` — direct handoff brief for a coding agent.
- `docs/00_EXECUTIVE_SUMMARY.md` — the short strategic answer.
- `docs/01_RESEARCH_SYNTHESIS.md` — research synthesis across standards, libraries, engines, perft, reachability, and metamorphic testing.
- `docs/02_INVARIANT_LAYERS.md` — the layered model and where each family belongs.
- `docs/03_INTEGRATION_PLAYBOOK.md` — how to wire the checks into import, make/unmake, search, perft, and CI.
- `docs/04_EXTERNAL_POSITION_POLICY.md` — explicit guidance for imported FENs and strictness levels.
- `docs/05_TEST_STRATEGY.md` — perft, random walks, differential testing, metamorphic tests, and endgame oracles.
- `docs/06_BIBLIOGRAPHY.md` — curated source list with why each source matters.
- `machine/invariants_catalog.json` — machine-readable catalog of all invariants.
- `machine/invariants_catalog.csv` — flat spreadsheet-friendly version of the same catalog.
- `machine/checkpoints.json` — validation stages and which invariants belong to each.
- `machine/perft_reference.json` — standard reference positions and counts.
- `machine/test_vectors.json` — synthetic and standard FEN cases with expected outcomes.
- `machine/policies.json` — explicit EP, castling, and validity-level policy choices.
- `machine/status_taxonomy.json` — suggested error categories and API surface.
- `machine/metamorphic_relations.json` — metamorphic and oracle relations for CI / research harnesses.
- `machine/validation_report_schema.json` — a suggested schema for validation reports.
- `examples/` — pseudocode and CI integration notes.

## What is in the invariant catalog

The catalog contains **111 invariants** split across:

- representation: 32
- local legality: 32
- history / transition: 25
- reachability / import heuristics: 10
- metamorphic / oracle: 12

Severity distribution:

- fatal: 52
- strict: 37
- policy: 8
- heuristic: 8
- oracle: 6

## Recommended adoption order

1. Implement the validity levels and choose your EP / castling policy.
2. Add `validate_position(mode, stage)` and `validate_transition(before, move, after)`.
3. Wire **LIGHT** checks to every `after_make` and `after_unmake` in debug builds.
4. Wire **FULL** checks to perft, random walks, and sampled deep-checks.
5. Treat imported FENs separately from engine-generated states.
6. Add differential testing against a trusted reference implementation.
7. Add Syzygy / perft / divide oracles in CI.

## Highest-value takeaway

If your engine only evolves states from the initial position using its own legal move function, then aggressive invariants plus make/unmake exactness plus perft plus differential testing buy you extremely strong practical trust. If you accept arbitrary external FENs as “legal chess positions,” you need a second layer of import policy because **basic-valid** and **reachable** are not the same thing.

Start with `AGENT_BRIEF.md`.
