# experiments/tests/test_tracker.py
import pytest
import numpy as np
from harness.tracker import BayesianComplianceTracker


class TestTrackerInit:
    def test_initial_beliefs(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format", "constraint", "persona", "safety", "tool_use"],
            initial_mu=1.5,
            initial_sigma=1.0,
        )
        assert len(tracker.beliefs) == 5
        assert tracker.beliefs["format"].mu == pytest.approx(1.5)
        assert tracker.beliefs["format"].sigma == pytest.approx(1.0)


class TestTrackerUpdate:
    def test_high_score_increases_mu(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=1.5,
            initial_sigma=1.0,
        )
        old_mu = tracker.beliefs["format"].mu
        tracker.update("format", score=3)
        assert tracker.beliefs["format"].mu > old_mu

    def test_low_score_decreases_mu(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=1.5,
            initial_sigma=1.0,
        )
        old_mu = tracker.beliefs["format"].mu
        tracker.update("format", score=0)
        assert tracker.beliefs["format"].mu < old_mu

    def test_update_reduces_sigma(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=1.5,
            initial_sigma=1.0,
        )
        old_sigma = tracker.beliefs["format"].sigma
        tracker.update("format", score=2)
        assert tracker.beliefs["format"].sigma < old_sigma


class TestTrackerDecay:
    def test_decay_reduces_mu_toward_zero(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=2.5,
            initial_sigma=0.5,
        )
        tracker.apply_decay(gamma=0.95)
        assert tracker.beliefs["format"].mu < 2.5

    def test_decay_increases_sigma(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=1.5,
            initial_sigma=0.5,
        )
        tracker.apply_decay(gamma=0.95)
        assert tracker.beliefs["format"].sigma > 0.5


class TestTrackerCompliance:
    def test_compliance_probability(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=2.5,
            initial_sigma=0.3,
        )
        p = tracker.compliance_probability("format", threshold=2)
        # With mu=2.5 and low sigma, P(score >= 2) should be high
        assert p > 0.5

    def test_low_mu_gives_low_compliance(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format"],
            initial_mu=0.5,
            initial_sigma=0.3,
        )
        p = tracker.compliance_probability("format", threshold=2)
        assert p < 0.5

    def test_get_reinforcement_ranking(self):
        tracker = BayesianComplianceTracker(
            instruction_types=["format", "safety"],
            initial_mu=1.5,
            initial_sigma=1.0,
        )
        # Make safety worse
        tracker.update("safety", score=0)
        tracker.update("safety", score=0)
        ranking = tracker.get_reinforcement_ranking(threshold=2)
        # Safety should be first (lowest compliance probability)
        assert ranking[0] == "safety"
