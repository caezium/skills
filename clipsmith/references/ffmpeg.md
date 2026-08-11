# ffmpeg cheat-sheet

For operations the bundled scripts don't cover, compose a step yourself. These are the filters
you'll reach for most. Prefer adding a step to your plan over forcing the brief into a script.

## Trim a single clip
```
ffmpeg -ss 12.0 -t 3.0 -i in.mp4 -c:v libx264 -crf 20 -c:a aac out.mp4
```
`-ss` before `-i` = fast (keyframe) seek; after `-i` = accurate but slower.

## Reframe (already in assemble.py, but for one-offs)
Cover-crop to 9:16 without distortion:
```
-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
```
Off-center crop (subject on the right third): add `crop=1080:1920:x=(iw-1080)*0.66`.
Pad/letterbox instead of crop: `scale=1080:-2,pad=1080:1920:0:(1920-ih)/2`.

## Speed / ramp
```
-vf "setpts=0.5*PTS" -af "atempo=2.0"          # 2x (atempo valid 0.5–2.0; chain for more)
-vf "setpts=2.0*PTS" -af "atempo=0.5"          # 0.5x slow-mo (no audio? drop -af)
```

## Crossfade between two clips (xfade / acrossfade)
```
-filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=<clip0_len-0.5>[v];
                 [0:a][1:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]"
```
For N clips, chain pairwise (xfade result with next clip), accumulating the offset. Hard cuts
(assemble.py's default) are usually better for beat montages; reserve crossfades for slow b-roll.

## Overlay text (no libass needed)
```
-vf "drawtext=text='LAP 12':x=(w-tw)/2:y=h-120:fontsize=64:fontcolor=white:
     box=1:boxcolor=black@0.5:boxborderw=12"
```
Timed: add `:enable='between(t,2,5)'`. For full karaoke/word-by-word, render a transparent
overlay video (Pillow → qtrle) and `overlay` it — heavier; only if drawtext won't do.

## Burn subtitles (needs libass; most ffmpeg builds have it)
```
-vf "subtitles=caps.srt"            # or style: subtitles=caps.srt:force_style='Fontsize=24'
```
assemble.py `--captions` does this. If your ffmpeg lacks libass, fall back to timed drawtext.

## Mix / duck audio
```
# music under voice at -12 dB, summed (not auto-normalized):
-filter_complex "[0:a]volume=0.251[a0];[a0][1:a]amix=inputs=2:normalize=0:duration=first[a]"
```
`volume=` gain is linear; dB→linear = 10^(dB/20) (−12 dB ≈ 0.251, −6 ≈ 0.501, −18 ≈ 0.126).

## Loudness normalize (do once, at the end)
```
-af "loudnorm=I=-14:TP=-1.5:LRA=11"     # ~-14 LUFS = social-platform target
```

## Concat (if not using assemble.py)
Use the concat **filter** for mixed sources (re-decodes, no path issues):
```
-filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]"
```
The concat **demuxer** is faster (stream-copy) but requires identical codecs AND **absolute
paths** in the list file (it resolves relative paths against the list file's own directory).

## Extract a frame to look at
```
ffmpeg -ss 40 -i in.mp4 -frames:v 1 -q:v 3 frame.jpg
```
