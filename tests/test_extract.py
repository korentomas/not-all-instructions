"""Extraction-layer integrity: model-label canonicalization, dedup, allowlist.

The deterministic channel keys an observation on
(model, codebase, condition, decision, turn, epoch). If two *providers* serve
the SAME model under labels that differ only by provider-prefix or case
(`azureai/DeepSeek-V3.2` vs `openrouter/deepseek/deepseek-v3.2`), the naive
`split('/')[-1]` label leaves two distinct keys for one cell - a duplicated
observation that fakes precision (σ_β biased down, β HDIs too tight). These
tests pin the collapse, while protecting genuinely-different models from being
merged, and exercise the candidate-model allowlist.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from retention.analysis import extract
from retention.analysis.extract import _model_key, _model_short, load_scores


# ---- canonical key ---------------------------------------------------------


def test_model_key_collapses_provider_and_case_variants():
    # provider prefix differs, casing differs - same underlying model
    assert _model_key("azureai/DeepSeek-V3.2") == _model_key(
        "openrouter/deepseek/deepseek-v3.2"
    )
    # plain provider-prefix variants collapse too
    assert _model_key("azureai/llama-3.3-70b") == _model_key(
        "openrouter/meta-llama/llama-3.3-70b"
    )


def test_model_key_preserves_genuinely_different_models():
    # a distinct slug (base vs -instruct) must NOT be merged
    assert _model_key("openrouter/meta-llama/llama-3.3-70b") != _model_key(
        "openrouter/meta-llama/llama-3.3-70b-instruct"
    )


def test_model_short_stays_readable():
    # display label is provider-stripped but case-preserved
    assert _model_short("azureai/DeepSeek-V3.2") == "DeepSeek-V3.2"


# ---- load_scores: dedup + allowlist over stubbed logs ----------------------


def _stub_log(model: str, *, codebase="cb", condition="treatment", epoch=0,
              decision="dec_a", turn=20, score=2):
    """Minimal stand-in for an inspect EvalLog with one deterministic score."""
    sample = SimpleNamespace(
        scores={
            "deterministic_compliance": SimpleNamespace(
                value={f"{decision}@{turn}": score}
            )
        },
        metadata={"codebase": codebase, "condition": condition},
        epoch=epoch,
    )
    return SimpleNamespace(eval=SimpleNamespace(model=model), samples=[sample])


def _patch_logs(monkeypatch, logs):
    monkeypatch.setattr(extract, "_iter_logs", lambda _log_dir: logs)


def test_load_scores_collapses_case_variant_duplicate(monkeypatch):
    # SAME (codebase, condition, decision, turn, epoch) cell, two provider labels
    # that differ only by prefix/case - must dedup to a single observation.
    logs = [
        _stub_log("azureai/DeepSeek-V3.2", score=2),
        _stub_log("openrouter/deepseek/deepseek-v3.2", score=3),
    ]
    _patch_logs(monkeypatch, logs)
    df = load_scores("ignored")
    assert len(df) == 1, "case-variant duplicate of one cell was not collapsed"
    assert df.model.nunique() == 1


def test_load_scores_keeps_genuinely_different_models(monkeypatch):
    # base vs -instruct are different models → two rows survive.
    logs = [
        _stub_log("openrouter/meta-llama/llama-3.3-70b", score=2),
        _stub_log("openrouter/meta-llama/llama-3.3-70b-instruct", score=3),
    ]
    _patch_logs(monkeypatch, logs)
    df = load_scores("ignored")
    assert len(df) == 2
    assert df.model.nunique() == 2


def test_load_scores_allowlist_drops_stray_models(monkeypatch):
    logs = [
        _stub_log("openrouter/qwen/qwen3.5-27b", score=2),
        _stub_log("openrouter/mistralai/mistral-large-2512", score=1),  # stray
    ]
    _patch_logs(monkeypatch, logs)
    # allowlist accepts a provider-prefixed / cased label and matches canonically
    df = load_scores("ignored", models=["openrouter/qwen/qwen3.5-27b"])
    assert set(df.model) == {"qwen3.5-27b"}
    # default (None) keeps everything
    df_all = load_scores("ignored")
    assert df_all.model.nunique() == 2


def test_load_scores_empty_when_no_logs(monkeypatch):
    _patch_logs(monkeypatch, [])
    assert isinstance(load_scores("ignored"), pd.DataFrame)
