"""
Carga de datos históricos externos — DOCUMENTADO COMO NO DISPONIBLE en
este entorno sandbox, no como una promesa de que "ya funciona".

Se intentó (todos bloqueados por la política de red del entorno, no
por falta de credenciales — ver /root/.ccr/README.md):

  - raw.githubusercontent.com/JeffSackmann/tennis_atp  (resultados
    históricos ATP/WTA punto por punto y por partido, GRATIS y
    público — la fuente más usada en tennis analytics académico)
  - cdn.jsdelivr.net/gh/JeffSackmann/...                (mismo dataset,
    mirror en otro dominio — también bloqueado)
  - www.tennis-data.co.uk                                (resultados +
    cuotas históricas de cierre de Bet365/Pinnacle/etc., GRATIS,
    la fuente estándar para backtesting de estrategias de apuestas
    de tenis)

Los tres devuelven 403/404 por política de red del sandbox (confirmado
vía $HTTPS_PROXY/__agentproxy/status: "policy denial"), no por que el
dato no exista o sea pago.

QUÉ HACER PARA TENER DATOS REALES
----------------------------------
Este módulo expone la interfaz que usaría el resto del motor
(`load_sackmann_matches`, `load_tennis_data_odds`) para que, corriendo
este mismo código en un entorno con acceso normal a internet (tu
computadora, un servidor propio, GitHub Actions sin restricciones,
etc.), sólo haga falta implementar el `_fetch` de cada función —
la lógica de parseo a `MatchRecord` ya está lista y probada.

Alternativa sin escribir código: descargar manualmente los CSV/XLSX
desde esas dos URLs y pasar la carpeta local a `load_from_local_dir`,
que sí funciona en este entorno (no depende de red).
"""

import csv
import os
from dataclasses import dataclass


@dataclass
class MatchRecord:
    date: str
    surface: str
    winner: str
    loser: str
    winner_rank: int | None = None
    loser_rank: int | None = None
    winner_odds: float | None = None
    loser_odds: float | None = None
    score: str | None = None


class DataSourceUnavailable(Exception):
    """Se lanza cuando una fuente externa no es alcanzable desde este entorno."""


def load_sackmann_matches(year: int) -> list[MatchRecord]:
    """
    Intenta descargar atp_matches_{year}.csv del repo de Jeff Sackmann.
    En este sandbox SIEMPRE lanza DataSourceUnavailable — ver docstring
    del módulo. Fuera del sandbox, con `requests` disponible, esto
    funcionaría descargando el CSV real.
    """
    raise DataSourceUnavailable(
        f"No se pudo obtener atp_matches_{year}.csv: github.com está "
        "fuera de la política de red permitida en este entorno. "
        "Corré este mismo método en un entorno con acceso normal a "
        "internet, o descargá el CSV manualmente y usá load_from_local_dir()."
    )


def load_tennis_data_odds(year: int, tour: str = "atp") -> list[MatchRecord]:
    """
    Intenta descargar el Excel de tennis-data.co.uk con resultados +
    cuotas de cierre para `year`. Mismo bloqueo que arriba en este
    sandbox.
    """
    raise DataSourceUnavailable(
        f"No se pudo obtener las cuotas históricas {tour.upper()} {year} "
        "de tennis-data.co.uk: bloqueado por la política de red del "
        "entorno. Descargalo manualmente (es gratis) y usá "
        "load_from_local_dir()."
    )


def load_from_local_dir(path: str) -> list[MatchRecord]:
    """
    Carga archivos CSV ya descargados manualmente (por ejemplo, si el
    usuario bajó atp_matches_2024.csv de Sackmann a mano y lo subió a
    este proyecto). Esto SÍ funciona en el sandbox, porque no depende
    de la red — solo lee archivos locales.

    Espera columnas mínimas: tourney_date, surface, winner_name,
    loser_name, winner_rank, loser_rank, score (formato Sackmann) — se
    adapta automáticamente si faltan columnas de ranking.
    """
    if not os.path.isdir(path):
        raise FileNotFoundError(f"No existe el directorio: {path}")

    records: list[MatchRecord] = []
    for filename in sorted(os.listdir(path)):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(path, filename)
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    records.append(MatchRecord(
                        date=row.get("tourney_date", ""),
                        surface=row.get("surface", "").lower(),
                        winner=row.get("winner_name", ""),
                        loser=row.get("loser_name", ""),
                        winner_rank=_safe_int(row.get("winner_rank")),
                        loser_rank=_safe_int(row.get("loser_rank")),
                        score=row.get("score"),
                    ))
                except KeyError:
                    continue
    return records


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_elo_from_matches(matches: list[MatchRecord], k_factor: float = 32.0):
    """
    Dado un historial real de partidos (en orden cronológico), calibra
    un EloRating real jugador por jugador. Esta es la función que
    convertiría el proxy rank->Elo en un Elo de verdad, en cuanto haya
    datos disponibles (localmente o en un entorno con internet).
    """
    from elo import EloRating

    elo = EloRating(k_factor=k_factor)
    for m in matches:
        elo.record_match(winner=m.winner, loser=m.loser, surface=m.surface or None)
    return elo
