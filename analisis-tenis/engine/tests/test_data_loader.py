import csv
import os
import tempfile

import pytest

from data_loader import (
    load_sackmann_matches,
    load_tennis_data_odds,
    load_from_local_dir,
    build_elo_from_matches,
    DataSourceUnavailable,
    MatchRecord,
)


class TestExternalSourcesUnavailable:
    def test_sackmann_raises_documented_error(self):
        with pytest.raises(DataSourceUnavailable):
            load_sackmann_matches(2024)

    def test_tennis_data_raises_documented_error(self):
        with pytest.raises(DataSourceUnavailable):
            load_tennis_data_odds(2024, tour="atp")


class TestLoadFromLocalDir:
    def test_missing_directory_raises(self):
        with pytest.raises(FileNotFoundError):
            load_from_local_dir("/no/existe/este/path")

    def test_parses_minimal_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "atp_matches_2024.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "tourney_date", "surface", "winner_name", "loser_name",
                    "winner_rank", "loser_rank", "score",
                ])
                writer.writeheader()
                writer.writerow({
                    "tourney_date": "20240701", "surface": "Grass",
                    "winner_name": "Jugador A", "loser_name": "Jugador B",
                    "winner_rank": "5", "loser_rank": "40", "score": "6-4 6-3",
                })

            records = load_from_local_dir(tmp)
            assert len(records) == 1
            assert records[0].winner == "Jugador A"
            assert records[0].winner_rank == 5
            assert records[0].surface == "grass"

    def test_ignores_non_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "readme.txt"), "w") as f:
                f.write("no es un csv")
            records = load_from_local_dir(tmp)
            assert records == []


class TestBuildEloFromMatches:
    def test_builds_elo_ratings_from_real_history(self):
        matches = [
            MatchRecord(date="1", surface="grass", winner="A", loser="B"),
            MatchRecord(date="2", surface="grass", winner="A", loser="C"),
            MatchRecord(date="3", surface="grass", winner="B", loser="C"),
        ]
        elo = build_elo_from_matches(matches)
        assert elo.get_rating("A") > elo.get_rating("C")
        assert elo.matches_played["A"] == 2

    def test_surface_specific_ratings_populated(self):
        matches = [MatchRecord(date="1", surface="clay", winner="A", loser="B")]
        elo = build_elo_from_matches(matches)
        assert elo.get_rating("A", surface="clay") > 1500.0
