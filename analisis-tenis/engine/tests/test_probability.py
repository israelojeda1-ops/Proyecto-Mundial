import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from probability import (
    prob_win_game_on_serve,
    prob_win_tiebreak,
    prob_win_set,
    prob_win_match,
    match_win_probability,
)


class TestProbWinGame:
    def test_symmetric_point_gives_half(self):
        assert math.isclose(prob_win_game_on_serve(0.5), 0.5, abs_tol=1e-9)

    def test_certain_win(self):
        assert prob_win_game_on_serve(1.0) == 1.0

    def test_certain_loss(self):
        assert prob_win_game_on_serve(0.0) == 0.0

    def test_monotonic_increasing(self):
        ps = [0.1 * i for i in range(1, 10)]
        probs = [prob_win_game_on_serve(p) for p in ps]
        assert probs == sorted(probs)

    def test_typical_serve_pct_gives_high_hold(self):
        # Un jugador que gana 65% de sus puntos de saque debería
        # ganar su juego de saque una gran mayoría de las veces
        # (valor de referencia conocido en literatura de tennis
        # analytics: p=0.65 -> hold ~0.83).
        hold = prob_win_game_on_serve(0.65)
        assert 0.78 < hold < 0.90

    def test_rejects_invalid_input(self):
        import pytest
        with pytest.raises(ValueError):
            prob_win_game_on_serve(1.5)
        with pytest.raises(ValueError):
            prob_win_game_on_serve(-0.1)


class TestProbWinTiebreak:
    def test_symmetric_gives_half(self):
        assert math.isclose(prob_win_tiebreak(0.5, 0.5), 0.5, abs_tol=1e-9)

    def test_stronger_server_favored(self):
        assert prob_win_tiebreak(0.7, 0.5) > 0.5

    def test_certain_win_both_serves(self):
        # Si A siempre gana su punto de saque y B nunca gana el suyo
        # (es decir, A también gana todos los puntos de retorno)
        assert math.isclose(prob_win_tiebreak(1.0, 0.0), 1.0, abs_tol=1e-9)


class TestProbWinSet:
    def test_symmetric_gives_half(self):
        p = prob_win_set(0.75, 0.75, 0.62, 0.62)
        assert math.isclose(p, 0.5, abs_tol=1e-9)

    def test_stronger_hold_favored(self):
        p = prob_win_set(0.85, 0.65, 0.65, 0.55)
        assert p > 0.5

    def test_bounds(self):
        p = prob_win_set(0.9, 0.5, 0.65, 0.55)
        assert 0.0 <= p <= 1.0


class TestProbWinMatch:
    def test_symmetric_gives_half_bo3(self):
        assert math.isclose(prob_win_match(0.5, best_of=3), 0.5, abs_tol=1e-9)

    def test_symmetric_gives_half_bo5(self):
        assert math.isclose(prob_win_match(0.5, best_of=5), 0.5, abs_tol=1e-9)

    def test_best_of_5_amplifies_favorite_more_than_bo3(self):
        # Un favorito con set_prob=0.6 tiene más probabilidad de ganar
        # el partido a 5 sets que a 3 (menos varianza, favorece al mejor).
        p_bo3 = prob_win_match(0.6, best_of=3)
        p_bo5 = prob_win_match(0.6, best_of=5)
        assert p_bo5 > p_bo3

    def test_invalid_best_of(self):
        import pytest
        with pytest.raises(ValueError):
            prob_win_match(0.5, best_of=4)


class TestMatchWinProbabilityPipeline:
    def test_equal_players_gives_half(self):
        result = match_win_probability(0.63, 0.63, best_of=3)
        assert math.isclose(result["match_prob_a"], 0.5, abs_tol=1e-9)

    def test_better_server_favored(self):
        # Fritz-like server (65% puntos de saque) vs. Kypson-like (58%)
        result = match_win_probability(0.65, 0.58, best_of=5)
        assert result["match_prob_a"] > 0.5
        assert result["match_prob_a"] + result["match_prob_b"] == 1.0

    def test_output_is_auditable(self):
        result = match_win_probability(0.6, 0.55, best_of=3)
        for key in ("hold_a", "hold_b", "break_a", "break_b", "set_prob_a", "match_prob_a", "match_prob_b"):
            assert key in result
            assert 0.0 <= result[key] <= 1.0
