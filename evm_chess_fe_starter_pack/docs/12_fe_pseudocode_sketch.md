# Fe-shaped pseudocode sketch

This file is **illustrative pseudocode**, not guaranteed compile-ready Fe. It is meant to give your coder agent a structure to start from.

## 1. Core data model sketch

```fe
type MatchId = u256
type Move = u32

pub enum Side {
    White,
    Black,
}

pub enum GameStatus {
    Ongoing,
    WhiteWon,
    BlackWon,
    Draw,
}

pub enum EndReason {
    None,
    Checkmate,
    Stalemate,
    Threefold,
    Fivefold,
    FiftyMove,
    SeventyFiveMove,
    DeadPosition,
    Resignation,
    Timeout,
    TimeoutNoMate,
    AgreedDraw,
}

pub enum ValidationError {
    NoPieceAtSource,
    WrongSideToMove,
    FriendlyOccupiedDestination,
    BadGeometry,
    BlockedPath,
    IllegalCastle,
    IllegalEnPassant,
    MissingPromotionChoice,
    LeavesKingInCheck,
    FalseDrawClaim,
    GameEnded,
    NotYourTurn,
    DeadlineNotExpired,
}
```

## 2. Packed match storage sketch

```fe
pub struct MatchStorage {
    pub board_word: u256,
    pub meta_word: u256,
    pub white: Address,
    pub black: Address,
    pub wager: u256,
    pub status: u8,
    pub end_reason: u8,
    pub next_deadline: u64,

    // Optional bounded repetition ring:
    pub rep_head: u16,
    pub rep_len: u16,
    pub repetition_ring: StorageMap<u16, u256>,
}
```

## 3. Contract sketch

```fe
use std::abi::sol

msg ChessMsg {
    #[selector = sol("submitMove(uint256,uint32,uint8)")]
    SubmitMove { match_id: u256, mv: u32, claim_flags: u8 } -> bool,

    #[selector = sol("claimDrawNow(uint256,uint8)")]
    ClaimDrawNow { match_id: u256, reason: u8 } -> bool,

    #[selector = sol("claimTimeout(uint256)")]
    ClaimTimeout { match_id: u256 } -> bool,

    #[selector = sol("resign(uint256)")]
    Resign { match_id: u256 } -> bool,
}

pub struct ManagerStorage {
    pub next_match_id: u256,
    pub matches: StorageMap<u256, MatchStorage>,
}

contract ChessManager {
    store: ManagerStorage,
}
```

## 4. Event sketch

```fe
pub struct MoveAccepted {
    pub match_id: u256,
    pub mv: u32,
    pub board_hash: u256,
    pub meta_word: u256,
}

pub struct GameEnded {
    pub match_id: u256,
    pub status: u8,
    pub reason: u8,
}
```

## 5. Core pure helper signatures

```fe
fn piece_at(board_word: u256, sq: u8) -> u8
fn set_piece(board_word: u256, sq: u8, piece: u8) -> u256
fn clear_piece(board_word: u256, sq: u8) -> u256

fn side_to_move(meta_word: u256) -> bool
fn castling_rights(meta_word: u256) -> u8
fn ep_file(meta_word: u256) -> u8
fn halfmove_clock(meta_word: u256) -> u16
fn white_king_sq(meta_word: u256) -> u8
fn black_king_sq(meta_word: u256) -> u8

fn decode_move(mv: u32) -> (u8, u8, u8)
fn encode_move(from_sq: u8, to_sq: u8, promo: u8) -> u32
```

## 6. Attack and legality helpers

```fe
fn is_square_attacked(board_word: u256, meta_word: u256, sq: u8, by_white: bool) -> bool

fn in_check(board_word: u256, meta_word: u256, white_side: bool) -> bool {
    if white_side {
        return is_square_attacked(board_word, meta_word, white_king_sq(meta_word), false)
    } else {
        return is_square_attacked(board_word, meta_word, black_king_sq(meta_word), true)
    }
}

fn apply_unchecked_move(board_word: u256, meta_word: u256, mv: u32) -> (u256, u256)

fn validate_move(
    board_word: u256,
    meta_word: u256,
    mv: u32
) -> Result<(u256, u256), ValidationError>
```

## 7. Suggested validation structure

```fe
fn validate_move(board_word: u256, meta_word: u256, mv: u32) -> Result<(u256, u256), ValidationError> {
    let (from_sq, to_sq, promo) = decode_move(mv)
    let moving_piece = piece_at(board_word, from_sq)

    // 1. Source/ownership
    // 2. Destination friendly occupancy
    // 3. Geometry / sliding-path checks
    // 4. Special-case castle / ep / promotion checks
    // 5. Apply to scratch state
    let (next_board, next_meta) = apply_unchecked_move(board_word, meta_word, mv)

    // 6. Self-check rejection
    if side_to_move(meta_word) {
        if in_check(next_board, next_meta, true) {
            return Result::Err(ValidationError::LeavesKingInCheck)
        }
    } else {
        if in_check(next_board, next_meta, false) {
            return Result::Err(ValidationError::LeavesKingInCheck)
        }
    }

    return Result::Ok((next_board, next_meta))
}
```

## 8. Submission handler sketch

```fe
pub fn submit_move(self, match_id: u256, mv: u32, claim_flags: u8)
    uses (ctx: Ctx, log: Log, store: mut Storage)
    -> bool
{
    let mut m = self.store.matches.get(match_id)
    assert(m.status == 0, "game ended")

    // Turn authentication
    let caller = ctx.caller()
    if side_to_move(m.meta_word) {
        assert(caller == m.white, "not white")
    } else {
        assert(caller == m.black, "not black")
    }

    // Deadline policy
    assert(ctx.block_timestamp() <= m.next_deadline as u256, "deadline expired")

    let validated = validate_move(m.board_word, m.meta_word, mv)
    match validated {
        Result::Err(_) => {
            revert("illegal move")
        }
        Result::Ok((next_board, next_meta)) => {
            m.board_word = next_board
            m.meta_word = next_meta

            // Update repetition ring / hash
            // Evaluate mate, stalemate, auto draws
            // Evaluate claim flags

            self.store.matches.set(match_id, m)

            let board_hash = canonical_position_hash(next_board, next_meta)
            emit MoveAccepted { match_id: match_id, mv: mv, board_hash: board_hash, meta_word: next_meta }

            return true
        }
    }
}
```

## 9. Canonical repetition hash sketch

```fe
fn canonical_position_hash(board_word: u256, meta_word: u256) -> u256 {
    // Normalize to repetition-relevant state only:
    // - board
    // - side to move
    // - castling rights
    // - legal ep availability only when relevant

    let canonical = pack_canonical_repetition_state(board_word, meta_word)
    return keccak256(canonical)
}
```

## 10. Mate/stalemate probe sketch

```fe
fn classify_after_move(board_word: u256, meta_word: u256) -> (u8, u8) {
    let stm_is_white = side_to_move(meta_word)
    let checked = in_check(board_word, meta_word, stm_is_white)

    if has_any_legal_move(board_word, meta_word, stm_is_white) {
        // Still ongoing unless auto draw triggered
        return (0, 0)
    }

    if checked {
        if stm_is_white {
            return (GAME_STATUS_BLACK_WON, END_REASON_CHECKMATE)
        } else {
            return (GAME_STATUS_WHITE_WON, END_REASON_CHECKMATE)
        }
    } else {
        return (GAME_STATUS_DRAW, END_REASON_STALEMATE)
    }
}
```

## 11. If you support multiple matches

Prefer one of:

### A. Manager + `StorageMap<match_id, MatchStorage>`
Good if Fe ergonomics are acceptable and you want one contract.

### B. Factory deploying one match contract per game
Good if you want hard isolation and simpler per-game storage reasoning.

### C. Thin manager + transcript root + dispute contract
Good for optimistic settlement models.

## 12. Do not bake these mistakes into the first version

- do not make SAN part of the ABI
- do not store raw strings as move history
- do not trust caller-supplied castle/ep flags
- do not couple repetition equality to full FEN text equality
- do not start with arbitrary FEN import in the production contract
