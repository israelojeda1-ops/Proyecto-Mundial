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
├── index.html                  ← HTML principal del dashboard
├── odds.js                     ← Lógica de cálculo de cuotas (implied prob, remove vig, edge) y render
├── styles.css                  ← Estilos (dark mode, cards por partido, tabla de cuotas)
└── data/
    └── wimbledon_2026.json     ← Partidos, cuotas por casa, proyección propia y contexto

.github/workflows/
└── tennis-daily.yml            ← Action que actualiza datos diariamente + deploy a gh-pages/analisis-tenis
```

## Estado Actual

- [x] Archivos HTML/JS/CSS creados y probados en navegador (Playwright)
- [x] Datos de Wimbledon 2026 Ronda 1 cargados (9 partidos del 1 de julio, basados en la captura de Sofascore)
- [x] Cálculo de probabilidad implícita, remoción de margen y edge funcionando correctamente
- [x] GitHub Actions configurado (deploy a subcarpeta propia en `gh-pages` para no pisar `world-cup-predictor`)
- [ ] GitHub Pages habilitado (requiere configuración manual en Settings del repo, si aún no está activo)

## Para Habilitar GitHub Pages

1. Ir a `Settings → Pages` en el repositorio
2. Source: `Deploy from a branch` → rama `gh-pages`, carpeta `/ (root)`
3. El dashboard quedará disponible en `https://<usuario>.github.io/<repo>/analisis-tenis/`
4. El workflow `tennis-daily.yml` se encarga del deploy automático diario, o se puede ejecutar manualmente desde `Actions → Tennis Odds Daily Update → Run workflow`

## Próximos pasos opcionales

- Agregar más rondas de Wimbledon 2026 (Ronda 2 en adelante) a medida que avanza el cuadro
- Agregar otros torneos ATP (US Open, Masters 1000, etc.) con su propio archivo de datos
- Integrar una API real de cuotas (The Odds API, Betfair Exchange, etc.) para reemplazar los datos simulados
- Añadir un selector de torneo en el header para alternar entre distintos eventos
- Calcular un "Kelly stake" sugerido junto al edge para quienes gestionan bankroll

## Prompt Sugerido para la Próxima Sesión

> Continúa el panel de Análisis Tenis en `israelojeda1-ops/proyecto-mundial`, rama `claude/tennis-betting-odds-95x47s`. El `ANALISIS_TENIS_TASK.md` en la raíz tiene el plan completo. Agrega los partidos de la Ronda 2 de Wimbledon al JSON y añade un selector de torneo para poder alternar entre Wimbledon y otro torneo ATP.
