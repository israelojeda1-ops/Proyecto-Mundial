import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elo import EloRating, DEFAULT_RATING


class TestExpectedScore:
    def test_equal_ratings_gives_half(self):
        elo = EloRating()
        assert math.isclose(elo.expected_score(1500, 1500), 0.5, abs_tol=1e-9)

    def test_higher_rating_favored(self):
        elo = EloRating()
        assert elo.expected_score(1600, 1500) > 0.5

    def test_symmetric(self):
        elo = EloRating()
        e_ab = elo.expected_score(1600, 1400)
        e_ba = elo.expected_score(1400, 1600)
        assert math.isclose(e_ab + e_ba, 1.0, abs_tol=1e-9)

    def test_known_reference_value(self):
        # Diferencia de 400 puntos -> ~90.9% de probabilidad (valor
        # de referencia estándar en la literatura de rating Elo).
        elo = EloRating()
        e = elo.expected_score(1900, 1500)
        assert math.isclose(e, 0.9091, abs_tol=0.001)


class TestRecordMatch:
    def test_new_players_start_at_default(self):
        elo = EloRating()
        assert elo.get_rating("Nuevo Jugador") == DEFAULT_RATING

    def test_winner_gains_loser_loses(self):
        elo = EloRating()
        r_w_before = elo.get_rating("A")
        r_l_before = elo.get_rating("B")
        elo.record_match(winner="A", loser="B")
        assert elo.get_rating("A") > r_w_before
        assert elo.get_rating("B") < r_l_before

    def test_zero_sum_between_two_new_players(self):
        # Con rating inicial igual, la ganancia de uno debe ser
        # exactamente la pérdida del otro (K idéntico para ambos).
        elo = EloRating()
        elo.record_match(winner="A", loser="B")
        gain = elo.get_rating("A") - DEFAULT_RATING
        loss = DEFAULT_RATING - elo.get_rating("B")
        assert math.isclose(gain, loss, abs_tol=1e-9)

    def test_upset_produces_larger_swing_than_expected_win(self):
        elo = EloRating()
        elo.ratings_overall["Favorito"] = 1800
        elo.ratings_overall["Underdog"] = 1400

        # Escenario esperado: gana el favorito -> cambio chico
        elo_expected = EloRating()
        elo_expected.ratings_overall["Favorito"] = 1800
        elo_expected.ratings_overall["Underdog"] = 1400
        elo_expected.record_match(winner="Favorito", loser="Underdog")
        swing_expected = elo_expected.ratings_overall["Favorito"] - 1800

        # Escenario sorpresa: gana el underdog -> cambio grande
        elo.record_match(winner="Underdog", loser="Favorito")
        swing_upset = elo.ratings_overall["Underdog"] - 1400

        assert swing_upset > swing_expected

    def test_surface_specific_ratings_are_independent(self):
        elo = EloRating()
        elo.record_match(winner="A", loser="B", surface="grass")
        assert elo.get_rating("A", surface="grass") > DEFAULT_RATING
        # No debería afectar el rating en otra superficie ni el overall
        # de un jugador que no jugó ese partido en esa superficie.
        assert elo.get_rating("A", surface="clay") == DEFAULT_RATING

    def test_match_counter_increments(self):
        elo = EloRating()
        elo.record_match(winner="A", loser="B")
        elo.record_match(winner="A", loser="C")
        assert elo.matches_played["A"] == 2
        assert elo.matches_played["B"] == 1


class TestSeedFromRank:
    def test_rank_1_gets_highest_seed(self):
        elo = EloRating()
        elo.seed_from_rank("Top1", atp_wta_rank=1)
        elo.seed_from_rank("Top100", atp_wta_rank=100)
        assert elo.get_rating("Top1") > elo.get_rating("Top100")

    def test_seed_is_deterministic(self):
        elo = EloRating()
        elo.seed_from_rank("Jugador", atp_wta_rank=50)
        r1 = elo.get_rating("Jugador")
        elo2 = EloRating()
        elo2.seed_from_rank("Jugador", atp_wta_rank=50)
        r2 = elo2.get_rating("Jugador")
        assert r1 == r2

    def test_win_probability_uses_seeded_ratings(self):
        elo = EloRating()
        elo.seed_from_rank("Top10", atp_wta_rank=10)
        elo.seed_from_rank("Top150", atp_wta_rank=150)
        assert elo.win_probability("Top10", "Top150") > 0.5
