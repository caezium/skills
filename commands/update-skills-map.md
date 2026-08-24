---
description: Refresh and validate the installed-skills HTML map without committing or pushing it.
---

# Update Skills Map

Refresh the full-machine installed-skills snapshot and validate the generated
site:

```sh
~/skills/bin/update-skills-map.sh
```

Do not stage, commit, push, or modify unrelated working-tree changes. Report
the number of unique skills, whether any skills landed in `Needs review`, and
the path to the locally generated snapshot so the user can review it.
