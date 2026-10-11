import csv
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.smooth_strengths import calculate_strengths, smoothed_strength


class SmoothingTests(unittest.TestCase):
    def test_zero_goals_remain_possible_after_smoothing(self):
        self.assertEqual(smoothed_strength(0, 2, 1.57, 3), Decimal("0.60"))
        self.assertEqual(smoothed_strength(0, 3, 1.57, 3), Decimal("0.50"))

    def test_no_matches_uses_league_average(self):
        self.assertEqual(smoothed_strength(0, 0, 1.57, 3), Decimal("1.00"))

    def test_zero_k_matches_paper_example(self):
        self.assertEqual(smoothed_strength(46, 19, 1.63, 0), Decimal("1.48"))
        self.assertEqual(smoothed_strength(0, 2, 1.57, 0), Decimal("0.00"))

    def test_prior_influence_decreases_with_more_matches(self):
        self.assertLess(smoothed_strength(0, 20, 1.57, 3), smoothed_strength(0, 2, 1.57, 3))
        self.assertGreater(smoothed_strength(0, 2, 1.57, 10), smoothed_strength(0, 2, 1.57, 3))

    def test_defence_uses_opponents_scoring_baseline(self):
        snapshot = {
            "league_home_average": 2, "league_away_average": 1,
            "teams": [{"team": "Example", "homePlayed": 2, "awayPlayed": 2,
                       "homeGF": 6, "homeGA": 2, "awayGF": 3, "awayGA": 4}],
        }
        self.assertEqual(calculate_strengths(snapshot, 2)[0], {
            "team": "Example", "attackstrengthhome": Decimal("1.25"),
            "attackstrengthaway": Decimal("1.25"),
            "defencestrengthhome": Decimal("1.00"),
            "defencestrengthaway": Decimal("1.00"),
        })

    def test_invalid_inputs_are_rejected(self):
        for args in [(0, 0, 1.57, 0), (1, 0, 1.57, 3), (0, 2, 0, 3),
                     (0, 2, 1.57, -1), (0, 2, 1.57, "NaN")]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                smoothed_strength(*args)

    def test_saved_csv_matches_snapshot_and_has_no_zero_strengths(self):
        with (ROOT / "data/team_strength_inputs.json").open() as source:
            snapshot = json.load(source)
        with (ROOT / "data/teams.csv").open() as source:
            saved = list(csv.DictReader(source))
        self.assertEqual(len(saved), 20)
        self.assertEqual(len({row["team"] for row in saved}), 20)
        for row, expected in zip(saved, calculate_strengths(snapshot)):
            self.assertEqual(row["team"], expected["team"])
            for key in expected:
                if key != "team":
                    self.assertEqual(Decimal(row[key]), expected[key])
                    self.assertGreater(expected[key], 0)
        teams = snapshot["teams"]
        for key in ("homePlayed", "awayPlayed"):
            self.assertEqual(sum(t[key] for t in teams), snapshot["completed_matches"])
        for key in ("homeGF", "awayGA"):
            self.assertEqual(sum(t[key] for t in teams), snapshot["total_home_goals"])
        for key in ("awayGF", "homeGA"):
            self.assertEqual(sum(t[key] for t in teams), snapshot["total_away_goals"])


if __name__ == "__main__":
    unittest.main()
