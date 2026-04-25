# V1 vs V2 Comparison Analysis

**Date:** 2026-02-06
**Queries tested:** 4 (1 head-to-head, 3 V1-only)
**Scope:** Quick smoke test, not full 17-query matrix

---

## Part 1: Head-to-Head -- "kanye west" (NEWS Query)

### Dimension-by-Dimension Scoring

#### 1. Query Parsing Display

Does it show the `🔍 **{TOPIC}** · {QUERY_TYPE}` line before running tools?

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 1 | No parsing display at all. Output starts with "## What I learned:" -- jumps straight into synthesis. No acknowledgment of topic or query type before research. |
| V2 | 1 | No parsing display either. Output starts with "Here's what I found:" then "## What I learned:" -- same problem as V1. |

**Analysis:** Neither version actually rendered the query parsing display. V2 SKILL.md explicitly requires `🔍 **kanye west** · News` before any tools run, but the agent did not produce it. This is a V2 instruction that failed to land. Both score 1/5.

Possible cause: The parsing display is supposed to appear *before* tools are called -- it may have been shown during execution but not captured in the final output text. If so, both outputs represent only the post-research synthesis, not the full session. Regardless, based on what is in the output files, neither shows it.

---

#### 2. Source Coverage (Reddit/X/Web counts)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 3 | `Reddit: 0 relevant threads` / `X: 30 posts │ ~10 likes` / `Web: 20+ pages`. Two of three sources returned results. Reddit was zero. |
| V2 | 3 | `Reddit: 0 threads (no results this cycle)` / `X: 29 posts │ 33 likes │ 14 reposts` / `Web: 30+ pages`. Same pattern: two of three returned results. |

**Analysis:** Nearly identical coverage. Both got zero Reddit results (likely a script/API issue for this topic, not a SKILL.md problem). V2 has slightly more precise X metrics (33 likes, 14 reposts vs. V1's vague "~10 likes"). V2 has more web pages (30+ vs 20+). Both miss the 10+ Reddit threshold for a score of 4+.

---

#### 3. Citation Quality (sparse vs every-sentence)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 2 | No inline citations at all. The body text makes claims ("full-page Wall Street Journal apology," "Hellwatt Festival in Italy") but never attributes them to a specific source. The stats box lists "Washington Post, Billboard, AllHipHop" but the body has zero `per @handle` or `per Rolling Stone` attributions. |
| V2 | 5 | Every bold section ends with a sparse, clean citation. Examples: `"per Rolling Stone"`, `"per The Washington Post"`, `"per Billboard"`, `"per AllHipHop"`, `"per The News International"`. One citation per topic, never chained. Exactly what V2 SKILL.md specifies. |

**Analysis:** This is the single biggest quality gap between V1 and V2. V1's output reads like a Wikipedia summary -- informative but ungrounded. V2 reads like a researched briefing where every claim has a named source. V2 nails the "sparse citation" rule from its SKILL.md: `"cite 1 source per pattern, short format: 'per @handle' or 'per r/sub'"`.

V1 quote (no citation): `"He'll headline the new Hellwatt Festival in Italy (July 4-18, 2026)."`
V2 quote (cited): `"Ye is headlining a brand-new festival at the 103,000-capacity RCF Arena in Italy over three weekends from July 4-18, 2026 — his first-ever live concert in Italy, per Billboard."`

---

#### 4. Summary Structure (bold topic headers, organized sections)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 3 | Has a coherent narrative structure with a paragraph of synthesis, then a `**KEY THEMES:**` numbered list. But the opening is a single dense paragraph, not broken into scannable sections with bold headers. |
| V2 | 5 | Each storyline gets its own bold header: `**BULLY Album — March 20, 2026 via Gamma**`, `**Public Apology for Antisemitism**`, `**Hellwatt Festival in Italy**`, `**Health Concerns**`, `**Grammys Ban**`, `**Kim & Lewis Hamilton Buzz**`. Each is a standalone scannable unit with 1-3 sentences. |

**Analysis:** V2 follows the SKILL.md template exactly: `**{Topic 1}** — [1-2 sentences, per source]`. V1 uses a blob + list approach which is readable but less scannable. V2 is notably better for a user who wants to skim and find the story they care about.

V1 structure: 1 dense paragraph -> 5-item `KEY THEMES` list
V2 structure: 6 bold topic cards, each self-contained -> no KEY THEMES list (but doesn't need one because the structure itself is the organization)

---

#### 5. Stats Box Format (emoji tree vs plain text)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 4 | Uses `├─` tree format with emoji: `├─ 🟠 Reddit: 0 relevant threads` / `├─ 🔵 X: 30 posts` / `├─ 🌐 Web: 20+ pages` / `└─ Top voices:`. Minor deviation: says "0 relevant threads (filtered out noise)" instead of the V1 SKILL.md template "0 threads (no results this cycle)". Also omits the `🗣️` emoji on the Top voices line. |
| V2 | 5 | Perfect match to V2 SKILL.md template: `├─ 🟠 Reddit: 0 threads (no results this cycle)` / `├─ 🔵 X: 29 posts │ 33 likes │ 14 reposts (via xAI)` / `├─ 🌐 Web: 30+ pages │ rollingstone.com, ...` / `└─ 🗣️ Top voices: @honest30bgfan_ (33 likes), @HipHopCrave_ │ Rolling Stone, Washington Post, Complex`. Includes `(via xAI)` notation, `🗣️` emoji, @handles with engagement counts. |

**Analysis:** V2 is tighter and matches its template exactly. V1 is close but has minor deviations (custom "filtered out noise" text, missing `🗣️` emoji, no @handles or engagement counts on Top voices). V2's inclusion of actual @handles with like counts (`@honest30bgfan_ (33 likes)`) adds credibility.

---

#### 6. Research Grounding (actual research vs generic knowledge)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 4 | Clearly grounded: mentions specific details like "Wall Street Journal apology (Jan 26, 2026)," "four-month-long manic episode," "frontal-lobe brain injury," "North West collaborated on 'Piercings on My Hand,'" "Monumental Plaza de Toros." These are specific enough to be from research, not pre-training. Minor generic leakage: the "KEY THEMES" list uses editorial framing ("Accountability arc," "Mental health transparency") that feels more like analysis than research extraction. |
| V2 | 5 | Every fact is specific and attributed: "12th studio album," "13-track project features Peso Pluma, Playboi Carti, and Ty Dolla Sign," "earlier leak versions used AI-deepfaked vocals, which have reportedly been re-recorded," "103,000-capacity RCF Arena." The AI-deepfaked vocals detail is a standout -- it is clearly from research, not something a model would know from pre-training. The Kim/Lewis Hamilton item (`"X chatter is heavily focused on Kim Kardashian's relationship with Lewis Hamilton"`) is explicitly sourced from X data, not general knowledge. |

**Analysis:** Both are well-grounded, but V2 has more "could only come from research" details. The deepfaked vocals story, the exact venue capacity, and the explicit X chatter observation are details that prove the synthesis is from the research output, not hallucinated.

---

#### 7. Prompt Quality (invitation to share vision, not dumping prompts)

| Version | Score | Evidence |
|---------|-------|----------|
| V1 | 3 | Ends with: `"Want to dive deeper into any of these threads — the apology, the new albums, the Grammys situation, or Bianca Censori? Just tell me what angle you're interested in."` This is a follow-up invitation, but it is NOT the SKILL.md-specified invitation. It is topic-specific and conversational, which is nice, but it does not ask the user to "share your vision for what you want to create." It misses the prompt-generation angle entirely. |
| V2 | 5 | Ends with exactly: `"Share your vision for what you want to create and I'll write a thoughtful prompt you can copy-paste directly into your tool of choice."` This matches the V2 SKILL.md template verbatim. It positions the skill correctly: not a news summarizer but a research-to-prompt pipeline. |

**Analysis:** V1's closing is friendly but off-brand. It treats the skill as a research tool, not a research-to-prompt tool. V2 correctly frames the next step as "tell me what to create and I'll write the prompt." This is a meaningful difference -- V1 would leave a user thinking they just got a summary, while V2 primes them to get a usable output.

---

### Head-to-Head Scorecard

| Dimension | V1 | V2 | Winner |
|-----------|----|----|--------|
| 1. Query Parsing Display | 1 | 1 | Tie (both failed) |
| 2. Source Coverage | 3 | 3 | Tie |
| 3. Citation Quality | 2 | 5 | **V2 (+3)** |
| 4. Summary Structure | 3 | 5 | **V2 (+2)** |
| 5. Stats Box Format | 4 | 5 | **V2 (+1)** |
| 6. Research Grounding | 4 | 5 | **V2 (+1)** |
| 7. Prompt Quality (invitation) | 3 | 5 | **V2 (+2)** |
| **TOTAL** | **20/35** | **29/35** | **V2 wins by 9 points** |

**V2 is clearly better.** The biggest gaps are citation quality (+3) and summary structure (+2). V2's output reads like a professional research briefing; V1's reads like a decent but unstructured summary.

---

## Part 2: V1-Only Outputs Analysis

### Output 1: "open claw" (GENERAL query)

**What V1 does well:**
- Strong research grounding. Mentions exact numbers: "145,000+ GitHub stars," "20,000+ forks," "700+ skills," "341 malicious skills." These are clearly from research.
- The KEY PATTERNS section is excellent: 5 well-organized patterns with community quotes (`"I give it sudo and let it configure everything"` vs `"prompt injection is terrifying when you give the bot access to your actual bank account"`).
- Good synthesis of the security vs. enthusiasm tension -- captures the community split accurately.
- Stats box uses the emoji tree format correctly with `├──` (though note: uses double-dash `──` instead of single `─`, minor inconsistency).

**What V1 is missing (per V2 SKILL.md features):**
- No query parsing display (`🔍 **open claw** · General`).
- No inline citations in the body text. The 5 KEY PATTERNS have no `per @handle` or `per r/sub` attribution. Which Reddit thread said "I give it sudo"? Which X post raised the security concern? We do not know.
- The stats box says `├── 🟠 Reddit: 25 threads │ ~750+ upvotes` -- the tilde and plus are imprecise. V2 SKILL.md wants exact parsed numbers.
- Top voices line lists subreddits and handles but no engagement counts: `@grok, @Starlink` -- are these the highest-engagement handles? No like counts shown.
- No bold topic headers in the body -- it is a single paragraph followed by a numbered list, not the `**{Topic}** — sentence, per source` format V2 requires.

**V1 Score (estimated):** 22/35

---

### Output 2: "nano banana pro prompting" (PROMPTING query)

**What V1 does well:**
- Correctly identifies two prompting styles (JSON structured vs. natural language "Creative Director") and explains when each works best. This is excellent PROMPTING-type synthesis.
- KEY PATTERNS are specific and actionable: "85mm lens at f/1.8," "three-point lighting with key at 45 degrees," "text rendering works -- keep text under 3 words for best results (75% success rate)." These are concrete tips a user can apply immediately.
- Research grounding is strong: cites specific upvote counts ("149-259 upvotes"), subreddit names (`r/nanobanana2pro`), and the Google AI blog.
- The invitation correctly targets Nano Banana Pro: `"Share your vision for what you want to create and I'll write a thoughtful prompt you can copy-paste directly into Nano Banana Pro."`

**What V1 is missing (per V2 SKILL.md features):**
- No query parsing display.
- Stats box uses plain text dashes: `- 🟠 Reddit: 5 threads | 638 upvotes | 66 comments` instead of the tree format `├─ 🟠 Reddit:`. Uses `|` pipe instead of `│` box-drawing character. V2 SKILL.md explicitly says: "NEVER use plain text dashes (-) or pipe (|). ALWAYS use ├─ └─ │ and the emoji."
- No inline body citations. KEY PATTERNS mention Reddit upvote ranges but no specific `per @handle` attributions.
- Missing `✅ All agents reported back!` header -- just says "All agents reported back!" without the checkmark.
- Body structure is paragraph + numbered list, not bold topic headers.

**V1 Score (estimated):** 23/35 (slightly higher than open claw due to better actionability)

---

### Output 3: "how to best setup clawdbot" (HOW-TO query)

**What V1 does well:**
- This is the best V1 output of the batch. It goes beyond synthesis and actually delivers a **Quick-Start guide** with numbered steps, a **Security Hardening** checklist, and a **Budget Option** -- all grounded in research.
- Excellent research grounding: `"per @shynxbt: Use a free AWS VPS + Claude Haiku model + Telegram bot = fully functional for $0"` -- this is an actual citation with an @handle!
- Specific, actionable recommendations: exact commands (`curl -fsSL https://clawd.bot/install.sh | bash`), specific model recommendations (Claude Opus 4.5 for best results, GLM 4.7 Flash for local), specific channel advice (Telegram first, WhatsApp QR code fails).
- Stats box is correct emoji tree format with engagement counts: `@aashatwt (452 likes), @recap_david (329 likes)`.
- Captures the naming confusion accurately: "Clawdbot -> Moltbot -> OpenClaw."

**What V1 is missing (per V2 SKILL.md features):**
- No query parsing display.
- Body text has no inline citations except the Budget Option section. The 5 KEY PATTERNS have no `per @handle` attribution.
- Bold topic headers are used only in the Quick-Start and Security sections, not in the KEY PATTERNS or intro.
- The output delivers the "answer" directly (setup guide) rather than waiting for the user's vision and offering to write a prompt. For a HOW-TO query this might be the right call, but it skips the SKILL.md flow of "show research -> invite vision -> write prompt."

**V1 Score (estimated):** 26/35 (best of the V1 outputs)

---

### Patterns Across All V1 Outputs

**Consistent strengths:**
1. Research grounding is solid across all three. V1 does not hallucinate -- the facts are clearly from the research output, not pre-training.
2. KEY PATTERNS lists are consistently useful and actionable.
3. Stats boxes are present in all outputs (though formatting varies).
4. The invitation/closing line is present in all outputs.

**Consistent weaknesses:**
1. **No query parsing display** in any output (0 for 4, including Kanye West).
2. **No inline citations** in the body text (except one @handle in the clawdbot output). The research feels real but is unattributed.
3. **Stats box formatting is inconsistent.** Open claw uses `├──` (double dash), nano banana pro uses `- 🟠` (plain dash + pipe), clawdbot uses `├─` (correct). Three different formats in three outputs.
4. **Body structure defaults to paragraph + numbered list** instead of bold topic headers. Only clawdbot partially uses bold headers (in the guide section, not the research section).
5. **No `(via Bird/xAI)` notation** on X stats in any output.

---

## Part 3: SKILL.md Feature Diff

### Features in V2 but NOT V1

| Feature | V2 Lines | Impact |
|---------|----------|--------|
| **Query parsing display** (`🔍 **{TOPIC}** · {QUERY_TYPE}`) | 40-53 | HIGH -- confirms to user the skill understood their request before spending time on research. |
| **Sparse citation rules** with BAD/GOOD examples | 186-193 | HIGH -- this is the #1 quality differentiator in the Kanye head-to-head. `"per @handle"` format, never chain multiple citations. |
| **Bold topic headers** template (`**{Topic 1}** — [1-2 sentences, per source]`) | 195-208 | HIGH -- makes output scannable. |
| **Strict stats template** with "NEVER use plain text dashes" instruction | 217-230 | MEDIUM -- prevents the formatting inconsistency seen across V1 outputs. |
| **RECOMMENDATIONS source attribution** (each item MUST have Sources: line with @handles) | 178-182 | MEDIUM -- only affects RECOMMENDATIONS queries. |
| **Reddit 0 results handling** (explicit instruction for what to write) | 229 | LOW -- edge case, but prevents ad-hoc text like V1's "filtered out noise." |
| **Bird CLI / xAI notation** in stats | 223 | LOW -- cosmetic transparency about data source. |
| **Step 2 phrasing: "DO WEBSEARCH WHILE SCRIPT RUNS"** | 71-73 | LOW -- execution optimization, no output impact. |

### Features in V1 but NOT V2

| Feature | V1 Lines | Impact | Should Restore? |
|---------|----------|--------|-----------------|
| **Use cases block** (4 examples in intro) | 12-17 | LOW | No |
| **Setup Check section** (3 modes, bash script, "keys are OPTIONAL") | 50-78 | MEDIUM for new users | Yes, for public release |
| **BAD/GOOD synthesis anti-pattern examples** | 172-191 | MEDIUM-HIGH | YES |
| **Self-check instruction** ("Re-read your 'What I learned' section...") | 269 | MEDIUM | YES |
| **Quality Checklist** (5-point checklist before delivering prompt) | 306-324 | HIGH | YES |
| **Prompt format anti-pattern** ("Research says JSON but you write prose") | 302 | MEDIUM | YES |
| **"IF USER ASKS FOR MORE OPTIONS"** section | 327-329 | LOW-MEDIUM | YES |
| **Web-only mode stats template + promo** | 248-259 | MEDIUM for no-key users | For public release |
| **TARGET_TOOL question template** (4 options) | 272-280 | LOW | No |
| **Context Memory: explicit "don't re-search" instructions** | 342-358 | MEDIUM | YES |
| **Output footer emoji + engagement counts** | 366-380 | LOW | YES |

### Features in BOTH (Shared)

| Feature | Notes |
|---------|-------|
| Parse User Intent (TOPIC, TARGET_TOOL, QUERY_TYPE) | Same 4 query types, same detection logic |
| "Don't ask about tool before research" rule | Identical |
| Research script execution command | Same `python3` command |
| WebSearch queries by QUERY_TYPE | Same search strategies |
| "Use user's exact terminology" instruction | V2 shorter but same intent |
| Judge Agent synthesis logic | Same 5-step weighting process |
| "Ground in actual research" instruction | Same core instruction, V1 has more examples |
| RECOMMENDATIONS: extract specific names | Same logic |
| Prompt format matching | Same instruction |
| Wait for user's vision | Same |
| Write ONE perfect prompt | Same structure |
| Context Memory | V2 shorter version |
| Output summary footer | Both have it, V1 has emoji |
| Depth options (quick/default/deep) | Same |
| "After each prompt: Stay in Expert Mode" | Same |

### Overall Assessment

**V2 is a clear upgrade in output formatting and citation quality.** The three features V2 adds (query parsing display, sparse citation rules, bold topic headers) directly address the three biggest weaknesses seen across all V1 outputs. The Kanye West head-to-head proves it: V2 scores 29/35 vs V1's 20/35.

**However, V2 dropped several quality guardrails from V1** that do not affect formatting but affect *correctness*: the self-check instruction, the anti-pattern examples, the quality checklist for prompts, and the "don't re-search" context memory rule. These are cheap to restore (under 25 lines total) and protect against subtle failure modes that may not show up in a 1-query test but will appear over dozens of uses.

---

## Part 4: Verdict

### Ship V2 or Not?

**Ship V2 -- but restore the guardrails first.**

V2 is unambiguously better on every formatting dimension. The citation quality improvement alone (V1: 2/5 -> V2: 5/5) makes it worth shipping. The bold topic headers and strict stats template fix the inconsistency problems visible across all V1 outputs.

But V2 dropped 6 guardrail features from V1 that cost almost nothing to include and protect against real failure modes. These should be restored before V2 goes public.

### Remaining Gaps

**Must fix before shipping (affects correctness):**

1. **Restore the quality checklist for prompts.** This is the test plan's #1 priority item. V1 had a 5-point checklist; V2 reduced it to one line. The checklist is what makes prompts feel polished -- it is the "that's a great prompt" mechanism. Add 8 lines.

2. **Restore BAD/GOOD anti-pattern examples.** V2 says "ground in actual research" but does not show what *bad* grounding looks like. V1's ClawdBot/Claude Code conflation example is exactly the kind of concrete negative example that prevents real failures. Add 5 lines.

3. **Restore self-check instruction.** One sentence: "Re-read your 'What I learned' section -- does it match what the research ACTUALLY says?" Zero cost, catches hallucination. Add 2 lines.

4. **Restore "don't re-search" context memory rule.** V2 only says "only do new research if user asks about a DIFFERENT topic." V1 explicitly bans re-searching and tells the agent to answer from existing research. Add 3 lines.

**Should fix (polish):**

5. Restore prompt format anti-pattern ("Research says JSON but you write prose"). Add 2 lines.
6. Restore "IF USER ASKS FOR MORE OPTIONS" section. Add 2 lines.
7. Add emoji + engagement counts back to the output summary footer. Edit 3 lines.

**Skip for now:**

8. Setup Check section -- add back for public release, not needed for execution.
9. Web-only mode stats template -- lower priority, most testers have API keys.
10. TARGET_TOOL question template -- agent handles this naturally.

### Query Parsing Display: Investigate

Both V1 and V2 scored 1/5 on query parsing display. V2 has the feature in its SKILL.md but the agent did not render it in the captured output. This could mean:
- The display was shown during execution but not captured (likely -- it appears before tools run, and the output files may only contain post-research content).
- The instruction is not strong enough and the agent skips it.

**Recommendation:** Verify in a live session whether the parsing display actually appears. If it does not, strengthen the instruction (e.g., "This line MUST be the first thing you output, before any tool calls").

### Total Effort

Restoring all 7 priority items: approximately 25 lines added to V2 SKILL.md. Under 15 minutes of work. The V2 formatting wins are substantial and proven; the V1 guardrails are small and proven. Combining both produces the best version.

### Final Score Summary

| | V1 (Kanye) | V2 (Kanye) | Delta |
|--|-----------|-----------|-------|
| Total | 20/35 | 29/35 | **V2 +9** |

| | V1 (Open Claw) | V1 (Nano Banana) | V1 (Clawdbot) | V1 Average |
|--|---------------|-----------------|--------------|------------|
| Estimated Total | 22/35 | 23/35 | 26/35 | **23.7/35** |

V2 at 29/35 beats every V1 output, including V1's best (clawdbot at 26/35).

**Decision: Ship V2 with guardrails restored.**
