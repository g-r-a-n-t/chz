# Position Validation Pseudocode

This is language-agnostic pseudocode. Adapt it to your engine architecture.

```text
function validate_position(pos, mode, stage, policy) -> ValidationReport:
    report = ValidationReport(
        ok = true,
        mode = mode,
        stage = stage,
        validity_level = "BASIC_VALID",
        failures = [],
        warnings = [],
        normalized_changes = [],
    )

    # 1. Representation invariants
    run_invariants(report, pos, mode, stage, group="representation")

    # 2. Local legality invariants
    run_invariants(report, pos, mode, stage, group="local_legality")

    # 3. History / transition invariants that can be checked from current state
    run_invariants(report, pos, mode, stage, group="history")

    # 4. Imported-position reachability heuristics
    if mode == IMPORT_STRICT:
        run_invariants(report, pos, mode, stage, group="reachability")

    # 5. Escalate validity level
    if any failure.severity in {"fatal", "strict"}:
        report.ok = false
        report.validity_level = "INVALID"
        return report

    if mode == IMPORT_STRICT:
        if any failure.severity == "heuristic":
            report.validity_level = "HEURISTIC_REACHABILITY_FAIL"
        else:
            report.validity_level = "HEURISTIC_REACHABILITY_PASS"

    return report
```

## Suggested helper split

```text
function validate_transition(before, move, after, mode):
    report = ValidationReport(...)
    report.merge(validate_position(after, mode, "after_make"))
    report.merge(assert_transition_semantics(before, move, after))
    return report
```

```text
function normalize_imported_position(pos, policy):
    if policy.ep == "strict_captureable":
        if pos.ep_square is not None and not has_legal_ep_capture(pos):
            pos.ep_square = None
            report.normalized_changes.push("ep_square_cleared_to_strict_internal_policy")
    return pos
```

## Cheap checks suitable for every make / unmake

- turn valid
- exactly one king each
- no pawns on back rank
- rights and EP field sane
- side not to move not in check
- clocks update correctly
- make/unmake exactness at selected points

## Expensive checks suitable for FULL mode

- board array vs bitboards
- piece lists vs board
- full attack-map recomputation
- hash / material / cache recomputation
- full legal move set recomputation
- replay-from-root state reconstruction
