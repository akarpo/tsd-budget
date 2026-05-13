"""
Download BoardDocs file attachments for priority agenda items.

Usage:
    python download_priority_files.py --hits data/keyword_hits.json \
                                       --out ../boarddocs/

Priority items are selected by matching title against PRIORITY_PATTERNS — only
items with attachments and recognized priority tags are downloaded. Files are
named with the format:
    YYYYMMDD_<tag>_<safe-original-filename>

Output: writes a manifest JSON next to the files describing what was downloaded.

The first call to BD-GetPublicFiles resolves item_unique → file URLs (which are
NOT discoverable from the agenda HTML alone). Each file then downloaded with
a plain GET to /Board.nsf/files/<FILE_ID>/$file/<name>.
"""

import argparse, json, os, re, sys, time
from urllib.parse import unquote
from boarddocs_api import get_public_files, download_file

# Items matching these patterns are considered priority. Order matters — first match wins.
PRIORITY_PATTERNS = [
    (r'audit', 'audit'),
    (r'Plante Moran', 'plante_moran'),
    (r'Special Education Update', 'sped_update'),
    (r'Student Achievement', 'achievement'),
    (r'Strategic Plan', 'strategic'),
    (r'Transportation Study', 'transport_study'),
    (r'Bus Time', 'bus_study'),
    (r'Attendance Area Review', 'attendance'),
    (r'Budget Priorities', 'budget_priorities'),
    (r'PUBLIC HEARING.*Budget', 'budget_hearing'),
    (r'Budget Adoption', 'budget_adoption'),
    (r'Budget Amendment', 'budget_amendment'),
    (r'Enrollment Projection', 'enrollment'),
    (r'Plante Moran CRESA', 'enrollment'),
]


def select_priority(hits: list[dict]) -> list[dict]:
    """Filter to priority items only; tag each with its category."""
    seen = set()
    out = []
    for h in hits:
        if not h.get('has_attachment'):
            continue
        for pat, tag in PRIORITY_PATTERNS:
            if re.search(pat, h['item_title'], re.IGNORECASE):
                key = (h['meeting_date'], h['item_title'])
                if key in seen:
                    break
                seen.add(key)
                out.append({**h, '_tag': tag})
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hits', required=True, help='Path to keyword_hits.json')
    ap.add_argument('--out', required=True, help='Output directory for PDFs')
    ap.add_argument('--manifest', default=None,
                    help='Path to manifest JSON (default: <out>/download_manifest.json)')
    ap.add_argument('--delay', type=float, default=0.4)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    manifest_path = args.manifest or os.path.join(args.out, 'download_manifest.json')

    hits = json.load(open(args.hits))
    priority = select_priority(hits)
    print(f"Priority items: {len(priority)} (filtered from {len(hits)} keyword hits)",
          file=sys.stderr)

    manifest = []
    for i, h in enumerate(priority):
        files = get_public_files(h['item_unique'])
        print(f"  [{i+1:>2}/{len(priority)}] {h['meeting_date']} [{h['_tag']:<18}] "
              f"{h['item_title'][:48]} | {len(files)} files", file=sys.stderr)
        for f in files:
            orig = unquote(f['href'].split('/$file/')[-1])
            safe = orig.replace('/', '_').replace(' ', '_')
            out_name = f"{h['meeting_date']}_{h['_tag']}_{safe}"
            out_path = os.path.join(args.out, out_name)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                status = 'exists'
            else:
                ok = download_file(f['href'], out_path)
                size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                status = 'OK' if ok else 'FAIL'
                print(f"      -> {status} ({size:,}) {out_name[:75]}", file=sys.stderr)
            manifest.append({**h, 'file_unique': f['unique'], 'file_href': f['href'],
                             'out_path': out_path, 'status': status})
            time.sleep(args.delay)
        time.sleep(args.delay)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    succeeded = len([m for m in manifest if m['status'] in ('OK', 'exists')])
    print(f"\nDone: {succeeded} files retained, manifest at {manifest_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
