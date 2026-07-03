"""
Demo end-to-end del motor cuantitativo, usando datos reales investigados
en esta sesión (estadísticas de saque, rankings ATP, cuotas reales de
Betano, y 2 resultados de Wimbledon 2026 ya confirmados).

Corre:
    python3 demo.py
"""

from elo import EloRating
from ev import analyze_bet
from probability import match_win_probability
from backtest import Bet, StakingMethod, run_backtest
from montecarlo import validate_match_model, validate_kelly_staking


def section(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def demo_point_to_match_model() -> None:
    section("1) MODELO PUNTO -> JUEGO -> SET -> PARTIDO (Fritz vs Kypson)")
    print(
        "Fritz sacó 14 aces y 0 dobles faltas en su R1 de Wimbledon 2026 "
        "(saque muy eficiente, ~68% de puntos ganados al servicio en el "
        "circuito). Kypson es top-113 con un saque muy inferior (~60%)."
    )
    result = match_win_probability(p_a_serve_point=0.68, p_b_serve_point=0.60, best_of=5)
    print(f"  Prob. de retener el saque (hold) Fritz: {result['hold_a']:.1%}")
    print(f"  Prob. de retener el saque (hold) Kypson: {result['hold_b']:.1%}")
    print(f"  Prob. de romper el saque Fritz: {result['break_a']:.1%}")
    print(f"  Prob. de ganar un set Fritz: {result['set_prob_a']:.1%}")
    print(f"  Prob. de ganar el partido Fritz (a 5 sets): {result['match_prob_a']:.1%}")
    print(
        f"  → Betano pagaba Fritz a 1.05 (implícito ~95.2%); el modelo, "
        f"desde estadísticas de saque puras, da {result['match_prob_a']:.1%}."
    )


def demo_elo_from_real_rankings() -> None:
    section("2) ELO SEMBRADO DESDE RANKING REAL (proxy documentado)")
    elo = EloRating()
    # Rankings reales investigados esta sesión (Wimbledon 2026, 2 jul).
    elo.seed_from_rank("G. Diallo", atp_wta_rank=38, surface="grass")
    elo.seed_from_rank("L. Sonego", atp_wta_rank=52, surface="grass")
    elo.seed_from_rank("A. Zverev", atp_wta_rank=3, surface="grass")
    elo.seed_from_rank("V. Royer", atp_wta_rank=75, surface="grass")

    p_diallo = elo.win_probability("G. Diallo", "L. Sonego", surface="grass")
    p_zverev = elo.win_probability("A. Zverev", "V. Royer", surface="grass")

    print(f"  Diallo vs Sonego (seed por ranking): Diallo {p_diallo:.1%}")
    print(f"  (Nuestra estimación investigada manualmente esta sesión: 62%)")
    print(f"  Zverev vs Royer (seed por ranking): Zverev {p_zverev:.1%}")
    print(f"  (Nuestra estimación investigada manualmente esta sesión: 90%)")
    print(
        "  ⚠️  Esto es un proxy rank->Elo, NO un Elo real calculado con "
        "historial de partidos (bloqueado en este entorno — ver README)."
    )


def demo_ev_and_kelly_on_real_odds() -> None:
    section("3) EV Y KELLY SOBRE CUOTAS REALES DE BETANO (2 jul 2026)")
    picks = [
        ("G. Diallo (vs Sonego)", 0.62, 1.81),
        ("K. Khachanov (vs Hanfmann)", 0.64, 1.63),
        ("A. de Minaur (vs Mannarino)", 0.81, 1.22),
        ("J. Lehečka (vs Molčan)", 0.80, 1.28),
        ("T. Fritz (vs Kypson)", 0.95, 1.06),
        ("F. Tiafoe (vs Choinski)", 0.78, 1.15),  # caso de riesgo real
    ]
    for name, prob, odds in picks:
        a = analyze_bet(true_probability=prob, decimal_odds=odds, min_edge_pp=3.0)
        tag = "💎 VALOR" if a.is_value else "  justo/riesgo"
        print(
            f"  {name:32s} p={prob:.0%}  cuota={odds:.2f}  "
            f"implícita={a.implied_probability:.1%}  edge={a.edge_pp:+.1f}pp  "
            f"EV={a.ev:+.1%}  Kelly 1/4={a.kelly_quarter:.2%} del bankroll  [{tag}]"
        )


def demo_montecarlo_validation() -> None:
    section("4) VALIDACIÓN MONTE CARLO DEL MODELO ANALÍTICO")
    for n in (10_000, 50_000):
        v = validate_match_model(p_a_point=0.65, p_b_point=0.58, best_of=5, n_simulations=n, seed=1)
        status = "✅ coincide" if v.within_tolerance else "❌ NO coincide"
        print(
            f"  n={n:>6,}  simulado={v.simulated_probability:.4f}  "
            f"analítico={v.analytical_probability:.4f}  "
            f"diff={v.absolute_diff:.4f}  {status}"
        )

    section("5) VALIDACIÓN MONTE CARLO DEL STAKING KELLY (2000 carreras x 400 apuestas)")
    kv = validate_kelly_staking(
        true_probability=0.58, decimal_odds=1.95,
        staking=StakingMethod.KELLY_QUARTER,
        n_bets_per_career=400, n_careers=2000, seed=42,
    )
    print(f"  EV teórico por apuesta: {kv.theoretical_ev:+.2%}")
    print(f"  ROI promedio simulado (2000 carreras): {kv.mean_roi:+.2%}")
    print(f"  ROI mediano simulado: {kv.median_roi:+.2%}")
    print(f"  % de carreras rentables: {kv.pct_profitable_careers:.1%}")


def demo_real_backtest_illustrative() -> None:
    section("6) BACKTEST ILUSTRATIVO CON RESULTADOS REALES YA CONFIRMADOS (n=2)")
    print(
        "⚠️  Muestra chica a propósito: son los únicos 2 resultados de "
        "Wimbledon 2026 confirmados durante esta sesión con cuota Betano "
        "real y probabilidad propia registrada ANTES del partido. No es "
        "un backtest estadísticamente significativo — ver README para "
        "cómo escalarlo con datos históricos reales."
    )
    bets = [
        Bet(true_probability=0.60, decimal_odds=1.42, won=True, label="Sinner 3-0 vs Borges"),
        Bet(true_probability=0.84, decimal_odds=1.19, won=True, label="Auger-Aliassime vs Prizmic"),
    ]
    # Staking FLAT y min_edge_pp muy bajo a propósito: acá queremos ver
    # el resultado de ESTAS 2 apuestas puntuales, no filtrar/dimensionar
    # por valor como haría una estrategia real. Con Kelly el stake
    # hubiera sido 0 en ambas (edge cercano a 0 o negativo contra nuestro
    # propio modelo, aunque igual acertaron) — eso es Kelly funcionando
    # bien, no un error: por eso para ilustrar el resultado real usamos
    # staking plano en vez de Kelly.
    result = run_backtest(bets, staking=StakingMethod.FLAT, initial_bankroll=100.0,
                           flat_stake_fraction=0.05, min_edge_pp=-100.0)
    for b in bets:
        print(f"  - {b.label}: p={b.true_probability:.0%}, cuota={b.decimal_odds}, resultado={'GANADA' if b.won else 'perdida'}")
    print(f"  Bankroll final: {result.final_bankroll:.2f} (inicial 100.00)")
    print(f"  ROI: {result.roi:+.2%}  |  Win rate: {result.win_rate:.0%}  |  Max drawdown: {result.max_drawdown:.2%}")


if __name__ == "__main__":
    demo_point_to_match_model()
    demo_elo_from_real_rankings()
    demo_ev_and_kelly_on_real_odds()
    demo_montecarlo_validation()
    demo_real_backtest_illustrative()
    print("\n" + "=" * 70)
    print("Fin de la demo. Ver README.md para alcance, límites y cómo extender.")
    print("=" * 70)
