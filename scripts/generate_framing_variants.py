"""Generate the framing arms from the canonical treatment templates.

    python scripts/generate_framing_variants.py

Writes data/conversations/{codebase}_v3_treatment_{positive,negation}.json.
Deterministic - re-running reproduces the committed files byte-for-byte
(tests/test_framing.py gates this).
"""

from pathlib import Path

from retention.framing import build_all

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    for path in build_all(root / "data" / "conversations"):
        print(f"wrote {path.relative_to(root)}")
