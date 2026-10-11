# Calculating team attack and defence strengths

The predictor estimates each team's attacking and defensive performance separately at home and away. These four ratings describe goals scored or conceded relative to the Premier League average. They provide the scoring rates used by the Poisson match model.

## Data and scope

The current snapshot covers the **2026/27 Premier League season**, using **56 completed matches through 10 October 2026**. Results were retrieved on 11 October from [Fixture Download](https://fixturedownload.com/results/epl-2026), using its [JSON feed](https://fixturedownload.com/feed/json/epl-2026). Fixtures without both scores and matches on or after 11 October are excluded.

For each team, the calculation records home and away matches played, goals scored, and goals conceded. Each team has played two or three matches at each venue. Averages therefore use the team's actual match count, rather than 19 matches or the total number of home and away games combined.

Only this season's Premier League results are included. Promoted clubs already have observations from the same league, so the paper's Championship adjustment is unnecessary. The paper's hypothetical Mac Allister transfer adjustment is also omitted because the observations reflect the current squads' actual performances.

The counts and source details are stored in [team_strength_inputs.json](data/team_strength_inputs.json). This is a fixed snapshot, not a live data feed.

## League scoring averages

Across the 56 matches, home teams scored 88 goals and away teams scored 73 goals. The league baselines are:

```text
H = league home goals per match = round(88 / 56, 2) = 1.57
A = league away goals per match = round(73 / 56, 2) = 1.30
```

A home team's goals are conceded by an away team, and vice versa. Consequently, the league average for goals conceded at home is A, while the average for goals conceded away is H. This determines which denominator belongs in each defensive rating.

## The original strength calculation

Without smoothing, each rating is the team's per-match goal rate divided by the corresponding league average.

| CSV field | Original calculation |
| --- | --- |
| `attackstrengthhome` | (Home goals scored / home matches) / H |
| `attackstrengthaway` | (Away goals scored / away matches) / A |
| `defencestrengthhome` | (Home goals conceded / home matches) / A |
| `defencestrengthaway` | (Away goals conceded / away matches) / H |

A rating of **1** represents the league average for that venue. An attack rating of **1.20** means a scoring rate 20% above average. A defence rating of **0.80** means a conceding rate 20% below average, so **lower defence values indicate better defending**. These ratings are multipliers, not probabilities, and may exceed 1. Defensive strength is not the mathematical reciprocal of attacking strength.

## Smoothing early season results

A team that has not yet scored would have an attack rating of zero under the original calculation. This would give it zero expected goals and therefore no chance of scoring in the Poisson model. Similarly, a zero defensive rating would imply that opponents cannot score. A few scoreless matches are insufficient evidence for either conclusion.

To reduce these extremes, the calculation adds the equivalent of **k league-average matches** to each estimate. For a given rating, let G be the observed goals, n the relevant home or away match count, and B the corresponding league baseline:

```text
Smoothed goal rate = (G + k * B) / (n + k)
Smoothed strength = smoothed goal rate / B
```

The current setting is **k = 3**, applied to every team and all four ratings. It is provisional and has not been selected through historical validation. The extra matches are a mathematical prior; they are not added to actual results, league totals, or standings.

Before rounding, smoothing combines the raw strength with the neutral rating of 1:

```text
Smoothed strength = [n / (n + k)] * raw strength + [k / (n + k)] * 1
```

With three observed matches and k = 3, each receives half the weight. With twelve observed matches, the team's results receive 80% and the league-average prior receives 20%. More evidence therefore reduces the influence of the prior. With no matches and a positive k, the calculation returns the league-average strength of 1.

| CSV field | Smoothed calculation before rounding |
| --- | --- |
| `attackstrengthhome` | ((Home goals scored + k * H) / (Home matches + k)) / H |
| `attackstrengthaway` | ((Away goals scored + k * A) / (Away matches + k)) / A |
| `defencestrengthhome` | ((Home goals conceded + k * A) / (Home matches + k)) / A |
| `defencestrengthaway` | ((Away goals conceded + k * H) / (Away matches + k)) / H |

## Rounding and a worked example

The implementation retains the paper's two-decimal calculation convention. League averages are rounded first, then the smoothed team goal rate is rounded before division by the league baseline. Finally, the strength is rounded to two decimal places. The calculator uses decimal arithmetic with half-up rounding.

Coventry scored **0 goals in 2 home matches**. With H = 1.57 and k = 3:

```text
Smoothed home goal rate = (0 + 3 * 1.57) / (2 + 3)
                       = 0.942
Rounded goal rate      = 0.94
Home attack strength   = round(0.94 / 1.57, 2)
                       = 0.60
```

Coventry remains below average, but its home scoring rate is no longer forced to zero. Hull's zero goals conceded in two home matches similarly produces a home defence rating of **0.60**, using A = 1.30. All 80 ratings in the current snapshot are positive.

Rounding is retained for consistency with the original method. It slightly changes the exact weighted-average relationship above and can discard information; smoothing does not guarantee a positive stored rating for every possible future dataset after rounding.

## From strengths to predicted scores

For a match between a home team and an away team, the model calculates:

```text
lambda_home = home team's home attack * away team's away defence * H
lambda_away = away team's away attack * home team's home defence * A
```

For example, Coventry playing at home against an average away defence of 1.00 has lambda_home = 0.60 * 1.00 * 1.57 = **0.942**. This is an expected goal count, not a predicted integer score or a shot-based expected-goals statistic.

The Poisson probability of a team scoring g goals is:

```text
P(G = g) = exp(-lambda) * lambda^g / g!
```

The match model assumes the teams' goal counts are independent conditional on these rates. It samples a score for each team, then repeats the process in Monte Carlo season simulations. The current code samples scores from 0 to 10 using their Poisson weights; `random.choices` normalizes these weights, so the simulation uses a truncated distribution rather than the full unbounded Poisson distribution.

## Reproducing the ratings

[smooth_strengths.py](src/data/smooth_strengths.py) recalculates all four ratings from the saved counts. From the repository root, run:

```bash
python src/data/smooth_strengths.py --k 3
```

This overwrites [teams.csv](data/teams.csv). To try another value without replacing the active ratings:

```bash
python src/data/smooth_strengths.py --k 5 --output /tmp/teams-k5.csv
```

Setting `--k 0` recovers the unsmoothed calculation when matches are available. Every run starts from the original counts, so running the script twice does not smooth the ratings twice. The script does not download new results. When refreshing the snapshot, update the league baselines in both the input file and [feature_engineering.py](src/data/feature_engineering.py) so they remain consistent.

## Limitations and validation

Smoothing reduces extreme estimates but does not make a small sample reliable. The ratings do not adjust for the quality of opponents already faced, injuries, lineups, red cards, or changes in tactics. The Poisson model also assumes fixed scoring rates within a match and conditional independence between the teams' goal counts.

The value of k should be chosen using chronological historical validation, then assessed on a separate held-out season. Each historical prediction must use only matches completed before that fixture; applying the current snapshot to earlier matches would leak future results. Testing early-season predictions is particularly relevant to this snapshot.

The existing season simulator replays all 380 fixtures from zero points. It does not yet preserve completed results and simulate only the remaining schedule, so its output is a hypothetical full season under these ratings rather than a forecast conditional on the current league table.
