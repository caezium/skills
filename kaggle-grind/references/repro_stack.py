"""
S6E6 "Predicting Stellar Class" — 19th/2742 (private 0.97037). Clean reproducible recipe.
================================================================================================
DRAFT — not published. Convert to .ipynb (jupytext/nbconvert) before any Kaggle upload.

WHAT THIS DOES (the honest, private-valid method that survived the public->private shakeup):
  Stack GENUINE out-of-fold (OOF) predictions — our own model zoo + publicly-shared grandmaster
  OOF corpora — with a multinomial Logistic Regression meta-model on log-prob (logit) features,
  then apply a per-class log-offset decision rule tuned for BALANCED ACCURACY.

WHY IT WORKS: the public LB was a 20% sample under balanced accuracy; the top public cluster was
  "ridge-flip" notebooks that edit specific PUBLIC test-row labels (a no-op on the private 80%).
  We ignored the public LB, optimized shared-fold CV, and stacked genuine OOFs. When the flips
  collapsed on private, this held and climbed ~200 places.

CREDITS (this result is built on the community's openly-shared genuine OOFs — thank you):
  - cdeotte/s6e6-oof-and-test-preds        (XGB/RealMLP/TabM/LGBM OOF+test)
  - lzsecurity/s6e6-high-scoring-base-model-oof-predictions  ("midnight" cat/lgb/xgb OOF+test)
  - fachri00/ps6e6-stacker                 (43-model OOF corpus)
  - broccoli beef (discussion 703535): spectral_type/galaxy_population are binned color indices.

REPRODUCIBILITY NOTE: this script consumes OOF .npy/.csv assets. Our OWN 22-model zoo OOFs are
  produced by the scripts in the parent repo (01..18, zoo2_*). To reproduce end-to-end you need
  either (a) our oof/ directory, or (b) just the public OOFs below for a strong ~0.970+ stack.
  The public-OOF-only path (set USE_OWN_ZOO=False) already reaches ~0.970 and is fully self-contained.
"""
import numpy as np, pandas as pd, glob, os, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

# ---- paths (Kaggle: /kaggle/input/...; local: adjust) ----
COMP   = "/kaggle/input/playground-series-s6e6"
CDEOTTE= "/kaggle/input/s6e6-oof-and-test-preds"
LZ     = "/kaggle/input/s6e6-high-scoring-base-model-oof-predictions"
FACHRI = "/kaggle/input/ps6e6-stacker"
OWN    = "./oof"              # our own zoo OOFs (optional)
USE_OWN_ZOO = os.path.isdir(OWN)

COLS = ["GALAXY","QSO","STAR"]; NTR, NTE = 577347, 247435; EPS = 1e-6
tr = pd.read_csv(f"{COMP}/train.csv"); te = pd.read_csv(f"{COMP}/test.csv")
y  = tr["class"].map({"GALAXY":0,"QSO":1,"STAR":2}).values
cl = lambda p: np.log(np.clip(p, EPS, 1.0))
def bal(p): return float(np.mean([(p[y==c]==c).mean() for c in range(3)]))

# ================================================================= collect genuine OOF sources
# Each entry: (name, oof[NTR,3], test[NTE,3]).  RIGOR: we only keep a source whose OOF argmax
# balanced-accuracy on our y lands in ~0.95-0.97 (proves correct id-alignment, not chance ~0.33).
models = []
def add(name, oof, test):
    if oof.shape==(NTR,3) and test.shape==(NTE,3):
        b = bal(oof.argmax(1))
        if b >= 0.955: models.append((name, oof, test, b))
        else: print(f"  reject {name}: OOF bal-acc {b:.4f} (misaligned/weak)")

# --- public: cdeotte (some files carry 'id', some are positional, tabm0 is a melted single col)
def cd_id(nm):  # id-bearing csvs
    o = pd.read_csv(f"{CDEOTTE}/oof_preds_{nm}.csv").sort_values("id")[COLS].values
    t = pd.read_csv(f"{CDEOTTE}/test_preds_{nm}.csv").sort_values("id")[COLS].values
    return o, t
def cd_pos(nm):  # positional csvs (no id)
    o = pd.read_csv(f"{CDEOTTE}/oof_final_{nm}.csv")[COLS].values
    t = pd.read_csv(f"{CDEOTTE}/test_final_{nm}.csv")[COLS].values
    return o, t
for nm in ["lgbm5_v1","realmlp0_v12","realmlp2_v10"]: add(f"cd_{nm}", *cd_id(nm))
for nm in ["tabm1_v1","xgb6_v1"]:                     add(f"cd_{nm}", *cd_pos(nm))
add("cd_tabm0",
    pd.read_csv(f"{CDEOTTE}/oof_preds_tabm0_v2.csv")["class"].values.reshape(NTR,3),   # C-order reshape
    pd.read_csv(f"{CDEOTTE}/test_preds_tabm0_v2.csv")["class"].values.reshape(NTE,3))

# --- public: lzsecurity midnight (npy; OOF concatenated train+external -> take first NTR rows)
for nm in ["cat","lgb","xgb"]:
    add(f"lz_{nm}", np.load(f"{LZ}/oof_{nm}_midnight.npy")[:NTR], np.load(f"{LZ}/test_{nm}_midnight.npy"))

# --- public: fachri ps6e6-stacker corpus (43 OOFs; positional; skip overlaps with cdeotte)
overlap = {"lgbm5_v1","realmlp0_v12","realmlp2_v10","tabm1_v1","xgb6_v1"}
for f in sorted(glob.glob(f"{FACHRI}/oof/*_oof.csv")):
    nm = os.path.basename(f)[:-8]
    if nm in overlap: continue
    tf = f.replace("/oof/","/test_pred/").replace("_oof.csv","_test.csv")
    if not os.path.exists(tf): continue
    try: add(f"stk_{nm}", pd.read_csv(f)[COLS].values, pd.read_csv(tf)[COLS].values)
    except Exception: pass

# --- optional: our own 22-model zoo (produced by 01..18/zoo2_* in the parent repo)
if USE_OWN_ZOO:
    for f in sorted(glob.glob(f"{OWN}/*_oof.npy")):
        nm = os.path.basename(f)[:-8]
        if nm in {"lgbm_interact","lgbm_locus","lgbm_pseudo_iter"}: continue   # confirmed-negative
        t = f.replace("_oof.npy","_test.npy")
        if os.path.exists(t): add(f"own_{nm}", np.load(f), np.load(t))

print(f"genuine sources kept: {len(models)}")

# ================================================================= correlation-prune (diversity)
# Keep a model only if its argmax LABELS disagree with every already-selected model on >0.8% of rows.
labs = {n: o.argmax(1) for n,o,t,b in models}
models.sort(key=lambda m: -m[3])           # strongest standalone first
selected = [models[0]]
for m in models[1:]:
    if max((labs[m[0]] == labs[s[0]]).mean() for s in selected) < 0.992:
        selected.append(m)
print(f"corr-pruned to {len(selected)} decorrelated models")

# ================================================================= LR meta on log-prob features
Xo = np.hstack([cl(o) for _,o,_,_ in selected])
Xt = np.hstack([cl(t) for _,_,t,_ in selected])
skf = list(StratifiedKFold(5, shuffle=True, random_state=42).split(np.zeros(NTR), y))
def meta(C):
    mo = np.zeros((NTR,3)); mt = np.zeros((NTE,3))
    for tri, vai in skf:
        sc = StandardScaler().fit(Xo[tri])
        lr = LogisticRegression(C=C, max_iter=200, n_jobs=-1).fit(sc.transform(Xo[tri]), y[tri])
        mo[vai] = lr.predict_proba(sc.transform(Xo[vai]))
        mt += lr.predict_proba(sc.transform(Xt)) / 5
    return mo, mt

# ================================================================= balanced-accuracy decision rule
# argmax under-predicts minorities; add a per-class log-offset [0,a,b] tuned to max balanced accuracy.
def tune(mo):
    lp = np.log(np.clip(mo, EPS, 1.0)); g = np.linspace(-3, 3, 61); best = (bal(mo.argmax(1)), np.zeros(3))
    for a in g:
        c1 = lp[:,1] + a
        for b in g:
            c2 = lp[:,2] + b
            pred = np.where(c2 >= np.maximum(lp[:,0], c1), 2, np.where(c1 >= lp[:,0], 1, 0))
            v = bal(pred)
            if v > best[0]: best = (v, np.array([0., a, b]))
    return best

best = (0, None, None, None)
for C in [0.05, 0.1, 0.3, 1.0]:
    mo, mt = meta(C); b, off = tune(mo)
    print(f"  LR C={C}: tuned OOF balanced-acc = {b:.5f}  offsets={off.round(3)}")
    if b > best[0]: best = (b, C, mt, off)
b, C, mt, off = best
print(f"BEST: C={C}  OOF {b:.5f}  (public-OOF-only reaches ~0.970; +own zoo -> ~0.9704 OOF / 0.97118 public / 0.97037 private)")

# NOISE FLOOR: at n=577k, balanced-acc SE ~ 0.0003 -> only trust Δ > ~0.0006 as a real gain.
pred = (np.log(np.clip(mt, EPS, 1.0)) + off).argmax(1)
inv = {0:"GALAXY", 1:"QSO", 2:"STAR"}
pd.DataFrame({"id": te["id"], "class": [inv[p] for p in pred]}).to_csv("submission.csv", index=False)
print("wrote submission.csv  |  class dist:", pd.Series(pred).map(inv).value_counts().to_dict())
