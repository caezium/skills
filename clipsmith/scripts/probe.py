#!/usr/bin/env python3
"""Probe media files → compact JSON (duration, fps, resolution, audio). Run this first.

    python scripts/probe.py video1.mp4 video2.mov
"""
import json
import subprocess
import sys


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True)
    if out.returncode != 0:
        return {"path": path, "error": out.stderr.strip()[-300:] or "ffprobe failed"}
    data = json.loads(out.stdout or "{}")
    info = {"path": path, "duration": 0.0, "has_video": False, "has_audio": False,
            "width": 0, "height": 0, "fps": 0.0, "sample_rate": 0, "channels": 0}
    try:
        info["duration"] = round(float(data.get("format", {}).get("duration", 0) or 0), 3)
    except (TypeError, ValueError):
        pass
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and not info["has_video"]:
            info["has_video"] = True
            info["width"] = int(s.get("width", 0) or 0)
            info["height"] = int(s.get("height", 0) or 0)
            info["vcodec"] = s.get("codec_name")
            num, _, den = (s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/0").partition("/")
            try:
                info["fps"] = round(float(num) / float(den), 3) if float(den) else 0.0
            except (ValueError, ZeroDivisionError):
                info["fps"] = 0.0
        elif s.get("codec_type") == "audio" and not info["has_audio"]:
            info["has_audio"] = True
            info["acodec"] = s.get("codec_name")
            info["sample_rate"] = int(s.get("sample_rate", 0) or 0)
            info["channels"] = int(s.get("channels", 0) or 0)
    if info["height"]:
        info["aspect"] = ("vertical" if info["width"] < info["height"]
                          else "square" if info["width"] == info["height"] else "landscape")
    return info


def main():
    if len(sys.argv) < 2:
        print("usage: probe.py FILE [FILE...]", file=sys.stderr)
        sys.exit(2)
    results = [probe(p) for p in sys.argv[1:]]
    print(json.dumps(results if len(results) > 1 else results[0], indent=2))


if __name__ == "__main__":
    main()
