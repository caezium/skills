#!/usr/bin/env python3
"""Make a fast 720p proxy for analysis (pure ffmpeg, no extra deps).

Analyze on the proxy; render the final cut from the original. Audio is kept (analysis
uses it) but downmixed/compressed since only the envelope matters.

    python scripts/proxy.py input.mp4 -o proxy.mp4
"""
import argparse
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", help="default: <input>.proxy.mp4")
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()
    out = args.out or os.path.splitext(args.input)[0] + ".proxy.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", args.input,
           "-vf", f"scale=-2:{args.height}", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-ac", "1", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip()[-400:], file=sys.stderr)
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
