# Scripts

Reproducible analysis tooling for the Troy School District structural-deficit project.

## File map

| Script | Purpose |
|---|---|
| `boarddocs_api.py` | Shared helpers for the public BoardDocs Domino API: `get_meetings()`, `get_agenda(meeting_unique)`, `get_public_files(item_unique)`, `download_file(href, out_path)`. Handles CloudFront WAF via Safari-like User-Agent. |
| `crawl_agendas.py` | For a year range, fetches each meeting's agenda HTML and writes JSON of items matching keyword regex. Default keywords cover audit / SpEd / budget / enrollment / strategic terms. |
| `download_priority_files.py` | Consumes the keyword-hits JSON, filters to priority-tagged items, resolves attachments via BD-GetPublicFiles, downloads PDFs with descriptive filenames, writes a manifest JSON. |
| `analyze_check_register.py` | Operates on `~/Downloads/tsd-checkregister/Troy_SD_Check_Register_FY11-FY26.xlsx`. Five views: top vendors, Edustaff history, out-of-district SpEd, contract-staffing vendors, function-family aggregation. |
| `compute_growth_rates.py` | Static dataset (sourced from FY24 ACFR Schedules of Pension/OPEB Contributions + check register vendor data). Produces growth-rate comparison: outsourced services vs active benefits vs retiree benefits, plus % of payroll view, plus absolute $ additions. |
| `extract_pptx_images.py` | Unzip a .pptx, dump embedded media, write a per-slide structural index. Used to surface chart-only slides 13-15 in the Oct 2025 Special Education Update. |

## Reproducing the BoardDocs harvest

```bash
# 1. Crawl agendas for 2023-2026 (full agenda data available)
python crawl_agendas.py --from 2023 --to 2026 --out data/keyword_hits_2023-2026.json

# 2. Crawl agendas for 2020-2022 (full data also available)
python crawl_agendas.py --from 2020 --to 2022 --out data/keyword_hits_2020-2022.json

# 3. Download priority files for each batch
python download_priority_files.py --hits data/keyword_hits_2023-2026.json --out ../boarddocs/
python download_priority_files.py --hits data/keyword_hits_2020-2022.json --out ../boarddocs/
```

Pre-2020 agendas are not accessible via the BoardDocs Public API (skeletal items only).

## Running the analyses

```bash
# Three-category growth-rate comparison (uses internal static data)
python compute_growth_rates.py

# Check register analyses (require the master xlsx from sibling tsd-checkregister project)
python analyze_check_register.py --view all
python analyze_check_register.py --view edustaff
python analyze_check_register.py --view outofdistrict
```

## Dependencies

- Python 3.9+
- `pandas`, `openpyxl` (`pip install pandas openpyxl`)
- `curl` (system; used via subprocess for BoardDocs API)

## Data dependency

`analyze_check_register.py` reads from a sibling project:
- `~/Downloads/tsd-checkregister/Troy_SD_Check_Register_FY11-FY26.xlsx`

That workbook (224,267 line items / $1.23B disbursed across FY11-FY26) is
produced by a separate parsing pipeline; see https://github.com/<owner>/tsd-checkregister.

## Notes on the BoardDocs API

The BD-* endpoints are undocumented but stable. Three observations from
reverse-engineering the agenda.js client code:

1. `BD-GetAgenda` returns HTML, not JSON. Item attachments are NOT in this HTML —
   each item only declares `has_attachment` via an `<i class="fa fa-file-text">`
   icon. File IDs are resolved by a second call to `BD-GetPublicFiles?open` with
   `data={'id': item_unique}`.

2. File URLs are stable: `/Board.nsf/files/<FILE_ID>/$file/<filename>`. Direct
   GET works with browser User-Agent and proper Referer.

3. CloudFront blocks requests without realistic browser headers. The minimum
   working set is Safari-like User-Agent, `Origin`, `Referer` to the Public
   page, and `X-Requested-With: XMLHttpRequest` for XHR endpoints.

4. Pre-2020 agendas return skeletal data (1 placeholder item per meeting).
   The "2018 Board Packets and Minutes" and "2019 Board Packets and Minutes"
   archive entries link to individual meetings but those sub-meeting agendas
   also return 0 items via the API. Historical content from 2010-2019 is
   not accessible via the Public API.
