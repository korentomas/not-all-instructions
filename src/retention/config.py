"""Model and provider config, read from ``models.toml`` at the repo root.

Change which models run, the judge panel, or any per-model setting by editing
that file; no Python change needed. A model with no ``[models."<id>"]`` block
uses the defaults: max_tokens 4096, full reasoning history, the provider's own
routing.

The ``framing`` profile merges ``[framing.models."<id>"]`` on top of the base
``[models]`` block, so the framing run can override a cap without repeating the
rest.
"""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

from inspect_ai.model import GenerateConfig, get_model

CONFIG_PATH = Path(__file__).resolve().parents[2] / "models.toml"
DEFAULT_MAX_TOKENS = 4096


@lru_cache(maxsize=1)
def _raw() -> dict:
    return tomllib.loads(CONFIG_PATH.read_text())


def candidates() -> list[str]:
    return list(_raw()["candidates"])


def framing_candidates() -> list[str]:
    return list(_raw()["framing_candidates"])


def judges() -> dict[str, str]:
    return dict(_raw()["judges"])


def ablation_judge() -> dict[str, str]:
    return dict(_raw()["ablation"])


def _spec(model: str, profile: str) -> dict:
    spec = dict(_raw().get("models", {}).get(model, {}))
    if profile != "main":
        spec.update(_raw().get(profile, {}).get("models", {}).get(model, {}))
    return spec


def _config_for(model: str, profile: str = "main") -> GenerateConfig:
    spec = _spec(model, profile)
    cfg = GenerateConfig(max_tokens=spec.get("max_tokens", DEFAULT_MAX_TOKENS))
    if "reasoning_history" in spec:
        cfg.reasoning_history = spec["reasoning_history"]
    order = spec.get("provider_order")
    if order:
        # Pin OpenRouter to specific backends, deterministically: no fallbacks,
        # tool-capable endpoints only.
        cfg.extra_body = {
            "provider": {
                "order": list(order),
                "allow_fallbacks": False,
                "require_parameters": True,
            }
        }
    return cfg


def build_models(model_ids: list[str], profile: str = "main") -> list:
    """Inspect models for ``model_ids`` with each one's per-model config applied."""
    return [get_model(m, config=_config_for(m, profile)) for m in model_ids]
