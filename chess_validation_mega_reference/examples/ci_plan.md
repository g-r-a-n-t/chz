# CI Plan

## Fast PR lane

- unit tests for primitive rules
- start-position perft through depth 5
- one special perft position with castling / EP stress
- make/unmake random walk smoke test
- root search non-mutation test
- small differential batch

## Nightly lane

- wider perft corpus
- divide on any failing perft branch
- long random walks with FULL sampling
- larger differential batch
- import fuzzing
- Syzygy oracle checks if tablebases are available

## Triage rule

When a failure occurs:

1. save FEN and move history
2. run FULL validation
3. if movegen-related, run divide / perft
4. if import-related, compare IMPORT_BASIC vs IMPORT_STRICT outputs
5. if search-related, replay PV and assert root non-mutation
