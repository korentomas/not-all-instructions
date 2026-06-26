"""dataset loader tests: conversation JSONs load into well-formed Samples."""

from retention.dataset import CODEBASES, retention_dataset

# 12 decision types (the v3 taxonomy scored by checkers.check_decision)
EXPECTED_DECISIONS = {
    "code_style_broadcasting", "code_style_listcomp",
    "architecture_extend", "architecture_standalone",
    "testing_parametrize", "testing_assert_almost",
    "naming_underscore", "naming_snake_no_abbrev",
    "dependencies_no_new", "dependencies_module_constants",
    "docs_numpy_style", "docs_regex_comments",
}


def test_loads_six_templates():
    ds = retention_dataset()
    # 3 codebases x {baseline, treatment}
    assert len(ds) == 6, f"expected 6 templates, got {len(ds)}"
    ids = {s.id for s in ds}
    for cb in CODEBASES:
        assert f"{cb}_baseline" in ids
        assert f"{cb}_treatment" in ids


def test_sample_metadata_shape():
    ds = retention_dataset()
    for s in ds:
        m = s.metadata
        assert m["codebase"] in CODEBASES
        assert m["condition"] in ("baseline", "treatment")
        assert isinstance(m["test_turns"], dict) and m["test_turns"], "test_turns must be non-empty"
        assert isinstance(m["turns"], list) and len(m["turns"]) > 0
        # input is the task description
        assert isinstance(s.input, str) and len(s.input) > 0


def test_baseline_vs_treatment_planting():
    ds = retention_dataset()
    by_id = {s.id: s for s in ds}

    # baseline: no instructions planted, but SAME test turns (spontaneous compliance)
    base = by_id["pymc_baseline"]
    assert base.metadata["planted_decisions"] == []
    assert len(base.metadata["test_turns"]) == 6

    # treatment: 12 decisions planted across the conversation
    treat = by_id["pymc_treatment"]
    planted_ids = {d["id"] for d in treat.metadata["planted_decisions"]}
    assert planted_ids == EXPECTED_DECISIONS


def test_test_turns_reference_known_decisions():
    ds = retention_dataset()
    for s in ds:
        for turn, decisions in s.metadata["test_turns"].items():
            assert isinstance(turn, int)
            for d in decisions:
                assert d in EXPECTED_DECISIONS, f"unknown decision {d} in {s.id}"
