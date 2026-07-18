#!/usr/bin/env python3
"""Text-fidelity diff for website clones.

Compares the text content of each served clone page against the downloaded
ground-truth HTML in the research directory. Strips tags/scripts/styles,
decodes entities, and reports the unique words present in the original but
missing from the clone. 100% means every word survived the port.

Usage:
    python3 fidelity-diff.py --research docs/research/example.com --base http://localhost:3210

Page mapping convention (matches the clone-site skill's download layout):
    index.html            -> /
    page-<slug>.html      -> /<slug>/
    <dir>/<slug>.html     -> /<dir>/<slug>/   (e.g. blog/, compare/)
"""
import argparse
import html as H
import re
import sys
import urllib.request
from pathlib import Path


def text(markup: str) -> str:
    markup = re.sub(r"<script[^>]*>.*?</script>", " ", markup, flags=re.S)
    markup = re.sub(r"<style[^>]*>.*?</style>", " ", markup, flags=re.S)
    markup = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", H.unescape(markup)).strip()


def route_for(path: Path, research: Path) -> str:
    rel = path.relative_to(research)
    if rel.name == "index.html":
        return "/"
    if rel.parent == Path("."):
        m = re.match(r"page-(.+)\.html$", rel.name)
        if m:
            return f"/{m.group(1)}/"
        return f"/{rel.stem}/"
    return f"/{rel.parent}/{rel.stem}/"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--research", required=True, help="dir with downloaded ground-truth HTML")
    ap.add_argument("--base", default="http://localhost:3210", help="served clone base URL")
    ap.add_argument("--threshold", type=float, default=0.99)
    args = ap.parse_args()

    research = Path(args.research)
    pages = sorted(p for p in research.rglob("*.html"))
    if not pages:
        print(f"no .html files under {research}", file=sys.stderr)
        return 2

    worst = 1.0
    failures = 0
    for page in pages:
        route = route_for(page, research)
        orig = text(page.read_text(errors="replace"))
        try:
            clone = text(urllib.request.urlopen(args.base + route).read().decode())
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"{route:45s} FETCH FAILED: {e}")
            failures += 1
            continue
        ow, cw = set(orig.split()), set(clone.split())
        missing = ow - cw
        sim = 1 - len(missing) / max(1, len(ow))
        worst = min(worst, sim)
        flag = "" if sim >= args.threshold else f"  missing: {sorted(missing)[:10]}"
        if sim < args.threshold:
            failures += 1
        print(f"{route:45s} {sim:.1%}{flag}")

    print(f"\nworst: {worst:.1%}  ({'PASS' if failures == 0 else f'{failures} page(s) below threshold'})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
