# Encrypted Cloud Custody — Existing Tool Probe: gsutil

Observed timestamp: **2026-08-11 21:25 JST**

Parent requirement:

`ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`

## Probe result

Read-only command:

`gsutil version -l`

Observed result materially includes:

- `gsutil version: 5.37`
- `using cloud sdk: True`
- `pass cloud sdk credentials to gsutil: True`
- `gsutil path: /usr/lib/google-cloud-sdk/bin/gsutil`
- platform/runtime information consistent with the current Ubuntu host
- configuration paths include the user's `.boto` location and a legacy Cloud SDK credential-scoped `.boto` location

The credential-scoped path contained an account identifier in terminal output. That identifier is intentionally not copied into this public evidence record because its raw value is unnecessary for the current engineering conclusion.

## Current classification

`GSUTIL_EXECUTABLE = PRESENT`

`GSUTIL_USES_CLOUD_SDK = OBSERVED`

`GSUTIL_CREDENTIAL_BRIDGE_TO_CLOUD_SDK = OBSERVED`

`CLOUD_CONFIGURATION_MATERIAL = PRESENT_AT_PATH_LEVEL`

This is stronger than simple executable presence: the installed gsutil is integrated with the Cloud SDK credential mechanism and sees configuration material on the host.

It does **not** yet prove that an active authenticated identity currently exists, that any bucket is accessible, or that upload/download authority is valid.

## Next safe probe

The next check should determine only whether an **ACTIVE** Cloud SDK auth entry exists, while suppressing account names and credentials.

No bucket listing, object listing, upload, download, delete, key inspection, token printing, or cloud mutation was performed in this probe.
