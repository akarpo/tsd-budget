"""
BoardDocs Public API helpers — Troy School District (committee A4EP6J588C05).

Lotus Domino-backed BoardDocs Public site requires browser-like headers to bypass
the CloudFront WAF. Three relevant endpoints (POST, x-www-form-urlencoded):

  - BD-GetMeetingsList   data: current_committee_id=<ID>
                         → JSON array of meetings

  - BD-GetAgenda         data: current_committee_id=<ID>&id=<meeting_unique>
                         → HTML fragment with <li class="item" unique="..."> nodes

  - BD-GetPublicFiles    data: id=<item_unique>
                         → HTML fragment with <a class="public-file"> nodes
                           whose href points to /Board.nsf/files/<FILE_ID>/$file/<name>

The agenda HTML contains item-level unique IDs but NOT attachment file IDs.
File IDs must be resolved per-item by calling BD-GetPublicFiles.

Files are downloaded from go.boarddocs.com via the same /Board.nsf/files/.../$file/...
URL — plain GET with browser User-Agent and Referer.
"""

import subprocess, re, time, json, os

COMMITTEE_ID = 'A4EP6J588C05'
BASE = 'https://go.boarddocs.com/mi/troysd/Board.nsf'

# Full Safari-like UA; minimum needed to pass CloudFront challenge as of 2026-05.
HEADERS = [
    '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
          '(KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    '-H', 'X-Requested-With: XMLHttpRequest',
    '-H', 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
    '-H', 'Origin: https://go.boarddocs.com',
    '-H', 'Referer: https://go.boarddocs.com/mi/troysd/Board.nsf/Public',
    '-H', 'Accept-Language: en-US,en;q=0.9',
]


def _post(endpoint: str, data: str) -> str:
    """POST to a BoardDocs endpoint, return response body as string."""
    cmd = ['curl', '-s', '--max-time', '30'] + HEADERS + \
          ['-X', 'POST', '--data', data, f'{BASE}/{endpoint}?open']
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def get_meetings() -> list[dict]:
    """All meetings for the committee. Returns list of dicts with unique, name, numberdate."""
    raw = _post('BD-GetMeetingsList', f'current_committee_id={COMMITTEE_ID}')
    return json.loads(raw)


_ITEM_RE = re.compile(
    r'<li[^>]+class="[^"]*item[^"]*"[^>]+unique="([^"]+)"[^>]*>(.*?)</li>',
    re.DOTALL,
)
_TITLE_RE = re.compile(r'<span class="title">([^<]+)</span>')
_ACTION_RE = re.compile(r'<div class="actiontype">\s*([^<\n]+)', re.DOTALL)
_ATTACH_RE = re.compile(r'fa-file-text')


def get_agenda(meeting_unique: str) -> list[dict]:
    """Agenda items for a meeting. Returns list with unique, title, action, has_attachment."""
    html = _post('BD-GetAgenda', f'current_committee_id={COMMITTEE_ID}&id={meeting_unique}')
    items = []
    for m in _ITEM_RE.finditer(html):
        body = m.group(2)
        t = _TITLE_RE.search(body)
        a = _ACTION_RE.search(body)
        items.append({
            'unique': m.group(1),
            'title': (t.group(1).strip() if t else ''),
            'action': (a.group(1).strip().rstrip(',').strip() if a else ''),
            'has_attachment': bool(_ATTACH_RE.search(body)),
        })
    return items


_FILE_RE = re.compile(
    r'<a class="public-file"[^>]*unique="([^"]+)"[^>]*href="([^"]+)">([^<]+)</a>'
)


def get_public_files(item_unique: str) -> list[dict]:
    """Public files attached to an agenda item. Returns list with unique, href, label."""
    html = _post('BD-GetPublicFiles', f'id={item_unique}')
    return [
        {'unique': m.group(1), 'href': m.group(2), 'label': m.group(3)}
        for m in _FILE_RE.finditer(html)
    ]


def download_file(href: str, out_path: str) -> bool:
    """Download a public file. href starts with /mi/troysd/Board.nsf/files/..."""
    url = f'https://go.boarddocs.com{href}'
    subprocess.run([
        'curl', '-s', '-L', '--max-time', '60',
        '-A', HEADERS[1],
        '-H', f'Referer: {BASE}/Public',
        '-o', out_path, url,
    ], capture_output=True)
    return os.path.exists(out_path) and os.path.getsize(out_path) > 1000
