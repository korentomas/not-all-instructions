# experiments/harness/reinforcer.py
"""Reinforcement strategies for instruction decay experiments.

Three strategies control when and how system instructions are re-injected
into the conversation:

- NoReinforcement: baseline — never re-injects instructions.
- UniformReinforcement: re-injects ALL instructions every N turns.
- SelectiveReinforcement: re-injects only the lowest-compliance instructions
  (as ranked by the Bayesian tracker) up to a token budget.
"""

from dataclasses import dataclass
from harness.tracker import BayesianComplianceTracker


@dataclass
class InstructionBank:
    instructions: dict[str, str]  # instruction_type -> instruction text

    def token_estimate(self, instruction_type: str) -> int:
        """Rough token count estimate (words * 1.3)."""
        text = self.instructions[instruction_type]
        return int(len(text.split()) * 1.3)


class NoReinforcement:
    def get_reinforcement(self, turn: int, bank: InstructionBank, tracker) -> str | None:
        return None


class UniformReinforcement:
    def __init__(self, every_n_turns: int = 5, token_budget: int = 250):
        self.every_n_turns = every_n_turns
        self.token_budget = token_budget

    def get_reinforcement(self, turn: int, bank: InstructionBank, tracker) -> str | None:
        if turn % self.every_n_turns != 0 or turn == 0:
            return None

        parts = ["Reminder of your instructions:"]
        for itype, text in bank.instructions.items():
            parts.append(f"- {text}")

        return "\n".join(parts)


class SelectiveReinforcement:
    def __init__(self, every_n_turns: int = 5, token_budget: int = 250):
        self.every_n_turns = every_n_turns
        self.token_budget = token_budget

    def get_reinforcement(
        self, turn: int, bank: InstructionBank, tracker: BayesianComplianceTracker
    ) -> str | None:
        if turn % self.every_n_turns != 0 or turn == 0:
            return None

        ranking = tracker.get_reinforcement_ranking(threshold=2)

        parts = ["Reminder of key instructions:"]
        tokens_used = 5  # header
        for itype in ranking:
            cost = bank.token_estimate(itype)
            if tokens_used + cost > self.token_budget:
                break
            parts.append(f"- {bank.instructions[itype]}")
            tokens_used += cost

        if len(parts) == 1:
            # Budget too small for even one instruction, force the most critical
            parts.append(f"- {bank.instructions[ranking[0]]}")

        return "\n".join(parts)
