#!/usr/bin/env python3
"""Render a cut list into the final video. The render workhorse — don't hand-roll this.

It builds one ffmpeg filtergraph that trims each segment from its source, reframes to a
uniform size (so mixed sources join cleanly), concatenates, optionally burns captions and
mixes/ducks a music bed, then loudness-normalizes. No temp files, no concat-demuxer path bugs.

Cut list JSON (file via --cuts, or stdin with --cuts -):
    {"clips": [{"src": "/abs/a.mp4", "start": 12.0, "dur": 3.0},
               {"src": "/abs/b.mp4", "start": 5.5,  "dur": 2.0}]}
(a bare list is also accepted; "in"/"out" may be used instead of start/dur)

    python scripts/assemble.py --cuts cuts.json -o reel.mp4 \
        --orientation vertical --music song.wav --source-audio-db -12 --captions caps.srt

Audio: by default each clip keeps its own audio. With --music, the track is the bed and the
source audio is mixed under it at --source-audio-db (use --mute-source for music-only, or
--mute for silent).
"""
import argparse
import json
import os
import subprocess
import sys

ORIENT = {"vertical": (1080, 1920), "square": (1080, 1080), "landscape": (1920, 1080)}


def probe_has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                        "stream=index", "-of", "csv=p=0", path], capture_output=True, text=True)
    return bool(r.stdout.strip())


def load_cuts(spec):
    raw = sys.stdin.read() if spec == "-" else open(spec).read()
    data = json.loads(raw)
    clips = data["clips"] if isinstance(data, dict) else data
    norm = []
    for c in clips:
        src = c["src"]
        start = float(c.get("start", c.get("in", 0.0)))
        if "dur" in c:
            dur = float(c["dur"])
        elif "out" in c:
            dur = float(c["out"]) - start
        else:
            raise ValueError(f"clip needs dur or out: {c}")
        norm.append({"src": os.path.abspath(src), "start": start, "dur": round(dur, 3)})
    return norm


def build(clips, args):
    w, h = (ORIENT[args.orientation] if args.orientation in ORIENT
            else (args.width, args.height) if args.width and args.height else (None, None))
    fps = args.fps
    want_src_audio = not args.mute and not args.mute_source
    inputs, fc = [], []
    for i, c in enumerate(clips):
        inputs += ["-ss", f"{c['start']:.3f}", "-t", f"{c['dur']:.3f}", "-i", c["src"]]
        vf = f"[{i}:v]"
        if w and h:
            vf += (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                   f"crop={w}:{h},setsar=1,")
        vf += f"fps={fps},format=yuv420p[v{i}]"
        fc.append(vf)
        if want_src_audio:
            if probe_has_audio(c["src"]):
                fc.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
            else:
                fc.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={c['dur']:.3f}[a{i}]")

    # concat filter reads pads per-segment in order: v0,a0,v1,a1,... (interleaved, not grouped)
    if want_src_audio:
        maps = "".join(f"[v{i}][a{i}]" for i in range(len(clips)))
        fc.append(f"{maps}concat=n={len(clips)}:v=1:a=1[vc][srcaud]")
    else:
        maps = "".join(f"[v{i}]" for i in range(len(clips)))
        fc.append(f"{maps}concat=n={len(clips)}:v=1[vc]")

    # captions burned over the concatenated video
    vlabel = "vc"
    if args.captions:
        sub = os.path.abspath(args.captions).replace(":", r"\:").replace("'", r"\'")
        fc.append(f"[vc]subtitles='{sub}'[vcap]")
        vlabel = "vcap"

    # audio chain
    music_idx = None
    if args.music:
        music_idx = len(clips)
        inputs += ["-i", os.path.abspath(args.music)]

    alabel = None
    if args.mute:
        alabel = None
    elif args.music and args.mute_source:
        fc.append(f"[{music_idx}:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        alabel = "aout"
    elif args.music:
        g = 10.0 ** (args.source_audio_db / 20.0)
        fc.append(f"[srcaud]volume={g:.4f}[srcd]")
        fc.append(f"[srcd][{music_idx}:a]amix=inputs=2:normalize=0:duration=first[mx]")
        fc.append(f"[mx]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        alabel = "aout"
    else:  # source audio only
        if args.loudnorm:
            fc.append(f"[srcaud]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
            alabel = "aout"
        else:
            alabel = "srcaud"

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
           "-map", f"[{vlabel}]"]
    if alabel:
        cmd += ["-map", f"[{alabel}]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(fps)]
    if args.music:
        cmd += ["-shortest"]
    cmd += [args.out]
    return cmd


def main():
    ap = argparse.ArgumentParser(description="Render a cut list into the final video.")
    ap.add_argument("--cuts", required=True, help="cut-list JSON file, or - for stdin")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--orientation", default="keep",
                    choices=["keep", "vertical", "square", "landscape"])
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--music", help="music bed (becomes the soundtrack)")
    ap.add_argument("--source-audio-db", type=float, default=-12.0,
                    help="source-audio level under the music (dB); default -12")
    ap.add_argument("--mute-source", action="store_true", help="music only, drop source audio")
    ap.add_argument("--mute", action="store_true", help="no audio at all")
    ap.add_argument("--captions", help="burn a .srt/.ass subtitle file over the video")
    ap.add_argument("--no-loudnorm", dest="loudnorm", action="store_false")
    args = ap.parse_args()

    clips = load_cuts(args.cuts)
    if not clips:
        print("empty cut list", file=sys.stderr)
        sys.exit(2)
    cmd = build(clips, args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg failed:\n" + " ".join(cmd) + "\n\n" + r.stderr.strip()[-800:],
              file=sys.stderr)
        sys.exit(1)
    total = round(sum(c["dur"] for c in clips), 2)
    print(json.dumps({"out": args.out, "clips": len(clips), "cut_duration": total}, indent=2))


if __name__ == "__main__":
    main()
