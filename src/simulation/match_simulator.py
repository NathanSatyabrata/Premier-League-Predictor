from models.poisson import goals_distribution
from data.feature_engineering import calculate_expected_goals
import random

AVGLEAGUEGOALSHOME = 1.63
AVGLEAGUEGOALSAWAY = 1.22

def simulate_match(homeTeam, awayTeam) -> tuple:
    home_xG, away_xG = calculate_expected_goals(homeTeam, awayTeam)

    hometeamProbs = goals_distribution(home_xG)
    awayteamProbs = goals_distribution(away_xG)

    return (teamScore(hometeamProbs), teamScore(awayteamProbs))

def teamScore(probabilities):
    goals = list(probabilities.keys())
    probs = list(probabilities.values())

    return random.choices(goals, probs, k=1)[0]

