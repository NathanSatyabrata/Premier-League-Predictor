import csv
import os
import json
import requests
import pandas as pd

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# saves fixture data locally so I do not have to keep requesting for API data
def fetch_season_fixtures(league_id = 39, season = 2024) -> pd.DataFrame:
    cache_dir = "data/raw"
    cache_file = f"{cache_dir}/fixtures_{league_id}_{season}.json"

    if os.path.exists(cache_file):
        print(f"Loading {season} Premier League season fixtures from local cache...")
        with open(cache_file, "r") as f:
            data = json.load(f)
    else:
        print(f"[Loader] Fetching {season} Premier League season fixtures from API...")
        url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
        response = requests.get(url, headers=HEADERS)

        # potential overusage of API tokens
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        data = response.json()

        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(data, f)

    matches = []
    for fixture_Data in data.get("response", []):
        fixture = fixture_Data["fixture"]
        status = fixture["status"]["short"]

        # if it is a finished match, INCLUDE IN DATA
        if status == "FT":
            matches.append({
                "Fixture_ID": fixture["id"],
                "Date": fixture["date"],
                "HomeTeam": fixture_Data["teams"]["home"]["name"],
                "AwayTeam": fixture_Data["teams"]["away"]["name"],
                "HomeGoals": fixture_Data["goals"]["home"],
                "AwayGoals": fixture_Data["goals"]["away"]
            })

    df = pd.DataFrame(matches)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").reset_index(drop=True)

def fetch_fixture_stats(fixture_id: int) -> dict:
    '''
        Helps acquire shots in a game, and posession, helping calculate shot per posession ratio
    '''

    cache_dir = "data/raw/stats"
    cache_file = f"{cache_dir}/stats_{fixture_id}.json"

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            data = json.load(f)
    else:
        url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        data = response.json()

        # save file locally
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(data, f)

    team_stats = {}

    for team in data.get("response", []):
        # default stats incase missing data
        shots = 0
        poss = 50.0

        for stat in team.get("statistics", []):
            if stat["type"] == "Total Shots" and stat["value"] is not None:
                shots = int(stat["value"])
            elif stat["type"] == "Ball Possession" and stat["value"] is not None:
                poss = float(str(stat["value"]).replace("%", ""))

        team_stats[team["team"]["name"]] = {
            "total_shots": shots,
            "possession": poss,
            "shotsPosRatio": round(float(shots/poss), 3)
        }

    return team_stats
 
def load_team_data(filepath):
    teams = []

    with open(filepath) as file:
        reader = csv.DictReader(file)

        for row in reader:
            teams.append(row)

    return teams

if __name__ == "__main__":
    print("Testing loader.py pipeline...")

    # Test 1: Load Season Fixtures
    df_fixtures = fetch_season_fixtures(league_id=39, season=2024)
    print(f"\n[Success] Loaded {len(df_fixtures)} finished matches!")
    print(df_fixtures.head())

    # Test 2: Load Stats for First Fixture
    if not df_fixtures.empty:
        sample_id = df_fixtures.iloc[0]["Fixture_ID"]
        sample_stats = fetch_fixture_stats(sample_id)
        print(f"\n[Success] Parsed Stats for Fixture {sample_id}:")
        print(sample_stats)
