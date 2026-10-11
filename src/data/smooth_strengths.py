"""Regenerate team strengths from the saved current-season goal counts."""

import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


DEFAULT_K = Decimal("3")  # Provisional; tune with chronological validation.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIELDS = [
    "team", "attackstrengthhome", "attackstrengthaway",
    "defencestrengthhome", "defencestrengthaway",
]


def smoothed_strength(goals, games, league_average, k=DEFAULT_K):
    """Add k league-average matches, retaining the IA's two-stage rounding."""
    goals, games, baseline, k = map(
        lambda value: Decimal(str(value)), (goals, games, league_average, k)
    )
    if not all(value.is_finite() for value in (goals, games, baseline, k)):
        raise ValueError("Inputs must be finite")
    if goals < 0 or games < 0 or baseline <= 0 or k < 0:
        raise ValueError("Counts and k must be nonnegative; league average must be positive")
    if games + k == 0:
        raise ValueError("No games available: use a positive k")
    if games == 0 and goals != 0:
        raise ValueError("Goals require at least one played game")
    rate = (goals + k * baseline) / (games + k)
    rate = rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (rate / baseline).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_strengths(snapshot, k=DEFAULT_K):
    """Use home scoring for home attack/away defence, and vice versa."""
    home_average = snapshot["league_home_average"]
    away_average = snapshot["league_away_average"]
    rows = []
    for team in snapshot["teams"]:
        rows.append(dict(zip(FIELDS, [
            team["team"],
            smoothed_strength(team["homeGF"], team["homePlayed"], home_average, k),
            smoothed_strength(team["awayGF"], team["awayPlayed"], away_average, k),
            smoothed_strength(team["homeGA"], team["homePlayed"], away_average, k),
            smoothed_strength(team["awayGA"], team["awayPlayed"], home_average, k),
        ])))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=Decimal, default=DEFAULT_K)
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "data/team_strength_inputs.json")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data/teams.csv")
    args = parser.parse_args()
    with args.input.open() as source:
        rows = calculate_strengths(json.load(source), args.k)
    with args.output.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} teams with k={args.k} to {args.output}")


if __name__ == "__main__":
    main()
