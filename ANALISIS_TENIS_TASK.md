# Análisis Tenis — Tarea Pendiente

## Contexto del Repositorio

- **Repo:** `israelojeda1-ops/proyecto-mundial`
- **Rama de trabajo:** `claude/tennis-betting-odds-95x47s`
- **Rama base:** `main`

## Objetivo

Crear un panel (dashboard) estático en HTML que ayude a **analizar cuotas de apuestas de tenis ATP** (Wimbledon y, a futuro, otros torneos), mostrando por partido:

| Campo | Descripción |
|---|---|
| Cuotas por casa de apuestas | Cuotas decimales de varias casas ficticias (datos simulados) |
| Probabilidad implícita sin margen | Se remueve el "vig"/overround de cada casa para obtener la probabilidad de mercado real |
| Nuestra proyección | Probabilidad propia estimada a partir de ranking, forma reciente, récord en superficie y H2H |
| Edge / Valor | Diferencia entre nuestra proyección y la probabilidad de mercado — resalta apuestas con posible valor (≥3 puntos porcentuales) |
| Contexto del partido | H2H, forma reciente, récord en césped, aces, % de primer saque, puntos de quiebre ganados |

## Decisiones de Diseño

- **Sin backend:** HTML + JavaScript puro, desplegable con GitHub Pages (convive con `world-cup-predictor` en la misma rama `gh-pages`, cada proyecto en su propia subcarpeta)
- **Datos:** Hardcodeados en `data/wimbledon_2026.json`, con partidos reales de Wimbledon 2026 Ronda 1 (basados en el cuadro visible en Sofascore) y cuotas/estadísticas simuladas
- **Cálculo de cuotas en el cliente:** `odds.js` calcula en tiempo real la probabilidad implícita, remueve el margen de cada casa y calcula el edge — no viene precalculado en el JSON
- **Actualización diaria:** GitHub Actions que regenera el marcador de fecha cada día (mismo patrón que `world-cup-daily.yml`)
- **Estilo:** Dark mode con paleta verde/púrpura inspirada en Wimbledon
- **Navegación:** Botones para navegar entre días del torneo
- **Responsable:** Disclaimer de datos simulados y juego responsable en el footer

## Estructura de Archivos

```
analisis-tenis/
├── index.html                       ← Dashboard principal (partidos del día, cuotas, edge)
├── combinada.html                   ← Analizador de combinadas (boletos reales + recomendación propia)
├── odds.js                          ← Lógica de cuotas del dashboard (implied prob, remove vig, edge)
├── combinada.js                     ← Lógica del analizador de combinadas + selector de boletos
├── styles.css                       ← Estilos compartidos (dark mode, cards, tablas, mercados de valor)
├── engine/                          ← Motor cuantitativo real en Python (ver engine/README.md)
│   ├── probability.py               Modelo punto→juego→set→partido (fórmulas cerradas + DP)
│   ├── elo.py                        Rating Elo por jugador/superficie
│   ├── ev.py                          EV, Kelly y Kelly fraccional
│   ├── backtest.py                    ROI/yield/drawdown, staking plano o Kelly
│   ├── montecarlo.py                 Validación Monte Carlo del modelo y del staking
│   ├── data_loader.py                 Interfaz a datos históricos reales (bloqueado por red del sandbox)
│   ├── demo.py                        Ejemplo end-to-end con datos reales
│   └── tests/                         83 tests, 97.4% cobertura
└── data/
    ├── wimbledon_2026.json           ← Partidos día a día (R1 → Final), cuotas por casa, proyección y contexto
    ├── combinada_2026-07-01.json     ← Combinada real de Betano (7 patas) + resultados confirmados
    ├── combinada_2026-07-02.json     ← Combinada real de Betano (10 patas)
    └── combinada_2026-07-02-valor5.json ← Combinada propia de 5 patas armada priorizando valor

.github/workflows/
├── tennis-daily.yml                 ← Deploy diario a gh-pages/analisis-tenis
└── tennis-engine-tests.yml          ← CI: corre pytest del motor cuantitativo (--cov-fail-under=90)
```

## Estado Actual

- [x] Dashboard principal con cuotas, probabilidad implícita, remoción de margen y edge
- [x] Datos cargados día a día: Ronda 1 (1 jul) → Ronda 2 (2 jul) → Ronda 3 (3 jul) → **Final (11-12 jul)**
- [x] Analizador de combinadas (`combinada.html`) con boletos reales investigados + mercados de valor (hándicap, total de juegos) por pata, y una combinada propia recomendada
- [x] Motor cuantitativo real en Python (`engine/`): modelo punto→partido, Elo, EV/Kelly, backtesting, validación Monte Carlo — ver `engine/README.md` para alcance y limitaciones (Elo sembrado por ranking como proxy; backtesting con datos históricos masivos bloqueado por política de red del sandbox, no por diseño)
- [x] GitHub Actions configurado (deploy a subcarpeta propia en `gh-pages` para no pisar `world-cup-predictor`) + CI de tests del motor
- [ ] GitHub Pages habilitado (requiere configuración manual en Settings del repo, si aún no está activo)

## Para Habilitar GitHub Pages

1. Ir a `Settings → Pages` en el repositorio
2. Source: `Deploy from a branch` → rama `gh-pages`, carpeta `/ (root)`
3. El dashboard queda disponible en `https://<usuario>.github.io/<repo>/analisis-tenis/`
4. El workflow `tennis-daily.yml` se encarga del deploy automático diario, o se puede ejecutar manualmente desde `Actions → Tennis Odds Daily Update → Run workflow`

## Próximos pasos opcionales

- Agregar otros torneos ATP/WTA (US Open, Masters 1000, etc.) con su propio archivo de datos y un selector de torneo en el header
- Conectar `engine/ev.py` al front-end para que el edge de cada pata se calcule con el motor real en vez de estimarse a mano
- Calibrar Elo real corriendo `engine/data_loader.py` fuera del sandbox (con acceso a Sackmann/tennis-data.co.uk) en vez del proxy por ranking
- Backtesting real de estrategias ("EV > 8% en ATP", etc.) una vez haya datos históricos con cuotas de cierre

## Prompt Sugerido para la Próxima Sesión

> Continúa el panel de Análisis Tenis en `israelojeda1-ops/proyecto-mundial`, rama `claude/tennis-betting-odds-95x47s`. El `ANALISIS_TENIS_TASK.md` en la raíz tiene el plan completo. Wimbledon 2026 ya terminó (final masculina 12 jul); el próximo paso natural es sumar un torneo nuevo (US Open o el que esté en curso) reutilizando el mismo dashboard, el analizador de combinadas y el motor cuantitativo en `engine/`.
