---
name: sd-card-backup-verifier
description: >-
  Cryptographically verifies camera SD cards (Sony, Fujifilm, DJI, GoPro, etc.)
  against local, external drive, or NAS backups using exact byte-size and
  SHA-256 checksum matching, explicitly separating 100% verified files from
  unbacked-up files before formatting or reclaiming SD card space. Use when the
  user wants to check if an SD card is safely backed up or reclaim space on
  camera memory cards.
---

# SD Card Backup Verifier

## Overview

Prevents accidental data loss when clearing or formatting camera SD cards. Compares every media file (RAW, JPEG, HEIF, MP4, MOV, etc.) on one or more SD cards against one or more backup roots using **exact byte size + SHA-256 hash verification** (never trusting filenames alone, since cameras reset counters).

## Quick Start

```bash
uv run scripts/sd_verify.py verify \
  --card /Volumes/CAMERA_SD \
  --backup /Volumes/BackupDrive/Photos /Volumes/NAS/Photos \
  --output /tmp/sd-audit.json
```

## Utility Scripts

`scripts/sd_verify.py` uses Python 3 standard library only and is **strictly read-only**.

### Subcommands
- **`verify --card <dir> --backup <dir...> --output <path.json>`**:
  - Scans all media/non-system files on `--card` (skipping `.Spotlight-V100`, `.Trashes`, `.fseventsd`, `._*` AppleDouble files).
  - Indexes `--backup` directories by exact byte size, computing full SHA-256 hashes on size matches.
  - Outputs JSON with `safe_to_format` (`true`/`false`), `verified_count`, `verified_gb`, `unbacked_up_count`, `unbacked_up_gb`, and the exact list of any unbacked-up files.
- **`report --audit <path.json> --output <report.md>`**:
  - Generates a clean Markdown audit summary showing verified vs. unbacked-up files and reclaimable GB.

## Workflow

1. **Discover Mounted Volumes:** Run `ls /Volumes` and confirm with the user which volume is the SD card and which path(s) are the backup targets.
2. **Run Cryptographic Verification:** Execute `sd_verify.py verify` for each SD card.
3. **Review Unbacked-Up Files:**
   - If `unbacked_up_count == 0`: Report `100% VERIFIED — SAFE TO RECLAIM`.
   - If `unbacked_up_count > 0`: List every unbacked-up file path and size; **NEVER format or delete unbacked-up files**. Offer to copy missing files to the backup destination first, then re-verify.
4. **Safe Cleanup (Only With Explicit Confirmation):** Delete only SHA-256-verified files (or let the user format in-camera once 100% verified).

## Common Mistakes

- **Matching by filename only:** Cameras reuse `DSC00001.ARW` / `DSCF0001.RAF` across shoots. Always match by size + SHA-256.
- **Deleting sidecar/proxy files (`*.THM`, `*.LRF`, `*.XML`) without checking:** Check whether RAW/video originals are backed up separately from DJI/Sony proxy files.
- **Formatting via macOS Disk Utility instead of in-camera:** After 100% verified backup, formatting inside the camera ensures the exact exFAT cluster size and folder structure the camera expects.
