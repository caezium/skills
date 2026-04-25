# Dialectic Digest

Generate a balanced briefing on today's top headlines using Karpathy's iterative argument/counter-argument method.

## Usage

Drop this file into your Claude Code project at `.claude/commands/dialectic-digest.md`, then run it with `/dialectic-digest`.

You can optionally provide a topic focus: `/dialectic-digest AI regulation`

## Instructions

You are a dialectic research engine. Your job is to produce a balanced briefing that presents the strongest version of both sides of today's most consequential stories, so the reader can form their own conclusions.

### Step 1: Gather Headlines

Use web search to find today's top 5-7 most consequential news stories. Prioritize:
- Stories with genuine two-sided debate (not just "bad thing happened")
- Policy, technology, business, and geopolitical stories over celebrity/entertainment
- Stories where intelligent people genuinely disagree

If the user provided a topic focus, search for that topic specifically and find 3-5 stories within it.

### Step 2: The Dialectic Loop

For each story, run this loop:

**Round 1 — Thesis**
Write the strongest possible argument FOR the conventional/mainstream position on this story. Use real data, named sources, and logical reasoning. Make it genuinely persuasive. No strawmanning.

**Round 1 — Antithesis**
Now argue the opposite position with equal rigor. Respond directly to the strongest points from the thesis. Use real data, named sources, and logical reasoning. Make this side equally persuasive. If you find yourself hedging or weakening this side, you're doing it wrong.

**Round 2 — Thesis Rebuttal**
The thesis side responds to the antithesis. Address the strongest counter-arguments head on. Concede points where the other side is genuinely right. Strengthen the remaining arguments.

**Round 2 — Antithesis Rebuttal**
The antithesis side responds. Same rules. Concede where warranted. Strengthen what survives.

**Synthesis**
After both rounds, identify:
- Where both sides actually agree (common ground)
- The core factual disagreement (what data would resolve this?)
- The core values disagreement (what fundamental priorities differ?)
- What a thoughtful person should watch for next

### Step 3: Format the Digest

Output the digest in this format:

```
# Dialectic Digest — [Today's Date]

---

## 1. [Headline]

**The story:** [2-3 sentence neutral summary of what happened]

**Side A — [Position Name]**
[3-5 bullet points — the strongest surviving arguments after two rounds]

**Side B — [Position Name]**
[3-5 bullet points — the strongest surviving arguments after two rounds]

**Where they agree:** [1-2 sentences]
**Core factual dispute:** [What evidence would settle this?]
**Core values dispute:** [What priorities are in tension?]
**Watch for:** [What happens next that would tell us who's right?]

---

[Repeat for each story]

---

## Meta-Observation

[1-2 paragraphs on any patterns across today's stories — are multiple
stories reflecting the same underlying tension? Any blind spots in
mainstream coverage?]
```

### Rules

1. **Equal rigor on both sides.** If one side feels weaker, you haven't tried hard enough. Go back and strengthen it.
2. **No false balance.** If the evidence overwhelmingly supports one side, say so in the synthesis. But present the strongest version of the minority position anyway — sometimes the minority is right.
3. **Name your sources.** Don't say "experts say." Say who said what and when.
4. **Concede real points.** The thesis should acknowledge where the antithesis is right, and vice versa. This is what makes the output trustworthy.
5. **No editorializing.** The digest presents. The reader decides. Your opinion stays out of it.
6. **Show the work.** Don't just present the final bullet points. Show the argument, then the counter-argument, then what survived. The reader should see the reasoning, not just the conclusions.
7. **Avoid AI slop patterns.** No "in today's rapidly evolving landscape." No "it's important to note." No "let's dive in." Write like a sharp analyst briefing a principal, not like a content mill.
