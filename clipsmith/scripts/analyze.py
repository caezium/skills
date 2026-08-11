#!/usr/bin/env python3
"""Analyze a video for editable structure: a per-second interest score + peaks, plus
optional beat grid, scene cuts, and silence spans. Caches to a sidecar so re-running is free.

    python scripts/analyze.py clip.mp4 --scenes --motion --beats --silence
    python scripts/analyze.py clip.mp4 --top 20            # just the score peaks

Output JSON:
  { "duration", "score": {"hop","times","values"}, "peaks":[{"t","score"}],
    "beats":[...], "tempo", "scenes":[t,...], "silences":[{"start","end"}] }

"Interest" = audio energy + onset + brightness, frame motion, and a scene-cut bonus — it finds
ACTIVITY, not necessarily what's interesting. Use frames.py + your own eyes to judge the peaks.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HOP = 0.5          # seconds between score samples
MOTION_FPS = 4.0
AUDIO_SR = 22050


def _sidecar(path):
    return os.path.splitext(path)[0] + ".clipsmith.json"


def _extract_audio(src, sr):
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-ar", str(sr),
                    "-ac", "1", wav], check=False)
    return wav if os.path.exists(wav) else None


def _norm(x):
    x = np.asarray(x, float)
    if x.size == 0:
        return x
    lo, hi = np.percentile(x, 5), np.percentile(x, 95)
    return np.clip((x - lo) / (hi - lo), 0, 1) if hi - lo > 1e-9 else np.zeros_like(x)


def _audio_signals(src, grid, want_beats, want_silence):
    import librosa
    wav = _extract_audio(src, AUDIO_SR)
    out = {"score": np.zeros_like(grid)}
    if not wav:
        return out
    y, sr = librosa.load(wav, sr=AUDIO_SR, mono=True)
    os.remove(wav)
    if y.size == 0:
        return out
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    n = min(len(rms), len(onset), len(centroid))
    t = librosa.frames_to_time(np.arange(n), sr=sr, hop_length=hop)
    combined = 0.5 * _norm(rms[:n]) + 0.3 * _norm(onset[:n]) + 0.2 * _norm(centroid[:n])
    out["score"] = np.interp(grid, t, combined, left=combined[0], right=combined[-1])
    if want_beats:
        tempo, beat_f = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        out["beats"] = [round(float(b), 3) for b in librosa.frames_to_time(beat_f, sr=sr)]
        out["tempo"] = round(float(np.atleast_1d(tempo)[0]), 2)
    if want_silence:
        # frames at least 20 dB below the track's median, ≥0.3s long
        db = librosa.amplitude_to_db(rms[:n], ref=np.median(rms[:n]) + 1e-9)
        quiet = db < -20
        sils, run = [], None
        for i, q in enumerate(quiet):
            if q and run is None:
                run = t[i]
            elif not q and run is not None:
                if t[i] - run >= 0.3:
                    sils.append({"start": round(run, 3), "end": round(float(t[i]), 3)})
                run = None
        if run is not None and t[-1] - run >= 0.3:
            sils.append({"start": round(run, 3), "end": round(float(t[-1]), 3)})
        out["silences"] = sils
    return out


def _motion(src, grid):
    import cv2
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return np.zeros_like(grid)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps / MOTION_FPS)))
    times, motion, prev, idx = [], [], None, 0
    while True:
        if not cap.grab():
            break
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            g = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 90))
            if prev is not None:
                motion.append(float(np.mean(np.abs(g.astype(np.int16) - prev.astype(np.int16)))))
                times.append(idx / fps)
            prev = g
        idx += 1
    cap.release()
    if not times:
        return np.zeros_like(grid)
    return np.interp(grid, np.array(times), _norm(motion), left=0, right=0)


def _scenes(src):
    try:
        from scenedetect import detect, ContentDetector
        return [round(s.get_seconds(), 3) for s, _ in detect(src, ContentDetector())]
    except Exception:
        return []


def analyze(path, args):
    info = _probe_inline(path)
    dur = info.get("duration", 0.0)
    if dur <= 0:
        return {"path": path, "error": "no duration / unreadable"}
    grid = np.arange(0.0, dur, HOP)
    asig = _audio_signals(path, grid, args.beats, args.silence) if info.get("has_audio") else {"score": np.zeros_like(grid)}
    score = asig["score"].copy()
    weights = 1.0
    if args.motion and info.get("has_video"):
        score = score + _motion(path, grid)
        weights += 1.0
    scenes = _scenes(path) if args.scenes and info.get("has_video") else []
    if scenes:
        bonus = np.zeros_like(grid)
        for ts in scenes:
            decay = np.exp(-np.maximum(0.0, grid - ts) / 0.7)
            decay[grid < ts] = 0.0
            bonus = np.maximum(bonus, decay)
        score = score + 0.5 * bonus
        weights += 0.5
    score = score / weights
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(score, distance=max(1, int(round(1.0 / HOP))), prominence=0.05)
    if peaks.size == 0 and score.size:
        peaks = np.array([int(np.argmax(score))])
    guard = 0.4
    peak_list = sorted(
        [{"t": round(float(grid[p]), 2), "score": round(float(score[p]), 3)}
         for p in peaks if guard < grid[p] < dur - guard],
        key=lambda d: d["score"], reverse=True)
    result = {
        "path": path, "duration": round(dur, 3),
        "score": {"hop": HOP, "times": [round(float(t), 2) for t in grid],
                  "values": [round(float(v), 3) for v in score]},
        "peaks": peak_list[:args.top],
    }
    if "beats" in asig:
        result["beats"] = asig["beats"]
        result["tempo"] = asig.get("tempo")
    if scenes:
        result["scenes"] = scenes
    if "silences" in asig:
        result["silences"] = asig["silences"]
    return result


def _probe_inline(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json",
                          "-show_format", "-show_streams", path], capture_output=True, text=True)
    data = json.loads(out.stdout or "{}")
    info = {"duration": 0.0, "has_video": False, "has_audio": False}
    try:
        info["duration"] = float(data.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        pass
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            info["has_video"] = True
        elif s.get("codec_type") == "audio":
            info["has_audio"] = True
    return info


def main():
    ap = argparse.ArgumentParser(description="Analyze a video for editable structure.")
    ap.add_argument("video")
    ap.add_argument("--scenes", action="store_true", help="detect scene-cut times")
    ap.add_argument("--motion", action="store_true", help="add frame-motion to the score")
    ap.add_argument("--beats", action="store_true", help="beat-track the audio (for montages)")
    ap.add_argument("--silence", action="store_true", help="detect silence spans (for jump-cuts)")
    ap.add_argument("--top", type=int, default=20, help="how many score peaks to return")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()
    if not (args.scenes or args.motion or args.beats or args.silence):
        args.motion = True  # sensible default: audio + motion
    sc = _sidecar(args.video)
    key = f"{os.path.getmtime(args.video)}|{args.scenes}{args.motion}{args.beats}{args.silence}{args.top}"
    if not args.no_cache and os.path.exists(sc):
        try:
            cached = json.load(open(sc))
            if cached.get("_key") == key:
                print(json.dumps(cached, indent=2))
                return
        except Exception:
            pass
    result = analyze(args.video, args)
    result["_key"] = key
    if not args.no_cache:
        json.dump(result, open(sc, "w"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
