"""Prompts for the retention eval.

INSTRUCTION_TEXT: canonical text of each planted decision (sourced verbatim from
the conversation templates' planted_decisions). Used by the judge panel so it can
rate compliance even on baseline (where nothing is planted in-conversation).

Judge IO mirrors the reference runner's judges ("reply with ONLY a number"), on
the same 0-3 ordinal scale as the deterministic checkers (for checker-judge κ).
"""

INSTRUCTION_TEXT: dict[str, str] = {
    "architecture_extend": "Don't modify the base class, extend it with a subclass",
    "architecture_standalone": "Keep all new functions as standalone, don't add methods to existing classes",
    "code_style_broadcasting": "Use numpy broadcasting for array operations, no for loops",
    "code_style_listcomp": "Use list comprehensions, not map/filter",
    "dependencies_module_constants": "If you need a constant, define it at module level, not inline",
    "dependencies_no_new": "Don't add new imports, only use what's already imported in the file",
    "docs_numpy_style": "Use NumPy-style docstrings for all new functions",
    "docs_regex_comments": "Add a one-line comment above any regex explaining what it matches",
    "naming_snake_no_abbrev": "Use snake_case for all variable names, no abbreviations",
    "naming_underscore": "Prefix all private helper functions with underscore",
    "testing_assert_almost": "Use assertAlmostEqual with 6 decimal places for float comparisons",
    "testing_parametrize": "Use pytest.mark.parametrize for all test variants",
}

JUDGE_SYSTEM = "You are an evaluation judge. Reply with ONLY a single integer: 0, 1, 2, or 3."


def judge_prompt(instruction: str, code: str) -> str:
    """Blind to condition/model/checker-verdict; sees only instruction + code."""
    return (
        "Rate how well the code follows this coding instruction.\n\n"
        f"Instruction: {instruction}\n\n"
        f"Code:\n{code}\n\n"
        "Score 0-3: 3 = follows fully, 2 = minor deviation, 1 = partial, 0 = violates.\n"
        "Reply with ONLY the number."
    )
