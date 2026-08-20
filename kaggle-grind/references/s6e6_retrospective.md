# S6E6 "Predicting Stellar Class" — Retrospective (19th / 2742 = top 0.7%)

## Outcome
- **Final: rank 19 / 2742 teams (top 0.7%), private LB 0.97037.** ▲202 places in the public→private shakeup.
- Finals = 2 genuine decorrelated stacks: `sub_mega` (public 0.97118 / private 0.97037) + `sub_cdstack` (public 0.97004). A flip was NEVER selected.
- **Beat Chris Deotte (Grandmaster, rank 25, private 0.97024)** — using his own published OOF assets as *inputs* plus a wider genuine corpus.

## What won it
1. **CV-not-public-LB discipline (the whole game).** Metric was Balanced Accuracy on a 20%-public / 80%-private split. The public top-3% (~0.97259) was a dense "ridge-flip" cluster — notebooks that edit specific *public* test-row labels via public-score feedback. Flips are a **no-op on private** → the entire cluster collapsed. Deotte confirmed post-comp: *"All public notebooks scoring above my starter were overfitting public LB… we cannot evaluate improvements on public LB, especially not for Balanced Accuracy."*
2. **Public grandmaster OOFs, stacked leak-free.** Our own 22-model zoo capped at public 0.96766. The break came from stacking **genuine public OOF corpora** (cdeotte/lz 9 models → 0.97004; then fachri's 43-OOF corpus + TabPFN → 0.97118). Stacking public *OOFs* (train-side, id-aligned, out-of-fold) is legitimate and private-valid — categorically different from copying a flip.
3. **Noise-floor rigor.** At n=577k, balanced-acc SE≈0.0003 → any Δ<~0.0006 is noise. This gate (a) stopped us wasting finals on 4th-decimal OOF nudges that had lost on LB before, and (b) correctly flagged sub_mega's +0.00114 as a REAL gain worth swapping in as final #1.
4. **Correct finals hedge (rule #13).** Two genuine, decorrelated stacks — not the flip. The flip would have looked top-3% on public that morning and cratered on private.

## What the winners/community confirmed (our instincts were right)
- **spectral_type/galaxy_population = binned color indices** (g-r, u-r thresholds; a depth-3 DecisionTree reproduces them at 100%). Add only ~+0.0002 to LGBM. → matches our weak-cat-model finding exactly.
- **External SDSS17 data doesn't help** (nybbler, 3rd place: "adversarial AUC is quite high"). → matches our external result (+0.0002, "did not break the wall").
- **The winning method = OOF-logit LR-stacker** (xiaoyang66, 52nd, used Deotte's exact recipe). We ran the same method on a *wider* corpus → 19th vs their 52nd. Same idea, better execution.

## Levers tested (full honesty — most were negative/noise)
Decision-rule tuning +0.009 (the one big lever). Everything else ≤+0.0002 or negative: FE colors/interaction/spline/TE, external SDSS, pseudo×2 (iterative NEGATIVE), stellar-locus (NEGATIVE), native cats (weak), CatBoost (genuinely weak 0.963), RealMLP/TabM/MLP/TabPFN-v2/v2.6 (all soft NNs ~0.95-0.96), multi-seed meta (0). The gains came ONLY from stacking stronger *external genuine* models.

---

## Workflow improvements (for the autonomous loop to do better next time)

1. **Check public-vs-private split + metric-overfit risk on DAY 1, not day 20.** The single biggest strategic fact — that public LB was a 20% flip-farmable sample and CV was the only honest signal — was knowable at hour 1 (read the LB description + one top "flip" notebook). We spent ~10 days treating 0.966 as a ceiling before realizing the 0.971 above us was fake. **Add a standing day-1 step: read the LB %-split, pull the #1 public notebook, classify it genuine-vs-probe.**

2. **Hunt public OOF *corpora* early and aggressively.** The 0.96766→0.97118 jump came entirely from public grandmaster OOFs (cdeotte, lz, fachri's 43-model corpus). We found them late (day 13+). **Add a standing step: `kaggle datasets list -s "<comp> oof"` + scan top notebooks for shared OOF/test-pred datasets in the first days.** Stacking public OOFs is the highest-EV genuine lever in Playground stacking comps and should be tried before grinding a bespoke zoo.

3. **Kill the "intrinsic ceiling" conclusion faster.** I declared 0.96766 the "genuine ceiling" and wrote it into memory — twice — before the user pushed back and it turned out to be only *our zoo's* ceiling. **Lesson: "ceiling" claims must be scoped ("ceiling of OUR models") and always paired with "what would a stronger external model add?" Never write an unqualified ceiling to memory.**

4. **Don't trust the file-upload sandbox for the final submit.** The browser file_upload tool refused all working-dir paths; only the user could drag-drop. On a deadline this is a single point of failure. **Lesson: verify the actual submit path (CLI vs browser-upload vs user-drag) EARLY, not in the final hours.** And when the CLI API 401s (it was down the entire final day for competitions.*/kernels.* while datasets.* worked), have the human-in-the-loop submit path confirmed well ahead.

5. **The cron loop worked but was redundant near the end.** Once the genuine lever was exhausted, each hourly pass just re-confirmed the ceiling and burned tokens. **Add a convergence check: if N consecutive passes produce no new candidate above the noise floor AND no new public OOF source, downgrade to a low-frequency monitor (e.g. 6h) instead of hourly.**

6. **Verify finals state EARLY and defensively.** We discovered on the final day that a *flip* was sitting in final slot #1 (auto-selected or left over) — a rule-#13 violation that would have cost the medal. **Add a standing check every pass once submissions exist: read the currently-selected finals and assert both are genuine (non-flip) — flag immediately if not.**

7. **Probe candidates even when "within noise" on the final day.** I nearly didn't submit sub_mega ("low-EV, within noise floor"). It scored +0.00114 (a real gain) and became final #1. **Lesson: on the final day with free submission budget, PROBE every distinct genuine candidate — the noise floor bounds confidence, not the decision to gather a cheap data point.**
