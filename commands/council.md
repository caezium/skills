---
name: llm-council
description: "Run any question, idea, or decision through a council of 5 AI advisors who independently analyze it, peer-review each other anonymously, and synthesize a final verdict. Based on Karpathy's LLM Council methodology. MANDATORY TRIGGERS: 'council this', 'run the council', 'war room this', 'pressure-test this', 'stress-test this', 'debate this'. STRONG TRIGGERS (use when combined with a real decision or tradeoff): 'should I X or Y', 'which option', 'what would you do', 'is this the right move', 'validate this', 'get multiple perspectives', 'I can't decide', 'I'm torn between'. Do NOT trigger on simple yes/no questions, factual lookups, or casual 'should I' without a meaningful tradeoff."
---

# LLM Council

Use this skill when the user has a real decision with stakes, tradeoffs, and uncertainty. The goal is to create productive tension, surface blind spots, and end with a clear recommendation.

## When To Use It

Good fits:
- Pricing, offer, positioning, hiring, product, strategy, messaging, and go-to-market decisions
- Questions where a wrong call is expensive
- Situations where the user explicitly wants multiple perspectives or a rigorous pressure test

Bad fits:
- Factual lookups with one correct answer
- Simple formatting, summarization, or drafting requests
- Casual "should I" questions with no meaningful tradeoff

## The Five Advisors

Use exactly these five thinking styles:

1. **The Contrarian** — Looks for failure modes, weak assumptions, hidden risks, and ignored downside.
2. **The First Principles Thinker** — Strips away assumptions, reframes the actual problem, and rebuilds from fundamentals.
3. **The Expansionist** — Looks for upside, leverage, asymmetric opportunities, and paths to a bigger win.
4. **The Outsider** — Assumes no insider context. Flags jargon, confusion, missing framing, and curse-of-knowledge issues.
5. **The Executor** — Focuses on feasibility, sequencing, time-to-value, and the fastest credible next move.

Do not collapse or rename these roles.

## Workflow

### Step 1: Frame the Question

Before framing, quickly gather context from the workspace:
- `CLAUDE.md` or `claude.md` in the project root
- `memory/` folders
- files the user attached or named
- relevant transcripts or prior council outputs

Spend no more than ~30 seconds on context gathering. Read the 2-3 files most likely to improve specificity.

Write a neutral framed question including:
1. The core decision
2. Key context from the user
3. Key context from workspace files
4. What is at stake

Do not steer the answer. If the request is too vague, ask one clarifying question, then proceed.

Save the framed question for the transcript.

### Step 2: Convene the Council (5 sub-agents in parallel)

Launch all 5 advisors simultaneously using the Agent tool. Each advisor gets:
1. Their identity and thinking style
2. The framed question
3. This instruction: "Respond independently. Do not hedge. Do not try to be balanced. Lean fully into your assigned angle. If you see a fatal flaw, say it. If you see major upside, say it. The synthesis happens later."

Target 150-300 words per advisor.

**Sub-agent prompt template:**

```
You are [Advisor Name] on an LLM Council.

Your thinking style: [advisor description]

A user has brought this question to the council:

---
[framed question]
---

Respond from your perspective. Be direct and specific. Don't hedge or try to be balanced. Lean fully into your assigned angle. The other advisors will cover the angles you're not covering.

Keep your response between 150-300 words. No preamble. Go straight into your analysis.
```

IMPORTANT: Launch all 5 Agent calls in a single message so they run in parallel.

### Step 3: Peer Review (5 sub-agents in parallel)

This step is required. Do not skip it.

Collect the 5 advisor responses. Anonymize them as Response A through E (randomize the mapping).

Launch 5 reviewer sub-agents in parallel. Each sees the framed question and all anonymized responses, then answers:
1. Which response is strongest and why?
2. Which response has the biggest blind spot and what is it?
3. What did all five responses miss?

Target under 200 words per review.

**Reviewer prompt template:**

```
You are reviewing the outputs of an LLM Council. Five advisors independently answered this question:

---
[framed question]
---

Here are their anonymized responses:

**Response A:** [response]
**Response B:** [response]
**Response C:** [response]
**Response D:** [response]
**Response E:** [response]

Answer these three questions. Be specific. Reference responses by letter.

1. Which response is the strongest? Why?
2. Which response has the biggest blind spot? What is it missing?
3. What did ALL five responses miss that the council should consider?

Keep your review under 200 words. Be direct.
```

### Step 4: Chairman Synthesis

After peer review, synthesize a final verdict from all advisor responses and all peer reviews. The chairman may disagree with the majority if reasoning supports it.

Use this exact output structure:

```
## Where the Council Agrees
[High-confidence convergence points.]

## Where the Council Clashes
[Real disagreements and why they exist.]

## Blind Spots the Council Caught
[Insights that surfaced through peer review.]

## The Recommendation
[A clear answer. No "it depends" cop-out.]

## The One Thing to Do First
[One concrete next step.]
```

### Step 5: Generate Artifacts

Create two files in the current workspace:

```
council-report-[timestamp].html
council-transcript-[timestamp].md
```

**HTML report** — single self-contained file with inline CSS:
1. The original question at the top
2. The chairman's verdict prominently displayed
3. A simple agreement/disagreement visual
4. Collapsible sections for each advisor's full response (collapsed by default)
5. Collapsible peer review section
6. Footer with timestamp and topic

Style: white background, subtle borders, system sans-serif font stack, soft accent colors per advisor. Professional briefing document aesthetic.

**Markdown transcript** — full record containing:
- Original question
- Framed question
- All 5 advisor responses
- Anonymization mapping
- All 5 peer reviews
- Chairman synthesis

Open the HTML report after generating it.

## Quality Bar

- Always run all 5 advisors in parallel using multiple Agent tool calls in one message.
- Always anonymize before peer review.
- Do not smooth over genuine disagreement.
- Prefer sharp, specific reasoning over polite vagueness.
- End with a recommendation and one first action.
- If context is thin, state the missing information instead of pretending certainty.
