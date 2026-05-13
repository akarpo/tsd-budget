#!/usr/bin/env bash
# Cloudflare Pages build script.
#
# Why this exists:
#   Cloudflare Pages defaults to deploying the repo root as the asset
#   directory. That includes .git/objects/pack/*.pack — currently ~85 MiB
#   — which exceeds the 25 MiB Workers Assets per-file limit and breaks
#   the deploy. This script writes a clean ./dist/ that contains only
#   tracked files, then Pages deploys dist/.
#
# Cloudflare Pages dashboard settings:
#   Build command:           bash build.sh
#   Build output directory:  dist
#
# Local use:
#   $ bash build.sh
#   $ open dist/index.html
#
set -euo pipefail

OUT=dist
rm -rf "$OUT"
mkdir -p "$OUT"

# `git archive` emits exactly the tracked files (respects .gitignore,
# excludes the .git/ directory). This is what Cloudflare's clone has.
git archive HEAD --format=tar | tar -x -C "$OUT"

# Defensive sweep — should already be excluded but cheap insurance.
rm -rf "$OUT/.git" "$OUT/dist"

# Report.
echo ""
echo "=== Build complete ==="
du -sh "$OUT"
echo ""
echo "Top-level contents:"
ls -la "$OUT" | head -12
echo ""
echo "Files > 5MB in build output (must all be < 25 MiB for Cloudflare):"
find "$OUT" -type f -size +5M -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' || true
