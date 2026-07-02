import math
import random

from backtest import Bet, StakingMethod, run_backtest


def make_bets(n, true_prob, decimal_odds, seed=42):
    rng = random.Random(seed)
    bets = []
    for i in range(n):
        won = rng.random() < true_prob
        bets.append(Bet(true_probability=true_prob, decimal_odds=decimal_odds, won=won, label=f"bet-{i}"))
    return bets


class TestRunBacktestBasics:
    def test_empty_bets_gives_zero_result(self):
        result = run_backtest([])
        assert result.n_bets == 0
        assert result.roi == 0.0
        assert result.final_bankroll == 100.0

    def test_all_wins_flat_staking(self):
        bets = [Bet(true_probability=0.9, decimal_odds=2.0, won=True) for _ in range(5)]
        result = run_backtest(bets, staking=StakingMethod.FLAT, initial_bankroll=100.0, flat_stake_fraction=0.1)
        assert result.n_wins == 5
        assert result.win_rate == 1.0
        assert result.total_profit > 0
        assert result.max_drawdown == 0.0

    def test_all_losses_flat_staking(self):
        bets = [Bet(true_probability=0.5, decimal_odds=2.0, won=False) for _ in range(5)]
        result = run_backtest(bets, staking=StakingMethod.FLAT, initial_bankroll=100.0, flat_stake_fraction=0.1)
        assert result.n_wins == 0
        assert result.total_profit < 0
        assert result.max_drawdown > 0

    def test_edge_filter_excludes_low_edge_bets(self):
        # true_probability=0.51, odds=2.0 -> implied 50%, edge = 1pp
        low_edge_bets = [Bet(true_probability=0.51, decimal_odds=2.0, won=True) for _ in range(3)]
        result = run_backtest(low_edge_bets, min_edge_pp=5.0)
        assert result.n_bets == 0

    def test_edge_filter_includes_high_edge_bets(self):
        high_edge_bets = [Bet(true_probability=0.65, decimal_odds=2.0, won=True) for _ in range(3)]
        result = run_backtest(high_edge_bets, min_edge_pp=5.0)
        assert result.n_bets == 3


class TestStakingMethods:
    def test_kelly_staking_grows_bankroll_with_real_edge(self):
        # Con edge real consistente y muestra grande, Kelly debería
        # crecer el bankroll en expectativa.
        bets = make_bets(500, true_prob=0.60, decimal_odds=2.0, seed=1)
        result = run_backtest(bets, staking=StakingMethod.KELLY, initial_bankroll=100.0)
        assert result.final_bankroll > 100.0

    def test_kelly_quarter_has_lower_drawdown_than_full_kelly(self):
        bets = make_bets(300, true_prob=0.55, decimal_odds=2.0, seed=7)
        result_full = run_backtest(bets, staking=StakingMethod.KELLY, initial_bankroll=100.0)
        result_quarter = run_backtest(bets, staking=StakingMethod.KELLY_QUARTER, initial_bankroll=100.0)
        assert result_quarter.max_drawdown <= result_full.max_drawdown

    def test_flat_staking_never_stakes_more_than_flat_fraction(self):
        bets = make_bets(50, true_prob=0.7, decimal_odds=2.5, seed=3)
        result = run_backtest(bets, staking=StakingMethod.FLAT, initial_bankroll=100.0, flat_stake_fraction=0.02)
        avg_stake = result.total_staked / result.n_bets
        assert math.isclose(avg_stake, 2.0, abs_tol=1e-9)


class TestEquityCurveAndDrawdown:
    def test_equity_curve_length_matches_bets_plus_one(self):
        bets = [Bet(true_probability=0.6, decimal_odds=2.0, won=True) for _ in range(4)]
        result = run_backtest(bets, staking=StakingMethod.FLAT)
        assert len(result.equity_curve) == 5  # bankroll inicial + 4 apuestas

    def test_drawdown_bounded_between_zero_and_one(self):
        bets = make_bets(200, true_prob=0.45, decimal_odds=2.0, seed=99)
        result = run_backtest(bets, staking=StakingMethod.KELLY_QUARTER, initial_bankroll=100.0)
        assert 0.0 <= result.max_drawdown <= 1.0

    def test_win_rate_matches_actual_wins(self):
        bets = [
            Bet(true_probability=0.5, decimal_odds=2.0, won=True),
            Bet(true_probability=0.5, decimal_odds=2.0, won=True),
            Bet(true_probability=0.5, decimal_odds=2.0, won=False),
            Bet(true_probability=0.5, decimal_odds=2.0, won=False),
        ]
        result = run_backtest(bets, staking=StakingMethod.FLAT)
        assert math.isclose(result.win_rate, 0.5, abs_tol=1e-9)
