# Nib characters

Drop-in characters for Nib. Pick one with `--avatar-pack <name>` and it becomes the
recurring star of your illustrations — no avatar of your own needed.

```sh
python3 skills/nib/scripts/generate.py --avatar-pack blip \
  --idea "small habits compound into a big result" --out out.png
```

## What's here

| pack | who |
| --- | --- |
| `blip`  | a deadpan little ink-drop with a red spark of an idea |
| `pip`   | a round seed sprouting a small idea-leaf |
| `hen`   | a chunky white hen with a red comb |
| `mo`    | a small mole with a red scarf |
| `scout` | an origami paper bird with a red crest |

## Add your own (PRs welcome — this is the whole contribution)

A character is a folder with up to three files:

```
characters/<name>/
  avatar.md      # the spec (below) — required
  reference.png  # one clean, front-facing image of the character on white — required
  preview.png    # optional: one example render of it performing an idea
```

`avatar.md`:

```
# <Name>
**Look:** marker            # default look for this character (optional)
**Aliases:** foo, bar       # extra names that also select this pack (optional)

<One paragraph describing the character's locked design: silhouette, face, colors,
and the ONE accent-carrying part. Describe it by design, not by name — the image
model renders the description, not the proper noun.>
```

Keep it one simple, recognizable character with exactly one accent part. The written
spec is what keeps it on-model, so make it specific. Open a PR adding your folder.
