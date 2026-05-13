"""
Extract embedded images and slide-by-slide text/structure from a .pptx file.

Used here to surface the Oct 2025 Special Education Update presentation's
image-only "Special Education Funding" slides 13-15 (which python-pptx text
extraction misses because they're rendered chart screenshots).

Usage:
    python extract_pptx_images.py <input.pptx> <out_dir>

Outputs:
    <out_dir>/imageNN.{png,jpeg}  — all embedded media, with original filenames
    <out_dir>/slides_index.txt    — per-slide structure: embed refs, has-chart,
                                    text excerpt
"""

import re, sys, os, zipfile


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    pptx_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    with zipfile.ZipFile(pptx_path) as z:
        # Dump media files
        media = [n for n in z.namelist() if n.startswith('ppt/media/')]
        for n in media:
            target = os.path.join(out_dir, os.path.basename(n))
            with z.open(n) as src, open(target, 'wb') as dst:
                dst.write(src.read())
        print(f"Extracted {len(media)} media files to {out_dir}/", file=sys.stderr)

        # Index slides
        slides = sorted(
            [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
            key=lambda x: int(re.search(r'slide(\d+)', x).group(1)),
        )
        index_lines = []
        for i, sp in enumerate(slides, start=1):
            with z.open(sp) as f:
                content = f.read().decode('utf-8', errors='ignore')
            # Resolve r:embed → media filenames via per-slide _rels file
            embeds = re.findall(r'r:embed="(rId\d+)"', content)
            rel_path = sp.replace('ppt/slides/', 'ppt/slides/_rels/') + '.rels'
            rel_map = {}
            try:
                with z.open(rel_path) as f:
                    rels = f.read().decode('utf-8', errors='ignore')
                for m in re.finditer(r'Id="(rId\d+)"[^>]+Target="([^"]+)"', rels):
                    rel_map[m.group(1)] = m.group(2)
            except KeyError:
                pass
            embedded = ', '.join(rel_map.get(r, r) for r in embeds)
            has_chart = '<c:chart' in content
            texts = re.findall(r'<a:t>([^<]+)</a:t>', content)
            text_preview = ' | '.join(texts[:5])[:160]
            index_lines.append(
                f"Slide {i:2d}: chart={has_chart}  embeds=[{embedded}]\n"
                f"          text: {text_preview}"
            )

        index_path = os.path.join(out_dir, 'slides_index.txt')
        with open(index_path, 'w') as f:
            f.write('\n'.join(index_lines))
        print(f"Wrote slide index to {index_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
