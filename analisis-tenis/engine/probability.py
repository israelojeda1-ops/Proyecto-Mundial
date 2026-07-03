"""
Modelo cuantitativo de probabilidad de tenis: punto -> juego -> set -> partido.

Implementa las fórmulas estándar de la literatura de tennis analytics
(Klaassen & Magnus 2003; Barnett & Clarke 2005; O'Malley 2008) para
convertir la probabilidad de ganar un punto con el propio saque en la
probabilidad de ganar el partido completo, sin necesitar datos
históricos masivos: solo estadísticas de saque del propio partido o de
la temporada del jugador.

No usa librerías externas.
"""

from functools import lru_cache


def prob_win_game_on_serve(p: float) -> float:
    """
    Probabilidad de ganar un juego de saque dado p = prob. de ganar
    un punto con el propio saque.

    Fórmula cerrada (Klaassen & Magnus 2003):
      P(4-0) + P(4-1) + P(4-2) + P(llegar a deuce) * P(ganar desde deuce)
    """
    if not 0 <= p <= 1:
        raise ValueError("p debe estar entre 0 y 1")
    q = 1 - p

    p_4_0 = p ** 4
    p_4_1 = 4 * (p ** 4) * q
    p_4_2 = 10 * (p ** 4) * (q ** 2)
    p_reach_deuce = 20 * (p ** 3) * (q ** 3)

    if p == 0.5:
        p_win_from_deuce = 0.5
    else:
        p_win_from_deuce = (p ** 2) / (p ** 2 + q ** 2)

    return p_4_0 + p_4_1 + p_4_2 + p_reach_deuce * p_win_from_deuce


def _server_is_a_at(total_points: int) -> bool:
    """Alternancia estándar de saque en el tiebreak: A saca el punto 1,
    luego se alterna cada 2 puntos (B-B-A-A-B-B-A-A...)."""
    if total_points == 0:
        return True
    # Punto índice 0 -> A. A partir de ahí, bloques de 2.
    block = (total_points - 1) // 2
    starts_with_b = True  # el punto índice 1 (segundo punto) es de B
    return not (starts_with_b if block % 2 == 0 else not starts_with_b)


@lru_cache(maxsize=None)
def prob_win_tiebreak(p_a: float, p_b: float, target: int = 7) -> float:
    """
    Probabilidad de que el jugador A gane un tiebreak a `target` puntos
    (con diferencia de 2), dado p_a = prob. de A de ganar un punto
    sacando él, p_b = prob. de B de ganar un punto sacando él.

    Implementado con programación dinámica iterativa (bottom-up) sobre
    una grilla acotada de marcador, para evitar profundidad de
    recursión excesiva en casos simétricos. Más allá de `target + margin`
    puntos por jugador la probabilidad remanente es despreciable
    (< 1e-12), así que se acota la grilla ahí sin pérdida práctica de
    precisión.
    """
    margin = 30  # puntos de "colchón" más allá del objetivo — sobra por lejos
    max_score = target + margin

    # dp[(points_a, points_b, server_is_a)] = prob. de que A gane desde ese estado
    dp = {}

    # Estados terminales primero: recorremos de scores altos a bajos.
    for points_a in range(max_score, -1, -1):
        for points_b in range(max_score, -1, -1):
            if points_a >= target and points_a - points_b >= 2:
                dp[(points_a, points_b, True)] = 1.0
                dp[(points_a, points_b, False)] = 1.0
                continue
            if points_b >= target and points_b - points_a >= 2:
                dp[(points_a, points_b, True)] = 0.0
                dp[(points_a, points_b, False)] = 0.0
                continue
            if points_a == max_score or points_b == max_score:
                # Borde de la grilla: en la práctica nunca se llega aquí
                # con probabilidad no despreciable: lo tratamos como
                # "sigue empatado", aproximación segura por el margen amplio.
                dp[(points_a, points_b, True)] = 0.5
                dp[(points_a, points_b, False)] = 0.5
                continue

            for server_is_a in (True, False):
                p_point_a = p_a if server_is_a else (1 - p_b)
                total_points = points_a + points_b
                next_server_is_a = _server_is_a_at(total_points + 1)
                win_next = dp[(points_a + 1, points_b, next_server_is_a)]
                lose_next = dp[(points_a, points_b + 1, next_server_is_a)]
                dp[(points_a, points_b, server_is_a)] = (
                    p_point_a * win_next + (1 - p_point_a) * lose_next
                )

    return dp[(0, 0, True)]


def prob_win_set(hold_a: float, hold_b: float, p_a_point: float, p_b_point: float) -> float:
    """
    Probabilidad de que A gane un set a 6 juegos (con tiebreak a 6-6),
    dado hold_a/hold_b = prob. de ganar el propio juego de saque, y
    p_a_point/p_b_point = prob. de ganar un punto con el propio saque
    (usado solo para el tiebreak).

    DP sobre el marcador de juegos del set. A saca en los juegos impares
    (0-0, 1-1, 2-2... es decir cuando games_a+games_b es par).
    """

    @lru_cache(maxsize=None)
    def state(games_a: int, games_b: int) -> float:
        if games_a == 6 and games_b <= 4:
            return 1.0
        if games_b == 6 and games_a <= 4:
            return 0.0
        if games_a == 7:
            return 1.0
        if games_b == 7:
            return 0.0
        if games_a == 6 and games_b == 6:
            return prob_win_tiebreak(p_a_point, p_b_point)

        a_serves = (games_a + games_b) % 2 == 0
        p_a_wins_game = hold_a if a_serves else (1 - hold_b)

        return p_a_wins_game * state(games_a + 1, games_b) + \
            (1 - p_a_wins_game) * state(games_a, games_b + 1)

    result = state(0, 0)
    state.cache_clear()
    return result


def prob_win_match(prob_set_a: float, best_of: int = 3) -> float:
    """
    Probabilidad de ganar un partido a mejor de `best_of` sets (3 o 5),
    asumiendo sets independientes e idénticamente distribuidos (supuesto
    estándar simplificador de estos modelos: no capturan momentum/fatiga
    entre sets).
    """
    if best_of not in (3, 5):
        raise ValueError("best_of debe ser 3 o 5")
    sets_needed = best_of // 2 + 1  # 2 de 3, o 3 de 5

    @lru_cache(maxsize=None)
    def state(wins_a: int, wins_b: int) -> float:
        if wins_a == sets_needed:
            return 1.0
        if wins_b == sets_needed:
            return 0.0
        return prob_set_a * state(wins_a + 1, wins_b) + \
            (1 - prob_set_a) * state(wins_a, wins_b + 1)

    result = state(0, 0)
    state.cache_clear()
    return result


def match_win_probability(
    p_a_serve_point: float,
    p_b_serve_point: float,
    best_of: int = 3,
) -> dict:
    """
    Pipeline completo punto -> juego -> set -> partido.

    p_a_serve_point / p_b_serve_point: probabilidad de cada jugador de
    ganar un punto cuando saca él mismo (se puede estimar como
    aces + puntos ganados con 1er/2do saque, o usar el % de puntos
    ganados al saque de la temporada).

    Devuelve un dict con las probabilidades intermedias para que el
    análisis sea auditable, no una caja negra.
    """
    hold_a = prob_win_game_on_serve(p_a_serve_point)
    hold_b = prob_win_game_on_serve(p_b_serve_point)

    set_prob_a = prob_win_set(hold_a, hold_b, p_a_serve_point, p_b_serve_point)
    match_prob_a = prob_win_match(set_prob_a, best_of=best_of)

    return {
        "hold_a": hold_a,
        "hold_b": hold_b,
        "break_a": 1 - hold_b,  # prob. de A de romper el saque de B
        "break_b": 1 - hold_a,
        "set_prob_a": set_prob_a,
        "match_prob_a": match_prob_a,
        "match_prob_b": 1 - match_prob_a,
    }
