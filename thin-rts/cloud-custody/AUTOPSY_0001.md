# AUTOPSY 0001 — Custody Prototype Death

Observed CI run: `Cloud Custody Candidate Tests` run 8

Status: `PROTOTYPE_KILLED / PATCH_REQUIRED`

The first WITNESS Meteor attack produced **8 material failures out of 13 tests**. This is accepted as successful destructive evidence.

## Material death causes

1. restore download was not generation-bound;
2. duplicate manifest paths were accepted;
3. an empty evidence bundle could be packaged as success;
4. extraction into a dirty destination could mix stale and restored material;
5. manifest `..` escape could reference material outside the restored root;
6. new-object upload used best-effort `--no-clobber` instead of an atomic generation-zero precondition;
7. source evidence could collide with the reserved internal manifest filename;
8. unmanifested extra files were silently accepted by verification.

## Classification

These failures do **not** prove that custom cryptography or a custom storage engine is needed.

Current responsibility classification remains:

- cryptography: `EXTERNALIZE` to GnuPG;
- cloud transport/storage: `EXTERNALIZE` to Google Cloud tooling/provider for the first adapter;
- manifest/path validation, generation binding, deterministic package/recovery verification: bounded `GLUE` candidate;
- custom crypto / custom object store / custom key vault: `DROP`.

## Darwin action

Patch only the demonstrated glue gaps. Do not expand architecture.

Then rerun the exact same frozen attack suite before adding new attack angles.

`SAME DEATH CAUSE MUST NOT RECUR UNCHANGED.`
