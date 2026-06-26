# experiments/harness/tracker.py
from dataclasses import dataclass
import numpy as np
from scipy.special import expit  # sigmoid


@dataclass
class Belief:
    mu: float
    sigma: float


class BayesianComplianceTracker:
    """Graded Response Model-based Bayesian compliance tracker.

    Maintains a Gaussian belief N(mu, sigma^2) over latent compliance
    for each instruction type. Updates via GRM likelihood with Laplace
    approximation. Decays between turns to model forgetting.
    """

    def __init__(
        self,
        instruction_types: list[str],
        initial_mu: float = 1.5,
        initial_sigma: float = 1.0,
        learning_rate: float = 0.3,
        discrimination: float = 1.0,
        thresholds: list[float] | None = None,
    ):
        self.beliefs = {
            itype: Belief(mu=initial_mu, sigma=initial_sigma)
            for itype in instruction_types
        }
        self.learning_rate = learning_rate
        self.discrimination = discrimination
        # GRM thresholds: boundaries between score levels 0|1, 1|2, 2|3
        self.thresholds = thresholds or [-0.5, 1.0, 2.0]

    def _grm_prob(self, score: int, theta: float) -> float:
        """P(X = score | theta) under GRM."""
        a = self.discrimination
        b = self.thresholds

        # P(X >= k) = sigmoid(a * (theta - b[k-1]))
        # P(X = k) = P(X >= k) - P(X >= k+1)
        def p_geq(k):
            if k <= 0:
                return 1.0
            if k > len(b):
                return 0.0
            return float(expit(a * (theta - b[k - 1])))

        return p_geq(score) - p_geq(score + 1)

    def _grm_log_likelihood_grad(self, score: int, theta: float) -> float:
        """Gradient of log P(X = score | theta) w.r.t. theta."""
        p = self._grm_prob(score, theta)
        if p < 1e-10:
            p = 1e-10

        eps = 1e-5
        p_plus = self._grm_prob(score, theta + eps)
        p_minus = self._grm_prob(score, theta - eps)
        grad = (p_plus - p_minus) / (2 * eps)

        return grad / p

    def _grm_fisher_info(self, theta: float) -> float:
        """Expected Fisher information at theta."""
        info = 0.0
        for score in range(len(self.thresholds) + 1):
            p = self._grm_prob(score, theta)
            if p < 1e-10:
                continue
            eps = 1e-5
            p_plus = self._grm_prob(score, theta + eps)
            p_minus = self._grm_prob(score, theta - eps)
            grad = (p_plus - p_minus) / (2 * eps)
            info += (grad ** 2) / p
        return info

    def update(self, instruction_type: str, score: int):
        """Update belief for an instruction type given observed score."""
        belief = self.beliefs[instruction_type]

        # Laplace approximation update
        grad = self._grm_log_likelihood_grad(score, belief.mu)
        fisher = self._grm_fisher_info(belief.mu)

        # Update mu
        belief.mu += self.learning_rate * grad

        # Update sigma (decrease with information gained)
        if fisher > 0:
            posterior_precision = (1.0 / belief.sigma**2) + fisher
            belief.sigma = (1.0 / posterior_precision) ** 0.5

    def apply_decay(self, gamma: float):
        """Apply forgetting decay to all beliefs between turns."""
        for belief in self.beliefs.values():
            # Mu decays toward a neutral prior
            belief.mu *= gamma
            # Sigma increases (uncertainty grows)
            belief.sigma = min(belief.sigma / gamma, 2.0)  # cap at 2.0

    def compliance_probability(self, instruction_type: str, threshold: int = 2) -> float:
        """P(score >= threshold) given current belief."""
        belief = self.beliefs[instruction_type]
        a = self.discrimination
        b = self.thresholds

        if threshold <= 0:
            return 1.0
        if threshold > len(b):
            return 0.0

        # Integrate P(score >= threshold | theta) over belief N(mu, sigma^2)
        # Approximate with point estimate at mu
        return float(expit(a * (belief.mu - b[threshold - 1])))

    def get_reinforcement_ranking(self, threshold: int = 2) -> list[str]:
        """Return instruction types sorted by compliance probability (ascending).
        First item = most in need of reinforcement."""
        probs = {
            itype: self.compliance_probability(itype, threshold)
            for itype in self.beliefs
        }
        return sorted(probs, key=lambda x: probs[x])

    def get_state(self) -> dict:
        """Serialize tracker state for logging."""
        return {
            itype: {"mu": b.mu, "sigma": b.sigma}
            for itype, b in self.beliefs.items()
        }
