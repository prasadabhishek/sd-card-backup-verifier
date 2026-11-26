# SD Card Backup Verifier

Read-only agent skill and Python CLI to cryptographically verify camera SD cards against local, external drive, or NAS backups (exact byte size + SHA-256) before clearing or formatting memory cards.

## Install as an Agent Skill

```bash
npx skills add prasadabhishek/sd-card-backup-verifier
```

## Standalone CLI Usage

```bash
uv run scripts/sd_verify.py verify \
  --card /Volumes/CAMERA_SD \
  --backup /Volumes/BackupDrive/Photos \
  --output /tmp/sd-audit.json

uv run scripts/sd_verify.py report \
  --audit /tmp/sd-audit.json \
  --output /tmp/sd-report.md
```

## License

MIT

---
Built by [Abhishek Prasad](https://abhishekprasad.fyi)
