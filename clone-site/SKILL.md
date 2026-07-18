---
name: clone-site
description: Clone any website from a URL into a pixel-faithful Next.js codebase — recon, asset/CSS extraction, parallel section builders, animation porting, and automated fidelity verification. Use whenever the user pastes a URL and asks to clone, copy, replicate, rebuild, reverse-engineer, or "make me a version of" a website or landing page — even if they don't say the word "clone". Also triggers on "/clone-site <url>". For multi-page sites it discovers and clones every page via the sitemap.
argument-hint: "<url> [<url2> ...] [notes like 'landing page only' or 'always animate']"
---

# Clone Site

Reverse-engineer the site(s) at `$ARGUMENTS` into a Next.js codebase. This skill encodes a refined version of the ai-website-cloner-template pipeline: the big lesson is that **most marketing sites are static (Astro, plain HTML, SSR), and for those the served source IS the ground truth** — downloading it beats hand-measuring computed styles every time. Only fall back to browser-side style extraction for true SPAs.

Default scope: every page in the site's sitemap, pixel-perfect, with real assets and working interactions. If the user scopes it down ("just the landing page"), honor that.

## Phase 0 — Project setup

1. Create the project OUTSIDE any repo you're currently in:
   ```bash
   git clone --depth 1 https://github.com/JCodesMore/ai-website-cloner-template.git ~/Desktop/<hostname>-clone
   cd ~/Desktop/<hostname>-clone && rm -rf .git && git init -q && npm install
   ```
   If the folder exists, ask before overwriting.
2. Make research dirs: `docs/research/<hostname>/`, `docs/research/components/`, `docs/design-references/`.

## Phase 1 — Stack detection (decides everything)

`curl -sS <url>` and inspect:

- **Content-complete HTML** (real headings/copy in the response; `_astro/` assets, or no root `<div id="root|__next">` shell) → **source-first path** (rest of this skill).
- **SPA shell** (empty root div, content materializes from JS) → the template's browser-extraction pipeline is the right tool; follow `.claude/skills/clone-website/SKILL.md` inside the scaffold (screenshots + `getComputedStyle()` extraction per section). The verification and parallel-builder phases below still apply.

Record: framework, stylesheet links, inline `<style>`/`<script>` blocks, font links, animation libraries (grep for `gsap`, `ScrollTrigger`, `lenis`, `framer`).

## Phase 2 — Download the ground truth (source-first path)

All into `docs/research/<hostname>/`:

1. **Every page**: fetch `sitemap.xml` (or `sitemap-index.xml`) for the definitive URL list. No sitemap → crawl nav/footer links one level. Save each page's HTML.
2. **Every stylesheet** — including page-specific ones (Astro emits per-page CSS files; different pages reference different ones).
3. **Every behavior script** — inline AND external `<script type="module">`. These minified files are the exact spec for animations; you will port them, not guess.
4. **Every asset** to `public/`: write a small Node download script. Sources of asset URLs: `<img src>` AND **every `srcset` variant**, `<video src/poster>`, CSS `url()` refs, favicons, webmanifest, OG images. Missing a `srcset` variant means broken images at other viewport widths — grep the HTML for all of them.
5. Take reference screenshots with Chrome MCP at 1440px (scroll through, screenshot each viewport-full) and note per-section behavior: what pins, what fades, what's tabbed vs scroll-driven. Two traps:
   - **Lazy images look blank** during fast programmatic scrolling — a blank card usually means `loading="lazy"` hadn't fired, not a real gap. Confirm via DOM (`naturalWidth > 0`) before "fixing" anything.
   - **`prefers-reduced-motion`**: if macOS Reduce Motion is on, both the original and your screenshots may show the static branches. Check `matchMedia('(prefers-reduced-motion: reduce)')` and read the source scripts for `reduce` gates so you know which animations exist even if you can't see them.

## Phase 3 — Foundation (do this yourself, not via agents)

1. **CSS verbatim**: concatenate all downloaded CSS + inline `<style>` blocks into `src/app/globals.css`, stripping framework scoping attrs (e.g. `[data-astro-cid-*]`). Keep the original class names. Do NOT translate to Tailwind — every translation step is drift risk, and fidelity beats idiom. Identical duplicate rules across per-page CSS files are harmless.
2. **Fonts**: replicate the original's Google Fonts `<link>` (or download self-hosted fonts). The CSS references literal family names, so `next/font`'s renamed families would break it — plain `<link>` in `layout.tsx` is correct here.
3. **layout.tsx metadata**: title, description, favicon, OG image from the original head.
4. `trailingSlash: true` in `next.config.ts` if the original uses trailing-slash URLs.
5. Install animation libs the site uses (`npm i gsap` etc.) — port to the npm package, never vendor the minified bundle.
6. Write `docs/research/PAGE_TOPOLOGY.md` (section map, interaction model per section) and `BEHAVIORS.md` (exact mechanisms from the de-minified scripts: trigger points, easings, durations, media-query gates). These are the builders' bible.

## Phase 4 — Parallel build

Split the page into sections (hero, nav, feature blocks, footer, modals...). For each, write a brief spec in `docs/research/components/<name>.spec.md`: target file, ground-truth fragment path, interaction model, behavior notes, gotchas.

Dispatch parallel builder agents (Agent tool, `general-purpose`), ~4–7 at once. Worktrees are unnecessary **if each agent owns disjoint files** — pre-write shared files yourself and forbid agents from touching them. Every builder prompt includes:

- Ground-truth fragment path + spec path + BEHAVIORS.md reference
- Conversion rules: strip scoping attrs; `class`→`className`, `srcset`→`srcSet`, camelCase SVG attrs, self-closing tags; **text verbatim — including apostrophe/quote style** (don't "fix" straight quotes to curly or vice versa; it shows up in the fidelity diff)
- "All CSS already exists in globals.css under the original class names — write NO new CSS, NO Tailwind"
- Port behaviors from the actual source scripts (de-minify), as hooks with cleanup; respect the original's media-query/motion gates unless the user asked otherwise
- "Only create/modify your own target files"; verify `npx tsc --noEmit`
- Ask builders to REPORT deviations and shared-component mismatches they notice — they catch real fidelity bugs (per-page CTA text variants, footer blocks present only on some pages)

Cross-component dependencies: use composition (`<Hero>{<HeroCard/>}</Hero>` via children) so agents never import each other's unfinished files.

**Multi-page sites**: extract shared chrome (Nav/Footer/Modals) into components with variant props FIRST — then per-page builders reuse them. Grep every page for the differences before assuming they're identical: nav light/dark variant, CTA label, `aria-current`, footer link blocks. Pages sharing one template (blog posts, comparison pages) batch 5 per agent.

Assemble `src/app/page.tsx` (and routes) yourself; run `npm run build` after merging.

## Phase 5 — Verify (don't skip; this catches what eyeballs miss)

1. `npx tsc --noEmit` and `npm run build` — must be clean.
2. `npx next start -p 3210` and run the bundled text-fidelity diff:
   ```bash
   python3 scripts/fidelity-diff.py --research docs/research/<hostname> --base http://localhost:3210
   ```
   (Copy `scripts/fidelity-diff.py` from this skill's directory into the project.) It strips tags/scripts, decodes entities, and reports missing words per page. Target ≥99%; chase every gap to root cause — real omissions vs entity-encoding artifacts vs apostrophe-style drift all look different in the output.
3. Live QA with Chrome MCP: side-by-side against the original at the same scroll positions; click every interactive element (tabs, accordions, toggles, modals); check the console for errors. Verify scroll-pinned sections actually pin (`.pin-spacer` exists, body height grew).
4. Commit with a summary of sections/components/assets. No AI attribution in the message.

## Judgment calls to surface to the user (don't silently decide)

- **Reduced motion**: if the original gates animations on `prefers-reduced-motion` and the user's OS has it on, the clone will look "broken but faithful". Default to matching the original's code; if the user reports missing animations, offer the always-animate override (drop the gates, comment the deviation).
- **Backend endpoints** (`/api/download`, form posts): a static clone can't replicate them. Keep the original URLs/actions and say so in the completion report.
- **Analytics** (PostHog, GA): strip them; note it.

## Completion report

Sections built, components created, assets downloaded, routes generated, build status, fidelity-diff scores, interactions tested, and known gaps (backend routes, uncloned linked pages).
