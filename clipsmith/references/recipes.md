# clipsmith recipes

Step-by-step pipelines for the common request shapes. These are *starting points* — read the
brief and adapt (different length, aspect, with/without music, etc.). Every recipe ends with the
verify step from SKILL.md; it's omitted below only to avoid repetition. Run scripts with the
skill's `.venv/bin/python`.

## Highlight reel — "best moments from these clips"

1. `probe.py *.mp4` → confirm durations/aspect.
2. For each long/4K source, `proxy.py src -o src.proxy.mp4`; analyze the proxy.
3. `analyze.py SRC --motion --scenes --top 20` per source → candidate peaks.
4. **Look:** `frames.py SRC --from-analysis a.json --contact-sheet sheet.jpg`, Read it, and keep
   the peaks that genuinely look exciting for the brief. This is the step that makes it good.
5. Build a cut list: for each kept peak, a window centered on it (`start = peak - len/2`),
   length ~1.5–3s (shorter = punchier). Order by time or by score; cap total to the target.
6. `assemble.py --cuts cuts.json -o reel.mp4 --orientation <as asked>`.

## Beat-synced montage — "cut these to this song"

1. `analyze.py MUSIC --beats` → beat times + tempo. (Music is just an audio file here.)
2. `analyze.py SRC --motion --scenes` per source → peaks; pick frames and judge as above.
3. Cut list: place clips so each cut **starts on a beat**. Pick a cut length of N beats
   (`--beats-per-cut` feel): faster songs / punchier briefs → 1–2 beats; chill → 4. Each clip's
   window is centered on a good peak.
4. `assemble.py --cuts cuts.json -o reel.mp4 --music MUSIC --mute-source` (music only) or
   `--source-audio-db -12` to keep the footage audio under the track.

## Supercut — "every time they say X"

1. `transcribe.py SRC --srt caps.srt` → segments with timestamps.
2. Search segments for the word/topic (substring or semantic — read the transcript and pick).
3. Cut list: one clip per hit, padded ~0.3s each side, snapped to segment edges so words aren't
   clipped mid-syllable.
4. `assemble.py --cuts cuts.json -o supercut.mp4` (keep source audio — the speech *is* the point).

## Silence removal / jump-cut — "tighten this up / remove the dead air"

1. `analyze.py SRC --silence` → silence spans.
2. Invert: the *keep* segments are the gaps between silences (optionally leave ~0.15s of padding
   so cuts breathe). Merge keep-segments separated by tiny silences.
3. Cut list = the keep segments, in order.
4. `assemble.py --cuts cuts.json -o tight.mp4` (keep source audio). Verify the speech still
   sounds natural — too-aggressive trimming clips breaths and sounds robotic.

## Vertical social reel — "make a TikTok/Reel of the best bit"

1. `analyze.py SRC --motion --scenes`; frames + judge → the single best ~15–30s span.
2. (Optional captions) `transcribe.py SRC --srt caps.srt`.
3. Cut list: usually one clip (the chosen span), or a few quick cuts within it.
4. `assemble.py --cuts cuts.json -o reel.mp4 --orientation vertical --captions caps.srt
   --music MUSIC --source-audio-db -10`.
5. Verify the 9:16 crop kept the subject in frame (look at output frames — the auto crop is
   center-weighted; if the action is off-center you may need a manual crop, see ffmpeg.md).

## Soundbite / talking-head — "pull the good quotes"

1. `transcribe.py SRC --srt caps.srt` → segments.
2. Read the transcript; pick the segments that are strong, self-contained lines.
3. Cut list: in/out on the segment boundaries (a touch of pre-roll so the first word isn't clipped).
4. `assemble.py --cuts cuts.json -o quotes.mp4 --captions caps.srt` (keep source audio).
