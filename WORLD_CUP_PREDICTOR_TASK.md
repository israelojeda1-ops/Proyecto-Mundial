# World Cup Predictor — Tarea Pendiente

## Contexto del Repositorio

- **Repo:** `israelojeda1-ops/proyecto-mundial`
- **Rama de trabajo:** `claude/world-cup-predictor-v2nc5h-8oojz5`
- **Rama base:** `main`

## Objetivo

Crear un predictor de resultados de partidos del Mundial 2026 que genere un **HTML estático** con los partidos del día, con las siguientes estadísticas por partido:

| Campo | Descripción |
|---|---|
| Resultado predicho | Marcador probable del partido |
| Posibles anotadores | Jugadores con mayor probabilidad de gol |
| Tiros al arco | Predicción de SOT (Shots on Target) por equipo |
| Tiros totales | Total de disparos esperados por equipo |
| Amarillas probables | Jugadores con historial de tarjetas |
| Corners | Tiros de esquina esperados por equipo |
| Pases (histórico) | Estadística de pases de partidos anteriores del torneo |
| Faltas | Faltas esperadas por equipo |
| Tacles | Tacles esperados por equipo |

## Decisiones de Diseño

- **Sin backend:** HTML + JavaScript puro, desplegable con GitHub Pages
- **Datos:** Hardcodeados en `data/fixtures_2026.json` con fixtures reales del Mundial 2026
- **Actualización diaria:** GitHub Actions que regenera la página cada día
- **Estilo:** Dark mode moderno, inspirado en dashboards dark de datos deportivos
- **Navegación:** Botones para navegar entre días del torneo

## Estructura de Archivos

```
world-cup-predictor/
├── index.html              ← HTML principal del predictor
├── predictor.js            ← Lógica de predicción y render
├── styles.css              ← Estilos (dark mode, cards por partido)
└── data/
    └── fixtures_2026.json  ← Datos del torneo (fechas, equipos, grupos, predicciones)

.github/workflows/
└── world-cup-daily.yml     ← Action que actualiza datos diariamente + deploy Pages
```

## Estado Actual

- [x] Archivos HTML/JS/CSS creados
- [x] Datos del Mundial 2026 cargados — Ronda de 16 (3 jornadas: 28, 29, 30 jun y 1 jul)
- [x] GitHub Actions configurado
- [x] Forma reciente, xG, H2H, bajas, MOTM por partido
- [ ] GitHub Pages habilitado (requiere configuración manual en Settings del repo)

## Partidos del Mundial 2026 (referencia)

El Mundial 2026 es co-organizado por **USA, Canadá y México**.
- Inicio fase de grupos: **11 de junio de 2026**
- Final: **19 de julio de 2026**
- 48 equipos, 104 partidos

Hoy es **29 de junio de 2026** — la fase de grupos está en curso (Jornada 3).

## Para Habilitar GitHub Pages

1. Ir a `Settings → Pages` en el repositorio
2. Source: `GitHub Actions`
3. El workflow `world-cup-daily.yml` se encarga del deploy automático
4. O ejecutar el workflow manualmente desde `Actions → World Cup Daily Update → Run workflow`

## Próximos pasos opcionales

- Agregar más partidos al JSON (Jornadas 1 y 2 completas)
- Integrar API pública (football-data.org o api-football.com) para datos en tiempo real
- Añadir tabla de grupos actualizada
- Añadir bracket de eliminatorias

## Prompt Sugerido para la Próxima Sesión

> Continúa el predictor del Mundial 2026 en `israelojeda1-ops/proyecto-mundial`, rama `claude/world-cup-predictor-v2nc5h-8oojz5`. El `WORLD_CUP_PREDICTOR_TASK.md` en la raíz tiene el plan completo. Agrega los partidos de la Jornada 1 y 2 completas al JSON, y añade una vista de tabla de grupos en `world-cup-predictor/index.html`.
