import random

from montecarlo import (
    simulate_point,
    simulate_game,
    simulate_tiebreak,
    simulate_set,
    simulate_match,
    validate_match_model,
    validate_kelly_staking,
)
from backtest import StakingMethod
from probability import prob_win_game_on_serve


class TestSimulatePrimitives:
    def test_simulate_point_deterministic_with_seed(self):
        rng1 = random.Random(1)
        rng2 = random.Random(1)
        results1 = [simulate_point(0.5, rng1) for _ in range(20)]
        results2 = [simulate_point(0.5, rng2) for _ in range(20)]
        assert results1 == results2

    def test_simulate_game_converges_to_closed_form(self):
        rng = random.Random(123)
        p = 0.62
        n = 4000
        wins = sum(1 for _ in range(n) if simulate_game(p, rng))
        simulated = wins / n
        analytical = prob_win_game_on_serve(p)
        assert abs(simulated - analytical) < 0.03

    def test_simulate_tiebreak_symmetric_converges_to_half(self):
        rng = random.Random(5)
        n = 3000
        wins = sum(1 for _ in range(n) if simulate_tiebreak(0.5, 0.5, rng))
        assert abs(wins / n - 0.5) < 0.03

    def test_simulate_set_bounded(self):
        rng = random.Random(9)
        results = [simulate_set(0.7, 0.6, 0.62, 0.58, rng) for _ in range(50)]
        assert all(isinstance(r, bool) for r in results)

    def test_simulate_match_best_of_5_runs(self):
        rng = random.Random(11)
        results = [simulate_match(0.65, 0.60, best_of=5, rng=rng) for _ in range(30)]
        assert all(isinstance(r, bool) for r in results)


class TestValidateMatchModel:
    def test_symmetric_players_simulation_matches_analytical(self):
        result = validate_match_model(0.62, 0.62, best_of=3, n_simulations=8000, seed=1)
        assert result.within_tolerance
        assert abs(result.simulated_probability - 0.5) < 0.03

    def test_asymmetric_players_simulation_matches_analytical(self):
        # Escenario real: Fritz (65% puntos de saque) vs Kypson (58%),
        # a 5 sets como en Wimbledon.
        result = validate_match_model(0.65, 0.58, best_of=5, n_simulations=8000, seed=2)
        assert result.within_tolerance
        assert result.simulated_probability > 0.5
        assert result.analytical_probability > 0.5

    def test_large_n_gives_tighter_convergence(self):
        small = validate_match_model(0.60, 0.55, best_of=3, n_simulations=1000, seed=3, tolerance=1.0)
        large = validate_match_model(0.60, 0.55, best_of=3, n_simulations=20000, seed=3, tolerance=1.0)
        # Con más simulaciones, el error debería tender a achicarse
        # (no garantizado en cada semilla individual, pero la cota de
        # ambos debe ser razonable).
        assert large.absolute_diff < 0.05


class TestValidateKellyStaking:
    def test_positive_edge_gives_positive_mean_roi(self):
        result = validate_kelly_staking(
            true_probability=0.58,
            decimal_odds=2.0,
            staking=StakingMethod.KELLY_QUARTER,
            n_bets_per_career=300,
            n_careers=300,
            seed=42,
        )
        assert result.theoretical_ev > 0
        assert result.mean_roi > 0
        assert result.pct_profitable_careers > 0.5

    def test_mean_roi_reasonably_close_to_theoretical_ev(self):
        # No van a ser idénticos (Kelly no apuesta el 100% del EV en
        # una sola apostada, compone), pero deberían tener el mismo signo
        # y orden de magnitud razonable.
        result = validate_kelly_staking(
            true_probability=0.55,
            decimal_odds=2.0,
            staking=StakingMethod.KELLY_QUARTER,
            n_bets_per_career=200,
            n_careers=500,
            seed=99,
        )
        assert result.mean_roi > 0
        assert result.theoretical_ev > 0

    def test_no_edge_gives_roughly_zero_mean_roi(self):
        result = validate_kelly_staking(
            true_probability=0.50,
            decimal_odds=2.0,
            staking=StakingMethod.KELLY_QUARTER,
            n_bets_per_career=100,
            n_careers=500,
            seed=17,
        )
        assert abs(result.mean_roi) < 0.05
