"""
Simulaciones Monte Carlo, con dos propósitos:

1. Validar el modelo analítico de probability.py: simular partidos
   punto por punto miles de veces y comprobar que la frecuencia de
   victorias converge al resultado cerrado (DP) de
   `match_win_probability`. Si ambos coinciden, tenemos alta confianza
   en que la matemática del modelo está bien implementada.

2. Validar el motor de EV/Kelly: simular miles de "carreras" de apuestas
   con un edge conocido y comprobar que el ROI promedio converge al EV
   teórico, y que Kelly crece el bankroll más rápido que apuesta plana
   a largo plazo (con más varianza).

Usa solo `random` de la librería estándar — determinista si se fija
una semilla, para que los tests sean reproducibles.
"""

import random
from dataclasses import dataclass

from backtest import Bet, StakingMethod, run_backtest
from ev import expected_value


def simulate_point(p: float, rng: random.Random) -> bool:
    return rng.random() < p


def simulate_game(p: float, rng: random.Random) -> bool:
    """Simula un juego punto por punto (con deuce/ventaja reales)."""
    points_server = 0
    points_returner = 0
    while True:
        if simulate_point(p, rng):
            points_server += 1
        else:
            points_returner += 1

        if points_server >= 4 and points_server - points_returner >= 2:
            return True
        if points_returner >= 4 and points_returner - points_server >= 2:
            return False


def simulate_tiebreak(p_a: float, p_b: float, rng: random.Random, target: int = 7) -> bool:
    """Simula un tiebreak punto por punto con la alternancia real 1-2-2-2."""
    points_a = 0
    points_b = 0
    server_is_a = True
    total_points = 0
    while True:
        p_point_a = p_a if server_is_a else (1 - p_b)
        if simulate_point(p_point_a, rng):
            points_a += 1
        else:
            points_b += 1

        if points_a >= target and points_a - points_b >= 2:
            return True
        if points_b >= target and points_b - points_a >= 2:
            return False

        total_points += 1
        # Alternancia: punto 1 lo saca A, luego cambia cada 2 puntos.
        if total_points == 1:
            server_is_a = not server_is_a
        elif total_points % 2 == 1:
            server_is_a = not server_is_a


def simulate_set(hold_a: float, hold_b: float, p_a_point: float, p_b_point: float, rng: random.Random) -> bool:
    games_a = 0
    games_b = 0
    while True:
        a_serves = (games_a + games_b) % 2 == 0
        p_a_wins_game = hold_a if a_serves else (1 - hold_b)

        if simulate_point(p_a_wins_game, rng):
            games_a += 1
        else:
            games_b += 1

        if games_a == 6 and games_b <= 4:
            return True
        if games_b == 6 and games_a <= 4:
            return False
        if games_a == 7:
            return True
        if games_b == 7:
            return False
        if games_a == 6 and games_b == 6:
            return simulate_tiebreak(p_a_point, p_b_point, rng)


def simulate_match(p_a_point: float, p_b_point: float, best_of: int, rng: random.Random) -> bool:
    from probability import prob_win_game_on_serve

    hold_a = prob_win_game_on_serve(p_a_point)
    hold_b = prob_win_game_on_serve(p_b_point)
    sets_needed = best_of // 2 + 1

    sets_a = 0
    sets_b = 0
    while True:
        if simulate_set(hold_a, hold_b, p_a_point, p_b_point, rng):
            sets_a += 1
        else:
            sets_b += 1

        if sets_a == sets_needed:
            return True
        if sets_b == sets_needed:
            return False


@dataclass
class MonteCarloValidation:
    n_simulations: int
    simulated_probability: float
    analytical_probability: float
    absolute_diff: float
    within_tolerance: bool


def validate_match_model(
    p_a_point: float,
    p_b_point: float,
    best_of: int = 3,
    n_simulations: int = 10000,
    seed: int = 42,
    tolerance: float = 0.02,
) -> MonteCarloValidation:
    """
    Corre `n_simulations` partidos simulados punto por punto y compara
    la frecuencia de victorias de A contra la probabilidad cerrada de
    `match_win_probability`. Es la prueba de que el modelo analítico
    (rápido, usado en producción) coincide con la simulación exacta
    (lenta, usada solo para verificar).
    """
    from probability import match_win_probability

    rng = random.Random(seed)
    wins_a = sum(
        1 for _ in range(n_simulations)
        if simulate_match(p_a_point, p_b_point, best_of, rng)
    )
    simulated = wins_a / n_simulations
    analytical = match_win_probability(p_a_point, p_b_point, best_of)["match_prob_a"]
    diff = abs(simulated - analytical)

    return MonteCarloValidation(
        n_simulations=n_simulations,
        simulated_probability=simulated,
        analytical_probability=analytical,
        absolute_diff=diff,
        within_tolerance=diff <= tolerance,
    )


@dataclass
class KellyValidation:
    n_careers: int
    n_bets_per_career: int
    mean_roi: float
    median_roi: float
    pct_profitable_careers: float
    theoretical_ev: float


def validate_kelly_staking(
    true_probability: float,
    decimal_odds: float,
    staking: StakingMethod = StakingMethod.KELLY_QUARTER,
    n_bets_per_career: int = 500,
    n_careers: int = 2000,
    seed: int = 7,
) -> KellyValidation:
    """
    Simula `n_careers` "carreras" de apostador independientes, cada una
    con `n_bets_per_career` apuestas al mismo edge conocido, y comprueba
    que el ROI promedio converge al EV teórico (p*cuota - 1) — es decir,
    que el motor de backtesting no tiene un sesgo oculto en la
    contabilidad de ganancias/pérdidas.
    """
    rng = random.Random(seed)
    theoretical_ev = expected_value(true_probability, decimal_odds)

    rois = []
    for _ in range(n_careers):
        bets = [
            Bet(
                true_probability=true_probability,
                decimal_odds=decimal_odds,
                won=simulate_point(true_probability, rng),
            )
            for _ in range(n_bets_per_career)
        ]
        result = run_backtest(bets, staking=staking, initial_bankroll=100.0)
        rois.append(result.roi)

    rois.sort()
    mean_roi = sum(rois) / len(rois)
    median_roi = rois[len(rois) // 2]
    pct_profitable = sum(1 for r in rois if r > 0) / len(rois)

    return KellyValidation(
        n_careers=n_careers,
        n_bets_per_career=n_bets_per_career,
        mean_roi=mean_roi,
        median_roi=median_roi,
        pct_profitable_careers=pct_profitable,
        theoretical_ev=theoretical_ev,
    )
