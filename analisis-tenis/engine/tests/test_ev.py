import math
import pytest

from ev import (
    implied_probability,
    remove_vig,
    overround,
    expected_value,
    kelly_fraction,
    fractional_kelly,
    analyze_bet,
)


class TestImpliedProbability:
    def test_even_money(self):
        assert math.isclose(implied_probability(2.0), 0.5, abs_tol=1e-9)

    def test_short_odds(self):
        assert math.isclose(implied_probability(1.25), 0.8, abs_tol=1e-9)

    def test_rejects_odds_at_or_below_one(self):
        with pytest.raises(ValueError):
            implied_probability(1.0)
        with pytest.raises(ValueError):
            implied_probability(0.9)


class TestRemoveVig:
    def test_normalizes_to_one(self):
        # Cuotas típicas con margen: 1.90 / 1.90 (implica 52.6%+52.6%=105.2%)
        raw_a = implied_probability(1.90)
        raw_b = implied_probability(1.90)
        fair_a, fair_b = remove_vig(raw_a, raw_b)
        assert math.isclose(fair_a + fair_b, 1.0, abs_tol=1e-9)
        assert math.isclose(fair_a, 0.5, abs_tol=1e-9)

    def test_preserves_relative_favorite(self):
        raw_a = implied_probability(1.30)
        raw_b = implied_probability(3.50)
        fair_a, fair_b = remove_vig(raw_a, raw_b)
        assert fair_a > fair_b


class TestOverround:
    def test_positive_margin(self):
        raw_a = implied_probability(1.90)
        raw_b = implied_probability(1.90)
        assert overround(raw_a, raw_b) > 0

    def test_no_margin_book(self):
        raw_a = implied_probability(2.0)
        raw_b = implied_probability(2.0)
        assert math.isclose(overround(raw_a, raw_b), 0.0, abs_tol=1e-9)


class TestExpectedValue:
    def test_fair_odds_zero_ev(self):
        # Si la cuota es exactamente 1/p, el EV es 0.
        assert math.isclose(expected_value(0.5, 2.0), 0.0, abs_tol=1e-9)

    def test_positive_ev_when_underpriced(self):
        # Modelo cree 60%, cuota paga como si fuera 50% -> EV positivo
        ev = expected_value(0.60, 2.0)
        assert ev > 0
        assert math.isclose(ev, 0.20, abs_tol=1e-9)

    def test_negative_ev_when_overpriced(self):
        ev = expected_value(0.40, 2.0)
        assert ev < 0

    def test_rejects_invalid_probability(self):
        with pytest.raises(ValueError):
            expected_value(1.5, 2.0)


class TestKellyFraction:
    def test_no_edge_gives_zero(self):
        assert kelly_fraction(0.5, 2.0) == 0.0

    def test_positive_edge_gives_positive_stake(self):
        f = kelly_fraction(0.60, 2.0)
        assert f > 0

    def test_never_negative(self):
        f = kelly_fraction(0.30, 2.0)
        assert f == 0.0

    def test_known_reference_value(self):
        # p=0.6, cuota=2.0 (b=1) -> f* = (0.6*1 - 0.4)/1 = 0.2
        f = kelly_fraction(0.60, 2.0)
        assert math.isclose(f, 0.20, abs_tol=1e-9)

    def test_higher_edge_gives_higher_stake(self):
        f_small_edge = kelly_fraction(0.52, 2.0)
        f_big_edge = kelly_fraction(0.70, 2.0)
        assert f_big_edge > f_small_edge


class TestFractionalKelly:
    def test_half_kelly_is_half_of_full(self):
        full = kelly_fraction(0.60, 2.0)
        half = fractional_kelly(0.60, 2.0, fraction=0.5)
        assert math.isclose(half, full * 0.5, abs_tol=1e-9)

    def test_rejects_invalid_fraction(self):
        with pytest.raises(ValueError):
            fractional_kelly(0.6, 2.0, fraction=0.0)
        with pytest.raises(ValueError):
            fractional_kelly(0.6, 2.0, fraction=1.5)


class TestAnalyzeBet:
    def test_flags_value_bet_correctly(self):
        # Cuota 2.20 implica 45.5%; modelo dice 55% -> edge ~9.5pp, valor
        analysis = analyze_bet(true_probability=0.55, decimal_odds=2.20)
        assert analysis.is_value
        assert analysis.ev > 0
        assert analysis.edge_pp > 5

    def test_flags_non_value_bet(self):
        # Cuota 1.20 implica 83.3%; modelo dice 81% -> sin valor
        analysis = analyze_bet(true_probability=0.81, decimal_odds=1.20)
        assert not analysis.is_value

    def test_respects_min_edge_threshold(self):
        # Edge positivo pero chico (1pp) no debería marcarse como valor
        # si el umbral mínimo es 3pp.
        analysis = analyze_bet(true_probability=0.51, decimal_odds=2.0, min_edge_pp=3.0)
        assert not analysis.is_value

    def test_kelly_quarter_is_quarter_of_full_kelly(self):
        analysis = analyze_bet(true_probability=0.60, decimal_odds=2.20)
        assert math.isclose(analysis.kelly_quarter, analysis.kelly * 0.25, abs_tol=1e-9)
