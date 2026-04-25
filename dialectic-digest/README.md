# Dialectic Digest

A Claude Code skill that takes today's top headlines, runs Karpathy's iterative argument/counter-argument loop on each one, and delivers a balanced briefing so you can read both sides and form your own conclusions.

Inspired by [this exchange](https://x.com/chamath/status/1905693488668361013) between Chamath Palihapitiya and Andrej Karpathy.

## Install

Copy the skill file into your Claude Code project:

```bash
mkdir -p .claude/commands
curl -o .claude/commands/dialectic-digest.md \
  https://raw.githubusercontent.com/Percival-Labs/dialectic-digest/main/dialectic-digest.md
```

Or just download `dialectic-digest.md` and drop it in `.claude/commands/`.

## Use

```
/dialectic-digest
```

Get today's top 5-7 headlines with full dialectic analysis.

```
/dialectic-digest AI regulation
```

Focus on a specific topic.

## What it does

For each headline, the skill runs two full rounds of argument and rebuttal:

1. **Thesis** — The strongest case for the mainstream position
2. **Antithesis** — An equally rigorous counter-argument
3. **Thesis Rebuttal** — Responds to the counter-argument, concedes where warranted
4. **Antithesis Rebuttal** — Responds back, concedes where warranted

Then a synthesis that identifies:
- Where both sides actually agree
- The core **factual** disagreement (what data would settle it?)
- The core **values** disagreement (what priorities are in tension?)
- What to **watch for** next

The iteration is the key insight. A single pass gives you "here's side A, here's side B." Two rounds of rebuttal force each side to engage with the other's strongest points and concede where they're wrong. What survives is worth reading.

## Example Output

See [`example-output.md`](./example-output.md) for a full run on the Meta/YouTube social media addiction verdict (March 28, 2026).

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (any version with web search)
- No API keys, dependencies, or setup beyond Claude Code itself

## How it works

It's one markdown file. The file contains structured instructions that Claude follows when you invoke the command. Claude uses its built-in web search to find today's headlines, then runs the dialectic loop using its own reasoning. No external services, no backend, no database.

## License

MIT. Do whatever you want with it.

---

Built by [Percival Labs](https://percival-labs.ai). We build trust infrastructure for the agent economy.
