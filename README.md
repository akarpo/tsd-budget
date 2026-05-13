# Troy School District — Structural Deficit Analysis

A working analytical record of how Troy School District (TSD, Oakland County, Michigan) arrived at its current ~$5-12M/year structural operating deficit, the cost drivers behind it, and the data backing each claim.

**Status:** analysis-complete, public-facing site not yet built. The full writeup is in [`ANALYSIS.md`](./ANALYSIS.md).

## What's in this folder

| Path | What it is |
|---|---|
| [`ANALYSIS.md`](./ANALYSIS.md) | The main writeup. 12 parts, ~10K words. Covers the deficit math, 10-year financial baseline, SpEd cost driver, ESSER cliff, MPSERS, the Levenson Report findings, the in-sourcing question, the lay-off-and-replace question, and the three-category growth-rate comparison. |
| [`inputs/`](./inputs/) | The three source documents that anchor the analysis: (a) the FY26 4-year General Fund projection (xlsx) prepared by Dan Trudel, CPA, Assistant Superintendent of Business Services; (b) the Special Ed Edustaff historical costs general-ledger summary (xlsx); (c) the November 2023 check register PDF. All three are authoritative TSD documents. |
| [`boarddocs/`](./boarddocs/) | 133 cached source documents harvested from TSD's BoardDocs portal: 5 audited ACFRs (FY21-FY25), 3 budget adoption cycles, 3 Plante Moran enrollment forecasts, the Oct 2025 Special Education Update, the Strategic Plan 2026, the Levenson "Improving Outcomes and Equity" report (Dec 2023), and supporting board presentations. |
| [`scripts/`](./scripts/) | Python tooling: BoardDocs API helpers, agenda crawler, file downloader, check-register analyzer, growth-rate computer, .pptx image extractor. See [`scripts/README.md`](./scripts/README.md). |
| [`scripts/data/`](./scripts/data/) | Harvest metadata: meeting indexes, keyword-match results, priority filter outputs, download manifests, extracted .pptx media. |

## How to read this

1. **For the deficit story**, read [`ANALYSIS.md`](./ANALYSIS.md). The TL;DR is in the first 50 lines.
2. **For underlying numbers**, the data tables in `ANALYSIS.md` cite their sources (ACFR page, check register query, board presentation). Source PDFs are in `boarddocs/` named by `YYYYMMDD_<tag>_<filename>.pdf`.
3. **For methodology**, see [`scripts/README.md`](./scripts/README.md). All analyses are reproducible from the inputs.

## Source provenance

- **TSD Annual Comprehensive Financial Reports (audited by Plante Moran)**: FY21, FY22, FY23, FY24, FY25 — pulled from BoardDocs board meeting attachments at the Oct/Nov audit-presentation meeting. Pre-FY21 ACFRs are not accessible via the BoardDocs Public API; analytically substituted by the 10-year statistical section in the FY24 ACFR (which covers FY15-FY24).
- **Budget presentations**: FY24, FY25, FY26 adoption + amendment cycles — also from BoardDocs.
- **Plante Moran CRESA enrollment forecasts**: 2023, 2025, 2026 vintages.
- **Special Education Update**: Oct 7, 2025 board workshop deck.
- **Levenson / New Solutions K12 Report**: "Improving Outcomes and Equity for Students with Disabilities and Other Students who Struggle" — Dec 2023, 32 pages.
- **Check register reconciliation**: 224,267 line items / $1.23B in disbursements FY11-FY26, sourced from the sibling `tsd-checkregister` project (a separate repo).
- **Statewide context**: Chalkbeat Detroit (Oct 30, 2025), Citizens Research Council of Michigan (July 2022), MI School Data, Michigan Autism State Plan.

## Wrong-entity note

The file `~/Downloads/Troy_ACFR_FY2025.pdf` (not in this folder) is the **City of Troy ACFR**, not the Troy School District ACFR. The City of Troy and Troy School District are separate governmental entities with separate financial reports. The TSD ACFRs are in `boarddocs/` with filenames like `20251111_audit_24680_Troy_School_District-0625-AUD-Final.pdf`.

## Reproducing the BoardDocs harvest

The BoardDocs Public API (Lotus Domino + CloudFront WAF) is undocumented but stable. The `scripts/` directory contains everything needed to re-run the harvest. See [`scripts/README.md`](./scripts/README.md) for the recipe.

## Deploying to Cloudflare Pages

Cloudflare Pages defaults to treating the repo root as the asset directory, which includes `.git/objects/pack/*.pack` (currently ~85 MiB — over Cloudflare's 25 MiB per-asset limit). To work around this, the repo includes a `build.sh` that produces a clean `dist/` containing only tracked files via `git archive`.

**Configure in the Cloudflare Pages dashboard:**

| Setting | Value |
|---|---|
| Build command | `bash build.sh` |
| Build output directory | `dist` |
| Root directory | (leave default / blank) |

The script is also runnable locally for preview: `bash build.sh && open dist/index.html`.

## License

Sources cited are in the public domain (audited financial reports posted to BoardDocs by TSD, statewide reports from state agencies). The analysis writeup, scripts, and metadata in this folder are released under MIT.
