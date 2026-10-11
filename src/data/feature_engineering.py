import pandas as pd
from data.loader import fetch_fixture_stats

# Match the 2026/27 teams.csv snapshot through 2026-10-10 (56 matches).
# Follow the Math IA's two-decimal averages; refresh with the team strengths.
# See README.md for the formulas, source and rounding convention.
LEAGUE_HOME_GOALS = 1.57
LEAGUE_AWAY_GOALS = 1.30

def calculate_expected_goals(home_team: dict, away_team: dict) -> tuple[float, float]:
    """
    Calculates expected goals (xG) for home and away teams based on ratings.
    """
    home_xg = (
        float(home_team["attackstrengthhome"])
        * float(away_team["defencestrengthaway"])
        * LEAGUE_HOME_GOALS
    )

    away_xg = (
        float(away_team["attackstrengthaway"])
        * float(home_team["defencestrengthhome"])
        * LEAGUE_AWAY_GOALS
    )

    return home_xg, away_xg

def compute_match_features(
    df_fixtures: pd.DataFrame, 
    match_row: pd.Series, 
    window: int = 5
) -> dict:
    """
    Transforms past historical data into an engineered feature vector for a target match.
    Ensures zero data leakage by filtering strictly on matches prior to match_row['Date'].
    """
    target_date = match_row["Date"]
    home_team = match_row["HomeTeam"]
    away_team = match_row["AwayTeam"]

    # 1. Prevent Data Leakage: Keep only games completed BEFORE this match date
    past_matches = df_fixtures[df_fixtures["Date"] < target_date]

    # 2. League Home Advantage Baseline (Home Goals / Away Goals across all past games)
    total_home_g = past_matches["HomeGoals"].sum() if not past_matches.empty else 1
    total_away_g = past_matches["AwayGoals"].sum() if not past_matches.empty else 1
    league_home_adv = round(total_home_g / total_away_g, 3) if total_away_g > 0 else 1.20

    # 3. Last 5 Games for Home & Away Teams
    home_last_5 = past_matches[
        (past_matches["HomeTeam"] == home_team) | (past_matches["AwayTeam"] == home_team)
    ].tail(window)

    away_last_5 = past_matches[
        (past_matches["HomeTeam"] == away_team) | (past_matches["AwayTeam"] == away_team)
    ].tail(window)

    # 4. Rolling Goals & Overall Form Points (Last 5 Games)
    home_gf, home_ga, home_overall_form = _extract_form_stats(home_last_5, home_team)
    away_gf, away_ga, away_overall_form = _extract_form_stats(away_last_5, away_team)

    # 5. Total Venue Form (Points earned exclusively at Home / Away this season)
    home_venue_form = _extract_venue_points(past_matches, home_team, is_home=True)
    away_venue_form = _extract_venue_points(past_matches, away_team, is_home=False)

    # 6. Shots per Possession Ratio (Last 5 Games)
    home_shots_poss = _extract_shots_per_poss(home_last_5, home_team)
    away_shots_poss = _extract_shots_per_poss(away_last_5, away_team)

    # 7. Return Final Engineered Feature Dictionary
    return {
        # Target Info
        "Fixture_ID": match_row["Fixture_ID"],
        "Date": target_date,
        "HomeTeam": home_team,
        "AwayTeam": away_team,
        
        # Home Features
        "home_goals_scored": round(home_gf, 2),
        "home_goals_conceded": round(home_ga, 2),
        "home_venue_form": home_venue_form,
        "home_overall_form": home_overall_form,
        "home_shots_per_poss": home_shots_poss,
        
        # Away Features
        "away_goals_scored": round(away_gf, 2),
        "away_goals_conceded": round(away_ga, 2),
        "away_venue_form": away_venue_form,
        "away_overall_form": away_overall_form,
        "away_shots_per_poss": away_shots_poss,
        
        # Baselines & Differentials
        "league_home_advantage": league_home_adv,
        "form_diff": home_overall_form - away_overall_form,
        "venue_form_diff": home_venue_form - away_venue_form,
        
        # Targets (Actual Match Results for Training)
        "target_home_goals": match_row["HomeGoals"],
        "target_away_goals": match_row["AwayGoals"]
    }


def _extract_form_stats(df: pd.DataFrame, team: str) -> tuple[float, float, int]:
    """Helper: Computes avg goals scored, avg goals conceded, and form points in last N games."""
    if df.empty:
        return 1.0, 1.0, 0
    gf, ga, pts = 0, 0, 0
    for _, row in df.iterrows():
        is_home = (row["HomeTeam"] == team)
        scored = row["HomeGoals"] if is_home else row["AwayGoals"]
        conceded = row["AwayGoals"] if is_home else row["HomeGoals"]
        gf += scored
        ga += conceded
        pts += 3 if scored > conceded else (1 if scored == conceded else 0)
    return gf / len(df), ga / len(df), pts


def _extract_venue_points(df: pd.DataFrame, team: str, is_home: bool) -> int:
    """Helper: Total points earned exclusively at home or away this season."""
    venue_df = df[df["HomeTeam"] == team] if is_home else df[df["AwayTeam"] == team]
    pts = 0
    for _, row in venue_df.iterrows():
        scored = row["HomeGoals"] if is_home else row["AwayGoals"]
        conceded = row["AwayGoals"] if is_home else row["HomeGoals"]
        pts += 3 if scored > conceded else (1 if scored == conceded else 0)
    return pts


def _extract_shots_per_poss(df: pd.DataFrame, team: str) -> float:
    """Helper: Fetches fixture stats for last 5 games and computes average Shots per Possession."""
    if df.empty:
        return 0.200
    
    total_shots = 0
    total_poss = 0.0
    valid_count = 0
    
    for _, row in df.iterrows():
        fixture_id = row["Fixture_ID"]
        stats = fetch_fixture_stats(fixture_id)
        
        if team in stats:
            total_shots += stats[team]["total_shots"]
            total_poss += stats[team]["possession"]
            valid_count += 1
            
    if valid_count == 0 or total_poss == 0:
        return 0.200
        
    return round(total_shots / total_poss, 3)
