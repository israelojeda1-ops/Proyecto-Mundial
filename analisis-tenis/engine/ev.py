"""
Cálculo de probabilidad implícita, remoción de margen (vig), valor
esperado (EV) y tamaño de apuesta óptimo (criterio de Kelly).

Todas las funciones trabajan con cuotas decimales (formato europeo:
1.85, 2.40, etc. — pago total incluyendo el stake).
"""

from dataclasses import dataclass


def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("La cuota decimal debe ser mayor a 1.0")
    return 1.0 / decimal_odds


def remove_vig(prob_a_raw: float, prob_b_raw: float) -> tuple[float, float]:
    """
    Normaliza dos probabilidades implícitas (que suman >100% por el
    margen de la casa) para que sumen exactamente 100%.
    """
    total = prob_a_raw + prob_b_raw
    if total <= 0:
        raise ValueError("La suma de probabilidades debe ser positiva")
    return prob_a_raw / total, prob_b_raw / total


def overround(prob_a_raw: float, prob_b_raw: float) -> float:
    """Margen de la casa como fracción (0.05 = 5%)."""
    return prob_a_raw + prob_b_raw - 1.0


def expected_value(true_probability: float, decimal_odds: float) -> float:
    """
    EV como fracción del stake apostado.
    EV = p * (cuota - 1) - (1 - p)  =  p * cuota - 1

    EV > 0 significa que, en promedio y a largo plazo, la apuesta es
    rentable dado el `true_probability` estimado.
    """
    if not 0.0 <= true_probability <= 1.0:
        raise ValueError("true_probability debe estar entre 0 y 1")
    return true_probability * decimal_odds - 1.0


def kelly_fraction(true_probability: float, decimal_odds: float) -> float:
    """
    Fracción del bankroll a apostar según el criterio de Kelly completo.

    f* = (p * b - q) / b   donde b = cuota - 1 (ganancia neta por unidad),
                                 q = 1 - p

    Devuelve 0 si no hay valor (Kelly negativo -> no apostar), nunca
    un valor negativo.
    """
    if not 0.0 <= true_probability <= 1.0:
        raise ValueError("true_probability debe estar entre 0 y 1")
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - true_probability
    f = (true_probability * b - q) / b
    return max(f, 0.0)


def fractional_kelly(true_probability: float, decimal_odds: float, fraction: float = 0.5) -> float:
    """
    Kelly fraccional (p.ej. "medio Kelly" con fraction=0.5): reduce la
    varianza a costa de crecimiento esperado más lento. Es lo que
    recomienda la práctica profesional en vez de Kelly completo, que es
    muy agresivo frente a errores de estimación del modelo.
    """
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction debe estar entre 0 (exclusivo) y 1")
    return kelly_fraction(true_probability, decimal_odds) * fraction


@dataclass
class ValueBetAnalysis:
    true_probability: float
    implied_probability: float
    decimal_odds: float
    edge_pp: float  # puntos porcentuales de diferencia
    ev: float  # fracción, 0.18 = +18%
    kelly: float  # fracción del bankroll, Kelly completo
    kelly_quarter: float  # Kelly a 1/4, tamaño recomendado por defecto
    is_value: bool  # True si EV > 0 Y el edge supera un umbral mínimo


def analyze_bet(true_probability: float, decimal_odds: float, min_edge_pp: float = 2.0) -> ValueBetAnalysis:
    """
    Análisis completo de una apuesta: junta probabilidad implícita, EV
    y Kelly en un solo objeto auditable, igual que se pediría en una
    mesa de trading deportivo.
    """
    implied = implied_probability(decimal_odds)
    edge_pp = (true_probability - implied) * 100
    ev = expected_value(true_probability, decimal_odds)
    k = kelly_fraction(true_probability, decimal_odds)
    k_quarter = k * 0.25

    return ValueBetAnalysis(
        true_probability=true_probability,
        implied_probability=implied,
        decimal_odds=decimal_odds,
        edge_pp=edge_pp,
        ev=ev,
        kelly=k,
        kelly_quarter=k_quarter,
        is_value=(ev > 0 and edge_pp >= min_edge_pp),
    )
