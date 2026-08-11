#!/usr/bin/env python3
"""Extract frames at timestamps so you (the agent) can LOOK and judge which moments are good.

This is the taste step. After analyze.py finds candidate peaks, pull frames here and Read them
to decide which actually fit the brief — detection finds activity, your eyes find "interesting".

    # individual frames at explicit times (Read them one by one):
    python scripts/frames.py clip.mp4 --at 12,40,75 -o frames/
    # frames at every peak from an analyze.py JSON:
    python scripts/analyze.py clip.mp4 --top 15 > a.json
    python scripts/frames.py clip.mp4 --from-analysis a.json -o frames/
    # one tiled+labeled contact sheet (fewer Reads; needs Pillow):
    python scripts/frames.py clip.mp4 --at 12,40,75 --contact-sheet sheet.jpg

Frames are named t<seconds>.jpg so the timestamp is visible without opening them.
"""
import argparse
import json
import math
import os
import subprocess
import sys


def grab(src, t, out, width=480):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", src,
                    "-frames:v", "1", "-q:v", "3", "-vf", f"scale={width}:-2", out], check=False)
    return out if os.path.exists(out) else None


def make_contact_sheet(frame_paths, times, out):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    imgs = [Image.open(p).convert("RGB") for p in frame_paths]
    if not imgs:
        return None
    cw, ch = imgs[0].size
    cols = min(4, len(imgs))
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * cw, rows * ch), (16, 16, 16))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    for i, (im, t) in enumerate(zip(imgs, times)):
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.paste(im.resize((cw, ch)), (x, y))
        label = f"{t:.1f}s"
        draw.rectangle([x + 4, y + 4, x + 12 + draw.textlength(label, font=font), y + 32],
                       fill=(0, 0, 0))
        draw.text((x + 8, y + 6), label, fill=(255, 255, 255), font=font)
    sheet.save(out, quality=85)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--at", help="comma-separated timestamps in seconds, e.g. 12,40,75")
    ap.add_argument("--from-analysis", help="analyze.py JSON file; uses its peak times")
    ap.add_argument("-o", "--out-dir", default="clipsmith_frames")
    ap.add_argument("--contact-sheet", help="write a single tiled+labeled JPG here (needs Pillow)")
    ap.add_argument("--width", type=int, default=480)
    args = ap.parse_args()

    times = []
    if args.at:
        times = [float(x) for x in args.at.split(",") if x.strip()]
    elif args.from_analysis:
        times = [p["t"] for p in json.load(open(args.from_analysis)).get("peaks", [])]
    if not times:
        print("no timestamps (use --at or --from-analysis)", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=True)
    written = []
    for t in times:
        p = grab(args.video, t, os.path.join(args.out_dir, f"t{t:07.2f}.jpg"), args.width)
        if p:
            written.append(p)

    if args.contact_sheet:
        sheet = make_contact_sheet(written, times, args.contact_sheet)
        if sheet:
            print(json.dumps({"contact_sheet": sheet, "frames": written}, indent=2))
            return
        print("(Pillow not available — wrote individual frames instead)", file=sys.stderr)
    print(json.dumps({"frames": written, "dir": args.out_dir}, indent=2))


if __name__ == "__main__":
    main()
