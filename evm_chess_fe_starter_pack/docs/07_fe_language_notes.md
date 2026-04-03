# Fe language notes

## 1. Project maturity

Treat Fe as promising but still evolving.

That means:
- isolate your rules core behind a stable internal interface
- expect syntax and ergonomics to keep moving
- avoid overfitting the design to any one temporary compiler quirk

If you make the chess core mostly pure and compact, porting and refactoring remain manageable.

## 2. Features that are useful for this project

Fe currently gives you a number of useful building blocks:

- static typing
- Rust-like syntax
- explicit effects via `uses`
- message-based contract interface
- structs, enums, tuples, fixed arrays
- `StorageMap`
- pattern matching
- `Option` / `Result`
- cryptographic intrinsics such as `keccak256`
- context intrinsics such as caller and block timestamp
- built-in testing support

These are enough to sketch a clean chess arbiter architecture.

## 3. Why explicit effects are nice here

Chess settlement logic naturally crosses concerns:
- caller authentication
- timestamp/deadline checks
- storage mutation
- event emission

Fe’s explicit effect model helps keep those dependencies visible.

That is especially useful when separating:
- pure chess-state transitions
- contract-side authorization and settlement concerns

## 4. Suggested module split

Recommended project layout:

- `core/types.fe`
- `core/encoding.fe`
- `core/board.fe`
- `core/attacks.fe`
- `core/rules.fe`
- `core/termination.fe`
- `contract/match.fe`
- `contract/manager.fe` (optional)
- `tests/...`

Keep the `core/*` modules as pure or nearly pure as possible.

## 5. Storage design in Fe

A practical Fe design is:

- one storage struct for match state
- a thin contract wrapper
- helper methods on storage structs or plain helper modules

If using many matches:
- manager contract with `StorageMap<MatchId, MatchStorage>`
- or a factory pattern with one contract per match

## 6. Fixed arrays and enums

Useful applications:

### Fixed arrays
- direction tables for attack generation
- small constant offset sets for king/knight moves
- compact helper buffers

### Enums
- game status
- termination reason
- claim flags / draw reasons
- validation errors

This is a better fit than magic numeric constants scattered across the code.

## 7. Runtime hashing

Fe exposes a `keccak256` intrinsic. That is valuable for:
- canonical repetition hashes
- transcript commitments
- signed-state or proof helpers
- domain-separated challenge data

It lets you avoid dragging a giant Zobrist table into runtime code unless you really want one.

## 8. Context and timing

Fe exposes context intrinsics such as caller and block timestamp.

Use them for:
- turn ownership
- timeout claims
- move deadlines
- chain/domain separation where needed

But remember:
- block timestamp is not a perfect chess clock
- use generous, coarse-grained time policies

## 9. Testing

Fe has built-in unit and integration testing support. That is important because a chess backend is fundamentally a testing project.

Use Fe tests for:
- packing/unpacking
- attack detection
- move legality spot tests
- terminal-state spot tests
- contract wrapper behavior
- revert paths for illegal moves and false claims

Then use off-chain differential tests against python-chess for wider coverage.

## 10. Compiler/backend caution

Because Fe is still evolving:
- do not start with clever low-level tricks
- first get a simple, correct reference implementation in Fe
- then profile and optimize
- only after that consider more exotic packing or transient-storage tricks

## 11. Suggested public API style

Keep the public contract API narrow and stable:

- `create_match`
- `submit_move`
- `claim_draw_now`
- `claim_timeout`
- `resign`

Then keep detailed helper logic private.

This minimizes ABI churn while Fe evolves.

## 12. Error modeling

Define explicit internal error categories:

- `NoPieceAtSource`
- `WrongSideToMove`
- `FriendlyOccupiedDestination`
- `BadGeometry`
- `BlockedPath`
- `IllegalCastle`
- `IllegalEnPassant`
- `MissingPromotionChoice`
- `LeavesKingInCheck`
- `FalseDrawClaim`
- `GameAlreadyEnded`
- `DeadlineNotExpired`
- `NotYourTurn`

Even if Fe syntax changes, keeping this conceptual error taxonomy helps auditability.

## 13. Recommended development style in Fe

1. implement the simplest correct version
2. keep helpers small
3. make board/meta packing explicit
4. comment every bit layout
5. use property-like tests for helper invariants
6. mirror all complex cases in off-chain test harnesses

## 14. Bottom line

Fe is viable for this project as a serious experiment, but the safest strategy is:

- pure chess core
- thin contract shell
- heavy test coverage
- minimal ABI
- avoid premature low-level cleverness
