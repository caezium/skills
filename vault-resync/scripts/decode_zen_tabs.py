#!/usr/bin/env python3
"""Decode live Zen/Firefox tabs and write a categorized triage note.

Zen (and Firefox) store the live session in `sessionstore-backups/recovery.jsonlz4`,
a "mozlz4" container: 8-byte magic `mozLz40\\0`, 4-byte LE uncompressed size, then a
raw LZ4 *block*. There is no pip dependency available on a fresh Mac and `pip install lz4`
is blocked by PEP 668, so this bundles a tiny pure-Python LZ4 block decoder. Don't fight it.

Usage:
    python3 decode_zen_tabs.py --out /path/to/01_inbox/tabs/zen-tabs-YYYY-MM-DD.md --date YYYY-MM-DD
"""
import argparse, glob, json, os, re
from urllib.parse import urlparse
from collections import defaultdict


def lz4_decompress(src: bytes) -> bytes:
    out = bytearray(); i = 0; n = len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        out += src[i:i + lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        start = len(out) - off
        for j in range(ml):
            out.append(out[start + j])
    return bytes(out)


def read_mozlz4(path: str) -> bytes:
    d = open(path, "rb").read()
    assert d[:8] == b"mozLz40\x00", f"not a mozlz4 file: {path}"
    return lz4_decompress(d[12:])  # skip 8-byte magic + 4-byte size header


def collect_tabs(profiles_base: str):
    cands = (glob.glob(profiles_base + "/*/sessionstore-backups/recovery.jsonlz4")
             + glob.glob(profiles_base + "/*/sessionstore.jsonlz4"))
    best = None
    for p in sorted(cands, key=os.path.getmtime, reverse=True):
        try:
            j = json.loads(read_mozlz4(p))
            n = sum(len(w.get("tabs", [])) for w in j.get("windows", []))
            if best is None and n > 0:
                best = j
        except Exception:
            continue
    if not best:
        return []
    urls = []
    for w in best.get("windows", []):
        for t in w.get("tabs", []):
            try:
                cur = t["entries"][t.get("index", 1) - 1]
                u = cur.get("url", ""); ti = (cur.get("title") or "").strip()
                if u.startswith("http"):
                    urls.append((ti, u))
            except Exception:
                pass
    seen = set()
    return [(ti, u) for ti, u in urls if not (u in seen or seen.add(u))]


def categorize(ti, u):
    d = urlparse(u).netloc.lower()
    d = d[4:] if d.startswith("www.") else d
    if d in ("localhost", "127.0.0.1", "") or u.startswith("about:"):
        return None
    if "google." in d and "/search" in u:
        return None
    if d.endswith("github.com"):
        return "code"
    if d in ("arxiv.org", "aclanthology.org", "openreview.net", "papers.nips.cc", "dl.acm.org") or u.lower().endswith(".pdf"):
        return "papers"
    if d in ("youtube.com", "youtu.be", "m.youtube.com", "bilibili.com"):
        return "video"
    if d in ("x.com", "twitter.com", "reddit.com", "news.ycombinator.com", "linkedin.com"):
        return "social"
    if "docs." in d or d.endswith("readthedocs.io"):
        return "docs"
    if any(k in d for k in ("openai", "anthropic", "huggingface", "kaggle", "colab", "lovable", "supabase", "vercel", "cloudflare")):
        return "ai_tools"
    return "other"


LABELS = {"video": "🎥 Video (clip candidates)", "code": "🛠️ Code / repos",
          "papers": "📄 Papers & PDFs", "ai_tools": "🤖 AI tools / dashboards",
          "docs": "📚 Docs", "social": "💬 Social / threads", "other": "🌐 Other"}
ORDER = ["video", "code", "papers", "ai_tools", "docs", "social", "other"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output .md path")
    ap.add_argument("--date", required=True, help="capture date YYYY-MM-DD")
    ap.add_argument("--profiles", default=os.path.expanduser("~/Library/Application Support/zen/Profiles"),
                    help="browser Profiles dir (default: Zen)")
    args = ap.parse_args()

    tabs = collect_tabs(args.profiles)
    if not tabs:
        print("NO_TABS — check the browser profile path / that the browser has run")
        return
    buckets = defaultdict(list); dropped = 0
    for ti, u in tabs:
        c = categorize(ti, u)
        if c is None:
            dropped += 1; continue
        buckets[c].append((ti or u, u))
    total = sum(len(v) for v in buckets.values())

    out = ["---", "tags: [inbox, tabs]", "source: zen-browser",
           f"captured: {args.date}", "status: to-process", "---", "",
           f"# 🗂️ Browser tabs to triage — {args.date}", "",
           f"> {len(tabs)} unique live tabs. {dropped} noise dropped → **{total} to triage**.", "",
           "## Summary"]
    for c in ORDER:
        if buckets.get(c):
            out.append(f"- **{LABELS[c]}** — {len(buckets[c])}")
    out.append("")
    for c in ORDER:
        if not buckets.get(c):
            continue
        out.append(f"## {LABELS[c]} ({len(buckets[c])})")
        for ti, u in buckets[c]:
            clean = re.sub(r"\s+", " ", ti)[:120]
            out.append(f"- [ ] [{clean}]({u})")
        out.append("")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w").write("\n".join(out))
    print(f"wrote {total} tabs ({dropped} dropped) -> {args.out}")


if __name__ == "__main__":
    main()
