# Palettes

Nib's colour grammar is **"colour has a job"** (from the methodology): the base
ink carries the linework and the avatar, and a bright accent is spent only on
the one or two things that matter — **red** for a problem / friction / result,
**orange** for the main flow or path, a calm **blue** for a secondary note or
system state, on the white ground. Rather too few colours than too many.

The grammar is the constant. A **palette** only swaps which exact hues fill those
three jobs — useful when art has to sit next to existing content (a blog, a
brand) without a hard visual break.

## Resolution (first match wins)

1. **Explicit accent** — `--accent "#e0533d"` (or a named hue, "emerald"), or a
   brand hex the user gives. Becomes the *problem/result* red slot; pick a
   complementary flow hue for orange if needed.
2. **Site / brand match** — when illustrating for a known site, read its theme
   tokens (background → the ground if not pure white, body text → base ink,
   link / brand colour → the accent) and use those exact hexes. New art then
   sits beside existing content cleanly. Re-extract if the brand changes.
3. **House default** — black base ink, with red `#e0533d` / orange `#f0853f` /
   blue `#3f6df0` filling the three accent jobs on white.

## Passing it to the engine

Add the resolved hues to the prompt with `--accent`:

```sh
python3 scripts/generate.py --idea "..." --style marker \
  --avatar avatar.png --accent "#1f7a4d" --out out.png
```

`--accent` names the hex for the red/result slot so it doesn't drift to a
generic crayon red; the engine folds a short palette line into the prompt
("use {hex} as the single accent that marks the problem/result; keep the rest
black ink on white"). Keep it to **one** named accent in most images — the
whole point of the grammar is restraint.

## Notes

- Dark-ground looks (chalk, phosphor) carry their own ground and invert the
  grammar (light line on dark); the accent still marks the one thing that
  matters, lifted to read on that ground — see `references/styles.md`.
- Never let a palette become decoration: if every element is coloured, the
  accent has stopped meaning anything. One job, one accent.
