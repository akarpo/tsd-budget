# Troy School District — Structural Deficit Analysis

A working analytical record of how Troy School District (TSD, Oakland County, Michigan) arrived at its current ~$5-12M/year structural operating deficit, the cost drivers behind it, and the data backing each claim.

**Status:** published. The analysis is live as a data-driven site at **[tsd-budget.karpowitsch.org](https://tsd-budget.karpowitsch.org)** (built from [`index.html`](./index.html)). The same writeup in plain markdown — with the charts rendered as tables — is [`ANALYSIS.md`](./ANALYSIS.md).

## What's in this folder

| Path | What it is |
|---|---|
| [`index.html`](./index.html) | The published site: a self-contained, single-file analysis with interactive charts (Chart.js), ten sections, and per-section collapsible source panels. This is the canonical, actively-maintained version of the analysis. Deployed at [tsd-budget.karpowitsch.org](https://tsd-budget.karpowitsch.org). |
| [`ANALYSIS.md`](./ANALYSIS.md) | Markdown companion to `index.html` — same ten sections, same FY25-audited figures, same sources, with the charts rendered as data tables. Regenerated from the site so the two stay in sync. Covers the deficit math, the FY15-FY25 cost baseline, the SpEd general-fund subsidy, the HCA/Edustaff buildup, the cost-growth ranking, the ESSER cliff, MPSERS pass-through, vendor cost growth, the per-pupil squeeze, and the synthesis. |
| [`inputs/`](./inputs/) | The three primary source documents that anchor the analysis: (a) the FY26 4-year General Fund projection (xlsx) prepared by Dan Trudel, CPA, Assistant Superintendent of Business Services; (b) the Special Ed Edustaff historical costs general-ledger summary (xlsx); (c) the November 2023 check register PDF. All three are authoritative TSD documents. |
| [`boarddocs/`](./boarddocs/) | ~140 cached source documents harvested from TSD's BoardDocs portal: 70 PDFs (5 audited ACFRs FY21-FY25, budget adoption + amendment cycles, Plante Moran enrollment forecasts, the Oct 2025 Special Education Update, the Strategic Plan 2026, the Levenson "Improving Outcomes and Equity" report, supporting board presentations), `.pptx` decks, and `.r2.md` text extractions of the PDFs. Large PDFs are also mirrored on the `media.karpowitsch.org` CDN, which the published site links to. |
| [`scripts/`](./scripts/) | Python tooling: BoardDocs API helpers, agenda crawler, file downloader, check-register analyzer, growth-rate computer, `.pptx` image extractor, and R2 upload helpers. See [`scripts/README.md`](./scripts/README.md). |
| [`scripts/data/`](./scripts/data/) | Harvest metadata: meeting indexes, keyword-match results, priority filter outputs, download manifests, extracted `.pptx` media. |
| [`build.sh`](./build.sh) · [`.assetsignore`](./.assetsignore) | Deploy/build support — see [Deploying to Cloudflare](#deploying-to-cloudflare) below. |

## How to read this

1. **For the analysis**, read the site at **[tsd-budget.karpowitsch.org](https://tsd-budget.karpowitsch.org)** — or [`ANALYSIS.md`](./ANALYSIS.md) for the same content in markdown. Either way the TL;DR is up top.
2. **For underlying numbers**, every section carries its own source list (collapsible panels on the site, "Sources for this section" blocks in `ANALYSIS.md`) citing the ACFR page, check-register query, or board presentation behind each claim. Source PDFs are in `boarddocs/`, named `YYYYMMDD_<tag>_<filename>.pdf`.
3. **For methodology**, see [`scripts/README.md`](./scripts/README.md). All analyses are reproducible from the inputs.

## Source provenance

- **TSD Annual Comprehensive Financial Reports (audited by Plante Moran)**: FY21, FY22, FY23, FY24, FY25 — pulled from BoardDocs board meeting attachments at the Oct/Nov audit-presentation meeting. The FY25 ACFR (accepted by the Board Nov 18, 2025) is the most recent audited year and the spine of the current analysis. Pre-FY21 ACFRs are not accessible via the BoardDocs Public API; FY15-FY20 data points are analytically substituted from the 10-year statistical sections of the FY24 and FY25 ACFRs.
- **Budget presentations**: FY24, FY25, FY26 adoption + amendment cycles — also from BoardDocs. The FY26 cycle includes the June 2025 Original, the January 2026 Amendment #1, the March 2026 Amendment #2, and the January 2026 Board Budget Planning Workshop.
- **Plante Moran CRESA enrollment forecasts**: 2023, 2025, 2026 vintages.
- **Special Education Update**: Oct 7, 2025 board workshop deck.
- **Levenson / New Solutions K12 Report**: "Improving Outcomes and Equity for Students with Disabilities and Other Students who Struggle" — Dec 2023, 32 pages.
- **Check register reconciliation**: 224,267 line items / $1.23B in disbursements FY11-FY26, sourced from the sibling `tsd-checkregister` project (a separate repo).
- **Statewide context**: Chalkbeat Detroit (Oct 30, 2025), Citizens Research Council of Michigan (July 2022), MI School Data, Michigan Autism State Plan.

## Reproducing the BoardDocs harvest

The BoardDocs Public API (Lotus Domino + CloudFront WAF) is undocumented but stable. The `scripts/` directory contains everything needed to re-run the harvest. See [`scripts/README.md`](./scripts/README.md) for the recipe.

## Deploying to Cloudflare

This project is wired to Cloudflare as a **Workers Static Assets** project (auto-detected from the GitHub connection — the dashboard shows `Framework: Static`, `Output Directory: .`, `Executing user deploy command: npx wrangler deploy`). Push to `main` triggers a deploy; the site serves at [tsd-budget.karpowitsch.org](https://tsd-budget.karpowitsch.org).

The repo-root deploy mode would otherwise include `.git/objects/pack/*.pack` (~88 MiB — over Cloudflare's 25 MiB per-asset limit). The fix lives in [`.assetsignore`](./.assetsignore), which excludes `.git/`, build artifacts, and editor/OS cruft from the deployed asset set. No dashboard settings need to change.

For local preview, [`build.sh`](./build.sh) writes a clean `dist/` mirror via `git archive`: `bash build.sh && open dist/index.html`. (Note: `build.sh`'s header comments describe an earlier Cloudflare *Pages* build-command setup; the live deploy uses the Workers Static Assets + `.assetsignore` path described above, and `build.sh` is now local-preview only.)

## License

Sources cited are in the public domain (audited financial reports posted to BoardDocs by TSD, statewide reports from state agencies). The analysis writeup, scripts, and metadata in this folder are released under MIT.
