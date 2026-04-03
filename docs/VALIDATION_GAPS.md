# validation gaps (tooling-limited)

This doc tracks validation we *want* but can’t practically run yet, mostly due to missing tooling or environment constraints.

## Gaps

- **Strict FIDE dead-position** (beyond insufficient material): needs tablebases/exhaustive search for bounded endgames, or a claim/dispute mechanism (witness line / refutation) for larger positions.
- **Transaction-level E2E** (RPC + revert semantics + events): current tests use hevm `exec` and Fe unit tests; full flows would benefit from a local node (ex: Anvil) + integration tests.
- **Browser UI E2E**: requires running a local HTTP server + optional wallet/RPC; the current sandbox blocks socket creation, so this can’t be exercised here.
- **Act specs/proofs**: `../act` exists but is not wired into this repo’s CI/dev loop; would require building/installing Act tooling and writing formal specs for `ChzRules`.
- **Deeper perft**: hevm-driven perft is too slow for high depths; would need a faster native runner (or alternative execution harness) to push to the canonical perft depths broadly.
- **Syzygy regression**: tablebase files are large and not vendored; wiring Syzygy-based spot checks would require adding/pointing to a tablebase directory.

