---
name: kaggle-grind
description: >-
  Autonomous, disciplined Kaggle competition workflow — the loop that took Playground S6E6 to
  19th/2742 (top 0.7%). Use when working a Kaggle competition (Playground/tabular especially):
  building a model zoo, stacking, deciding what to submit, choosing final submissions, or reacting
  to a public leaderboard that looks suspiciously high. Encodes the hard-won rules: trust CV not a
  flip-farmable public LB, hunt and stack genuine public OOF corpora, gate every candidate on the
  statistical noise floor, hedge two genuine decorrelated finals (never a flip), verify finals every
  pass, and run a resume-surviving scheduled loop. Triggers: "kaggle", "leaderboard", "OOF", "stack",
  "which submission", "final selection", "the LB shuffled", "public score", "should I submit".
---

# kaggle-grind — the autonomous competition loop

This skill encodes a **process**, not a model. It reliably converts "disciplined grind" into medal-zone
finishes by refusing the traps that sink most teams. It was validated on Playground S6E6: **19th / 2742
(top 0.7%), ▲202 places in the private shakeup, above a Grandmaster** — by doing exactly the below.

## The one idea that matters most
**Public LB ≠ the target.** Many comps (especially Playground) score the public LB on a small sample
(e.g. 20% of test). Under fragile metrics (balanced accuracy, small-sample AUC) the public top fills
with **public-LB-probing / "flip"** notebooks that reverse-engineer *public* test-row labels. Those are a
**no-op on the private set** and collapse in the shakeup. **Optimize CV. Treat the public LB as one noisy
sample, never the objective.** (A Grandmaster confirmed this post-S6E6, verbatim.)

## The loop (run each of these as a pass; a cron can drive it — see below)

### 0. Day-1 recon (do this FIRST, not on day 20)
- Read the LB description: **what % is public?** Note the metric and whether it's shakeup-prone.
- Pull the #1 public notebook (`kaggle kernels list -c <comp> --sort-by scoreDescending`,
  `kaggle kernels pull`). **Classify it: genuine model vs public-LB-probe.** Fingerprints of a flip/probe:
  many teams at the *identical* 5-decimal score; 1–2-submission teams at the top; code that edits specific
  `test_row_id -> label` using known public scores; hardcoded "bad id" lists.
- Compute the **noise floor**: for balanced accuracy on n rows, SE ≈ sqrt(sum_k r_k(1-r_k)/n_k)/K ≈ ~0.0003
  at n~500k. **Any OOF/LB Δ below ~2·SE (~0.0006) is noise.** Write it down; gate everything on it.

### 1. Build a shared-fold, leak-free OOF zoo
- ONE fold split across every model: `StratifiedKFold(k, shuffle=True, random_state=42)`. Non-negotiable —
  it's what makes OOFs stackable. Save each model's OOF `(n_train,C)` + test `(n_test,C)` as .npy.
- Diverse families: LGBM/XGB/CatBoost/HistGB/ExtraTrees + a couple NN families + logreg/kNN. But expect
  trees to dominate tabular; NNs are often soft. Diversity for the *stack*, not for standalone strength.
- Leakage paranoia: fit every y-dependent transform (target encoding, scaler, pseudo-labels) on train[~fold]
  ONLY. Verify: a shuffled-label control must give ~chance.

### 2. ★ Hunt and stack GENUINE public OOF corpora (the highest-EV lever)
- This is usually what breaks your own-zoo ceiling. Search **early**:
  `kaggle datasets list -s "<comp> oof"`, `-s "<comp> stacker"`, and scan top notebooks for shared
  OOF/test-pred datasets. Grandmasters publish these (e.g. cdeotte-style OOF+test dumps).
- **RIGOR before trusting any external OOF**: id-align it to your train/test order, then verify its OOF
  argmax balanced-accuracy on your y lands in the sane model range (e.g. 0.95–0.97), NOT ~chance. A file
  that scores chance is misaligned — reject it. (A naive misaligned blend cost us a submission once.)
- Stacking public **OOFs** (train-side, out-of-fold, id-aligned) is legitimate and **private-valid** —
  categorically different from copying a flip submission.

### 3. Meta-stack + decision rule
- Multinomial **Logistic Regression on log-prob (logit) features** of all OOFs. Regularized LR generalizes
  where Caruana hill-climbing overfits. Sweep C.
- **Correlation-prune** first: keep a model only if its argmax labels disagree with every selected model on
  >~0.8% of rows. Diversity, not count, drives the gain.
- **Decision rule** (metric-specific, often the biggest single lever): for balanced accuracy, tune a per-class
  **log-offset** `[0,a,b]` added to log-probs before argmax — argmax under-predicts minorities.

### 4. Gate, probe, accept
- Accept a candidate only if OOF Δ **exceeds the noise floor** AND (ideally) an LB probe confirms. Many
  "higher OOF" candidates LOSE on LB — trust LB-held gains, distrust 4th-decimal OOF nudges.
- BUT on the **final day with free submission budget, PROBE every distinct genuine candidate anyway** — the
  noise floor bounds confidence, not the value of a cheap real data point. (Our final #1 was "within noise"
  on OOF yet +0.0011 on LB.)

### 5. Finals (the medal decision — rule #13)
- Pick **two GENUINE, decorrelated** submissions. **NEVER a flip** as a final (vanity on public, no-op/risk
  on private). Submit strong candidates EARLY (dense plateaus tiebreak by submission time).
- **Verify the selected finals EVERY pass** once submissions exist — assert both are genuine. (A flip had
  auto-slotted into final #1; caught on deadline day. That check alone can save the medal.)
- Manually pin — don't let Kaggle auto-pick two correlated public-bests.

## Anti-patterns (proven to waste time / lose)
- Treating a flip-farmed public LB as the ceiling. (We wasted ~10 days on this once.)
- Writing an **unqualified "ceiling"** conclusion. Scope it: "ceiling of OUR models" + always ask "what would
  a stronger external model add?" Our "genuine ceiling" was wrong twice — public OOFs broke it.
- Chasing 4th-decimal OOF gains, more tree-FE, or more correlated GBDTs. Cats that are binned color-indices,
  external data with high adversarial AUC, iterative pseudo — usually ≤+0.0002 or negative.
- Local-eval "improvements" that aren't verified to generalize (they overfit your exact local set).

## Running it as a durable loop (optional)
- Use the host harness's recurring-monitor or scheduled-task mechanism to fire a self-contained pass prompt.
  In Claude Code this may be a cron integration; in Codex/T3 use the product's recurring monitoring flow.
  Guard with a lock file
  (`/tmp/<comp>_loop.lock`, epoch + TTL) so passes don't overlap. `/tmp` is wiped on reboot — **re-download
  public OOF datasets each pass.** Use `nohup python -u ...` for long jobs so they survive session resumes.
- **Convergence downgrade**: if N consecutive passes find no candidate above the noise floor AND no new public
  OOF source, drop cron frequency (hourly → 6h) — don't burn tokens re-confirming a ceiling.
- **CLI/submit caveat**: Kaggle's `competitions.*`/`kernels.*` API can 401 for hours while `datasets.*` works.
  Confirm your real submit path EARLY (CLI vs browser-upload vs user-drag). The browser file-upload tool is
  sandboxed to session-shared paths — it can't upload arbitrary repo files, so a human may need to drag-drop.

## Reference
See `references/s6e6_retrospective.md` for the full worked example (every lever, the exact numbers, the
7 workflow improvements) and `references/repro_stack.py` for the winning stack recipe.
