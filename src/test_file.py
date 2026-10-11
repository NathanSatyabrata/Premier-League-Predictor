import csv
import math
import random
from tabulate import tabulate
from operator import itemgetter

#variables
prem_teams = []
match_log = []
leaguegoalshome = 1.63
leaguegoalsaway = 1.22
positionsLiverpool = {}

def main():
    with open("premteamdata2.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            #creates a dictionary of the teams' attacking/defence strength home and away by reading the data of each team in the CSV file
            prem_teams.append({"teamname": row["team"], "attackstrengthhome": row["attackstrengthhome"], "attackstrengthaway": row["attackstrengthaway"], "defencestrengthhome": row["defencestrengthhome"], "defencestrengthaway": row["defencestrengthaway"], "gamesPlayed": 0, "Wins": 0, "Draws": 0, "Loss": 0, "goalsFor": 0, "goalsAgainst": 0, "goalDifference": 0, "Points": 0})

        for i in range(50):
            for teaminitial in prem_teams:
                for team in prem_teams:
                    #counteractive measures
                    try:
                        teamindex = prem_teams.index(team)
                        #team1 is the hometeam and team2 is the away team
                        team1 = teaminitial
                        team2 = prem_teams[teamindex]
                        havetheyplayed = hasmatchbeenplayed(team1, team2)

                        #if they have not played, add it to the matchlog
                        if havetheyplayed == False:
                            match_log.append(f"{team1['teamname']} vs. {team2['teamname']}")
                        else:
                            continue
                        #simulate match function
                        simulate_match(team1, team2)
                    except:
                        continue

            datatodisplay = []
            for team in prem_teams:
                #0th index is the position of the team
                datatodisplay.append([1, team['teamname'],team['gamesPlayed'],team['Wins'],team['Draws'],team['Loss'],team['goalsFor'],team['goalsAgainst'],team['goalDifference'],team['Points']])

            #sorts the table using the team's position, goal difference and goal scored
            newdatatodisplay = sorted(datatodisplay, key=itemgetter(9,8,6), reverse=True)

            # function that captures the position of Liverpool in each simulation
            position = 1
            for team in newdatatodisplay:
                team[0] = position
                if team[1] == "Liverpool":
                    try:
                        positionsLiverpool[team[0]] += 1
                    except:
                        d1 = {team[0]: 1}
                        positionsLiverpool.update(d1)
                position+=1

            # clears stats for a new simulation
            match_log.clear()
            clearstats(prem_teams)

        # generates the data in text format THIS IS WHERE I ACQUIRE THE DATA
        f = open("LiverpoolPositionsData2.txt","w")
        for position, occurrence in positionsLiverpool.items():
            if position == 1:
                f.write(f"{position}st: {occurrence}\n")
            elif position == 2:
                f.write(f"{position}nd: {occurrence}\n")
            elif position == 3:
                f.write(f"{position}rd: {occurrence}\n")
            else:
                f.write(f"{position}th: {occurrence}\n")
        f.close()



def simulate_match(team1, team2):
    hometeamgoalprobability = []
    awayteamgoalprobability = []
    matchresults = []
    probabilities = []

    # gets the goal expectancy of both teams
    team1goalexpectancy = calculate_goalexpectancyofhometeam(team1, team2)
    team2goalexpectancy = calculate_goalexpectancyofawayteam(team1, team2)

    """Calculates the probability of i amount of goals being scored using Poisson Distribution. Does it from 0 goals to 5."""
    for i in range(6):
        probability = (team1goalexpectancy**float(i))*float((math.e**(-team1goalexpectancy)))/(math.factorial(i))
        hometeamgoalprobability.append(f"{i}: {probability}")

    # same thing here but for the away team
    for j in range(6):
        probability = (team2goalexpectancy**float(j))*float((math.e**(-team2goalexpectancy)))/(math.factorial(j))
        awayteamgoalprobability.append(f"{j}: {probability}")

    # calculates the probability of each possible match result
    for homegoals in hometeamgoalprobability:
        for awaygoals in awayteamgoalprobability:
            home = homegoals.split(": ")
            away = awaygoals.split(": ")
            hometeamgoals = int(home[0])
            hometeamgoalsprobability = float(home[1])

            awayteamgoals = int(away[0])
            awayteamgoalsprobability = float(away[1])

            #multiplies the probability of both teams scoring a certain number of goals (possible match)
            ultimateprobability = hometeamgoalsprobability * awayteamgoalsprobability
            matchresults.append(f"{team1['teamname']} {hometeamgoals} - {awayteamgoals} {team2['teamname']}")
            probabilities.append(ultimateprobability)

    #chooses score based on probability, the random.choices function I was talking about
    result = random.choices(matchresults, probabilities, k=1)
    hometeamgoals = []
    awayteamgoals = []

    # updates stats of both teams based on chosen result
    for score in result:
        for char in score:
            if char.isnumeric():
                if hometeamgoals:
                    awayteamgoals.append(int(char))
                else:
                    hometeamgoals.append(int(char))
    update_Stats(team1, team2, hometeamgoals[0], awayteamgoals[0])

    return


def hasmatchbeenplayed(team1, team2):
    #check if the teamnames are the same to remove any confusion
    if team1['teamname'] == team2['teamname']:
        return True

    #checks if there is an existing game that has been played
    for game in match_log:
        if game == f"{team1['teamname']} vs. {team2['teamname']}":
            return True
    return False

# functions to calculate goal expectancy using the goal expectancy formulas
def calculate_goalexpectancyofhometeam(hometeam, awayteam):
    return float(hometeam['attackstrengthhome']) * float(awayteam['defencestrengthaway']) * float(leaguegoalshome)

def calculate_goalexpectancyofawayteam(hometeam, awayteam):
    return float(awayteam['attackstrengthaway']) * float(hometeam['defencestrengthhome']) * float(leaguegoalsaway)

#updating stats based on result
def update_Stats(hometeam, awayteam, homegoals, awaygoals):

    #if hometeam won
    if homegoals - awaygoals > 0:
        hometeam["Wins"] += 1
        awayteam["Loss"] += 1
        hometeam["Points"] += 3
    #if draw
    elif homegoals == awaygoals:
        hometeam["Draws"] += 1
        awayteam["Draws"] += 1
        hometeam["Points"] += 1
        awayteam["Points"] += 1
    #if awayteam won
    elif homegoals - awaygoals < 0:
        hometeam["Loss"] += 1
        awayteam["Wins"] += 1
        awayteam["Points"] += 3

    hometeam["gamesPlayed"] += 1
    awayteam["gamesPlayed"] += 1

    hometeam["goalsFor"] += homegoals
    hometeam["goalsAgainst"] += awaygoals

    awayteam["goalsFor"] += awaygoals
    awayteam["goalsAgainst"] += homegoals

    hometeam["goalDifference"] = hometeam["goalsFor"] - hometeam["goalsAgainst"]
    awayteam["goalDifference"] = awayteam["goalsFor"] - awayteam["goalsAgainst"]

    return

# clears stats in preparation for a new simulation
def clearstats(teams):
    for team in teams:
        team['gamesPlayed'] = 0
        team['Wins'] = 0
        team['Draws'] = 0
        team['Loss'] = 0
        team['goalsFor'] = 0
        team['goalsAgainst'] = 0
        team['goalDifference'] = 0
        team['Points'] = 0
    return

main()