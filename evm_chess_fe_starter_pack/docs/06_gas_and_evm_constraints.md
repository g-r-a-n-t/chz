# Gas and EVM constraints

## 1. What the EVM punishes

The EVM punishes:
- persistent storage writes
- cold storage/account access
- oversized runtime code
- oversized initcode
- per-move data structures that grow forever

It generally tolerates:
- arithmetic
- bit twiddling
- bounded loops
- recomputation that avoids extra storage

For chess, that means: **spend computation to save writes**.

## 2. Storage access after EIP-2929 / EIP-2930

Modern EVM execution distinguishes cold vs warm access.

Consequences for chess:
- the first read of a slot in a transaction is materially more expensive than later warm reads
- compacting board state into a few predictable slots is valuable
- access lists can help if your relayer/front-end already knows which slots will be touched

Practical lesson:
- try to keep the hot per-match state in as few slots as possible

## 3. Why packed board state is attractive

Compare the update footprint of one move:

### Multi-bitboard persistence
May touch:
- piece bitboard
- occupancy bitboards
- king square or auxiliary slots
- castling / clocks / ep slot

### Nibbleboard persistence
Usually touches:
- board slot
- meta slot
- maybe one repetition/history slot

That difference is enormous for gas economics.

## 4. Code size limits

The EVM still has a hard runtime code-size limit. Your contract can fail to deploy if runtime code is too large.

Implications:
- giant constant tables are not free
- chess code plus manager plus settlement plus bridge helpers can bloat fast
- be careful about embedding unnecessary lookup tables or giant test fixtures into runtime code

If the rules core grows too large:
- split the system
- keep the match contract thin
- consider a separate manager/factory
- avoid feature creep inside runtime logic

## 5. Initcode limit and constructor discipline

Deployment code also has a hard size ceiling, and initcode is separately metered.

Implications:
- do not dump huge generated tables into constructor-time logic
- do not overuse constructor-side bulk initialization if it bloats initcode
- prefer compact runtime representations and fixed logic

## 6. Storage refunds are not a design crutch

Old “clear later and get refund” strategies are much less attractive now.

For chess:
- do not assume you can cheaply clear large histories at game end
- prefer bounded storage from the start
- prefer overwrite-in-place patterns over ever-growing per-game mappings

## 7. Transient storage

Transient storage is useful only within a single transaction.

That means:
- good for intra-call bookkeeping
- good for reentrancy locks or temporary scratch keyed data
- **not** useful for storing chess state across moves

If Fe and your deployment target expose it cleanly, it can help internal implementation details. It does not solve persistent game history.

## 8. Event logs vs storage

Move transcripts are a perfect example of data that often belongs in events instead of storage.

Store permanently only what future contract logic must read.

Examples:

### Good storage
- current board
- current meta
- player identities
- wager and payout status
- deadlines
- minimal repetition/history state if the contract itself needs it

### Good logs
- move stream
- position hash after move
- UI-facing metadata
- off-chain reconstruction aids

## 9. Repetition economics

Repetition is where gas cost can silently explode.

### Worst approaches
- store the full board every move forever
- use unbounded per-position mappings without lifecycle discipline

### Better approaches
- bounded ring buffer of hashes
- epoch reset for repetition segment
- keep the segment only as large as required by rules

## 10. Hashing choice and code size

### Large Zobrist table
Pros:
- incremental updates

Cons:
- runtime code bulk
- bookkeeping complexity
- collision questions if you truncate

### Keccak of canonical compact state
Pros:
- no giant constant table
- simple and auditable
- collision-resistant
- naturally EVM-native

For a settlement contract, keccak is often the cleaner choice.

## 11. When access lists are worth it

Access lists can help if:
- your relayer knows the match slots in advance
- the transaction is already curated by software
- you are on a chain where this optimization is meaningful operationally

They are not mandatory. They are an optional optimization.

## 12. Bounded loops are okay

Do not overreact to the idea of loops.

On EVM, a bounded loop over:
- 8 directions
- 64 squares
- up to ~150 repetition entries

may be perfectly acceptable compared with extra storage complexity.

The real enemy is usually **persistent writes**, not every bounded scan.

## 13. Gas-first engineering rules for this project

1. Pack board into one slot.
2. Pack metadata into one slot.
3. Cache king squares.
4. Derive special-move flags from state.
5. Keep history bounded.
6. Use logs for transcripts.
7. Keep the on-chain ABI minimal.
8. Prefer L2 for every-move settlement.
9. Avoid giant runtime lookup tables unless they clearly win.
10. Profile before inventing complicated micro-optimizations.

## 14. L1 vs L2 recommendation

### L1
Best for:
- escrow
- notarization
- final settlement
- dispute resolution

Worst for:
- fast per-move live play

### L2
Best for:
- every-move validation
- experimental full on-chain chess
- cheaper state updates
- better UX

If you want to “settle chess on-chain,” the strongest product framing is usually:
- play off-chain or on L2
- settle and dispute on the chain that makes economic sense

## 15. Main gas-sensitive hotspots in a chess backend

- castling-right and ep updates if stored clumsily
- repetition tracking
- move history persistence
- terminal-state detection if you insist on full move generation
- oversized contract logic due to constant tables and variants

## 16. Practical recommendation

Use:
- nibbleboard
- compact meta word
- compact move encoding
- keccak-based canonical repetition hash
- bounded repetition history
- logs for transcript
- L2 or optimistic settlement model

That combination is the most plausible path to something both correct and economically sane.
