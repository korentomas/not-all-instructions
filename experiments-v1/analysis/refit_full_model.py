"""Refit the v1 FULL model (per-decision baseline+treatment PLUS per-model and
per-codebase intercepts) on the original 244 observations, to verify and archive
the convergence behaviour the paper reports (the full-model trace was never saved).
Run from anywhere; reads experiments-v1/data/{phase1,phase3}.
"""
import json, os, glob, warnings
import numpy as np, pandas as pd, arviz as az, pymc as pm, pytensor.tensor as pt
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
RANDOM_SEED = sum(map(ord, "retention-full-model-v1"))
rng = np.random.default_rng(RANDOM_SEED)

rows = []
for sub in ("phase1", "phase3"):
    for f in sorted(glob.glob(os.path.join(DATA, sub, "*.json"))):
        if "v3" not in os.path.basename(f):
            continue
        log = json.load(open(f))
        if "turns" not in log:
            continue
        model = log.get("model", "unknown").split("/")[-1]
        for t in log["turns"]:
            if t["turn"] < 20:
                continue
            for k, v in t.get("compliance", {}).items():
                if k.startswith("decision:"):
                    rows.append({"model": model, "condition": log.get("condition", "treatment"),
                                 "codebase": log.get("codebase"), "decision": k.split(":")[1],
                                 "score": int(v["score"])})
df = pd.DataFrame(rows).drop_duplicates()
print(f"loaded {len(df)} obs | models {df.model.nunique()} | codebases {df.codebase.nunique()} "
      f"| conditions {sorted(df.condition.unique())}")
print("baseline obs by model:", df[df.condition=='baseline'].model.value_counts().to_dict())

decisions = sorted(df.decision.unique()); models = sorted(df.model.unique()); codebases = sorted(df.codebase.unique())
d_idx = pd.Categorical(df.decision, categories=decisions).codes
m_idx = pd.Categorical(df.model, categories=models).codes
c_idx = pd.Categorical(df.codebase, categories=codebases).codes
treat = (df.condition == "treatment").astype(int).values
y = df.score.values
coords = {"decision": decisions, "model": models, "codebase": codebases, "obs": np.arange(len(df))}

with pm.Model(coords=coords) as full:
    dd = pm.Data("d", d_idx, dims="obs"); tt = pm.Data("t", treat, dims="obs")
    md = pm.Data("m", m_idx, dims="obs"); cd = pm.Data("c", c_idx, dims="obs")
    c1 = pm.Normal("c1", 0, 1.5); dc = pm.Exponential("dc", 1, shape=2)
    cut = pm.Deterministic("cutpoints", pt.stack([c1, c1+dc[0], c1+dc[0]+dc[1]]))
    mu_a = pm.Normal("mu_alpha", 0, 1.5); sa = pm.Exponential("sigma_alpha", 1)
    alpha = pm.Deterministic("alpha", mu_a + sa*pm.Normal("alpha_raw",0,1,dims="decision"), dims="decision")
    mu_b = pm.Normal("mu_beta", 0, 1); sb = pm.Exponential("sigma_beta", 1)
    beta = pm.Deterministic("beta", mu_b + sb*pm.Normal("beta_raw",0,1,dims="decision"), dims="decision")
    sm = pm.Exponential("sigma_model", 1)
    gm = pm.Deterministic("g_model", sm*pm.Normal("g_model_raw",0,1,dims="model"), dims="model")
    sc = pm.Exponential("sigma_codebase", 1)
    gc = pm.Deterministic("g_codebase", sc*pm.Normal("g_codebase_raw",0,1,dims="codebase"), dims="codebase")
    eta = alpha[dd] + beta[dd]*tt + gm[md] + gc[cd]
    pm.OrderedLogistic("score", eta=eta, cutpoints=cut, observed=y, dims="obs")
    idata = pm.sample(draws=1000, tune=1000, target_accept=0.95, random_seed=rng, progressbar=False)

idata.to_netcdf(os.path.join(HERE, "retention_full_model.nc"))
ndiv = int(idata.sample_stats.diverging.sum())
print(f"\nFULL MODEL: divergences = {ndiv} / {idata.sample_stats.diverging.size}")
print(az.summary(idata, var_names=["sigma_model","sigma_codebase","sigma_alpha","sigma_beta"], hdi_prob=0.94)[["mean","hdi_3%","hdi_97%","r_hat"]].to_string())
print("\narchived -> retention_full_model.nc")
