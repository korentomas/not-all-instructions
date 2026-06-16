# logs/ layout

Inspect `.eval` logs (gitignored - large, regenerable). Analysis reads across the
active dirs via `python analyze.py <dir> <dir> ...` (dedups on the natural key).

## Active - feed the final balanced result

| dir | contents |
|-----|----------|
| `retention-v2/` | qwen3.5-27b ✓30, gpt-oss-120b ✓30 (the first clean candidates). Also holds dropped-model error logs (DeepSeek/llama on Azure) - analysis filters by model. |
| `retention-v2-orfill/` | llama-3.3-70b-instruct ✓30 via OpenRouter (extension baseline). |
| `retention-v2-v1models/` | the 4 v1 paper models via OpenRouter: nemotron-3-super-120b, gemma-4-26b, gemini-3.1-flash-lite, gpt-5.4-nano. |

Final candidate set = qwen, gpt-oss, llama, nemotron, gemma, gemini, gpt-5.4-nano
(v1 core + extensions). Judges: claude-haiku-4.5 + mistral-medium-3.1 + grok-4.3.

## _archive/ - superseded, kept for provenance, not used by analysis

- `smoke-azure/`, `smoke-mixed/`, `or-smoke/` - plumbing smokes (provider validation).
- `llama-probe/` - solo llama reliability probe.
- `solo-*/`, `retention-v2-fill/` - wedged Azure straggler attempts (DeepSeek/llama
  throttled on Azure; superseded by the OpenRouter runs).
- `retention-v2-mistral/` - mistral-large 30/30 but DROPPED (Mistral became a judge
  family, so it can't be a candidate).

## Re-scoring

Logs persist `store.turn_outputs` (raw model code), so re-judging (new panel) and
re-scoring (CHECKERS_VERSION 3) run as a CPU pass over stored outputs - no re-generation.
