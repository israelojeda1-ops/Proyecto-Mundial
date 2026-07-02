"""
Motor cuantitativo de Análisis Tenis.

Módulo autocontenido en Python puro (sin dependencias externas para
correr, solo pytest/pytest-cov para testear) que implementa:

  - probability.py   Modelo punto -> juego -> set -> partido (fórmulas
                      cerradas + programación dinámica).
  - elo.py            Rating Elo por jugador y por superficie.
  - ev.py              Probabilidad implícita, remoción de margen,
                      Expected Value y Kelly Criterion (completo y
                      fraccional).
  - backtest.py        Motor de backtesting genérico (ROI, yield, win
                      rate, max drawdown) con staking plano o Kelly.
  - montecarlo.py     Simulaciones Monte Carlo que validan el modelo
                      analítico y el motor de staking contra
                      simulación punto por punto.
  - data_loader.py    Interfaz para datos históricos reales (Sackmann,
                      tennis-data.co.uk) — documentado como bloqueado
                      en este sandbox por política de red, listo para
                      correr en un entorno con internet normal.
  - demo.py           Script end-to-end con datos reales de esta sesión.

Ver README.md para alcance, limitaciones y cómo extenderlo.
"""
