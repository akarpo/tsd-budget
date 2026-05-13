"""
Crawl Troy School District BoardDocs agendas for keyword-matching items.

Usage:
    python crawl_agendas.py --from 2023 --to 2026 --out data/keyword_hits.json

What it does:
    1. Fetches the full meetings list once (BD-GetMeetingsList).
    2. For each meeting in the requested year range, fetches the agenda HTML
       (BD-GetAgenda) and parses out <li class="item"> nodes.
    3. Tests each item's title + action type against a keyword regex.
    4. Writes matching items to JSON (meeting_date, meeting_unique, item_unique,
       item_title, item_action, has_attachment).

Notes on coverage:
    - 2013-2017: meetings exist in the index but each agenda returns 1 placeholder
      item only. Pre-2020 individual agenda content was not migrated to the
      Public-facing BoardDocs API.
    - 2018-2019: archived as annual packets ("YYYY Board Packets and Minutes")
      with sub-items pointing to individual meetings; the sub-meetings also
      return 0 agenda items.
    - 2020-2026: full agenda content available with attached files resolvable
      via boarddocs_api.get_public_files().

Rate limiting: 0.3-0.4s between requests is sufficient to avoid CloudFront
WAF blocks; longer delays may be needed if your IP gets rate-limited.
"""

import argparse, json, re, sys, time
from boarddocs_api import get_meetings, get_agenda

DEFAULT_KEYWORDS = [
    'levenson', 'new solutions', 'special education', 'spec ed', 'sped', ' iep ',
    'audit', 'financial report', 'annual financial', 'acfr', 'cafr',
    'budget', 'enrollment', 'esser', 'health care aide', 'student support',
    'custodi', 'burr', 'facilit', 'mpsers', 'pension', 'opeb', 'retir',
    'strategic plan', 'attendance area', 'transportation study', 'plante',
    'consult', 'achievement', 'wing lake', 'edustaff',
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='from_year', type=int, required=True)
    ap.add_argument('--to', dest='to_year', type=int, required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=0.35,
                    help='Seconds between requests (default 0.35)')
    ap.add_argument('--keywords', nargs='+', default=DEFAULT_KEYWORDS)
    args = ap.parse_args()

    print(f"Fetching meetings list...", file=sys.stderr)
    all_meetings = get_meetings()
    years = {str(y) for y in range(args.from_year, args.to_year + 1)}
    meetings = [m for m in all_meetings if m.get('numberdate', '')[:4] in years]
    meetings.sort(key=lambda m: m['numberdate'])
    print(f"Found {len(meetings)} meetings in {args.from_year}-{args.to_year}", file=sys.stderr)

    keyword_re = re.compile('|'.join(re.escape(k) for k in args.keywords), re.I)
    results = []
    for i, m in enumerate(meetings):
        items = get_agenda(m['unique'])
        matches = 0
        for it in items:
            text = (it['title'] + ' ' + it['action']).lower()
            if keyword_re.search(text):
                results.append({
                    'meeting_date': m['numberdate'],
                    'meeting_unique': m['unique'],
                    'meeting_name': m['name'],
                    'item_unique': it['unique'],
                    'item_title': it['title'],
                    'item_action': it['action'],
                    'has_attachment': it['has_attachment'],
                })
                matches += 1
        if (i + 1) % 10 == 0 or i == len(meetings) - 1:
            print(f"  [{i+1:>3}/{len(meetings)}] {m['numberdate']} | {len(items)} items, "
                  f"{matches} matches (cumulative {len(results)})", file=sys.stderr)
        time.sleep(args.delay)

    with open(args.out, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {len(results)} keyword-matched items to {args.out}", file=sys.stderr)


if __name__ == '__main__':
    main()
