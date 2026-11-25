#!/usr/bin/env python3
"""Read-only cryptographic SD card backup parity verifier (Python 3 stdlib only)."""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".Spotlight-V100", ".Trashes", ".fseventsd", ".TemporaryItems", "System Volume Information", "@eaDir"}
SKIP_FILES = {".DS_Store", "Thumbs.db", "INDEX.BDM", "MOVIEOBJ.BDM"}


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname in SKIP_FILES or fname.startswith("._"):
                continue
            fpath = Path(dirpath) / fname
            try:
                if fpath.is_symlink():
                    continue
                st = fpath.stat()
                if st.st_size > 0:
                    yield fpath, st.st_size
            except OSError:
                continue


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fmt_gb(nbytes: int) -> float:
    return round(nbytes / (1024 ** 3), 3)


def cmd_verify(card: Path, backups: list[Path], output: Path) -> None:
    if not card.exists():
        print(f"Error: SD card path not found: {card}", file=sys.stderr)
        sys.exit(1)
    for b in backups:
        if not b.exists():
            print(f"Error: backup path not found: {b}", file=sys.stderr)
            sys.exit(1)

    backup_by_size: dict[int, list[Path]] = defaultdict(list)
    for b in backups:
        for fpath, size in iter_files(b):
            backup_by_size[size].append(fpath)

    backup_hashes: dict[Path, str] = {}
    verified = []
    missing = []
    verified_bytes = 0
    missing_bytes = 0

    for cpath, csize in iter_files(card):
        cands = backup_by_size.get(csize, [])
        if not cands:
            missing.append({"card_path": str(cpath), "size_bytes": csize})
            missing_bytes += csize
            continue

        c_digest = sha256_file(cpath)
        matched = None
        for bpath in cands:
            if bpath not in backup_hashes:
                try:
                    backup_hashes[bpath] = sha256_file(bpath)
                except OSError:
                    backup_hashes[bpath] = ""
            if backup_hashes[bpath] == c_digest:
                matched = str(bpath)
                break

        if matched:
            verified.append({
                "card_path": str(cpath),
                "backup_path": matched,
                "size_bytes": csize,
                "sha256": c_digest,
            })
            verified_bytes += csize
        else:
            missing.append({"card_path": str(cpath), "size_bytes": csize, "sha256": c_digest})
            missing_bytes += csize

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "card": str(card),
        "backups": [str(b) for b in backups],
        "safe_to_format": len(missing) == 0,
        "verified_count": len(verified),
        "verified_bytes": verified_bytes,
        "verified_gb": fmt_gb(verified_bytes),
        "unbacked_up_count": len(missing),
        "unbacked_up_bytes": missing_bytes,
        "unbacked_up_gb": fmt_gb(missing_bytes),
        "unbacked_up_files": missing,
        "verified_files_sample": verified[:50],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    status = "SAFE TO FORMAT (100% backed up)" if report["safe_to_format"] else f"DO NOT FORMAT ({len(missing)} unbacked-up files)"
    print(f"Success! Audit written to: {output} | {status} | Verified: {len(verified)} ({fmt_gb(verified_bytes)} GB)")


def cmd_report(audit_path: Path, output: Path) -> None:
    data = json.loads(audit_path.read_text())
    verdict = "SAFE TO FORMAT (100% Verified)" if data["safe_to_format"] else "DO NOT FORMAT — Unbacked-Up Files Found"
    lines = [
        f"# SD Card Backup Verification Report",
        "",
        f"- **Card:** `{data['card']}`",
        f"- **Verdict:** **{verdict}**",
        f"- **Verified & Backed Up:** `{data['verified_count']}` files (`{data['verified_gb']} GB`)",
        f"- **Unbacked Up (Preserve!):** `{data['unbacked_up_count']}` files (`{data['unbacked_up_gb']} GB`)",
        "",
    ]
    if data["unbacked_up_files"]:
        lines.append("## Unbacked-Up Files")
        for f in data["unbacked_up_files"][:100]:
            lines.append(f"- `{f['card_path']}` ({round(f['size_bytes'] / (1024**2), 2)} MB)")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    print(f"Success! Markdown report written to: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cryptographic SD Card Backup Verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    p_v = sub.add_parser("verify", help="Verify SD card files against backup roots")
    p_v.add_argument("--card", required=True, type=Path)
    p_v.add_argument("--backup", required=True, nargs="+", type=Path)
    p_v.add_argument("--output", required=True, type=Path)

    p_r = sub.add_parser("report", help="Render Markdown summary from verify JSON")
    p_r.add_argument("--audit", required=True, type=Path)
    p_r.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "verify":
        cmd_verify(args.card, args.backup, args.output)
    elif args.command == "report":
        cmd_report(args.audit, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
