import pandas as pd
from simulation.match_simulator import simulate_match


def simulate_single_season(teams: list[dict]) -> dict[str, dict]:
    stats = {
        team["team"]: {
            "MP": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0
        }
        for team in teams
    }

    # simulate double round-robin
    for home_team in teams:
        for away_team in teams:
            if home_team["team"] == away_team["team"]:
                continue

            home_goals, away_goals = simulate_match(home_team, away_team)
            _update_match_stats(stats, home_team["team"], away_team["team"], home_goals, away_goals)

    # computes final GD after simulation is done
    for team_name in stats:
        stats[team_name]["GD"] = stats[team_name]["GF"] - stats[team_name]["GA"]

    return stats


def run_monte_carlo(teams: list[dict], num_simulations: int = 10000) -> pd.DataFrame:
    """
    Runs Monte Carlo season simulations and aggregates finish probabilities.
    """
    num_teams = len(teams)
    
    # Track statistics across all simulations
    team_metrics = {
        team["team"]: {
            "Total_Pts": 0,
            "Total_Pos": 0,
            "Title_Wins": 0,
            "Top_4": 0,
            "Relegated": 0,
        }
        for team in teams
    }

    for _ in range(num_simulations):
        season_stats = simulate_single_season(teams)

        sorted_teams = sorted(
            season_stats.items(),
            key=lambda x: (x[1]["Pts"], x[1]["GD"], x[1]["GF"]),
            reverse=True
        )

        # add stats
        for rank, (team_name, stats) in enumerate(sorted_teams, start=1):
            metrics = team_metrics[team_name]
            metrics["Total_Pts"] += stats["Pts"]
            metrics["Total_Pos"] += rank

            if rank == 1:
                metrics["Title_Wins"] += 1
            if rank <= 4:
                metrics["Top_4"] += 1
            if rank >= (num_teams - 2):  # relegation
                metrics["Relegated"] += 1

    # format final summary data table
    summary_data = []
    for team_name, metrics in team_metrics.items():
        summary_data.append({
            "Team": team_name,
            "xPts": round(metrics["Total_Pts"] / num_simulations, 1),
            "Avg Pos": round(metrics["Total_Pos"] / num_simulations, 1),
            "Title %": round((metrics["Title_Wins"] / num_simulations) * 100, 2),
            "Top 4 %": round((metrics["Top_4"] / num_simulations) * 100, 2),
            "Relegation %": round((metrics["Relegated"] / num_simulations) * 100, 2),
        })

    df = pd.DataFrame(summary_data)
    
    # sort by expected points (xPts) descending
    df = df.sort_values(by="xPts", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))
    
    return df


def _update_match_stats(stats: dict, home_name: str, away_name: str, home_goals: int, away_goals: int) -> None:
    """Helper function to update in-memory match stats."""
    home = stats[home_name]
    away = stats[away_name]

    home["MP"] += 1
    away["MP"] += 1
    home["GF"] += home_goals
    home["GA"] += away_goals
    away["GF"] += away_goals
    away["GA"] += home_goals

    if home_goals > away_goals:
        home["W"] += 1
        home["Pts"] += 3
        away["L"] += 1
    elif home_goals == away_goals:
        home["D"] += 1
        home["Pts"] += 1
        away["D"] += 1
        away["Pts"] += 1
    else:
        away["W"] += 1
        away["Pts"] += 3
        home["L"] += 1