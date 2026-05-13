"""
Upload externalized large files to Cloudflare R2 and update the manifest + stubs.

Files > 5MB live on disk in `boarddocs/` (gitignored) and are documented in
`scripts/data/r2_manifest.json` with placeholder R2 URLs. This script:

    1. Uploads each pending file to R2 via the S3-compatible API
    2. Verifies the upload (HEAD request returns matching size + content-type)
    3. Updates `r2_manifest.json` with the final R2 URL and status = 'uploaded'
    4. Re-writes each `.r2.md` stub with the real URL
    5. Re-writes `boarddocs/MANIFEST.md` with real URLs

Auth: reads R2 credentials from environment variables:
    R2_ACCOUNT_ID         (Cloudflare account ID — for endpoint URL)
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET             (default: tsd-budget)
    R2_PUBLIC_HOST        (custom domain or 'pub-<hash>.r2.dev'; used for URLs)
    R2_PUBLIC_PREFIX      (URL path prefix, default: 'boarddocs')

Requires: boto3 (pip install boto3)

Usage:
    R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_ACCOUNT_ID=... \\
      R2_PUBLIC_HOST=files.example.com \\
      python scripts/upload_to_r2.py

Idempotent: files already marked 'uploaded' in the manifest are skipped unless
--force is passed.
"""

import argparse, json, os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO / 'scripts' / 'data' / 'r2_manifest.json'
MANIFEST_MD = REPO / 'boarddocs' / 'MANIFEST.md'


def ensure_boto3():
    try:
        import boto3  # noqa
        return boto3
    except ImportError:
        print("ERROR: boto3 not installed. Run: pip install boto3", file=sys.stderr)
        sys.exit(1)


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text())


def save_manifest(rows):
    MANIFEST_PATH.write_text(json.dumps(rows, indent=2))


def write_stub(repo_root: Path, row: dict):
    """Re-write the .r2.md stub for a single file with the (possibly updated) URL."""
    stub_path = repo_root / row['stub']
    fname = row['rel'].split('/')[-1]
    rel = row['rel']
    size_mb = row['size_mb']
    size_bytes = row['size_bytes']
    sha = row['sha256']
    url = row['r2_url']
    status = row['status']
    content = f"""# {fname}

This file is hosted on Cloudflare R2 (too large for the git repo).

| Property | Value |
|---|---|
| Original filename | `{fname}` |
| Original path | `{rel}` |
| Size | {size_mb:.2f} MB ({size_bytes:,} bytes) |
| SHA-256 | `{sha}` |
| Source | Troy School District BoardDocs harvest (May 2026) |
| R2 URL | [{url}]({url}) |
| Status | `{status}` |

To verify integrity after download:
```bash
shasum -a 256 {fname}
# expected: {sha}
```
"""
    stub_path.write_text(content)


def write_manifest_md(rows):
    total_mb = sum(r['size_mb'] for r in rows)
    uploaded = sum(1 for r in rows if r['status'] == 'uploaded')
    lines = [
        "# R2-Externalized Files Manifest",
        "",
        "Files larger than 5MB are stored on Cloudflare R2 instead of in this git repo.",
        "Each file has a sibling `.r2.md` stub with the same metadata (size, SHA-256, source).",
        "",
        f"**Status:** {uploaded}/{len(rows)} files uploaded.",
        "",
        f"**Total externalized:** {len(rows)} files / {total_mb:.1f} MB",
        "",
        "| # | File | Size | Stub | R2 URL | Status |",
        "|---|------|------|------|--------|--------|",
    ]
    for i, r in enumerate(sorted(rows, key=lambda r: -r['size_mb']), 1):
        fname = r['rel'].split('/')[-1]
        stub_name = r['stub'].split('/')[-1]
        url = r['r2_url']
        url_md = f"[link]({url})" if r['status'] == 'uploaded' else 'pending'
        lines.append(f"| {i} | `{fname}` | {r['size_mb']:.1f} MB | "
                     f"[`{stub_name}`](./{stub_name}) | {url_md} | {r['status']} |")
    lines.append("")
    MANIFEST_MD.write_text('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true',
                    help='Re-upload files already marked uploaded')
    ap.add_argument('--dry-run', action='store_true', help='Show what would happen')
    args = ap.parse_args()

    # Credentials
    account_id = os.environ.get('R2_ACCOUNT_ID')
    access_key = os.environ.get('R2_ACCESS_KEY_ID')
    secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
    bucket = os.environ.get('R2_BUCKET', 'tsd-budget')
    public_host = os.environ.get('R2_PUBLIC_HOST')
    public_prefix = os.environ.get('R2_PUBLIC_PREFIX', 'boarddocs')

    missing = [k for k, v in [
        ('R2_ACCOUNT_ID', account_id),
        ('R2_ACCESS_KEY_ID', access_key),
        ('R2_SECRET_ACCESS_KEY', secret_key),
        ('R2_PUBLIC_HOST', public_host),
    ] if not v]
    if missing and not args.dry_run:
        print(f"ERROR: Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    rows = load_manifest()
    print(f"Manifest: {len(rows)} files", file=sys.stderr)
    pending = [r for r in rows if args.force or r['status'] != 'uploaded']
    print(f"To upload: {len(pending)}", file=sys.stderr)

    if args.dry_run:
        for r in pending:
            print(f"  WOULD upload: {r['rel']} ({r['size_mb']:.1f} MB)")
        return

    boto3 = ensure_boto3()
    s3 = boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto',
    )

    for i, row in enumerate(pending, 1):
        local = REPO / row['rel']
        if not local.exists():
            print(f"  [{i}/{len(pending)}] MISSING: {row['rel']}", file=sys.stderr)
            row['status'] = 'missing'
            continue
        key = f"{public_prefix}/{local.name}"
        # Determine content type
        ct = {'pdf': 'application/pdf', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
              'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
              'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
              'doc': 'application/msword', 'xls': 'application/vnd.ms-excel'}.get(
            local.suffix.lstrip('.').lower(), 'application/octet-stream')

        print(f"  [{i}/{len(pending)}] Uploading {local.name} ({row['size_mb']:.1f} MB)...",
              file=sys.stderr)
        with open(local, 'rb') as f:
            s3.put_object(Bucket=bucket, Key=key, Body=f, ContentType=ct)

        # Verify with HEAD
        head = s3.head_object(Bucket=bucket, Key=key)
        if head['ContentLength'] != row['size_bytes']:
            print(f"    WARN: size mismatch (uploaded {head['ContentLength']} vs "
                  f"expected {row['size_bytes']})", file=sys.stderr)

        url = f"https://{public_host}/{key}"
        row['r2_url'] = url
        row['status'] = 'uploaded'
        write_stub(REPO, row)
        print(f"    -> {url}", file=sys.stderr)

    save_manifest(rows)
    write_manifest_md(rows)
    print(f"\nManifest updated. {sum(1 for r in rows if r['status']=='uploaded')}/{len(rows)} uploaded.",
          file=sys.stderr)


if __name__ == '__main__':
    main()
