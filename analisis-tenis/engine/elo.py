"""
Motor de rating Elo para tenis, con ratings separados por superficie.

Implementa la actualización Elo estándar (la misma familia de fórmulas
que usa FIDE en ajedrez, adaptada a tenis por Sackmann/Tennis Abstract
y otros). El sistema en sí es correcto y genérico: lo que falta en este
entorno son partidos históricos masivos para *calibrar* los ratings de
cientos de jugadores desde cero (ver README del motor).

Como fallback documentado cuando no hay historial de partidos
suficiente, se puede sembrar (`seed_from_rank`) un rating inicial a
partir del ranking ATP/WTA — es una aproximación grosera, no un
sustituto de Elo calculado con datos reales, y se marca explícitamente
como tal en el resultado.
"""

from dataclasses import dataclass, field


DEFAULT_RATING = 1500.0
DEFAULT_K = 32.0


@dataclass
class EloRating:
    """
    Sistema de ratings Elo por jugador, con un rating "general" y
    ratings específicos por superficie (césped, arcilla, dura, indoor).
    """

    k_factor: float = DEFAULT_K
    ratings_overall: dict = field(default_factory=dict)
    ratings_by_surface: dict = field(default_factory=dict)  # {surface: {player: rating}}
    matches_played: dict = field(default_factory=dict)  # conteo, para K dinámico opcional

    def get_rating(self, player: str, surface: str | None = None) -> float:
        if surface:
            return self.ratings_by_surface.get(surface, {}).get(player, DEFAULT_RATING)
        return self.ratings_overall.get(player, DEFAULT_RATING)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Probabilidad esperada de que A gane, según la diferencia de rating."""
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

    def win_probability(self, player_a: str, player_b: str, surface: str | None = None) -> float:
        r_a = self.get_rating(player_a, surface)
        r_b = self.get_rating(player_b, surface)
        return self.expected_score(r_a, r_b)

    def record_match(self, winner: str, loser: str, surface: str | None = None) -> None:
        """
        Actualiza los ratings (overall y de superficie si se especifica)
        tras un partido real winner vs loser.
        """
        self._update_pair(self.ratings_overall, winner, loser)
        if surface:
            surface_dict = self.ratings_by_surface.setdefault(surface, {})
            self._update_pair(surface_dict, winner, loser)

        self.matches_played[winner] = self.matches_played.get(winner, 0) + 1
        self.matches_played[loser] = self.matches_played.get(loser, 0) + 1

    def _update_pair(self, ratings: dict, winner: str, loser: str) -> None:
        r_w = ratings.get(winner, DEFAULT_RATING)
        r_l = ratings.get(loser, DEFAULT_RATING)

        e_w = self.expected_score(r_w, r_l)
        e_l = 1.0 - e_w

        ratings[winner] = r_w + self.k_factor * (1.0 - e_w)
        ratings[loser] = r_l + self.k_factor * (0.0 - e_l)

    def seed_from_rank(self, player: str, atp_wta_rank: int, surface: str | None = None) -> None:
        """
        ⚠️ Aproximación documentada, NO un Elo real calculado con datos
        históricos. Se usa solo cuando no hay partidos previos
        disponibles para ese jugador en este entorno. Mapea el ranking
        a un rating inicial razonable: 1500 + una penalización
        logarítmica por cada puesto fuera del top-1.

        Un rating calculado con miles de partidos reales (fuera de este
        sandbox, ver data_loader.py) siempre debería preferirse sobre
        este seed.
        """
        import math
        penalty = 220 * math.log10(max(atp_wta_rank, 1))
        rating = 2100 - penalty
        self.ratings_overall[player] = rating
        if surface:
            self.ratings_by_surface.setdefault(surface, {})[player] = rating
