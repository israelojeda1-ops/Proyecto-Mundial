"""
Motor de backtesting genérico: dado un historial de apuestas (probabilidad
estimada, cuota, resultado real) y una estrategia de staking, calcula
ROI, yield, win rate y máximo drawdown.

No asume ninguna fuente de datos particular: recibe una lista de
`Bet` ya armada. Ver data_loader.py para cómo (intentar) poblarla con
datos históricos reales, y demo.py para un ejemplo con datos reales
limitados disponibles en este entorno.
"""

from dataclasses import dataclass
from enum import Enum


class StakingMethod(Enum):
    FLAT = "flat"
    KELLY = "kelly"
    KELLY_QUARTER = "kelly_quarter"


@dataclass
class Bet:
    true_probability: float
    decimal_odds: float
    won: bool
    label: str = ""


@dataclass
class BacktestResult:
    n_bets: int
    n_wins: int
    win_rate: float
    total_staked: float
    total_profit: float
    roi: float  # profit / total_staked
    yield_pct: float  # alias de roi en %, terminología estándar de la industria
    final_bankroll: float
    max_drawdown: float  # como fracción del pico de bankroll (0.20 = -20%)
    equity_curve: list


def run_backtest(
    bets: list[Bet],
    staking: StakingMethod = StakingMethod.FLAT,
    initial_bankroll: float = 100.0,
    flat_stake_fraction: float = 0.01,
    min_edge_pp: float = 0.0,
) -> BacktestResult:
    """
    Corre una estrategia sobre una lista de apuestas históricas, en
    orden cronológico (se asume que `bets` ya viene ordenada por fecha).

    - staking FLAT: apuesta `flat_stake_fraction` del bankroll INICIAL
      en cada pick (staking plano clásico, no compuesto).
    - staking KELLY / KELLY_QUARTER: recalcula el stake como fracción
      del bankroll ACTUAL en cada apuesta (crecimiento compuesto).
    - min_edge_pp filtra: solo se apuestan picks cuyo edge (prob. propia
      - prob. implícita) sea >= min_edge_pp puntos porcentuales. Así se
      puede testear reglas del tipo "solo EV > 8% en tenis ATP".
    """
    from ev import kelly_fraction, implied_probability

    bankroll = initial_bankroll
    equity_curve = [bankroll]
    total_staked = 0.0
    total_profit = 0.0
    n_wins = 0
    n_bets = 0
    peak = bankroll
    max_drawdown = 0.0

    for bet in bets:
        implied = implied_probability(bet.decimal_odds)
        edge_pp = (bet.true_probability - implied) * 100
        if edge_pp < min_edge_pp:
            continue

        if staking == StakingMethod.FLAT:
            stake = initial_bankroll * flat_stake_fraction
        elif staking == StakingMethod.KELLY:
            stake = bankroll * kelly_fraction(bet.true_probability, bet.decimal_odds)
        elif staking == StakingMethod.KELLY_QUARTER:
            stake = bankroll * kelly_fraction(bet.true_probability, bet.decimal_odds) * 0.25
        else:
            raise ValueError(f"Staking desconocido: {staking}")

        if stake <= 0:
            continue

        n_bets += 1
        total_staked += stake

        if bet.won:
            profit = stake * (bet.decimal_odds - 1.0)
            n_wins += 1
        else:
            profit = -stake

        bankroll += profit
        total_profit += profit
        equity_curve.append(bankroll)

        peak = max(peak, bankroll)
        drawdown = (peak - bankroll) / peak if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)

    roi = (total_profit / total_staked) if total_staked > 0 else 0.0

    return BacktestResult(
        n_bets=n_bets,
        n_wins=n_wins,
        win_rate=(n_wins / n_bets) if n_bets > 0 else 0.0,
        total_staked=total_staked,
        total_profit=total_profit,
        roi=roi,
        yield_pct=roi * 100,
        final_bankroll=bankroll,
        max_drawdown=max_drawdown,
        equity_curve=equity_curve,
    )
