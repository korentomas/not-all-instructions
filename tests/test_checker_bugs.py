"""CHECKERS_VERSION 4 - regression tests for the regex false-pos/neg the opus panel
found by running check_decision on realistic code, plus the v4 abstain contract
(no-context -> -1, context-without-pattern -> 0). Each test encodes one bug:
the BEFORE behavior was wrong; these pin the corrected behavior.
"""

from retention.checkers import CHECKERS_VERSION, check_decision


def _s(decision: str, code: str) -> int:
    return check_decision(decision, f"```python\n{code}\n```").score


def test_version_is_5():
    assert CHECKERS_VERSION == "5"


# ── v5: dependencies_no_new is context-aware (re-shown existing import != new) ──


def test_no_new_imports_reshown_existing_import_is_compliant():
    # The rule is "use only what's already imported in the file". Re-showing an
    # import that is ALREADY present in the context is NOT a new import -> 3.
    # (v4 scored any import line 0, manufacturing the headline negative effect.)
    code = "```python\nimport numpy as np\ndef f(x):\n    return np.sum(x)\n```"
    assert check_decision("dependencies_no_new", code, already_imported={"numpy"}).score == 3


def test_no_new_imports_from_import_resolves_top_level_module():
    code = "```python\nfrom numpy import array\nx = array([1, 2])\n```"
    assert check_decision("dependencies_no_new", code, already_imported={"numpy"}).score == 3


def test_no_new_imports_genuinely_new_dependency_is_violation():
    code = "```python\nimport torch\ndef f(x):\n    return torch.tensor(x)\n```"
    assert check_decision("dependencies_no_new", code, already_imported={"numpy"}).score == 0


def test_no_new_imports_mixed_reshown_and_new_is_violation():
    code = "```python\nimport numpy as np\nimport torch\n```"
    assert check_decision("dependencies_no_new", code, already_imported={"numpy"}).score == 0


def test_no_new_imports_without_context_keeps_v1_behavior():
    # No context provided (default) -> any import counts as new (the v1 semantics),
    # so the existing regression tests for in-function/dynamic imports still hold.
    code = "```python\nimport os\ndef f():\n    return os.getcwd()\n```"
    assert check_decision("dependencies_no_new", code).score == 0


# ── v5: architecture_extend detects in-place modification of an existing class ──


def test_extend_inplace_method_assignment_is_violation():
    # Monkeypatching a method onto an existing class is "modify in place" -> 0.
    assert _s("architecture_extend", "Model.fit = my_fit") == 0


def test_extend_setattr_on_class_is_violation():
    assert _s("architecture_extend", "setattr(Model, 'fit', my_fit)") == 0


def test_extend_genuine_subclass_still_compliant():
    assert _s("architecture_extend", "class MyModel(Model):\n    def extra(self):\n        return 1") == 3


def test_broadcasting_catches_enumerate_zip_while():
    # element-wise loops that aren't `for i in range(len(...))` must still score 0
    assert _s("code_style_broadcasting", "for i, v in enumerate(a):\n    out[i] = v * 2") == 0
    assert _s("code_style_broadcasting", "for p, q in zip(a, b):\n    r.append(p + q)") == 0
    assert _s("code_style_broadcasting", "while i < len(a):\n    out[i] = a[i]\n    i += 1") == 0
    # genuine vectorized code still scores 3
    assert _s("code_style_broadcasting", "out = np.multiply(a, b)") == 3


def test_standalone_nested_helper_is_not_a_method():
    # a nested def inside a STANDALONE function is not a class method -> still 3
    code = "def outer(x):\n    def _inner(y):\n        return y + 1\n    return _inner(x)"
    assert _s("architecture_standalone", code) == 3
    # a def indented under a class IS a method -> 0
    assert _s("architecture_standalone", "class C:\n    def method(self):\n        return 1") == 0


def test_snake_does_not_capture_equality_operand():
    # `assert ab == cd` must NOT be read as variables `ab`/`cd` (fully snake code -> 3)
    code = "total_count = 0\ndef test_x():\n    assert total_count == expected_value"
    assert _s("naming_snake_no_abbrev", code) == 3


def test_no_new_imports_catches_in_function_and_dynamic():
    assert _s("dependencies_no_new", "def f():\n    import os\n    return os.getcwd()") == 0
    assert _s("dependencies_no_new", "mod = __import__('math')") == 0


def test_module_constants_allows_type_annotation():
    # `MAX_ITER: int = 100` is a module constant -> 3 (old regex rejected it)
    assert _s("dependencies_module_constants", "MAX_ITER: int = 100\ndef f():\n    return MAX_ITER") == 3


def test_regex_comment_tolerates_blank_line_and_inline():
    assert _s("docs_regex_comments", "# match digits\n\nre.findall(r'\\d+', s)") == 3
    assert _s("docs_regex_comments", "re.findall(r'\\d+', s)  # match digits") == 3


def test_assert_almost_recognizes_isclose_and_abs_tol():
    assert _s("testing_assert_almost", "def test_x():\n    assert math.isclose(a, b)") == 3
    assert _s("testing_assert_almost", "def test_x():\n    assert abs(a - b) < 1e-6") == 3


# ── abstain contract: "no signal" must score -1 (excluded downstream), never 1/2/3 ──

ALL_DECISIONS = [
    "code_style_broadcasting",
    "code_style_listcomp",
    "architecture_extend",
    "architecture_standalone",
    "testing_parametrize",
    "testing_assert_almost",
    "naming_underscore",
    "naming_snake_no_abbrev",
    "dependencies_no_new",
    "dependencies_module_constants",
    "docs_numpy_style",
    "docs_regex_comments",
]


def test_empty_input_abstains_for_every_checker():
    # No code to inspect -> no opportunity to apply any rule -> abstain (-1).
    for decision in ALL_DECISIONS:
        assert _s(decision, "") == -1, f"{decision} should abstain on empty input"


def test_gate_no_code_path_abstains():
    # Plain prose, no code block and no code-like tokens -> gate abstains (-1, was 1).
    assert check_decision("testing_parametrize", "Just prose, nothing to evaluate.").score == -1


def test_gate_unknown_decision_abstains():
    assert check_decision("nope_not_a_rule", "```python\nx = 1\n```").score == -1


def test_positive_rules_score_0_when_context_present_pattern_absent():
    # Relevant construct present but the compliant pattern is absent -> real violation 0.
    cases = {
        # element-wise loop over data, no numpy vectorization
        "code_style_broadcasting": "for i in range(len(a)):\n    out[i] = a[i] * 2",
        # map/filter instead of a comprehension
        "code_style_listcomp": "r = list(map(f, xs))",
        # a class defined from scratch, not extended via subclassing
        "architecture_extend": "class Foo:\n    def m(self):\n        return 1",
        # methods bolted onto a class instead of standalone functions
        "architecture_standalone": "class C:\n    def m(self):\n        return 1",
        # separate test functions, no parametrize
        "testing_parametrize": "def test_a():\n    assert add(1, 2) == 3\n\ndef test_b():\n    assert add(2, 2) == 4",
        # exact float comparison
        "testing_assert_almost": "def test_x():\n    assertEqual(a, b)",
        # an internal helper that is not underscore-prefixed
        "naming_underscore": "def helper(x):\n    return x + 1\ndef main():\n    return helper(1)",
        # inline magic number, no module constant
        "dependencies_module_constants": "def f(x):\n    return x * 3.14159",
        # function with no docstring at all
        "docs_numpy_style": "def f(x):\n    return x",
        # regex with no documenting comment
        "docs_regex_comments": 'm = re.findall(r"\\d+", s)',
    }
    for decision, code in cases.items():
        assert _s(decision, code) == 0, f"{decision} should score 0 (context present, pattern absent)"


def test_parametrize_detects_class_method_tests():
    # Class-based suites indent their tests; the violation branch must still fire.
    code = (
        "class TestAdd:\n"
        "    def test_a(self):\n"
        "        assert add(1, 2) == 3\n"
        "    def test_b(self):\n"
        "        assert add(2, 2) == 4"
    )
    assert _s("testing_parametrize", code) == 0
    # No tests at all -> abstain, not a free 3.
    assert _s("testing_parametrize", "def add(a, b):\n    return a + b") == -1


def test_underscore_does_not_penalize_lone_public_entry_point():
    # A single public function nothing else calls is an entry point, not a helper.
    assert _s("naming_underscore", "def solve(x):\n    return x * 2") == -1


def test_snake_abstains_with_no_identifiers():
    # No bound names to inspect -> abstain (was a free 3).
    assert _s("naming_snake_no_abbrev", "assert foo() == bar()") == -1


def test_module_constants_catches_magic_in_expression():
    # Magic number embedded in an expression (not a standalone assignment) -> 0.
    assert _s("dependencies_module_constants", "def scale(v):\n    return v / 255 + 0.5 * 1024") == 0
    # No numeric/constant context at all -> abstain.
    assert _s("dependencies_module_constants", "def f(x):\n    return g(x)") == -1


def test_no_new_imports_compliant_when_code_present_no_import():
    # NEGATIVE rule: absence of an import IS compliance when there is real code.
    assert _s("dependencies_no_new", "def f(x):\n    return x * 2") == 3


def test_compliant_code_scores_3_for_every_rule():
    cases = {
        "code_style_broadcasting": "out = np.multiply(a, b)",
        "code_style_listcomp": "r = [f(x) for x in xs]",
        "architecture_extend": "class Foo(Base):\n    def m(self):\n        return 1",
        "architecture_standalone": "def solve(x):\n    return x * 2",
        "testing_parametrize": '@pytest.mark.parametrize("a,b", [(1, 2)])\ndef test_a(a, b):\n    assert add(a, b)',
        "testing_assert_almost": "def test_x():\n    assert math.isclose(a, b)",
        "naming_underscore": "def _helper(x):\n    return x + 1\ndef main():\n    return _helper(1)",
        "naming_snake_no_abbrev": "total_count = 0\nresult_value = total_count + 1",
        "dependencies_no_new": "def f(x):\n    return x * 2",
        "dependencies_module_constants": "PI = 3.14159\ndef area(r):\n    return PI * r * r",
        "docs_numpy_style": 'def f(x):\n    """Do.\n\n    Parameters\n    ----------\n    x : int\n    """\n    return x',
        "docs_regex_comments": '# match digits\nm = re.findall(r"\\d+", s)',
    }
    for decision, code in cases.items():
        assert _s(decision, code) == 3, f"{decision} should score 3 on compliant code"
