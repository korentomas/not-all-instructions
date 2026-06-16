"""instruction_retention task: dataset + solver + scorer wired together."""

from inspect_ai import Task, task

from retention.dataset import CONDITIONS, retention_dataset
from retention.scorer import deterministic_compliance, judge_panel
from retention.solver import retention_harness


@task
def instruction_retention(conditions: tuple[str, ...] = CONDITIONS) -> Task:
    """`conditions` selects the measurement arms: the default factorial is
    {baseline, treatment}; run_framing.py passes the framing arms
    {treatment_positive, treatment_negation} instead."""
    return Task(
        dataset=retention_dataset(conditions=tuple(conditions)),
        solver=retention_harness(),
        # two channels: deterministic checkers (primary) + cross-family judge panel
        # (secondary, for checker-judge κ). κ itself is computed offline in analysis/.
        scorer=[deterministic_compliance(), judge_panel()],
        version="1-A",
    )
