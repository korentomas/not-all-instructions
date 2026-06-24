#!/usr/bin/env python3
"""Generate 6 v3 conversation JSON files (3 codebases x baseline + treatment)."""

import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "conversations")

# ============================================================
# Decision definitions
# ============================================================
EARLY_DECISIONS = [
    {"turn": 1, "id": "code_style_broadcasting", "timing": "early",
     "category": "code_style",
     "instruction": "Use numpy broadcasting for array operations, no for loops"},
    {"turn": 2, "id": "architecture_extend", "timing": "early",
     "category": "architecture",
     "instruction": "Don't modify the base class, extend it with a subclass"},
    {"turn": 3, "id": "testing_parametrize", "timing": "early",
     "category": "testing",
     "instruction": "Use pytest.mark.parametrize for all test variants"},
    {"turn": 4, "id": "naming_underscore", "timing": "early",
     "category": "naming",
     "instruction": "Prefix all private helper functions with underscore"},
    {"turn": 5, "id": "dependencies_no_new", "timing": "early",
     "category": "dependencies",
     "instruction": "Don't add new imports, only use what's already imported in the file"},
    {"turn": 7, "id": "docs_numpy_style", "timing": "early",
     "category": "documentation",
     "instruction": "Use NumPy-style docstrings for all new functions"},
]

LATE_DECISIONS = [
    {"turn": 14, "id": "code_style_listcomp", "timing": "late",
     "category": "code_style",
     "instruction": "Use list comprehensions, not map/filter"},
    {"turn": 15, "id": "architecture_standalone", "timing": "late",
     "category": "architecture",
     "instruction": "Keep all new functions as standalone, don't add methods to existing classes"},
    {"turn": 16, "id": "testing_assert_almost", "timing": "late",
     "category": "testing",
     "instruction": "Use assertAlmostEqual with 6 decimal places for float comparisons"},
    {"turn": 17, "id": "naming_snake_no_abbrev", "timing": "late",
     "category": "naming",
     "instruction": "Use snake_case for all variable names, no abbreviations"},
    {"turn": 18, "id": "dependencies_module_constants", "timing": "late",
     "category": "dependencies",
     "instruction": "If you need a constant, define it at module level, not inline"},
    {"turn": 19, "id": "docs_regex_comments", "timing": "late",
     "category": "documentation",
     "instruction": "Add a one-line comment above any regex explaining what it matches"},
]

ALL_DECISIONS = EARLY_DECISIONS + LATE_DECISIONS

# ============================================================
# Test turns (identical across baseline and treatment)
# ============================================================
# These are templates; the actual content gets adapted per codebase below.
TEST_TURN_TEMPLATE = [
    {"turn": 20, "tests_decisions": ["code_style_broadcasting", "code_style_listcomp"]},
    {"turn": 21, "tests_decisions": ["architecture_extend", "architecture_standalone"]},
    {"turn": 22, "tests_decisions": ["testing_parametrize", "testing_assert_almost"]},
    {"turn": 23, "tests_decisions": ["naming_underscore", "naming_snake_no_abbrev"]},
    {"turn": 24, "tests_decisions": ["dependencies_no_new", "dependencies_module_constants"]},
    {"turn": 25, "tests_decisions": ["docs_numpy_style", "docs_regex_comments"]},
]


# ============================================================
# BAMBI
# ============================================================
BAMBI_CONFIG = {
    "codebase": "bambi",
    "repo_path": "codebases/bambi",
    "task_description": "Extend Bambi's family system with a custom scoring and normalization module for posterior predictive checks",
    # File injection schedule (path relative to repo root)
    # Cumulative bytes by turn 20: ~367K = ~92K tokens
    "inject_schedule": {
        0: ["bambi/families/family.py"],                  # 13.8K -> 13.8K
        1: ["bambi/families/univariate.py"],              # 17.9K -> 31.7K
        2: ["bambi/models.py"],                           # 56.7K -> 88.4K
        3: ["tests/test_models.py"],                      # 54.2K -> 142.6K
        4: ["bambi/backend/terms.py"],                    # 25.5K -> 168.1K
        5: ["bambi/model_components.py"],                 # 23.9K -> 192.0K
        6: ["bambi/interpret/effects.py"],                # 33.6K -> 225.6K
        7: ["bambi/backend/pymc.py"],                     # 16.0K -> 241.6K
        8: ["bambi/transformations.py"],                  # 15.5K -> 257.1K
        9: ["bambi/interpret/types.py"],                  # 12.5K -> 269.6K
        10: ["bambi/backend/model_components.py"],        # 12.4K -> 282.0K
        11: ["bambi/defaults/families.py"],               # 9.3K -> 291.3K
        12: ["bambi/data/datasets.py"],                   # 11.7K -> 303.0K
        13: ["bambi/interpret/plots.py"],                 # 10.2K -> 313.2K
        14: ["bambi/priors/scaler.py"],                   # 8.5K -> 321.7K
        15: ["tests/test_model_construction.py"],         # 20.9K -> 342.6K
        16: ["bambi/interpret/utils.py"],                 # 8.2K -> 350.8K
        17: ["bambi/backend/utils.py"],                   # 6.1K -> 356.9K
        18: ["bambi/utils.py"],                           # 5.3K -> 362.2K
        19: ["bambi/families/link.py"],                   # 5.3K -> 367.5K
        # Test turns: no new files
        20: [], 21: [], 22: [], 23: [], 24: [], 25: [],
    },
    # Turn content for non-decision, non-test turns (treatment and baseline share these)
    "turn_content": {
        0: "I'm working on the Bambi codebase. We need to add a custom scoring and normalization module for posterior predictive checks. Start by reading the base Family class so I understand the interface.",
        6: "Good. Now let's look at the interpret module to understand how Bambi handles effects computation -- this will inform how we structure our normalization code. Read the effects module.",
        8: "Let me look at the transformations module to understand what data transformations Bambi already supports.",
        9: "Read the interpret types module -- I want to see the data structures used for storing computed results.",
        10: "Now read the backend model components to understand how components are compiled and linked to families.",
        11: "Read the defaults/families.py to see how families are registered and what defaults are set.",
        12: "Read the datasets module -- I want to understand the data loading patterns used in Bambi.",
        13: "Now read the interpret plots module to see how computed results are visualized. This will help us design the output format for our normalization functions.",
    },
    # Treatment-specific turn content (decision + task)
    "treatment_content": {
        1: "Important: when writing array operations for this project, always use numpy broadcasting instead of for loops. This keeps things vectorized and fast. Now read the univariate families module to see the existing distribution implementations.",
        2: "One more thing -- if we need to add new functionality to the family system, don't modify the base Family class directly. Instead, extend it with a subclass. Now read the main models.py to understand how models use families.",
        3: "For all test variants we write, use pytest.mark.parametrize rather than writing separate test functions. Read the test_models.py file to see how existing tests are structured.",
        4: "Also, prefix all private helper functions with an underscore -- I want a clear distinction between public API and internal helpers. Now read the backend terms module.",
        5: "Don't add new imports to any file -- only use what's already imported. We want to keep dependencies minimal. Read the model_components module next.",
        7: "One last convention: use NumPy-style docstrings for all new functions we write -- with the Parameters/Returns sections using dashes. Now read the PyMC backend to understand how the model is compiled.",
        14: "Going forward, use list comprehensions instead of map/filter when transforming collections. It's more readable. Now read the prior scaler module.",
        15: "For any new functions we add from here on, keep them as standalone functions rather than adding methods to existing classes. Read the test_model_construction.py for more context on how the model building is tested.",
        16: "When writing float comparison tests, use assertAlmostEqual with 6 decimal places to avoid floating point precision issues. Read the interpret utils module.",
        17: "For all variable names, use full snake_case with no abbreviations -- spell things out completely for readability. Read the backend utils.",
        18: "If you need any constants (thresholds, tolerances, etc.), define them at module level, not inline in functions. Read the utils module.",
        19: "Whenever you write a regex, add a one-line comment above it explaining what pattern it matches. Now read the link functions module.",
    },
    # Baseline-specific turn content (neutral filler instead of decisions)
    "baseline_content": {
        1: "Now let's look at the univariate families module to see the existing distribution implementations.",
        2: "Read the main models.py file to understand how models use families and how the fit/predict pipeline works.",
        3: "Read the test_models.py file to see how existing families and models are tested.",
        4: "Now read the backend terms module to understand how model terms are compiled.",
        5: "Read the model_components module to see how components are structured and linked.",
        7: "Now read the PyMC backend to understand how the model is compiled and how families interact with the backend.",
        14: "Let's continue. Read the prior scaler module to understand how priors are scaled.",
        15: "Read the test_model_construction.py for more context on how model building is validated.",
        16: "Read the interpret utils module to see the utility functions used in interpretation.",
        17: "Read the backend utils module.",
        18: "Read the main utils module to see what general utilities are available.",
        19: "Read the link functions module to understand how link functions are defined and used.",
    },
    # Test turn content (IDENTICAL for baseline and treatment)
    "test_content": {
        20: "Write a function that normalizes an array of posterior predictive scores to the [0, 1] range. It should handle batched arrays where each row is a different draw and each column is an observation. Include handling for edge cases like constant arrays.",
        21: "Add a new method for computing weighted averages of family log-likelihoods across observations. The weights should be per-observation importance weights. Make sure it integrates with the existing family interface.",
        22: "Write tests for the normalization function you created. Cover standard cases, edge cases (empty arrays, single element, constant values, NaN handling), and different array shapes.",
        23: "Add a helper function to validate input shapes before normalization -- it should check that the input is 2D, that no dimension is zero, and raise informative errors. Also validate that weights (if provided) match the observation dimension.",
        24: "Add error handling for edge cases in the weighted average computation: zero weights, negative weights, mismatched dimensions, and missing values. Use appropriate error types and messages that match what's already used in the codebase.",
        25: "Write the main computation function that takes a family's posterior predictive output, normalizes it, computes weighted summaries, and returns a structured result. Include a complete docstring. The function should parse the family name from a string pattern like 'family_name(param1, param2)' to determine the right normalization strategy.",
    },
}


# ============================================================
# ARVIZ
# ============================================================
ARVIZ_CONFIG = {
    "codebase": "arviz",
    "repo_path": "codebases/arviz-stats",
    "task_description": "Add custom convergence diagnostics with weighted R-hat and bulk/tail ESS normalization to ArviZ stats",
    "inject_schedule": {
        # ArviZ-stats files: ~600K target by turn 20
        # Also inject some arviz-base files for additional context
        0: ["src/arviz_stats/base/diagnostics.py"],             # 53.8K -> 53.8K
        1: ["src/arviz_stats/base/array.py"],                   # 52.9K -> 106.7K
        2: ["src/arviz_stats/summary.py"],                      # 43.3K -> 150.0K
        3: ["tests/base/test_array.py"],                        # 56.5K -> 206.5K
        4: ["src/arviz_stats/base/dataarray.py"],               # 38.5K -> 245.0K
        5: ["src/arviz_stats/loo/helper_loo.py"],               # 52.1K -> 297.1K
        6: ["src/arviz_stats/base/density.py"],                 # 36.6K -> 333.7K
        7: ["src/arviz_stats/sampling_diagnostics.py"],         # 35.0K -> 368.7K
        8: ["src/arviz_stats/loo/loo_moment_match.py"],         # 37.7K -> 406.4K
        9: ["src/arviz_stats/metrics.py"],                      # 26.2K -> 432.6K
        10: ["src/arviz_stats/loo/compare.py"],                 # 26.0K -> 458.6K
        11: ["src/arviz_stats/loo/loo_subsample.py"],           # 26.1K -> 484.7K
        12: ["src/arviz_stats/visualization.py"],               # 22.7K -> 507.4K
        13: ["src/arviz_stats/base/core.py"],                   # 22.2K -> 529.6K
        14: ["src/arviz_stats/accessors.py"],                   # 19.5K -> 549.1K
        15: ["tests/loo/test_helper_loo.py"],                   # 29.0K -> 578.1K
        16: ["src/arviz_stats/loo/loo_expectations.py"],        # 16.9K -> 595.0K
        17: ["src/arviz_stats/loo/loo.py"],                     # 18.8K -> 613.8K
        18: ["src/arviz_stats/ecdf_utils.py"],                  # 13.8K -> 627.6K
        19: ["tests/conftest.py"],                              # 16.1K -> 643.7K
        20: [], 21: [], 22: [], 23: [], 24: [], 25: [],
    },
    "turn_content": {
        0: "I'm working on the ArviZ stats library. We need to add custom convergence diagnostics with weighted R-hat and bulk/tail ESS normalization. Start by reading the base diagnostics module.",
        6: "Read the density estimation module -- we may need kernel density estimation for some of our diagnostic visualizations.",
        8: "Read the LOO moment matching module to understand how ArviZ handles iterative statistical computations.",
        9: "Read the metrics module to see what model comparison metrics are already implemented.",
        10: "Read the LOO compare module to understand how model comparison results are structured.",
        11: "Read the LOO subsample module for understanding how ArviZ handles subsampling in large datasets.",
        12: "Read the visualization module to understand how diagnostic results are formatted for plotting.",
        13: "Read the base core module to see the fundamental statistical operations available.",
    },
    "treatment_content": {
        1: "Important: for all array operations in this project, use numpy broadcasting -- no for loops. This is critical for performance with large MCMC chains. Now read the base array module to see the existing array operations.",
        2: "When we add new diagnostic functionality, don't modify the existing base classes directly. Extend them with subclasses instead. Read the summary module to understand how diagnostics are aggregated.",
        3: "For all test variants, use pytest.mark.parametrize -- we need to test across different chain lengths and parameter counts efficiently. Read the test_array.py to see existing test patterns.",
        4: "Prefix all private helper functions with underscore to keep the public API clean. Read the dataarray module next.",
        5: "Don't add any new imports -- only use what's already imported in each file. ArviZ has strict dependency management. Read the LOO helper module for reference.",
        7: "Use NumPy-style docstrings for all new functions -- with Parameters/Returns sections using dashes underneath. Read the sampling diagnostics module to see how diagnostic functions are documented.",
        14: "From now on, use list comprehensions instead of map/filter for collection transformations. Read the accessors module.",
        15: "Keep all new functions as standalone functions, don't add methods to existing classes. This keeps the diagnostic utilities modular and testable. Read the LOO test helper file.",
        16: "For float comparisons in tests, use assertAlmostEqual with 6 decimal places. MCMC diagnostics need precise but not exact comparisons. Read the LOO expectations module.",
        17: "Use full snake_case for all variable names -- no abbreviations. Spell out 'effective_sample_size' not 'ess', 'convergence_diagnostic' not 'conv_diag'. Read the main LOO module.",
        18: "Define any constants (tolerance thresholds, convergence criteria) at module level, not inline. Read the ECDF utils module.",
        19: "Add a one-line comment above any regex explaining what it matches -- diagnostics often parse chain names with patterns. Read the test conftest for testing conventions.",
    },
    "baseline_content": {
        1: "Read the base array module to see the existing array operations and utilities.",
        2: "Read the summary module to understand how diagnostics are aggregated and displayed.",
        3: "Read the test_array.py to see the existing test patterns for the stats base module.",
        4: "Read the dataarray module to understand how ArviZ wraps statistical computations on xarray DataArrays.",
        5: "Read the LOO helper module -- it has patterns for complex statistical computations we can learn from.",
        7: "Read the sampling diagnostics module to see how existing diagnostic functions are structured.",
        14: "Let's continue. Read the accessors module to understand ArviZ's accessor pattern.",
        15: "Read the LOO test helper file to see how complex statistical tests are structured.",
        16: "Read the LOO expectations module.",
        17: "Read the main LOO module to understand the full LOO computation pipeline.",
        18: "Read the ECDF utils module.",
        19: "Read the test conftest to understand the testing infrastructure and fixtures.",
    },
    "test_content": {
        20: "Write a function that normalizes an array of R-hat diagnostic values across multiple chains. It should take a 2D array where rows are parameters and columns are chain splits, and return per-parameter normalized diagnostics in [0, 1]. Handle edge cases like chains with zero variance.",
        21: "Add a new method for computing weighted effective sample sizes. The function should accept per-draw importance weights and compute a weighted ESS that accounts for weight variability. Make sure it integrates with the existing diagnostics interface.",
        22: "Write tests for the R-hat normalization function. Cover standard convergence scenarios, edge cases (single chain, single parameter, constant chains, NaN values), and verify numerical accuracy of the results.",
        23: "Add a helper function to validate the shape and contents of MCMC chain arrays before computing diagnostics. It should check dimensionality, minimum chain length, and that values are finite. Raise informative errors for each failure mode.",
        24: "Add error handling for edge cases in the weighted ESS computation: zero weights, negative weights, single-draw chains, and missing values. Use error types consistent with what ArviZ already uses.",
        25: "Write the main diagnostic computation function that takes raw MCMC chains, normalizes R-hat values, computes weighted ESS, and returns a structured diagnostic summary. Include a complete docstring. The function should parse chain metadata from a string pattern like 'chain[0]:param_name' to identify parameters.",
    },
}


# ============================================================
# PYMC
# ============================================================
PYMC_CONFIG = {
    "codebase": "pymc",
    "repo_path": "codebases/pymc",
    "task_description": "Add a custom distribution with gradient-based diagnostics and step size adaptation utilities to PyMC",
    "inject_schedule": {
        # PyMC files: ~800K target by turn 20
        0: ["pymc/distributions/continuous.py"],                 # 125.7K -> 125.7K
        1: ["pymc/distributions/multivariate.py"],               # 99.8K -> 225.5K
        2: ["pymc/model/core.py"],                               # 89.9K -> 315.4K
        3: ["tests/distributions/test_continuous.py"],           # 90.1K -> 405.5K
        4: ["pymc/sampling/mcmc.py"],                            # 67.2K -> 472.7K
        5: ["pymc/distributions/discrete.py"],                   # 43.0K -> 515.7K
        6: ["pymc/variational/opvi.py"],                         # 57.9K -> 573.6K
        7: ["pymc/testing.py"],                                  # 49.7K -> 623.3K
        8: ["pymc/gp/gp.py"],                                   # 49.8K -> 673.1K
        9: ["pymc/distributions/mixture.py"],                    # 38.0K -> 711.1K
        10: ["pymc/sampling/forward.py"],                        # 42.9K -> 754.0K
        11: ["pymc/step_methods/metropolis.py"],                 # 43.0K -> 797.0K
        12: ["pymc/gp/cov.py"],                                 # 42.3K -> 839.3K
        13: ["pymc/distributions/distribution.py"],              # 32.9K -> 872.2K
        14: ["pymc/logprob/transforms.py"],                      # 32.6K -> 904.8K
        15: ["pymc/pytensorf.py"],                               # 34.5K -> 939.3K
        16: ["pymc/distributions/timeseries.py"],                # 37.6K -> 976.9K
        17: ["pymc/variational/updates.py"],                     # 37.9K -> 1014.8K
        18: ["pymc/step_methods/hmc/quadpotential.py"],          # 33.0K -> 1047.8K
        19: ["pymc/model_graph.py"],                             # 29.6K -> 1077.4K
        20: [], 21: [], 22: [], 23: [], 24: [], 25: [],
    },
    "turn_content": {
        0: "I'm working on the PyMC codebase. We need to add a custom distribution with gradient-based diagnostics and step size adaptation utilities. Start by reading the continuous distributions module to understand how distributions are defined.",
        6: "Read the variational inference OPVI module -- it has patterns for gradient computation that are relevant to our diagnostic utilities.",
        8: "Read the Gaussian process module to see how PyMC handles complex model components with custom gradients.",
        9: "Read the mixture distributions module to understand how compound distributions are implemented.",
        10: "Read the forward sampling module to see how PyMC generates samples from distributions.",
        11: "Read the Metropolis step methods to understand the step adaptation mechanisms.",
        12: "Read the GP covariance functions module to see how complex mathematical operations are structured.",
        13: "Read the base distribution module to understand the Distribution class interface.",
    },
    "treatment_content": {
        1: "Important: for all array operations in this codebase, always use numpy broadcasting -- no for loops over arrays. PyMC relies on vectorized operations for gradient computation. Read the multivariate distributions module.",
        2: "When adding new functionality, don't modify the base Distribution class or Model class. Extend them with subclasses instead. Read model/core.py to understand the model compilation pipeline.",
        3: "For all test variants, use pytest.mark.parametrize. PyMC tests many distribution configurations this way. Read test_continuous.py to see the pattern.",
        4: "Prefix all private helper functions with underscore -- PyMC has a clear convention for this. Read the MCMC sampling module.",
        5: "Don't add new imports -- only use what's already imported in each file. PyMC's dependency graph is carefully managed. Read the discrete distributions module.",
        7: "Use NumPy-style docstrings for all new functions -- with Parameters/Returns sections and dashed underlines. PyMC follows this convention consistently. Read the testing utilities module.",
        14: "From here on, use list comprehensions instead of map/filter for collection transformations. Read the logprob transforms module.",
        15: "Keep all new functions as standalone functions, don't add methods to existing classes. Read the pytensorf utility module.",
        16: "For float comparisons in tests, use assertAlmostEqual with 6 decimal places -- gradient computations need tolerance. Read the timeseries distributions module.",
        17: "Use full snake_case for all variable names with no abbreviations. Spell things out completely -- 'step_size_adaptation' not 'ss_adapt'. Read the variational updates module.",
        18: "Define any constants (tolerance values, default step sizes, convergence thresholds) at module level, not inline in functions. Read the HMC quadpotential module.",
        19: "Add a one-line comment above every regex explaining what it matches -- PyMC uses patterns for variable name parsing. Read the model graph module.",
    },
    "baseline_content": {
        1: "Read the multivariate distributions module to see how complex distributions are defined.",
        2: "Read model/core.py to understand the model compilation pipeline and how distributions are registered.",
        3: "Read test_continuous.py to see how distribution tests are structured and parametrized.",
        4: "Read the MCMC sampling module to understand how step methods interact with distributions.",
        5: "Read the discrete distributions module for another perspective on distribution implementations.",
        7: "Read the testing utilities module to see PyMC's testing infrastructure and helpers.",
        14: "Let's continue. Read the logprob transforms module to understand how log-probabilities are computed.",
        15: "Read the pytensorf utility module for tensor operation patterns.",
        16: "Read the timeseries distributions module to see how stateful distributions work.",
        17: "Read the variational updates module.",
        18: "Read the HMC quadpotential module to understand mass matrix adaptation.",
        19: "Read the model graph module for understanding how model structure is represented.",
    },
    "test_content": {
        20: "Write a function that normalizes an array of gradient magnitudes across model parameters. It should take a 2D array where rows are MCMC iterations and columns are parameters, and return per-parameter normalized gradients in [0, 1]. Handle edge cases like zero-gradient parameters.",
        21: "Add a new method for computing weighted step size estimates from gradient statistics. The function should accept per-parameter importance weights and compute an adapted step size. Make sure it integrates with the existing step method interface.",
        22: "Write tests for the gradient normalization function. Cover standard cases, edge cases (single parameter, single iteration, zero gradients, infinite values), and verify the numerical accuracy of the normalized output.",
        23: "Add a helper function to validate input shapes for gradient arrays before computing diagnostics. Check that the array is 2D, has enough iterations (minimum 10), and that all values are finite. Raise informative errors for each validation failure.",
        24: "Add error handling for edge cases in the weighted step size computation: zero weights, negative weights, single-iteration chains, and NaN gradient values. Use error types consistent with what PyMC already uses in its step methods.",
        25: "Write the main diagnostic computation function that takes raw gradient arrays, normalizes them, computes weighted step sizes, and returns a structured diagnostic result. Include a complete docstring. The function should parse parameter names from a string pattern like 'model::variable_name[index]' to group related parameters.",
    },
}


def build_conversation(config, condition):
    """Build a conversation JSON for a codebase and condition.

    condition: 'baseline' or 'treatment'
    """
    turns = []

    # Build planted_decisions list (treatment only)
    planted_decisions = []
    if condition == "treatment":
        for d in ALL_DECISIONS:
            planted_decisions.append({
                "turn": d["turn"],
                "id": d["id"],
                "category": d["category"],
                "timing": d["timing"],
                "instruction": d["instruction"],
            })

    # Build test_turns metadata
    test_turns_meta = []
    for tt in TEST_TURN_TEMPLATE:
        test_turns_meta.append({
            "turn": tt["turn"],
            "tests_decisions": tt["tests_decisions"],
        })

    # Decision turn numbers
    decision_turns = {d["turn"] for d in ALL_DECISIONS}

    for turn_num in range(26):
        inject_files = config["inject_schedule"].get(turn_num, [])
        turn_data = {
            "turn": turn_num,
            "inject_files": inject_files,
        }

        if turn_num >= 20:
            # Test turn -- identical for both conditions
            turn_data["content"] = config["test_content"][turn_num]
            turn_data["tests_decisions"] = TEST_TURN_TEMPLATE[turn_num - 20]["tests_decisions"]
        elif turn_num in decision_turns:
            # Decision turn
            if condition == "treatment":
                turn_data["content"] = config["treatment_content"][turn_num]
                # Find the decision for this turn
                decision = next(d for d in ALL_DECISIONS if d["turn"] == turn_num)
                turn_data["planted_decision"] = {
                    "id": decision["id"],
                    "timing": decision["timing"],
                }
            else:
                # Baseline: neutral content
                turn_data["content"] = config["baseline_content"][turn_num]
        else:
            # Non-decision, non-test turn: shared content
            turn_data["content"] = config["turn_content"][turn_num]

        turns.append(turn_data)

    conversation = {
        "codebase": config["codebase"],
        "repo_path": config["repo_path"],
        "condition": condition,
        "task_description": config["task_description"],
        "planted_decisions": planted_decisions,
        "test_turns": test_turns_meta,
        "turns": turns,
    }

    return conversation


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    configs = {
        "bambi": BAMBI_CONFIG,
        "arviz": ARVIZ_CONFIG,
        "pymc": PYMC_CONFIG,
    }

    for name, config in configs.items():
        for condition in ["baseline", "treatment"]:
            conversation = build_conversation(config, condition)
            filename = f"{name}_v3_{condition}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "w") as f:
                json.dump(conversation, f, indent=2)
            print(f"  Written: {filename} ({len(conversation['turns'])} turns)")

    # Validate all file paths exist
    print("\nValidating file paths...")
    base_dir = os.path.join(os.path.dirname(__file__), "..", "codebases")
    errors = []
    for name, config in configs.items():
        repo_dir = os.path.join(base_dir, config["repo_path"].replace("codebases/", ""))
        for turn_num, files in config["inject_schedule"].items():
            for f in files:
                full_path = os.path.join(repo_dir, f)
                if not os.path.exists(full_path):
                    errors.append(f"  MISSING: {config['repo_path']}/{f}")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(e)
    else:
        print("  All file paths verified.")

    # Print token estimates
    print("\nToken estimates (bytes / 4):")
    for name, config in configs.items():
        repo_dir = os.path.join(base_dir, config["repo_path"].replace("codebases/", ""))
        total_bytes = 0
        for turn_num in range(20):  # Only up to turn 20
            for f in config["inject_schedule"].get(turn_num, []):
                full_path = os.path.join(repo_dir, f)
                if os.path.exists(full_path):
                    total_bytes += os.path.getsize(full_path)
        print(f"  {name}: {total_bytes:,} bytes = ~{total_bytes // 4:,} tokens by turn 20")


if __name__ == "__main__":
    main()
