"""Index-based access for aligned backtest observations.

Helper to allow array-like access to BacktestObservation lists
for transition counting in Christoffersen test.
"""

from manco_risk.risk.models.backtest_result import BacktestObservation


def get_breach_sequence(aligned_observations: list[BacktestObservation]) -> list[bool]:
    """Extract breach sequence from aligned observations.

    Parameters
    ----------
    aligned_observations : list[BacktestObservation]
        Observations sorted by date (guaranteed by BacktestResult).

    Returns
    -------
    list[bool]
        Sequence of breach flags, ordered by date.
        True = breach, False = no breach.
    """
    return [obs.is_breach for obs in aligned_observations]
