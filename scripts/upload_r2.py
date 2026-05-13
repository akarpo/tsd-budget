#!/usr/bin/env python3
"""Upload .gitignore'd large files to Cloudflare R2 and update .r2.md stubs.

Reads the list of files to upload from the repo's .gitignore (entries prefixed
with `/boarddocs/`). Uploads each via `wrangler r2 object put` to
`media/tsd-budget/<original-path>`, then rewrites the matching `.r2.md` stub
with the live `https://media.karpowitsch.org/tsd-budget/...` URL and marks
status as uploaded.

Requires CLOUDFLARE_API_TOKEN in env.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUCKET = "media"
PREFIX = "tsd-budget"
CUSTOM_DOMAIN = "media.karpowitsch.org"

MIME = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def files_from_gitignore() -> list[Path]:
    gi = (REPO / ".gitignore").read_text().splitlines()
    paths = []
    for line in gi:
        line = line.strip()
        if line.startswith("/boarddocs/") and not line.startswith("#"):
            paths.append(REPO / line.lstrip("/"))
    return paths


def upload(local: Path, key: str) -> None:
    ext = local.suffix.lower()
    ct = MIME.get(ext, "application/octet-stream")
    cmd = [
        "wrangler", "r2", "object", "put",
        f"{BUCKET}/{key}",
        "--file", str(local),
        "--content-type", ct,
        "--remote",
    ]
    print(f"  uploading -> {BUCKET}/{key}  ({ct})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: wrangler failed (exit {result.returncode})", file=sys.stderr)
        print(f"  stderr: {result.stderr}", file=sys.stderr)
        raise SystemExit(2)


def update_stub(stub: Path, public_url: str) -> None:
    """Rewrite the R2 URL line and status line in a .r2.md stub."""
    text = stub.read_text()
    # Replace the "R2 URL" table row value (anything after "R2 URL |" up to newline)
    text = re.sub(
        r"^(\| R2 URL \| ).*$",
        rf"\1{public_url} |",
        text,
        flags=re.MULTILINE,
    )
    # Replace status line
    text = re.sub(
        r"\*\*Status:\*\* `pending R2 upload`[^\n]*",
        "**Status:** uploaded to R2.",
        text,
    )
    stub.write_text(text)


def main() -> int:
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        print("ERROR: CLOUDFLARE_API_TOKEN not set", file=sys.stderr)
        return 1

    files = files_from_gitignore()
    print(f"Found {len(files)} files to upload to R2 bucket '{BUCKET}' under '{PREFIX}/'\n")

    missing = [f for f in files if not f.exists()]
    if missing:
        print("ERROR: these files are listed in .gitignore but missing locally:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        return 1

    for i, local in enumerate(files, 1):
        rel = local.relative_to(REPO).as_posix()  # e.g. boarddocs/foo.pdf
        key = f"{PREFIX}/{rel}"
        public_url = f"https://{CUSTOM_DOMAIN}/{key}"
        stub = local.with_suffix(local.suffix + ".r2.md")

        print(f"[{i}/{len(files)}] {rel}")
        upload(local, key)

        if stub.exists():
            update_stub(stub, public_url)
            print(f"  stub updated -> {stub.name}")
        else:
            print(f"  WARNING: stub not found at {stub}")
        print()

    print(f"Done. {len(files)} files uploaded; stubs rewritten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
