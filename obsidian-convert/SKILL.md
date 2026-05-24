---
name: obsidian-convert
description: Convert source files (PDFs, DOCX, image-only PDFs) into Obsidian-flavored markdown notes that preserve the original content **verbatim** while applying proper Obsidian styling — YAML frontmatter with tags/aliases, callouts, LaTeX math, footnotes, wikilinks, and tables. Use this skill whenever the user wants to convert, transcribe, extract, rebuild, "turn into a note", or "make an Obsidian version" of a PDF / source document, even if they don't explicitly say "Obsidian". Also use it when the user mentions textbook chapters, lecture slides, exam papers, formula sheets, definition lists, or revision materials that need to become markdown notes in their vault. Triggers on phrases like "convert this PDF", "make me a note from", "transcribe this into markdown", "rebuild this as markdown", "extract verbatim", "turn this into a study note", or when the user points at a `.pdf`/`.docx` in their vault and asks to do something with the contents.
---

# Obsidian Convert

Convert source files into Obsidian-flavored markdown notes that preserve **all** original content verbatim while applying the user's Obsidian styling conventions.

## Core principle: verbatim fidelity

The most important rule is that **no content gets lost or paraphrased**. Every numbered point, every exemplar answer, every footnote annotation, every formula, every quoted passage must appear in the output exactly as written in the source. The user is studying from these notes — if you summarize, you've made the note useless for revision.

You're allowed to **restructure** (split a wall of text into bullets, lift Q&A into callouts, turn comparisons into tables) but you're **not** allowed to **abbreviate**.

The only things you should strip are pure layout artifacts:
- Page numbers (e.g., the standalone `1`, `2`, `3` at the bottom of each page)
- Repeated page headers / running headers (e.g., `吉屋教研组` reappearing at the top of every page)
- Decorative whitespace between page breaks
- PDF font-substitution artifacts (orphan ligature glyphs like `ﬁ`, `ﬂ` floating on their own lines — rejoin them into their words)

If you're ever unsure whether to keep something, keep it.

## Workflow

### 1. Identify the source type and extract text

Source PDFs come in three flavors. Detect which one you have before deciding how to extract.

**Text-extractable PDFs** (the common case — textbook chapters, exam papers, formula sheets typeset in TeX/Word):
```bash
mkdir -p /tmp/pdf_extracts
pdftotext -layout "<source.pdf>" /tmp/pdf_extracts/<name>.txt
wc -l /tmp/pdf_extracts/<name>.txt
```
If the extract has more than ~50 lines and you can read text in it (not just garbage), it worked. Read the `.txt` instead of the PDF — bypasses the 32 MB API attachment limit and is much faster.

**Image-only PDFs** (scans, photos, handwritten notes, slide decks with everything rendered as images): `pdftotext` returns < 2 KB of mostly nothing. Fall back to `Read` with the `pages` parameter (max 20 per call):
```
Read("<source.pdf>", pages="1-20")
```
Read in chunks if the document is longer.

**DOCX**: try `pandoc -t markdown <file.docx>` if pandoc is installed, otherwise note that you couldn't extract and ask the user how to proceed.

### 2. Plan the structure before writing

Before opening `Write`, skim the entire extracted text and decide:
- What's the H1 title? (Usually the document's actual title.)
- What are the major H2 sections? (Chapter sections, topic groupings, syllabus units.)
- Where are the point lists, exemplar answers, Q&A blocks, tables, equations? Each needs different styling — see [references/styling-rules.md](references/styling-rules.md).
- What footnote markers appear? Map them to `[^1]`, `[^2]`… and decide where the definitions live (inline after the paragraph that references them, or all at the bottom).
- Are there obvious related notes already in the vault to wikilink to? (e.g., a Chapter 3 note should link `[[Chapter 2]]` and `[[Chapter 4]]` for navigation.)

Quick mental check: if you can't answer "what's the H1 and what are the H2s" after skimming, you don't understand the doc well enough yet.

### 3. Write the note in one pass

Use the `Write` tool with the full structured markdown. The full styling spec is in [references/styling-rules.md](references/styling-rules.md) — read it before writing if you're unsure about a callout type or frontmatter convention. The most important conventions:

**Frontmatter** (always):
```yaml
---
draft: false
tags:
  - <subject>      # e.g., history, physics, economics, chinese
  - igcse          # or a-level, etc.
  - <topic-slug>   # e.g., chapter1, versailles
aliases:
  - <Alt name 1>
  - <Chinese name if applicable>
---
```

**Title line** (always): `# <title from source>`

**Source attribution blockquote** (always, right after the H1):
```markdown
> Source PDF: `<filename.pdf>`. <one-line description of what's in the doc>.
```

**Callout mapping** (see styling-rules.md for the full table):
- Point lists → `> [!note]- Point List` (collapsed)
- Exemplar / model answers → `> [!example]- Exemplar Answer` (collapsed)
- Definitions → `> [!def]`
- Quoted source text / poems / passages to memorize → `> [!quote]`
- Q&A discussion questions → `> [!question]`
- Sidebar info, related-notes lists → `> [!info]`
- Strategy tips, exam advice → `> [!tip]`
- Cautions, common mistakes → `> [!warning]`
- Critical reminders → `> [!important]`

**LaTeX math** (always, never plain ASCII for equations): `$inline$` and `$$display$$`. Use `\frac`, `\sin`, `\cos`, `\theta`, `\sqrt`, etc.

**Footnotes** (always for source annotations): `[^1]` markers in text, definitions placed inline near the paragraph that uses them (Obsidian renders them at the bottom regardless, but inline definitions are easier to maintain). Preserve Chinese / non-English annotations verbatim.

**Wikilinks** (for cross-navigation): `[[Note Name]]` between related notes. After the source attribution blockquote, add navigation hints if part of a series:
```markdown
> 🔗 **Previous:** [[Chapter N-1]] | **Next:** [[Chapter N+1]]
```

### 4. Verify before reporting done

After writing, do a quick sanity check:
- Open the file (`Read` it back) and skim — does every section from the source appear?
- Did you accidentally drop any point list items, exemplar paragraphs, or footnotes?
- Are there any plain-ASCII equations that should be LaTeX?
- Did Chinese / non-English annotations get preserved verbatim?
- Are the callout types appropriate (point list → `[!note]`, not `[!info]`)?

If the source had 30 numbered points and your output has 28, that's a bug — find the missing two before reporting done.

## Where to save the output

If the user gave you a specific path, use it. Otherwise, save it next to the source PDF — same folder, same base name with `.md`:
- `vault/path/chapter1.pdf` → `vault/path/chapter1.md`

If the existing folder has a `MOC.md` or `00_MOC.md`, also update it to link the new note. See [references/styling-rules.md#mocs-and-navigation](references/styling-rules.md) for MOC conventions.

## Bulk conversion

If the user hands you many files at once (e.g., 8 chapter PDFs, all the formula sheets, an entire vault scan), use parallel sub-agents to spread the work. Each agent gets one source file and writes one destination markdown file independently. Brief each agent with:
- The exact source path (or pre-extracted `.txt` path)
- The exact destination path
- A pointer to this skill (`~/.claude/skills/obsidian-convert/SKILL.md`) so they apply the same styling
- Any series-specific wikilinks they should include

Wait for all agents to finish, then update the MOC and report.

## Anti-patterns to avoid

- **Summarizing exemplar answers** to "save space" — never. These are the model essays the student studies from.
- **Renumbering point lists** so they don't match the source — preserve original numbering even if it seems weird.
- **Dropping Chinese annotations** because they look like noise — they're the student's gloss on technical terms.
- **Skipping image-referenced sections** because the image won't render in markdown — keep the surrounding text and add a `> [!info]` note pointing at the source PDF page.
- **Writing plain ASCII for equations** (`v = lambda * f`) instead of LaTeX (`$v = \lambda f$`).
- **Adding new frontmatter properties** the user's vault doesn't already use — match the conventions of neighbouring notes (run `Read` on a sibling note to check).
- **Inventing wikilinks to notes that don't exist** — only link `[[Note Name]]` if you've verified the note exists, or if it's clearly a known sibling in a series (Chapter 3 ↔ Chapter 2/4).

## Reference files

- [references/styling-rules.md](references/styling-rules.md) — full Obsidian Flavored Markdown styling spec for this skill (frontmatter, callouts, LaTeX, footnotes, wikilinks, tables, MOC conventions)
- [references/extraction-patterns.md](references/extraction-patterns.md) — how to extract from text PDFs, image-only PDFs, DOCX, and common gotchas
