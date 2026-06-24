---
name: nib
description: >-
  Turns an idea or an article into original white-background, hand-drawn
  editorial illustrations starring a recurring avatar the user owns — one
  caught scene per idea, in one of several print looks. Use when the user asks
  to illustrate a post/article/concept with a consistent character, or invokes
  "nib". Not for generic draw/make-an-image requests.
version: 0.1.1
argument-hint: "[idea or article path/URL] | build a character | set avatar <image> | style <name> | explainer"
license: MIT
metadata:
  category: creative
  requires:
    bins: [python3]
---

# Nib

Make original editorial illustrations for written content. **One image explains
one idea.** A **recurring avatar** — supplied once by the user — is the subject
of every scene and *performs* the idea (pushes, sorts, steers, builds, holds);
it is never decoration. The methodology is the constant; the **avatar** and the
**look** are the parameters.

This is a configurable house style, not a generic image generator. It is
intentionally not a photo, not a logo, not a corporate infographic, not a UI
mockup.

## Setup (once)

1. **A character.** The user's own **avatar image** (a mascot, logo character,
   anything — save its path); a bundled one via `--avatar-pack <name>` (see
   `characters/`); or **build a new one** with the user
   (`references/character-builder.md`). The character is the reference on every
   generation.
2. **A backend** — one of:
   - **Codex (free)** — a logged-in Codex CLI (`codex login`). Generates on the
     user's ChatGPT / Codex subscription, no API key. *Default when no key is set.*
   - **OpenRouter** — an `OPENROUTER_API_KEY` (`sk-or-…`). Exact 16:9, and lets
     you pick the model with `--model`.

## Workflow

1. **Read the input.**
   - A **URL** → fetch the page and extract the readable article text first
     (use your web-fetch / Defuddle capability), then treat it as an article.
   - A single **idea** → one illustration.
   - An **article / post** (or the user's **own draft / notes** they want
     illustrated) → pick the **load-bearing moments** (a judgment, a flow, a
     before/after, a trap, a loop), 4–8 of them. Not one image per paragraph —
     the ones that matter. Treat this set as a **starting point the user
     shapes**: show it first, let them drop moments they don't want, **add
     their own**, or ask for **more candidates**, then illustrate only the
     chosen ones. (The desktop app's Article mode exposes the same controls —
     per-shot select, add-a-shot, "More ideas", and a parallel "Generate".)
2. **Pick a look** for the piece — one of **13** (see `references/styles.md`):
   marker, riso, blueprint, woodcut, pixel, clay, gouache, chalk, diorama,
   enamel, felt, manila, phosphor. One look per piece.
3. For each idea, **invent a fresh, concrete physical metaphor** in which the
   avatar performs the idea (see `references/methodology.md`). One **caught
   scene** is the default; switch to the **explainer** register — a hand-drawn
   sketch-diagram — only when the user asks ("diagram the flow") or the idea is
   itself a traceable structure (`references/composition.md`, `--register explainer`).
4. **Generate** by calling the engine once per image:

   ```sh
   python3 scripts/generate.py \
     --idea "trust is built one piece of evidence at a time" \
     --style marker \
     --avatar /path/to/avatar.png \
     --out ./out/trust.png
   ```

   It builds the full prompt (methodology + look + idea), sends the character as
   the reference for consistency, and writes a 16:9 PNG. Useful flags:
   - `--backend auto|openrouter|codex` — `auto` uses the OpenRouter key if set,
     else the free Codex lane.
   - `--model <id>` — OpenRouter image model (default `google/gemini-3.1-flash-image-preview`).
   - `--avatar-pack <name>` — use a bundled character (see `characters/`) instead
     of `--avatar`.
   - `--avatar-spec "<text>"` — a written description of the character (silhouette,
     face, the one accent part) that locks its design. Combine with the image —
     it markedly improves consistency.
   - `--accent "<hex|name>"` — pin the one accent colour (a brand hex / site
     colour); see `references/palettes.md`.
   - `--register explainer` — draw a hand-built sketch-diagram instead of a single
     caught scene (`references/composition.md`).
   - `--doctor` — print backend readiness (which lane will run, and why) and exit.
5. **Review** against `references/quality-bar.md` (white background, one idea,
   avatar performing the action, short labels only, not a slide). Regenerate
   any that miss.
6. Report each saved path.

## Example prompts

Invoke Nib from your agent like:

- `Use nib to illustrate: "one fish, many dishes"`
- `Use nib to make illustrations for this article: https://jamesclear.com/feedback-loops`
- `Use nib to build a character with me, then illustrate "the information well"`
- `Use nib to diagram the flow of a RAG pipeline (explainer)`
- `Use nib to turn this post into a 5-image set in chalk: <paste a URL or text>`

## Notes

- Keep text in the image short; the model can misspell long labels.
- The avatar is the reference on every call — that is what keeps the character
  consistent across a whole article.
- For options, generate 2–3 variants of a shot (run the engine a few times with
  the same idea) and let the user pick.
- Cost: **free** on the Codex lane (uses the user's ChatGPT / Codex subscription),
  or a few cents per image on OpenRouter (`google/gemini-3.1-flash-image-preview`) —
  a full post is well under a dollar either way. Run `--doctor` to see which lane
  is ready.
- A written **`--avatar-spec`** (describe the character in words) markedly improves
  consistency over the image reference alone — use it whenever you have a description.
- Inspired by [xiaohei (小黑)](https://github.com/helloianneo/ian-xiaohei-illustrations)
  by helloianneo — this methodology is an adaptation of its hand-drawn editorial
  approach, reworded in Nib's own voice.
