# Encrypted Cloud Custody — Existing Transport Inventory

Observed timestamp: **2026-08-11 21:23 JST**

Parent requirement:

`ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`

Read-only inventory command:

`type -a rclone rsync scp sftp curl aws gsutil az restic duplicity borg`

Observed results materially include:

Present:

- `rsync` at `/usr/bin/rsync` and `/bin/rsync`
- `scp` at `/usr/bin/scp` and `/bin/scp`
- `sftp` at `/usr/bin/sftp` and `/bin/sftp`
- `curl` at `/usr/bin/curl` and `/bin/curl`
- `gsutil` at `/usr/bin/gsutil` and `/bin/gsutil`

Not found in current PATH:

- `rclone`
- `aws`
- `az`
- `restic`
- `duplicity`
- `borg`

## Current interpretation

A provider-neutral transport tool (`rclone`) is not currently installed, but several mature existing transports are present. Most importantly, `gsutil` is already installed, which creates a concrete existing Google Cloud Storage transport candidate for the first custody proof.

This does **not** yet prove that `gsutil` is configured, authenticated, authorized to a user-approved bucket, or suitable for the final provider-neutral architecture.

`TRANSPORT_EXISTS != REMOTE_CUSTODY_WORKS`

`PROVIDER_SPECIFIC_AVAILABLE != PROVIDER_NEUTRAL_COMPLETE`

The available transports should now be split by materially different trust and operating models rather than tested identically:

1. `gsutil`: object-storage candidate with cloud object identity/stat/list semantics.
2. `scp` / `sftp` / `rsync`: host-to-host transport candidates requiring a separately controlled remote host/path.
3. `curl`: protocol primitive, not by itself a custody backend.

The next bounded test should inspect `gsutil` version/configuration state without uploading, mutating, or exposing credentials.

No remote object, cloud bucket, SSH host, credential, source file, or repository state was modified by this inventory.
