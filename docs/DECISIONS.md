# decisions

This is the running log of chz scope/architecture decisions.

Last updated: 2026-03-31 (America/Denver).

## 2026-03-31 — initial architecture + semantics

1) Deployment model (`OPEN_QUESTIONS #1`): **1.c**
- **Hybrid**: implement “every move on-chain” first, but design ABI/state so an optimistic/dispute model can be added later.

2) Contract shape (`OPEN_QUESTIONS #2`): **2.c**
- Prefer a **split architecture**: a “rules” contract + thin match contract(s).

3) Code size stance (`OPEN_QUESTIONS #3`): **3.a**
- Assume the full validator + settlement *can* fit; optimize/split further only if measurements force it.
- Note: this is compatible with (2.c); the split is primarily for modularity/verification, not just code-size survival.

4) Dead position policy (`OPEN_QUESTIONS #4`): **4.c**
- Target **strict/complete FIDE dead-position** handling (acknowledged hard).
- Practical note: we may need a staged approach (prove exactness for a subset first, then expand), or a dispute/proof path for rare cases if exact on-chain detection becomes infeasible.

5) Timeout semantics (`OPEN_QUESTIONS #5`): **deferred**
- User guidance: “realistically it will be hard to enforce realistic time control, so don't worry about it yet”.
- Action: keep deadline/time-control logic as a *secondary* concern until the validator + settlement core is stable; revisit exact timeout semantics later.

6) Draw claims (`OPEN_QUESTIONS #6`): **6.c (user unsure)**
- Support **both**:
  - claim-now calls (separate tx), and
  - claim-by-move flags inside `submit_move` (single tx).
- Note: if this increases complexity too early, we can temporarily ship v0 with claim-now only and add claim-by-move once repetition/halfmove logic is stable.

7) Repetition storage (`OPEN_QUESTIONS #7`): **chosen**
- Strategy: **bounded scan**.
- Max size: **160** entries.
- Implementation note (v0): uses a simple linear buffer (no wrap) because:
  - history resets on pawn moves and captures, and
  - the 75-move rule ends the game at 150 halfmoves, so the scan stays bounded.
- Reset rule (implemented): pawn move OR capture.

8) Time controls (`OPEN_QUESTIONS #8`): **8.b**
- **No deadlines/timeouts in v0**.
- We can add deadlines later once validator correctness is solid (and after deciding timeout semantics).

9) Move submission (`OPEN_QUESTIONS #9`): **chosen**
- v0: **direct player calls only**.
- Later: add signed-move/relayer flow as part of dispute/UX layers (Model B work).

10) Transparency (`OPEN_QUESTIONS #10`): **chosen**
- Emit **compact move + canonical position hash** per accepted move (logs), not full board/meta.

11) Differential oracle shape (`OPEN_QUESTIONS #11`): **chosen**
- Start with **transcript replay + state agreement** against `python-chess`.
  - Generate legal games off-chain with `python-chess`.
  - Feed the exact move transcript into chz.
  - Compare resulting canonical state/hash and key flags.
- Add **full legal-move enumeration** checks later as part of perft + deeper differential coverage.

12) Benchmark harness (`OPEN_QUESTIONS #12`): **chosen**
- Use a **mix**:
  - `fe build` for bytecode size + artifacts,
  - **hevm** for gas and tracing on compiled bytecode,
  - Foundry as an optional later layer for gas snapshots once the contract surface stabilizes.

13) HEVM proofs (`OPEN_QUESTIONS #13`): **chosen**
- Focus on these properties first:
  - packing invariants (`piece_at/set/clear/move`)
  - self-check rejection (“Ok move ⇒ mover king not attacked”)
  - castling-rights monotonicity (never re-added)
  - EP lifetime (available for at most one ply)
  - repetition canonicalization (legal-EP normalization inputs)
