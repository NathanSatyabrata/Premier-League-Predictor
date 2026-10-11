from data.loader import load_team_data
from simulation.season_simulator import run_monte_carlo

def main():
    file = "data/teams.csv"
    teams = load_team_data(file)

    # generates detailed result about xPts, avg position, champions percentage, top 4 percentage and relegation percentage
    print("Running 10,000 Premier League Season Simulations...\n")
    results = run_monte_carlo(teams, num_simulations=10000)

    print(results.to_string(index=False))

if __name__ == "__main__":
    main()