# open questions / decision gates

These are the questions that will realistically affect scope, ABI stability, and engineering effort.

## Architecture

1. **Deployment model**: fully on-chain moves (A) vs optimistic/dispute (B)? *(answered: 1.c; see `docs/DECISIONS.md`)*
2. **Contract shape**: manager-with-map vs one-contract-per-match vs “rules contract + thin match”? *(answered: 2.c; see `docs/DECISIONS.md`)*
3. **Code size risk**: do we expect the full validator + settlement to fit under EIP-170? *(answered: 3.a; see `docs/DECISIONS.md`)*

## Rules and semantics

4. **Dead position**: trivial safe classes only (v0) vs attempt broader exactness? *(answered: 4.c; see `docs/DECISIONS.md`)*
5. **Timeout semantics**: FIDE “timeout win unless opponent cannot mate” vs product rule? *(deferred; see `docs/DECISIONS.md`)*
6. **Draw claims**: do we support “claim by intended move” in v0, or claim-now only? *(answered: 6.c; user unsure; see `docs/DECISIONS.md`)*
7. **Repetition storage**: ring buffer size and reset rules (what counts as repetition-irreversible)? *(answered; see `docs/DECISIONS.md`)*

## Product / UX

8. **Time controls**: correspondence-style only (recommended) vs trying to mirror Lichess clocks? *(answered: 8.b; see `docs/DECISIONS.md`)*
9. **Move submission**: direct player calls only vs signed moves via relayer? *(answered; see `docs/DECISIONS.md`)*
10. **Transparency**: store full move transcript in logs vs only hashes? *(answered; see `docs/DECISIONS.md`)*

## Tooling

11. **Differential oracle shape**: do we require full legal-move enumeration (hard) or only state agreement on legal transcripts (easier)? *(answered; see `docs/DECISIONS.md`)*
12. **Benchmark harness**: Fe test runner gas, hevm, Foundry, or a mix? *(answered; see `docs/DECISIONS.md`)*
13. **HEVM proofs**: which 3–5 properties are worth the effort? *(answered; see `docs/DECISIONS.md`)*
