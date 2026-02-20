# RTS BLOCK CUT PROTOCOL
(Execution Promotion System)

## PURPOSE
Convert a BLOCK draft into an executable numbered BLOCK.

RTS never executes automatically.
Human operator approves promotion.

## INPUT
Required:

logs/BLOCK_DRAFT_NEXT.md

Optional:

logs/EXECUTION_LOG.md
logs/RESULT_LOG.md
evolution/ACTIVE_PROPOSALS.md

## CUT COMMAND

Operator writes:

CUT

or

"CUT NEXT BLOCK"

## ACTION

RTS must:

1) Generate new BLOCK number.

Format:

BLOCK_000000XX.md

Increment from latest BLOCK number.

2) Copy contents from:

logs/BLOCK_DRAFT_NEXT.md

3) Save into:

logs/BLOCK_000000XX.md

4) Append record:

logs/EXECUTION_LOG.md

Example:

CUT executed.
BLOCK created: BLOCK_00000015.md

## SAFETY

If STATE == OVERLOAD:

Recommend pause confirmation.

Operator retains final authority.

## PROMPT OUTPUT

"BLOCK promoted.

Execute now?

YES / LATER / CANCEL"

Operator decides execution.
