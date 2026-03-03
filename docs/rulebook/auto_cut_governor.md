# RTS AUTO-CUT GOVERNOR (Operational Rule)

RTS uses proxy load metrics to decide when to prompt for a new BLOCK.

## CUT PROMPT CONDITIONS (any triggers)
1) Event Score >= 6
2) Conversation Turns >= 10
3) Elapsed Work Time >= 75 minutes

## EVENT SCORE
- External action (Stripe/Gumroad/DM/Email/Submission): +2
- Decision made (commit to plan / change direction): +2
- GitHub commit / file edit: +1
- Error -> fix loop: +1
- New feature added: +2

## USER RESPONSE
- "CUT"   -> generate BLOCK draft + numbering suggestion
- "SKIP"  -> continue session, postpone logging
- "LATER(30)" -> postpone prompt for 30 minutes equivalent

## SAFETY
If workload score >= 4, RTS must recommend logging and stopping heavy tasks.
