# Prune — Reference

Detection tooling, the false-positive catalog, the confidence rubric, safe-removal ordering, and the report template. SKILL.md drives the process; this file is the lookup.

---

## Detection toolbox

Run the analyzer for the stack, then corroborate with the reference-counting recipe below. Prefer one-shot runners (`npx`, `uvx`, `go run`) when a tool isn't installed rather than skipping. Each tool catches a lot but **none is authoritative** — they all miss dynamic usage, which is why Step 3 exists.

### JavaScript / TypeScript
| Tool | Command | Catches | Misses |
|---|---|---|---|
| **knip** (best all-in-one) | `npx knip` | Unused files, exports, types, deps, devDeps, duplicate exports | Dynamic `import(name)`, string-keyed access |
| ts-prune | `npx ts-prune` | Unused exported symbols | Same; noisier than knip |
| depcheck | `npx depcheck` | Unused & missing `package.json` deps | Deps used only in scripts/configs |
| madge | `npx madge --orphans --extensions ts,tsx,js,jsx src` | Orphan modules (imported by nothing) | Entry points look orphaned — exclude them |
| eslint | `npx eslint . --rule '{"no-unused-vars":"error"}'` | Unused locals/imports/params | File- and export-level deadness |
| Bundle bloat | `npx vite-bundle-visualizer` / `npx source-map-explorer dist/**/*.js` | What's actually shipping | Tree-shakeable-but-present code |

`knip` is the highest-leverage single command here — start with it.

### Python
| Tool | Command | Catches | Misses |
|---|---|---|---|
| **vulture** | `uvx vulture . --min-confidence 80` | Dead functions, classes, vars, unreachable code | `getattr`, plugin registries, framework hooks |
| deptry | `uvx deptry .` | Unused / missing / transitive / misplaced deps | Deps imported dynamically |
| ruff | `ruff check --select F401,F811,F841 .` | Unused imports (F401), redefinitions (F811), unused locals (F841) | Cross-module deadness |
| unimport | `uvx unimport --check` | Unused imports (autofix-capable) | — |

Tune `vulture --min-confidence`: 80+ for the High pile, lower only to *generate candidates* you'll verify.

### Go
| Tool | Command | Catches |
|---|---|---|
| **deadcode** (official) | `go run golang.org/x/tools/cmd/deadcode@latest ./...` | Functions unreachable from `main`/tests |
| staticcheck | `staticcheck ./...` (look for U1000) | Unused code, plus correctness lints |
| go vet | `go vet ./...` | Suspicious constructs |

### Rust
| Tool | Command | Catches |
|---|---|---|
| **cargo-machete** | `cargo machete` | Unused dependencies (fast, no nightly) |
| cargo-udeps | `cargo +nightly udeps` | Unused deps (more thorough, needs nightly) |
| compiler | `cargo check` then read `dead_code` warnings | Unused fns/fields/variants |

### Other / cross-language
- **Java/Kotlin**: IntelliJ "Analyze → Unused declaration" inspection; `detekt` rules; `gradle` dependency analysis plugins. Largely IDE-driven.
- **CSS**: `npx purgecss` against templates to find unreferenced selectors (verify — dynamic class names break it).
- **Anything**: the recipe below.

---

## Reference-counting recipe (the universal verifier)

When no tool fits, or to corroborate one that does, prove a symbol is unreferenced with ripgrep. The key move is searching **everything, not just source** — configs, templates, JSON, HTML, markdown all create live references that source-only tools miss.

```sh
# Count references to a symbol across the whole repo (excluding its own definition file)
rg -n --hidden -g '!.git' '\bSYMBOL\b' | grep -v 'path/to/definition'

# Files that import a module path (catch barrels/re-exports too)
rg -n "from ['\"].*module-name" -g '*.{ts,tsx,js,jsx,vue,svelte}'

# Is this file referenced anywhere — including non-code?
rg -n 'basename-without-ext' --hidden -g '!.git'
```

Caveats that demand a downgrade, not deletion:
- **Dynamic / computed names** (`obj[key]`, `getattr`, `import(var)`, reflection) won't show up — if the symbol's name could be assembled at runtime, it's at most Medium.
- **Barrel files / re-exports** (`export * from`) hide the real consumer one hop away — follow the chain.
- **Whole-word matches** can be fooled by common names; prefer specific identifiers.

---

## False-positive catalog

"Looks dead, is alive." For each candidate, rule these out before flagging. If you can't, downgrade.

| Trap | How it stays alive | How to check |
|---|---|---|
| **Dynamic dispatch / reflection** | `obj[methodName]()`, `getattr(o, n)`, registries keyed by string | Search for the registry / dispatch site, not the symbol name |
| **Dependency injection** | Wired by container/decorator, never imported directly | Check DI config, `@Injectable`/`@Component`/providers |
| **Framework by convention** | Routes, pages, fixtures discovered by path (Next/Nuxt `pages/`, Rails, Spring, `conftest.py`, Django apps) | Know the framework's magic dirs — these are entry points |
| **Public / exported API** | Consumed by *other* repos or published as a package | `package.json` `exports`/`bin`, `__all__`, `pub`, semver surface — never prune without owner sign-off |
| **Build / CLI / script entry points** | Invoked from `Makefile`, npm scripts, CI, cron | Grep build & CI configs |
| **Test-only utilities** | Referenced only from tests | If refs exist but all in tests → Medium, ask whether the test is still wanted |
| **Feature-flagged / env-gated** | Behind a flag or `if (process.env...)` that's currently off | Search flag names; "off today" ≠ dead |
| **Generated code** | protobuf, GraphQL/OpenAPI codegen, ORM models, migrations | Fix the generator/schema, never hand-delete output |
| **Serialization / persistence** | Field read from JSON/DB/wire by name | Check schemas, fixtures, stored payloads |
| **i18n keys / CSS classes** | Referenced from translation files or templates as strings | Search template + locale files |
| **Conditional / platform code** | `process.platform`, `#[cfg(...)]`, `sys.platform` | Other-platform paths look dead on yours |

---

## Confidence rubric

| Tier | Definition | Action |
|---|---|---|
| **High** | Tool-flagged **and** zero references repo-wide (incl. non-code) **and** no false-positive category applies **and** not in a protected dir | Safe to remove now, with verification |
| **Medium** | Tool-flagged but one unresolved signal — possible dynamic use, referenced only in tests, or a re-export chain you couldn't fully trace | Remove only after a targeted manual check; otherwise report |
| **Low** | Judgment call — "overly complex but working," "feels legacy," suspected duplication | Report and discuss; never auto-remove |

Blast radius (orthogonal to confidence): **leaf** (one file, no exports) · **module** (within a package) · **cross-cutting** (exported / API / config). Prefer leaf + High first.

---

## Protected by default

Do **not** propose deleting these without an explicit, separately-justified note:
- Generated code and its output dirs (`*_pb2.py`, `dist/`, `*.generated.*`)
- Vendored / third-party dirs, lockfiles
- Database migrations (history, not dead code — even when "unused")
- The public API surface (exported package entry points, `bin`)
- Feature-flag stubs / scaffolding for explicitly near-term work
- License, legal, and compliance files

---

## Safe-removal order

Remove references before definitions, leaves before roots. Re-run build + tests + typecheck after **each** numbered step; commit on green, revert on red.

1. **Dead imports & local variables** — zero blast radius, start here to build confidence.
2. **Unused private functions / methods / components** — within-module.
3. **Unused exported symbols** — only after a repo-wide reference check.
4. **Unused files / modules** — after confirming no imports *and* no config/glob/string references.
5. **Unused dependencies** — only once their last import is gone (order matters: removing the dep before the usage breaks the build).
6. **Dead routes / endpoints / queries** — after confirming no clients; treat anything public as cross-cutting.
7. **Duplicate-logic consolidation** — **last**. This is a refactor, not a deletion: do it behind passing tests, and prefer the simplest shared form. No new abstraction without a clear second use case — don't trade duplication for the wrong indirection.

---

## Report template

```markdown
## Prune report — <scope>

**Scoreboard**: <N> findings · ~<LOC> lines removable · <D> unused deps · <F> dead files
Baseline: build <pass/fail> · tests <pass/fail> · typecheck <pass/fail>

### High confidence (safe to remove)
| # | Category | What | Location | Evidence | Blast radius | LOC |
|---|---|---|---|---|---|---|
| 1 | Dead code | `oldHelper()` | src/utils/old.ts:12 | knip + 0 refs repo-wide | leaf | 24 |

### Medium confidence (verify first)
| # | Category | What | Location | Unresolved signal | Suggested check |
| ... |

### Low confidence (discuss — do not auto-remove)
- <judgment-call items, one line each>

### Per-finding detail (High & Medium)
**#1 — `oldHelper()` — src/utils/old.ts:12**
- Why unnecessary: replaced by `newHelper` in PR #X; no callers.
- Evidence: flagged by knip; `rg '\boldHelper\b'` → 0 hits outside definition.
- Risk: none identified; not exported, not dynamic.
- Removal step: delete fn + its now-unused `import {foo}`; re-run tests.
```

End the report with: deferred items + why, and a one-line recurrence suggestion (CI integration / ignore-config seeding).
