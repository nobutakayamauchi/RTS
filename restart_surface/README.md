# Compact Active + Restart Surface v1

A repository-local, non-authorizing restart representation. It keeps a fixed restart denominator in the active surface and leaves deep history behind current, traceable source pointers. It refuses silent truncation: if required restart state cannot fit the configured budget, construction fails closed.

`RESTART SURFACE != FULL HISTORY`

`COMPACT != DROP UNKNOWN`

`RESTART STATE != EXECUTION AUTHORITY`
