# Random Walk Validation Pseudocode

```text
function random_walk(seed, plies, full_check_period):
    rng = Random(seed)
    pos = start_position()
    root = clone(pos)

    for ply in 1..plies:
        validate_position(pos, LIGHT, "search_root")

        legal = generate_legal_moves(pos)
        assert legal not empty or terminal_state(pos)

        mv = rng.choice(legal)
        before = clone(pos)

        make_move(pos, mv)
        validate_position(pos, LIGHT, "after_make")

        if ply % full_check_period == 0:
            validate_position(pos, FULL, "periodic_deep_check")
            validate_transition(before, mv, pos, FULL)

        if rng.bernoulli(0.1):
            fen = serialize_fen(pos, policy="spec_fen")
            reparsed = parse_fen(fen)
            assert normalize(reparsed) == normalize(pos)

    while pos.move_stack not empty:
        unmake_move(pos)
        validate_position(pos, LIGHT, "after_unmake")

    assert pos == root
```

## Why this works

Random walks combine three strengths:

- they only visit reachable positions,
- they stress incremental state updates repeatedly,
- they expose long-range drift that small unit tests miss.
