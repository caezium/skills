---
description: Refresh and validate the installed-skills HTML map; pass "publish" to commit and push only the generated snapshot.
---

# Update Skills Map

Refresh the full-machine installed-skills snapshot and validate the generated
site:

```sh
~/skills/bin/update-skills-map.sh
```

If the user passed the exact argument `publish`, run this instead:

```sh
~/skills/bin/update-skills-map.sh --push
```

Do not stage, commit, or modify unrelated working-tree changes. Report the
number of unique skills, whether any skills landed in `Needs review`, and
whether the snapshot was only generated locally or pushed for deployment.
