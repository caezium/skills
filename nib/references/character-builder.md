# Character builder

Design a user's own recurring avatar and save it as a reusable character. The
goal is **one simple, recognizable character with exactly one accent part** — the
same acceptance criteria as the bundled packs in `characters/`. A build costs a
few renders (cents each on OpenRouter, free on the Codex lane); say so before
generating.

## 1. Interview — one short round (≤4 questions)

Ask only what changes the design; skip anything the context already answered:

- **What is it?** An object or creature from the user's domain, product, or brand
  (a teapot, a terminal cursor, a fox, a chicken). Push toward one simple
  silhouette — a shape you'd recognize as a solid black blob.
- **What look?** One look from the library for the model sheet and every scene:
  marker (default), riso, blueprint, woodcut, pixel, clay, gouache, manila,
  chalk, phosphor, enamel, felt, or diorama.
- **Where's the accent?** The ONE small part that carries a colour accent in
  every image (a comb, a scarf, a tail-tip, a spark above the head). Exactly one.
- **A name?** Optional — the best names read off the design. If the name doesn't
  read off the subject (an ox named "yoke"), ask for **aliases** ("ox", "zebu")
  so "use ox" resolves to the character later.

The **face is not an interview question.** Default to the house face — two dot
eyes, blank deadpan, no mouth — it's the most render-stable choice. Honour a
request for something else, but say the trade-off out loud: more facial detail
means more drift and harder consistency.

If the user **already has art** (a mascot drawing, a logo, a sketch), use it —
pass it as `--avatar` in step 3 so candidates stay close to the original while
the look translates it into the hand line.

## 2. Pressure-test before rendering

Push back early on anything that will not stay on-model:

- A concept that needs text or many distinctive parts to read as itself will
  drift — simplify to the one silhouette + one accent.
- More than one accent part splits attention and breaks the colour grammar
  (accent = the one thing that matters). Cut to one.
- Fine internal detail (filigree, gears, many limbs) won't survive regeneration.
  Keep limbs few and stubby and joined cleanly to the body.

## 3. Render the model sheet

Generate a **front-facing reference on white** — the character alone, no scene —
in the chosen look:

```sh
python3 scripts/generate.py \
  --idea "<the character> standing front-facing, full body, neutral, on plain white — a clean character reference sheet" \
  --style <look> --avatar <existing-art-if-any> --out ./mychar/reference.png
```

Show 2–3 candidates; let the user pick the cleanest silhouette. Re-roll, don't
edit, if one drifts.

## 4. Write the spec and save the pack

Write the locked design as a short paragraph — **by design, not by name** (the
model renders the description, not the proper noun). Save it next to the
reference so it's reusable and shareable:

```
characters/<name>/
  avatar.md      # see below — required
  reference.png  # the chosen model sheet — required
```

`avatar.md`:

```
# <Name>
**Look:** <look>            # optional default look
**Aliases:** foo, bar       # optional extra names that select this character

<One paragraph: silhouette, face, colours, and the ONE accent part. Describe it
by design. e.g. "A round, chunky white hen with a small red comb on top, two
black dot eyes and stubby wings — keep the red comb as the one accent.">
```

From then on, generate with `--avatar-pack <name>` (engine) or pick it in the
desktop app's avatar setup. The written spec is what holds the character on-model
across a whole article — always pass it, not just the image.
