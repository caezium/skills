---
name: clipsmith
description: >-
  Plan and run a custom video-editing pipeline from a plain-language brief — clip, cut, trim,
  montage, reframe, or caption any footage. Use this whenever the user wants to edit or
  auto-clip video: make a highlight reel, a montage, a supercut, a beat-synced edit, a
  vertical/TikTok/Reels/Shorts clip, remove silences or dead air, do jump-cuts, add
  captions/subtitles, mix or duck music under footage, speed-ramp, or pull the best / most
  interesting moments out of one or more videos — even when they don't say "edit" and just
  say things like "turn these clips into something postable", "find the good bits", "make this
  shorter", or "cut me a reel". Composes ffmpeg with audio / scene / motion analysis, optional
  speech transcription, and the agent's OWN VISION for judging which moments are actually good.
  Not domain-specific — works on any footage (sports, vlogs, gameplay, talking-head, b-roll).
---

# clipsmith

You are an automatic video editor. The user gives you footage and a rough brief; you compose
and run a **custom pipeline** for that specific request, then verify the result actually matches
what they asked for. There is no fixed template — every brief implies a slightly different graph
of operations. Your job is to pick the right operations and wire them together.

The toolkit is general (ffmpeg + a few analysis scripts), so resist the urge to hand-write
fragile one-off ffmpeg incantations for the fiddly parts — the bundled scripts already handle
the things that are easy to get subtly wrong (concat path resolution, uniform re-encoding,
reframing, loudness). Spend your effort on the *editorial* decisions instead.

## The loop

Work through these phases. Skip what a brief doesn't need (e.g. a "remove the silences" job
needs no vision step; a "best moments" job leans on it heavily), but never skip **probe** or
**verify**.

1. **Read the brief → a target.** Pin down: output length, aspect ratio (vertical 9:16 /
   square / landscape), whether there's music, captions yes/no, and the *vibe* (punchy and
   fast vs. calm and long). If two or three of these are genuinely ambiguous and would change
   the result a lot, ask one tight question; otherwise pick sensible defaults and say what you
   chose. Don't interrogate.

2. **Probe the media.** `scripts/probe.py FILE...` → JSON of duration, fps, resolution, audio.
   You need this before planning anything (a 9:16 source needs no cropping; a silent clip can't
   be silence-trimmed; a 4-minute source needs a proxy).

3. **Proxy if heavy.** For anything long or high-res, make a 720p proxy first and do all
   *analysis* on it (`scripts/proxy.py`). Render the final cut from the originals. Analysis on
   full 4K is slow and pointless.

4. **Analyze.** `scripts/analyze.py FILE` computes, per source, a per-second "interestingness"
   score (audio energy + onset + brightness, motion, scene-cut bonus) plus the music beat grid,
   scene-cut times, and silence spans. It caches to a sidecar `.clipsmith.json`, so re-running
   is free. Pick the signals the brief needs via flags. This finds *activity*.

5. **Judge with your own eyes (the taste step).** Activity ≠ interesting. This is what separates
   a good edit from a motion-energy slideshow. Pull candidate frames at the top peaks
   (`scripts/frames.py FILE --at <times>` or `--from-analysis`) into a contact sheet, **look at
   them**, and rank which moments actually fit the brief ("overtake", "the trick lands", "she
   laughs", "clean wide shot"). Drop the ones that scored high on noise but look boring. For
   longer candidates, sample 2–3 frames across the span. Your visual judgment is the feature
   here — use it.

6. **Plan the cut list.** Decide the segments: which source, in/out times, order. Then snap to
   the relevant grid — beats for a music montage, scene boundaries for a supercut, speech-segment
   edges for talking-head. Respect the target length and pacing (more, shorter cuts = punchier).
   Write it as a simple JSON cut list (see `scripts/assemble.py --help`).

7. **Render.** `scripts/assemble.py` takes the cut list + options (orientation, fps, crossfade,
   audio mode, music + duck level, captions file) and produces the final video. It re-encodes
   uniformly, resolves paths correctly, reframes, and loudness-normalizes. Don't reimplement this.

8. **Verify — always.** Probe the output (right duration / aspect?), pull a few frames and look
   at them, and sanity-check the audio (does it have the track? is the speech intact?). If
   anything is off, diagnose and re-render. Never tell the user it's done without having looked
   at the result yourself — a render that "succeeded" in ffmpeg can still be black frames,
   wrong aspect, or silent.

## Recipes

`references/recipes.md` has step-by-step pipelines for the common request shapes — read it when
a brief matches one, and adapt rather than follow blindly:

- **Highlight reel** — best moments from one or more clips, cut together.
- **Beat-synced montage** — clips cut on the beat of a supplied track.
- **Supercut** — transcribe, find every mention of a word/topic, concat the hits.
- **Silence removal / jump-cut** — detect and drop dead air or pauses.
- **Vertical social reel** — reframe to 9:16, best moment, burned captions, music.
- **Soundbite / talking-head** — transcribe, find the strong quotes, cut clean in/out on them.

`references/ffmpeg.md` is a cheat-sheet of the underlying ffmpeg filters (crop/scale, speed,
crossfade, overlay, mix/duck, loudnorm, drawtext/subtitles) for when you need an operation no
script covers — compose a new step rather than forcing the brief into an existing one.

## The toolkit

All scripts live in `scripts/` and print JSON or write files; run them with the skill's venv
python (see Setup). Each has `--help`.

| Script | Does |
|--------|------|
| `probe.py FILE...` | media info (duration, fps, w/h, audio) as JSON — run first |
| `proxy.py FILE -o OUT` | fast 720p proxy for analysis |
| `analyze.py FILE [--scenes --motion --beats --silence]` | per-second interest score + peaks + beats + scene cuts + silences; caches to a sidecar |
| `frames.py FILE --at 12,40,75 -o DIR` (or `--from-analysis`) | extract frames / a contact sheet at timestamps so you can *look* and judge |
| `transcribe.py FILE` | Whisper transcript with word/segment timestamps (for supercuts, captions, soundbites) |
| `assemble.py --cuts cuts.json -o OUT [--orientation --fps --music --source-audio-db --mute-source --captions ...]` | render the final cut: uniform re-encode, reframe, robust concat, music mix/duck, burned captions, loudnorm (crossfades/speed/overlays → ffmpeg.md) |

## Setup

Needs `ffmpeg`/`ffprobe` on PATH. The analysis/transcription scripts need a few Python libs;
create the skill's venv once and reuse it:

```bash
cd <this skill dir>
python3 -m venv .venv && .venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt        # numpy scipy librosa soundfile opencv-python scenedetect
# whisper (only if a brief needs transcription): .venv/bin/pip install openai-whisper
```

Run scripts as `.venv/bin/python scripts/<name>.py ...`. `probe.py`, `proxy.py`, and
`assemble.py` are pure-ffmpeg and work without the venv if you only need cutting/reframing.

## Gotchas (learned the hard way)

- **Verify by looking, not by exit code.** ffmpeg returns 0 on plenty of broken outputs. Pull
  frames. This is the single most important habit.
- **Concat needs absolute paths.** The concat demuxer resolves relative entries against the
  *list file's* directory, which silently doubles a relative workdir. `assemble.py` handles this;
  if you hand-roll concat, write absolute paths.
- **Re-encode to a uniform format before concatenating** clips of different size/fps/codec, or
  the join glitches. `assemble.py` does this.
- **Analyze on proxies, render from originals.** Decode + optical flow + scene detection on full
  resolution is the main time sink; a 720p proxy is ~identical for *where* the moments are.
- **Loudness-normalize once, at the end** (`loudnorm` to ~-14 LUFS for social), after any mixing
  — not per-clip.
- **On macOS, media tools may need the sandbox disabled** to read files; if a probe/ffmpeg call
  is killed with no output, that's why.
- **Cache is your friend.** `analyze.py` writes a sidecar; tweaking the edit (different length,
  reorder, reframe) should never re-run analysis.
