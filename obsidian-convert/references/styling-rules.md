# Obsidian-Flavored Markdown Styling Rules

Detailed conventions for the `obsidian-convert` skill. Read this when you're unsure how to render a particular piece of source content.

## Table of contents

1. [YAML frontmatter](#yaml-frontmatter)
2. [Heading hierarchy](#heading-hierarchy)
3. [Callouts — full mapping](#callouts--full-mapping)
4. [LaTeX math](#latex-math)
5. [Footnotes](#footnotes)
6. [Wikilinks and embeds](#wikilinks-and-embeds)
7. [Tables](#tables)
8. [Comments and highlights](#comments-and-highlights)
9. [MOCs and navigation](#mocs-and-navigation)
10. [Common source patterns → output mappings](#common-source-patterns--output-mappings)

---

## YAML frontmatter

Always include frontmatter at the very top of every converted note. Match the conventions of the user's existing notes.

**Minimum required:**
```yaml
---
draft: false
---
```

**Recommended for converted source documents:**
```yaml
---
draft: false
tags:
  - <subject>           # history, physics, economics, chinese, chemistry, etc.
  - <exam-level>        # igcse, a-level, gcse
  - <topic-slug>        # chapter1, versailles, motion, definitions
  - <doc-type>          # textbook, formula-sheet, past-paper, definitions
aliases:
  - <Alternative name>
  - <Original-language name if applicable>
---
```

**Why aliases matter:** the user searches the vault by name. If a note's title is `Chapter 1 — Was the Treaty of Versailles fair`, add aliases like `Chapter 1`, `Treaty of Versailles Chapter`, `T Chapter 1` so all the natural search phrases hit.

**Don't invent new property names** the vault doesn't already use. Run `Read` on a sibling note first to see what frontmatter style is already in use. Common existing properties to preserve if you see them: `date`, `cssclasses`, `status`, `Summary`.

---

## Heading hierarchy

- `# H1` — exactly one per note, the document title
- `## H2` — major sections (chapter sections, syllabus units, "Unit 1", "Unit 2", "Past Paper Questions")
- `### H3` — sub-sections (individual questions, individual poems, individual concepts)
- `#### H4` — granular sub-parts within an H3 (e.g., "(a)", "(b)", "(c)" sub-questions of a single past-paper question)

Don't skip levels. If the source has only two levels of hierarchy, use only H1 + H2 + H3.

---

## Callouts — full mapping

Obsidian callouts use `> [!type]` syntax. Append `-` to make collapsed by default, `+` to make expanded by default.

| Source pattern | Output callout |
|---|---|
| **Point List** / numbered bullet list of facts | `> [!note]- Point List` (collapsed) |
| **Exemplar Answer** / **Example Answer** / model essay | `> [!example]- Exemplar Answer` (collapsed — usually long) |
| **Definition** of a term | `> [!def] <Term>` |
| **Quoted source** — historical document, poem, passage to memorize, primary source for Source Paper | `> [!quote]` |
| **Q&A discussion question** | `> [!question] <The question>` followed by the answer in plain text |
| Sidebar info, "Related Notes" lists, glossary callouts | `> [!info]` |
| Strategy tips, exam advice, "remember to…" | `> [!tip]` |
| Cautions, common mistakes, "don't confuse with…" | `> [!warning]` |
| Critical reminders, syllabus must-knows | `> [!important]` |
| Procedure steps in a lab / experiment | `> [!important] Step N` |
| Background info, biographical notes | `> [!info]` |

**Collapsed (`-`) vs expanded:** collapse long content (exemplar essays, point lists with 8+ items, full poems). Leave short callouts (definitions, single tips) expanded.

**Custom titles:** add a title after the type to override the default. Example: `> [!info] Key Dates` shows "Key Dates" instead of the generic "Info".

**Nesting callouts:** add an extra `>` per nesting level. Useful for sub-points within a tip:
```markdown
> [!tip] Exam strategy
> Lead with your strongest argument.
>
> > [!warning] But don't…
> > …forget to address the counter-argument.
```

---

## LaTeX math

Always use LaTeX for equations. Never write ASCII formulas like `v = lambda * f` — render as `$v = \lambda f$`.

**Inline math:** wrap in single `$`:
```markdown
The wave equation is $v = f\lambda$ where $\lambda$ is wavelength.
```

**Display math:** wrap in `$$`:
```markdown
$$F = ma$$

$$\text{Power} = \frac{\text{Work done}}{\text{Time}} \qquad P = \frac{W}{t}$$
```

**Common LaTeX you'll need:**
| Want to render | LaTeX |
|---|---|
| Greek letters | `\alpha`, `\beta`, `\gamma`, `\theta`, `\lambda`, `\mu`, `\pi`, `\rho`, `\sigma`, `\omega`, `\Delta` |
| Fractions | `\frac{numerator}{denominator}` |
| Square root | `\sqrt{x}`, `\sqrt[3]{x}` |
| Subscript / superscript | `x^2`, `x_i`, `x_{12}`, `H_2O`, `^A_Z X` |
| Trig | `\sin`, `\cos`, `\tan`, `\sin^{-1}` |
| Units in equations | `\text{kg m/s}^2` (use `\text{}` to render plain text inside math mode) |
| Approximately | `\approx` |
| Times | `\times` (not `*`) |
| Degree | `^\circ` |
| Plus-minus | `\pm` |
| Sum / integral | `\sum_{i=1}^{n}`, `\int_0^\infty` |
| Aligned equations | use `\qquad` to space the worded version and the symbolic version: `$$\text{Power (W)} = \frac{\text{Work (J)}}{\text{Time (s)}} \qquad P = \frac{W}{t}$$` |

**Nuclide notation** (Chemistry/Physics): `${}^{A}_{Z}X$` or `$^A_Z X$`. Example: alpha decay `$^A_Z X \rightarrow {}^{A-4}_{Z-2} Y + {}^4_2 \text{He}$`.

**Chemistry formulas:** wrap in math mode so subscripts render. `$\text{H}_2\text{SO}_4$` not `H2SO4`.

---

## Footnotes

Use Obsidian footnotes for source annotations (often Chinese glosses on technical terms, definitions of acronyms, references).

**Pattern:** marker in text, definition placed nearby.

```markdown
The treaty imposed reparations[^1] on Germany.

[^1]: 赔偿，补偿。
```

**Numbering:** sequential `[^1]`, `[^2]`, `[^3]`… across the whole note. If the source uses non-sequential markers (e.g., footnotes 1, 3, 7 because the others are in other documents), renumber sequentially.

**Multiple paragraph footnotes:**
```markdown
[^longnote]: First paragraph.

    Second paragraph (indent 4 spaces to continue).
```

**Preserve Chinese annotations verbatim.** These are the student's domain glosses on technical terms — they're load-bearing for revision.

---

## Wikilinks and embeds

**Wikilinks** for navigation between notes in the vault:
```markdown
[[Chapter 2 — League of Nations]]
[[Chapter 2 — League of Nations|League chapter]]   # custom display text
[[Chapter 2 — League of Nations#Manchurian Crisis]]  # link to heading
```

**Embeds** (prefix with `!`) to inline content:
```markdown
![[diagram.png]]
![[diagram.png|400]]                # width override
![[Chapter 2 — League of Nations#Manchurian Crisis]]  # embed a section
```

**When to link:**
- After the source attribution blockquote, add navigation hints if part of a series:
  ```markdown
  > 🔗 **Previous:** [[Chapter 1]] | **Next:** [[Chapter 3]]
  ```
- At the bottom of the note, in a `> [!info] Related Notes` callout, list 3–6 logically related notes.
- Inline within prose, where mentioning another concept naturally invites a click: "as discussed in [[Treaty of Versailles]]…"

**Don't invent links.** Only link `[[Note Name]]` if:
- You can verify the note exists (run a quick `find` or `Bash ls`), OR
- It's clearly a known sibling in a series (Chapter 3 → Chapter 2/4), OR
- The user explicitly told you to link it.

Broken wikilinks aren't fatal (Obsidian renders them as red unresolved links and the user can create them later), but they're noisy.

---

## Tables

Use markdown tables for any comparison content — two sides of an argument, before/after, advantages vs disadvantages, leader profiles, formula references.

```markdown
| Leader | Country | Main Aims |
|---|---|---|
| Wilson | USA | Lasting peace, 14 Points, League |
| Lloyd George | UK | Naval dominance, moderate Germany |
| Clemenceau | France | Cripple Germany, recover Alsace-Lorraine |
```

**Alignment** (optional):
```markdown
| Left | Centre | Right |
|:---|:---:|---:|
| a | b | c |
```

**Long-cell content** (long Q&A answers, multi-sentence exemplars) is better as a callout than a table cell — tables are for compact comparison.

---

## Comments and highlights

**Highlight** important phrases with `==text==`:
```markdown
The ==War Guilt Clause (Article 231)== forced Germany to accept full blame.
```

**Comments** hidden from rendered view (good for translator notes-to-self):
```markdown
This passage covers 1923–1925. %%Note: source has a typo, "1924" should be "1923"%%
```

---

## MOCs and navigation

When you finish converting a note, check if the parent folder has a `00_MOC.md` (Map of Content). If so, add a link to the new note. If the MOC has structured sections (e.g., "Chapter 1", "Chapter 2"), insert under the right section.

**MOC anatomy** (when rebuilding from scratch):
```markdown
---
draft: false
tags:
  - <subject>
  - moc
aliases:
  - <Subject> MOC
---

# <Subject> — Map of Content

> One-line description of what this folder covers.

## 📘 Core Notes

- [[Note 1]]
- [[Note 2]]

## 📝 Practice & Past Papers

- [[Past Paper 1]]
- [[Past Paper 2]]

## 🔗 Related

- [[Sister MOC]]
- 📄 Syllabus: `syllabus.pdf`
```

**Emoji headers** (📘 🧪 🌊 🇷🇺 📝 📚 🔗 etc.) make the MOC scannable. Match the user's existing MOC style — if their MOCs don't use emoji, don't add them.

---

## Common source patterns → output mappings

These are real patterns from the user's vault. When you see them, you know what to do.

### Pattern: "Point List" followed by "Exemplar Answer"

Source typically looks like:
```
(b) Why did the victors not get everything they wanted?
Point List:
1    They disagreed with each other...
2    Clemenceau pushed for a harsh treaty...
Exemplar Answer:
     Firstly, the Big Three disagreed...
```

Render as:
```markdown
#### (b) Why did the victors not get everything they wanted?

> [!note]- Point List
> 1. They disagreed with each other…
> 2. Clemenceau pushed for a harsh treaty…

> [!example]- Exemplar Answer
>
> Firstly, the Big Three disagreed…
```

### Pattern: Definition table

Source:
```
| Term | Definition |
|------|------------|
| Speed | distance per unit time |
```

Keep as a markdown table. Use math mode for any chemical/physical notation inside cells.

### Pattern: Worked example

Source has a calculation worked through line-by-line. Wrap in `> [!example]` and use display math:
```markdown
> [!example] Worked example
>
> A 10 kg gun fires a 10 g bullet at 100 m/s. Find the recoil speed.
>
> $$\text{Momentum before} = 0$$
> $$0 = 0.01 \times 100 + 10v$$
> $$v = -0.1 \text{ m/s}$$
>
> The recoil speed is $0.1$ m/s.
```

### Pattern: Chinese poem with translation

Source has the poem text followed by a paraphrased translation.

```markdown
### 《春望》唐 杜甫（全⽂）

> [!quote]
> 国破⼭河在，城春草⽊深。
> 感时花溅泪，恨别⻦惊⼼。
> 烽⽕连三⽉，家书抵万⾦。
> ⽩头搔更短，浑欲不胜簪。

> [!example]- 译⽂
> (translation here, collapsed by default)
```

### Pattern: Source with footnote markers

Source:
```
The treaty imposed reparations¹ on Germany.

¹ 赔偿，补偿。
```

Render as:
```markdown
The treaty imposed reparations[^1] on Germany.

[^1]: 赔偿，补偿。
```

### Pattern: "Focus Points" / "Specified Content" preamble

History textbook chapters open with a list of focus points. Render as a regular bulleted list under an H2:
```markdown
## Focus Points

- How far did weaknesses in the League's organisation and membership make failure inevitable?
- How successful were the League's attempts at peacekeeping in the 1920s?

## Specified Content

- The structure, aims and membership of the League
- Successes and failures in peacekeeping during the 1920s
```

### Pattern: Past paper question with mark allocation

Source: `(c) ... [10]` where `[10]` is marks.

Render as an H4 with the marks in the heading:
```markdown
#### (c) How well did the League deal with international disputes in the 1920s? Explain your answer. [10]
```
