# Differential Harness Pseudocode

The best targets are reachable positions, not arbitrary imported FENs.

```text
function differential_test(seed, steps, reference):
    rng = Random(seed)
    pos = start_position()

    for i in 1..steps:
        legal_moves_engine = sorted(generate_legal_moves(pos))
        legal_moves_ref = sorted(reference.generate_legal_moves(pos.to_fen(policy="spec_fen")))

        assert legal_moves_engine == legal_moves_ref

        assert in_check(pos) == reference.in_check(...)
        assert is_checkmate(pos) == reference.is_checkmate(...)
        assert is_stalemate(pos) == reference.is_stalemate(...)

        mv = rng.choice(legal_moves_engine)
        before = clone(pos)
        make_move(pos, mv)

        validate_position(pos, FULL, "after_make")
        validate_transition(before, mv, pos, FULL)

    while pos.move_stack not empty:
        before = clone(pos)
        unmake_move(pos)
        validate_position(pos, FULL, "after_unmake")
```

## Notes

- Prefer positions reached from the standard initial position.
- Keep policy consistent across both implementations.
- Compare sorted move lists, not iteration order.
- Save failing FENs and seeds immediately.
- Re-run failures with FULL validation and divide/perft where relevant.
