# FRZ-000012 — Compact Active + Restart Surface v1

Goal: keep the always-loaded restart state bounded without losing restart competence.

Fixed restart denominator: goal, repo, branch, source commit, changed, verified, unresolved/UNKNOWN, rollback, do-not-touch, next authorized action. Deep history remains behind traceable source pointers. Over-budget state fails closed; it is never silently truncated. Restart state never grants execution or promotion authority.
