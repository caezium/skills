#!/usr/bin/env python3
"""Nib illustration engine.

Generates one white-background editorial illustration in which a recurring avatar
performs the given idea, in a chosen look. No third-party dependencies.

Two backends:
  - codex       Free for ChatGPT / Codex subscribers: drives the logged-in Codex
                CLI's built-in image generation. No API key needed. Aspect ratio
                is best-effort on this lane.
  - openrouter  Any image-output model on OpenRouter (default
                google/gemini-2.5-flash-image), via OPENROUTER_API_KEY. True 16:9.

The backend is chosen automatically: if OPENROUTER_API_KEY is set it is used
(fast, exact 16:9); otherwise the free Codex lane is used if you're logged in.
Force one with --backend.

Usage:
  OPENROUTER_API_KEY=sk-or-... python3 generate.py \
      --idea "trust is built one piece of evidence at a time" \
      --style marker --avatar avatar.png --out out.png

  python3 generate.py --idea "saying no protects the few things that matter" \
      --avatar-pack blip --backend codex --out out.png
"""
import argparse
import base64
import binascii
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-3.1-flash-image-preview")

# The methodology and look library are the single canonical source shared with
# the desktop app — see ../references/style-data.json.
_DATA_PATH = os.path.join(HERE, "..", "references", "style-data.json")
with open(_DATA_PATH, encoding="utf-8") as _f:
    _STYLE_DATA = json.load(_f)
BASE_METHODOLOGY: str = _STYLE_DATA["baseMethodology"]
STYLES: dict[str, str] = {look["id"]: look["look"] for look in _STYLE_DATA["looks"]}
DEFAULT_STYLE: str = _STYLE_DATA["defaultStyleId"]

# Bundled character packs live in the main repo so there's only one repo to share.
CHARACTERS_DIR = os.path.join(HERE, "..", "characters")


def build_prompt(
    idea: str,
    style: str,
    avatar_spec: str = "",
    accent: str = "",
    register: str = "editorial",
) -> str:
    look = STYLES.get(style, STYLES[DEFAULT_STYLE])
    parts = [BASE_METHODOLOGY, f"Look: {look}"]
    if register == "explainer":
        parts.append(
            "Register: EXPLAINER — draw the idea as a hand-built sketch-diagram: "
            "3-6 hand-drawn stations with one clear flow direction, the avatar working "
            "the one key station; a callout or two; no title block, legend, grid, or "
            "corner heading. Still on white, still hand-drawn, still one idea."
        )
    if accent.strip():
        parts.append(
            f"Palette: use {accent.strip()} as the single accent that marks the "
            "problem/result; keep the rest black ink on the white ground. One accent only."
        )
    if avatar_spec.strip():
        parts.append(
            "The recurring character — keep it exactly on-model in shape, color, and "
            f"proportions: {avatar_spec.strip()}"
        )
    parts.append(f"Concept to illustrate: {idea.strip()}")
    return "\n\n".join(parts)


# --- character packs ---------------------------------------------------------

def load_pack(name: str) -> tuple[str | None, str, str | None]:
    """Resolve a character pack in ../characters/<name>/.

    Returns (reference_image_path | None, spec_text, default_look | None).
    `avatar.md` format: a `# Name` heading, optional `**Look:** <id>` and
    `**Aliases:** a, b` lines, then a one-paragraph written design spec.
    """
    pack = os.path.join(CHARACTERS_DIR, name)
    if not os.path.isdir(pack):
        have = ", ".join(sorted(os.listdir(CHARACTERS_DIR))) if os.path.isdir(CHARACTERS_DIR) else "none"
        sys.exit(f"error: no character pack '{name}'. Available: {have}")
    ref = None
    for cand in ("reference.png", "reference.jpg", "reference.jpeg", "reference.webp"):
        p = os.path.join(pack, cand)
        if os.path.exists(p):
            ref = p
            break
    spec, look = "", None
    md = os.path.join(pack, "avatar.md")
    if os.path.exists(md):
        body = []
        for line in open(md, encoding="utf-8"):
            s = line.strip()
            if s.startswith("#"):
                continue
            m = re.match(r"\*\*Look:\*\*\s*([A-Za-z]+)", s)
            if m:
                look = m.group(1).lower()
                continue
            if re.match(r"\*\*Aliases:\*\*", s):
                continue
            body.append(s)
        spec = " ".join(x for x in body if x)
    return ref, spec, look


def avatar_data_url(path: str) -> str:
    with open(path, "rb") as f:
        b = f.read()
    ext = os.path.splitext(path)[1].lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/png")
    return f"data:{mime};base64,{base64.b64encode(b).decode()}"


def extract_image_url(msg: dict) -> str | None:
    """Find the generated image URL in a chat message (images[] or content[])."""
    for part in msg.get("images") or []:
        url = (part.get("image_url") or {}).get("url")
        if url:
            return url
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                url = (part.get("image_url") or {}).get("url")
                if url:
                    return url
    return None


def image_bytes_from_url(url: str) -> bytes:
    if url.startswith("data:"):
        b64 = url.split(",", 1)[1] if "," in url else ""
        return base64.b64decode(b64)
    if url.startswith(("http://", "https://")):
        with urllib.request.urlopen(url, timeout=120) as resp:
            return resp.read()
    return base64.b64decode(url)


def _write(out: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)


# --- backends ----------------------------------------------------------------

def generate_openrouter(prompt: str, avatar: str | None, out: str, model: str) -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        sys.exit("error: --backend openrouter needs OPENROUTER_API_KEY (an sk-or-… key).")
    content = []
    if avatar:
        content.append({"type": "image_url", "image_url": {"url": avatar_data_url(avatar)}})
    content.append({"type": "text", "text": prompt})
    body = {
        "model": model,
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": "16:9"},
        "messages": [{"role": "user", "content": content}],
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/caezium/nib",
            "X-Title": "Nib",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"OpenRouter API error {e.code}: {e.read().decode()[:600]}")
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e.reason}")

    msg = (data.get("choices") or [{}])[0].get("message") or {}
    url = extract_image_url(msg)
    if not url:
        sys.exit("OpenRouter returned no image. Ensure the model supports image output.")
    try:
        image_bytes = image_bytes_from_url(url)
    except urllib.error.URLError as e:
        sys.exit(f"network error fetching the generated image: {e.reason}")
    except (binascii.Error, ValueError) as e:
        sys.exit(f"could not decode the returned image: {e}")
    if not image_bytes:
        sys.exit("OpenRouter returned an empty image.")
    _write(out, image_bytes)
    return out


def _codex_run(args: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(["codex"] + args, capture_output=True, text=True, timeout=8)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception:
        return 1, ""


def _codex_features() -> dict[str, bool]:
    rc, out = _codex_run(["features", "list"])
    low = out.lower()
    return {
        "image_generation": rc == 0 and "image_generation" in low,
        "imagegenext": rc == 0 and "imagegenext" in low,
    }


def codex_available() -> bool:
    """Usable only when the CLI is on PATH, logged in, AND both the image tool and
    the `imagegenext` exec-artifact extension are present — without imagegenext,
    `codex exec` claims success but writes no PNG."""
    if not shutil.which("codex"):
        return False
    rc, out = _codex_run(["login", "status"])
    if rc != 0 or "logged in" not in out.lower():
        return False
    # `image_generation` is the listed capability; `imagegenext` is an
    # under-development feature `features list` doesn't print even though
    # `exec --enable imagegenext` accepts it, so don't require it here. Whether
    # the account is entitled (no HTTP 403) only shows up at render time.
    return _codex_features()["image_generation"]


def generate_codex(prompt: str, avatar: str | None, out: str) -> str:
    """Free lane: ask the logged-in Codex CLI to generate the image, then copy it.

    Codex runs read-only (no shell access — we never give the model file/command
    access, so an idea string can't inject commands). It writes the rendered PNG
    into ~/.codex/generated_images/<session>/; we pick up the new file.
    """
    if not codex_available():
        sys.exit("error: --backend codex needs the Codex CLI. Install it and run `codex login`.")
    gen_root = os.path.expanduser("~/.codex/generated_images")
    pat = os.path.join(gen_root, "**", "*.png")
    before = set(glob.glob(pat, recursive=True)) if os.path.isdir(gen_root) else set()

    workdir = tempfile.mkdtemp(prefix="nib-codex-")
    instruction = (
        prompt
        + "\n\nGenerate exactly ONE image matching the description above, rendered as a "
        "wide 16:9 landscape, using your built-in image generation tool. Do NOT run any "
        "shell commands and do NOT save or copy files yourself — only generate the image."
    )
    # `--enable imagegenext` is required for `codex exec` to emit the generated
    # image artifact (Codex CLI >=0.141); without it Codex may claim it generated
    # an image while no PNG ever appears.
    cmd = ["codex", "exec", "--skip-git-repo-check", "--enable", "imagegenext", "-C", workdir]
    if avatar:
        cmd += ["-i", avatar]
    # Pass the prompt on stdin: `-i` is variadic (<FILE>...) and would otherwise
    # swallow a positional prompt argument as another image file.
    try:
        subprocess.run(cmd, input=instruction.encode(), check=True, timeout=480,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        sys.exit("error: Codex timed out generating the image.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: Codex failed (exit {e.returncode}). Try `codex login`, or use --backend openrouter.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    after = glob.glob(pat, recursive=True) if os.path.isdir(gen_root) else []
    fresh = [p for p in after if p not in before]
    if not fresh:
        sys.exit("error: Codex produced no image (your plan may not include image generation). Use --backend openrouter.")
    newest = max(fresh, key=os.path.getmtime)
    with open(newest, "rb") as f:
        _write(out, f.read())
    return out


def resolve_backend(choice: str) -> str:
    if choice in ("openrouter", "codex"):
        return choice
    # auto: prefer a configured OpenRouter key (fast, exact 16:9); else the free Codex sub.
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        return "openrouter"
    if codex_available():
        return "codex"
    sys.exit("error: no backend available — set OPENROUTER_API_KEY, or install Codex and run `codex login` for the free lane.")


def doctor() -> None:
    """Report backend readiness — what the engine can generate on, and why."""
    print("Nib doctor — backend readiness\n")
    codex = shutil.which("codex")
    print(f"  codex CLI:          {('found: ' + codex) if codex else 'not found'}")
    if codex:
        rc, out = _codex_run(["login", "status"])
        logged = rc == 0 and "logged in" in out.lower()
        print(f"  codex login:        {'logged in' if logged else 'NOT logged in — run `codex login`'}")
        f = _codex_features()
        print(f"  image_generation:   {'yes' if f['image_generation'] else 'no'}")
        print(f"  imagegenext:        {'yes' if f['imagegenext'] else 'no — exec emits no image without it'}")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    print(f"  OPENROUTER_API_KEY: {'set' if key else 'not set'}")
    print(f"  default model:      {DEFAULT_MODEL}")
    chars = sorted(os.listdir(CHARACTERS_DIR)) if os.path.isdir(CHARACTERS_DIR) else []
    print(f"  bundled characters: {', '.join(chars) if chars else 'none'}")
    print(f"  looks ({len(STYLES)}):          {', '.join(STYLES)}")
    print()
    if key:
        print("  -> auto resolves to: openrouter (exact 16:9)")
    elif codex_available():
        print("  -> auto resolves to: codex (free, on your Codex subscription)")
    else:
        print("  -> auto: no usable backend — set OPENROUTER_API_KEY, or `codex login` + enable image generation")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a Nib illustration.")
    p.add_argument("--idea", help="the idea to illustrate (one sentence)")
    p.add_argument("--style", default=None, choices=list(STYLES), help="look (default: marker, or the pack's)")
    p.add_argument("--avatar", help="path to the avatar/reference image")
    p.add_argument("--avatar-spec", default="", help="a written description of your character, to lock its design")
    p.add_argument("--avatar-pack", help="use a bundled character from ../characters/<name>")
    p.add_argument("--accent", default="", help="hex or named accent colour (the one problem/result accent)")
    p.add_argument("--register", default="editorial", choices=["editorial", "explainer"],
                   help="editorial scene (default) or explainer sketch-diagram")
    p.add_argument("--out", help="output PNG path")
    p.add_argument("--backend", default="auto", choices=["auto", "openrouter", "codex"],
                   help="auto (default), openrouter (your API key), or codex (your ChatGPT sub — free)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter image model (openrouter backend only)")
    p.add_argument("--doctor", action="store_true", help="report backend readiness and exit")
    args = p.parse_args()

    if args.doctor:
        doctor()
        return
    if not args.idea or not args.out:
        p.error("--idea and --out are required (unless --doctor)")

    avatar, avatar_spec, pack_look = args.avatar, args.avatar_spec, None
    if args.avatar_pack:
        pack_ref, pack_spec, pack_look = load_pack(args.avatar_pack)
        avatar = avatar or pack_ref
        avatar_spec = avatar_spec or pack_spec
    style = args.style or pack_look or DEFAULT_STYLE
    if style not in STYLES:
        sys.exit(f"error: unknown style '{style}'. Choices: {', '.join(STYLES)}")

    prompt = build_prompt(args.idea, style, avatar_spec, args.accent, args.register)
    backend = resolve_backend(args.backend)
    if backend == "codex":
        print(generate_codex(prompt, avatar, args.out))
    else:
        print(generate_openrouter(prompt, avatar, args.out, args.model))


if __name__ == "__main__":
    main()
