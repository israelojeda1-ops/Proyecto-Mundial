# Motor Cuantitativo — Análisis Tenis

Motor de probabilidad, EV y Kelly Criterion para tenis, en Python puro
(sin dependencias externas para correr). Es la "Fase 1" de la
plataforma completa que se pidió (multi-deporte, backend, ML,
alertas) — acotada a un motor cuantitativo real para tenis,
porque el resto requiere infraestructura y APIs pagas que este
entorno sandbox no puede aprovisionar (ver [Limitaciones](#limitaciones-reales-de-este-entorno) abajo).

## Qué es real acá y qué no

| Componente | Estado |
|---|---|
| Modelo punto→juego→set→partido | ✅ Real. Fórmulas cerradas + DP, matemáticamente correctas, testeadas |
| EV / Kelly / Kelly fraccional | ✅ Real. Fórmulas estándar de la industria |
| Motor de backtesting (ROI/yield/drawdown) | ✅ Real. Funciona con cualquier lista de apuestas históricas |
| Validación Monte Carlo | ✅ Real. Simulación punto por punto independiente del modelo analítico |
| Elo | ⚠️ El **sistema** es real y está testeado, pero los **ratings actuales** están sembrados desde el ranking ATP/WTA (proxy documentado), no calculados con historial real de partidos — ver abajo por qué |
| Backtest con datos históricos masivos | ❌ No disponible en este entorno — bloqueo de red, no de código (ver abajo) |
| Multi-deporte, FastAPI, Postgres, Redis, Celery, alertas, ML | ❌ Fuera de alcance de esta fase — requiere servidor propio y presupuesto para APIs pagas |

## Por qué el Elo no está calibrado con datos reales

Se intentó descargar el dataset histórico de Jeff Sackmann (el
estándar gratuito y público en tennis analytics) y las cuotas
históricas de tennis-data.co.uk. Las tres URLs probadas devuelven
403/404 **por política de red del entorno sandbox** (confirmado con
`$HTTPS_PROXY/__agentproxy/status`, que loguea `"policy denial"` para
esos dominios) — no es una limitación del código ni falta de
credenciales pagas, esos datasets son gratis.

`data_loader.py` ya tiene la interfaz lista (`load_sackmann_matches`,
`load_tennis_data_odds`, `load_from_local_dir`,
`build_elo_from_matches`): corriendo este mismo código en cualquier
entorno con acceso normal a internet (tu compu, un servidor propio),
o subiendo los CSV descargados a mano, el Elo pasa de "proxy por
ranking" a "calculado con miles de partidos reales" sin cambiar nada
más del motor.

## Estructura

```
engine/
├── probability.py    Punto -> juego -> set -> partido (fórmulas cerradas + DP)
├── elo.py             Rating Elo por jugador y por superficie
├── ev.py               Implied prob, remove vig, EV, Kelly, Kelly fraccional
├── backtest.py         ROI, yield, win rate, max drawdown, staking plano/Kelly
├── montecarlo.py      Simulación punto por punto para validar el resto
├── data_loader.py      Interfaz a datos históricos reales (ver arriba)
├── demo.py             Ejemplo end-to-end con datos reales de esta sesión
├── requirements.txt
└── tests/              83 tests, 97.4% cobertura del núcleo (sin demo.py)
```

## Cómo correrlo

```bash
cd analisis-tenis/engine
pip install -r requirements.txt

# Tests + cobertura
python3 -m pytest tests/ --cov=. --cov-report=term-missing

# Demo end-to-end con datos reales
python3 demo.py
```

## Ejemplo real: modelo punto → partido

Con las estadísticas de saque reales que investigamos esta sesión
(Fritz: 14 aces, 0 dobles faltas en su R1 de Wimbledon 2026 ≈ 68% de
puntos de saque ganados; Kypson, top-113, ≈ 60%):

```
Prob. de retener el saque Fritz:  87.5%
Prob. de retener el saque Kypson: 73.6%
Prob. de ganar un set Fritz:      74.7%
Prob. de ganar el partido (5 sets): 89.3%
```

Betano pagaba a Fritz a cuota 1.05 (≈95.2% implícito). El modelo,
construido *solo* desde estadísticas de saque —sin mirar la cuota—,
da 89.3%. La diferencia (~6pp) es exactamente el tipo de señal que
en una mesa de trading deportivo dispararía una revisión manual: o el
mercado sabe algo que el modelo no capturó (forma reciente, lesión),
o el mercado está sobrevalorando al favorito.

## Ejemplo real: EV/Kelly sobre cuotas reales de Betano (2 jul 2026)

```
G. Diallo (vs Sonego)         p=62%  cuota=1.81  edge=+6.8pp  EV=+12.2%  Kelly 1/4=3.77%  [💎 VALOR]
K. Khachanov (vs Hanfmann)    p=64%  cuota=1.63  edge=+2.7pp  EV=+4.3%   Kelly 1/4=1.71%
F. Tiafoe (vs Choinski)       p=78%  cuota=1.15  edge=-9.0pp  EV=-10.3%  Kelly 1/4=0.00%
```

Nota que Tiafoe (favorito claro) tiene EV **negativo**: el modelo cree
que el mercado lo sobrevalora dado el problema de saque que mostró en
R1. Kelly correctamente asigna 0% de stake — el motor no recomienda
apostar solo porque alguien "vaya a ganar".

## Validación Monte Carlo

```
n=10,000   simulado=0.8630  analítico=0.8677  diff=0.0047  ✅ coincide
n=50,000   simulado=0.8666  analítico=0.8677  diff=0.0011  ✅ coincide
```

La simulación punto por punto (independiente del modelo DP) converge
al mismo resultado que la fórmula cerrada — evidencia de que la
matemática está bien implementada, no solo que "corre sin errores".

Sobre el staking: 2000 carreras simuladas de 400 apuestas cada una,
con un edge conocido (+13.1% EV teórico), dan un ROI promedio de
+11.49% y 99.4% de carreras rentables — el motor de backtesting no
tiene sesgos ocultos en la contabilidad.

## Backtest — honestidad sobre el tamaño de muestra

`demo.py` incluye un backtest con los únicos 2 resultados de Wimbledon
2026 confirmados durante esta sesión de investigación (Sinner 3-0 vs
Borges, Auger-Aliassime vs Prizmic), con cuota Betano real y
probabilidad propia registrada *antes* del partido. Sirve para probar
que el pipeline funciona de punta a punta — **no** es una muestra
estadísticamente significativa. Con n=2 cualquier resultado (bueno o
malo) es ruido, no señal.

Para un backtest real (el que pediría cualquier mesa de trading antes
de arriesgar dinero) hacen falta cientos o miles de partidos con cuota
de cierre real — eso requiere destrabar el acceso a
tennis-data.co.uk/Sackmann (fuera de este sandbox) o que integres una
API de cuotas históricas (OddsAPI, Betfair Historical Data, etc.).

## Próximos pasos si querés escalar esto

1. **Calibrar Elo real**: correr `data_loader.py` fuera del sandbox (o
   subir los CSV de Sackmann a mano) para tener ratings reales de
   los ~500 jugadores del top ATP/WTA en vez del proxy por ranking.
2. **Backtest real**: mismo bloqueo — con las cuotas históricas de
   tennis-data.co.uk se puede correr `backtest.run_backtest()` sobre
   miles de partidos reales y sacar ROI/yield/drawdown de verdad.
3. **Conectar al sitio**: usar `ev.analyze_bet()` para recalcular
   automáticamente el edge de cada pata en `combinada_*.json` en vez
   de escribir el número a mano.
4. **Otros deportes / infraestructura completa**: eso sí requiere el
   rediseño de arquitectura (FastAPI + Postgres + Redis + Celery +
   Docker) y APIs pagas (Sportradar, OddsAPI, HLTV...) que están fuera
   del alcance de lo que se puede construir y correr en este entorno.
