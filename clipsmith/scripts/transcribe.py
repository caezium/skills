#!/usr/bin/env python3
"""Transcribe speech with timestamps — for supercuts, soundbites, and burned captions.

Needs openai-whisper (heavy; install only when a brief needs speech):
    .venv/bin/pip install openai-whisper

    python scripts/transcribe.py talk.mp4 --model base --srt caps.srt
    python scripts/transcribe.py talk.mp4 > segments.json   # {text, segments:[{start,end,text}]}

Use the segments to: find keyword hits (supercut), pick strong quotes (soundbites), or feed
--srt straight to assemble.py --captions.
"""
import argparse
import json
import sys


def to_srt(segments):
    def ts(s):
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s%1)*1000):03d}"
    out = []
    for i, seg in enumerate(segments, 1):
        out.append(f"{i}\n{ts(seg['start'])} --> {ts(seg['end'])}\n{seg['text'].strip()}\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--model", default="base", help="tiny|base|small|medium (bigger=slower/better)")
    ap.add_argument("--srt", help="also write an .srt to this path")
    ap.add_argument("--language", default=None)
    args = ap.parse_args()
    try:
        import whisper
    except ImportError:
        print("openai-whisper not installed:  .venv/bin/pip install openai-whisper",
              file=sys.stderr)
        sys.exit(3)
    model = whisper.load_model(args.model)
    result = model.transcribe(args.media, language=args.language, verbose=False)
    segments = [{"start": round(s["start"], 3), "end": round(s["end"], 3),
                 "text": s["text"].strip()} for s in result.get("segments", [])]
    if args.srt:
        open(args.srt, "w").write(to_srt(segments))
    print(json.dumps({"text": result.get("text", "").strip(), "segments": segments,
                      "srt": args.srt}, indent=2))


if __name__ == "__main__":
    main()
