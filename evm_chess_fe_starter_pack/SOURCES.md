# Sources

Research snapshot date: 2026-03-30.

This pack was assembled from primary or near-primary sources where possible.

## Chess rules and semantics

- FIDE Laws of Chess (effective 1 Jan 2023)  
  https://handbook.fide.com/chapter/e012023

## Chess programming references

- Chessprogramming Wiki — Legal Move  
  https://www.chessprogramming.org/Legal_Move

- Chessprogramming Wiki — Checks and Pinned Pieces (Bitboards)  
  https://www.chessprogramming.org/Checks_and_Pinned_Pieces_(Bitboards)

- Chessprogramming Wiki — Bitboards  
  https://www.chessprogramming.org/Bitboards

- Chessprogramming Wiki — Magic Bitboards  
  https://www.chessprogramming.org/Magic_Bitboards

- Chessprogramming Wiki — Repetitions  
  https://www.chessprogramming.org/Repetitions

- Chessprogramming Wiki — En passant  
  https://www.chessprogramming.org/En_passant

- Chessprogramming Wiki — Zobrist Hashing  
  https://www.chessprogramming.org/Zobrist_Hashing

- Chessprogramming Wiki — Perft Results  
  https://www.chessprogramming.org/Perft_Results

## Python oracle and test tooling

- python-chess docs  
  https://python-chess.readthedocs.io/en/latest/

- python-chess core docs  
  https://python-chess.readthedocs.io/en/latest/core.html

- python-chess module source docs  
  https://python-chess.readthedocs.io/en/latest/_modules/chess.html

## Fe language

- Fe homepage  
  https://fe-lang.org/

- What is Fe?  
  https://fe-lang.org/getting-started/what-is-fe/

- Key Concepts  
  https://fe-lang.org/getting-started/key-concepts/

- Operators & Expressions  
  https://fe-lang.org/foundations/operators/

- Built-in Types Reference  
  https://fe-lang.org/appendix/types/

- Intrinsics Reference  
  https://fe-lang.org/appendix/intrinsics/

- Maps  
  https://fe-lang.org/compound-types/maps/

- Storage Fields  
  https://fe-lang.org/contracts/storage/

- Selector Calculation  
  https://fe-lang.org/appendix/selectors/

- Fe GitHub repository  
  https://github.com/argotorg/fe

## Lichess integration

- Lichess API Tips  
  https://lichess.org/page/api-tips

- Lichess Usage of eBoards / official Board API guidance  
  https://lichess.org/page/eboards

- Lichess API docs  
  https://lichess.org/api

- berserk usage docs  
  https://lichess-org.github.io/berserk/usage.html

## EVM / gas / protocol constraints

- EIP-170: Contract code size limit  
  https://eips.ethereum.org/EIPS/eip-170

- EIP-2200: Structured definitions for net gas metering of SSTORE  
  https://eips.ethereum.org/EIPS/eip-2200

- EIP-2929: Gas cost increases for state access opcodes  
  https://eips.ethereum.org/EIPS/eip-2929

- EIP-2930: Optional access lists  
  https://eips.ethereum.org/EIPS/eip-2930

- EIP-3529: Reduction in refunds  
  https://eips.ethereum.org/EIPS/eip-3529

- EIP-3860: Limit and meter initcode  
  https://eips.ethereum.org/EIPS/eip-3860

- EIP-1153: Transient storage opcodes  
  https://eips.ethereum.org/EIPS/eip-1153

## Notes on source use

- FIDE is the authoritative rules reference.
- Chessprogramming Wiki is the most useful implementation-oriented reference for move legality and representation tradeoffs.
- python-chess is an excellent differential-testing oracle, but certain helpers (especially “insufficient material”) should not be mistaken for a complete dead-position oracle.
- Fe is still evolving, so source pages should be re-checked before committing to production syntax.
