---
name: prune
description: Audit a codebase for dead code, duplication, unused dependencies, and cruft, then safely remove what no longer earns its place. Evidence-based (runs real dead-code analyzers, not vibes), confidence-tiered, and verification-gated. Use when the user wants to clean up / declutter / simplify a codebase, find dead or unused code, kill tech debt, shrink the bundle, remove unused dependencies, or says "prune", "what can we delete", "find dead code", "what should never have been here".
---

# Prune

Find what no longer earns its place in the codebase — dead code, duplicate logic, unused dependencies, abandoned files, needless complexity — and remove it safely.

Code is a liability, not an asset. Features ship in an hour; the cruft they leave behind is paid for every day after in slower builds, harder reading, and bugs hiding in code nobody uses. Pruning is gardening, not demolition: it is meant to be **run periodically**, and it composes with the rest of your workflow (`/simplify` for changed-diff cleanups, `/code-review` for bugs, `improve-codebase-architecture` for structure).

## Core principles

These are what separate this from "ask an LLM to find dead code" — honour them or the audit is worse than useless:

1. **Evidence over vibes.** Never assert "this is unused" from reading alone — LLMs miss dynamic references constantly. Prove it with a tool *and* a repo-wide reference search before flagging.
2. **Confidence-tiered, not "aggressive."** Every finding gets High / Medium / Low. Only **High** is removable without further checks. "Aggressive but safe" is a contradiction; tiers resolve it.
3. **Report before remove.** Default output is a report. Deletion happens only on explicit go-ahead.
4. **Verify every removal.** Re-run build + tests + typecheck after each batch. Green → commit. Red → revert that batch and downgrade the finding. The compiler/test suite is the source of truth, not your confidence.
5. **Smallest reversible steps.** Leaves before roots, one concern per commit. A pruning PR that can't be bisected isn't safe.

## Process

### 1. Scope & map the protected ground

- **Pick a scope.** Whole repo (default), a sub-path, or changed-since-a-ref (`git diff <ref>`). For a repeat run, scope tight — the author of this technique notes it's meant to be re-run, not run once over everything every time.
- **Detect the stack**: languages, package manager, build/test/typecheck commands (read `package.json` scripts, `Makefile`, `pyproject.toml`, `Cargo.toml`, CI config — don't assume).
- **Map what NOT to touch** before looking for anything to cut. Locate entry points, the public/exported API surface, and protected directories (generated code, vendored deps, migrations). See [REFERENCE.md](REFERENCE.md) § "Protected by default". Flagging these is the fastest way to lose trust.

### 2. Gather evidence (run the tools)

Run the language-appropriate analyzers from [REFERENCE.md](REFERENCE.md) § "Detection toolbox" — `knip` / `ts-prune` / `depcheck` for JS/TS, `vulture` / `deptry` / `ruff` for Python, `deadcode` / `staticcheck` for Go, `cargo-machete` / `udeps` for Rust, etc. If a tool isn't installed, prefer a one-shot runner (`npx`, `uvx`) over skipping; fall back to the ripgrep reference-counting recipe if nothing is available.

For each candidate the tools surface, gather corroborating evidence:
- **Reference count** across *all* files — code, configs, templates, JSON, HTML, docs — not just source (the recipe is in REFERENCE.md). Dead-by-tool + zero-references is the strong signal.
- **Git recency** (`git log -1 --format=%cr -- <file>`) for "abandoned file" candidates.

This populates the eight categories below with **evidence**, not guesses.

### 3. Rule out false positives

For every candidate, walk the [REFERENCE.md](REFERENCE.md) § "False-positive catalog" and try to find a path by which it's actually *alive*: dynamic dispatch / reflection / string-keyed registries, DI containers, framework-by-convention entry points (routes, pages, fixtures), public API consumed by other repos, build/CLI entry points, test-only helpers, feature-flagged or env-gated paths, generated code, serialization targets, i18n keys, CSS classes in templates.

If a plausible "actually alive" path survives, **drop the candidate or downgrade its confidence**. This step is the whole game — it's what makes pruning safe.

### 4. Score & report — then stop

Assign each surviving finding a **confidence** (High/Med/Low) and **blast radius** per the REFERENCE.md rubric. Produce the report using the template in [REFERENCE.md](REFERENCE.md) § "Report template": a scoreboard (counts + estimated LOC/deps removable) followed by findings grouped under the eight categories, each with —

1. **Dead code** — unused functions, files, components, routes, APIs, variables, imports, dependencies
2. **Duplicate logic** that should be consolidated
3. **Unused UI components**
4. **Overly complex** implementations that can be simplified
5. **Legacy code** no longer needed
6. **Redundant** database queries or API calls
7. **Abandoned / disconnected** files
8. **Tech-debt reduction** opportunities

…and for each: *what it is* (with `file:line`), *evidence* (which tool flagged it + reference count), *why it's unnecessary*, *blast radius / impact of removal*, *risks before deletion*, *recommended removal step*, *confidence*.

Order by ROI: high-confidence + low-risk + high-payoff first. **Default behaviour ends here** — present the report and ask which findings to act on. Do not delete anything yet.

### 5. Remove safely (only on explicit approval)

1. **Establish a green baseline** — run build + tests + typecheck first. If it's already red, say so and stop; you can't attribute later failures.
2. **Remove in dependency order, smallest reversible batches** (full order in REFERENCE.md): dead imports/locals → unused private symbols → unused exports → unused files → **then** unused deps (only after their last import is gone) → duplicate consolidation last (it's a refactor, not a deletion).
3. **After each batch**: re-run build + tests + typecheck.
   - **Green** → commit with a precise message (`prune: remove unused <X>`). One concern per commit.
   - **Red** → revert that batch, mark the finding "not safe — needs investigation," and continue with the rest.
4. Never bundle unrelated removals into one commit, and never delete generated/vendored/migration files to "fix" a warning — fix the generator instead.

### 6. Summarize & make it stick

- Report what was removed (LOC / files / deps), what was deferred and why, and what's left for human judgment (the Low-confidence pile).
- Cruft regrows. Suggest wiring the analyzer into CI or a periodic run, and seed/honour an ignore config so known-intentional items stop resurfacing each pass.
- Point to siblings for the parts pruning doesn't cover: `/simplify`, `/code-review`, `improve-codebase-architecture`.

## When this isn't the right tool

- **Bugs / correctness** → `/code-review`.
- **Cleaning up just-written changes** → `/simplify`.
- **Structural / testability refactors** (deep modules) → `improve-codebase-architecture`.
- **Adding the wrong feature in the first place** → that's a planning problem, not a pruning one.
