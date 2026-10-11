# Premier-League-Predictor
Predicts premier league matches

Read the [methodology](METHODOLOGY.md) for the attack and defence formulas,
current-season data, smoothing, worked example, and model limitations.

## Team strength snapshot

Method: Nathan Satyabrata's Math IA, *Will the signing of Alexis Mac Allister
help Liverpool win the 2023-24 Premier League?*, sections 4 and 6 (printed
pages 3-4 and 8-9). The original committed CSV matches the paper's Table 5.
The current snapshot applies those formulas to this season's results, with
league-average smoothing added to all four strengths for every team.

`data/teams.csv` contains the 20 Premier League teams for **2026/27**,
calculated from the **56 completed matches through 10 October 2026**.
Retrieved 11 October 2026 from
[Fixture Download](https://fixturedownload.com/results/epl-2026)
([JSON feed](https://fixturedownload.com/feed/json/epl-2026)).
Matches on or after 11 October are excluded, as are fixtures without both scores.
This is a fixed snapshot, not an automatic live update.

Following the paper's Table 2 and worked examples, round league and smoothed team
per-game averages to two decimal places before dividing, then round the
resulting strengths to two decimal places (ordinary half-up rounding).
Let H = round(total home goals / completed matches, 2) = round(88 / 56, 2) = 1.57,
and A = round(total away goals / completed matches, 2) = round(73 / 56, 2) = 1.30.
Each team has played two or three matches at each venue, so use its actual
home/away match counts rather than assuming equal games played.

| CSV field | Calculation |
| --- | --- |
| attackstrengthhome | ((Home goals scored + k * H) / (Home matches + k)) / H |
| attackstrengthaway | ((Away goals scored + k * A) / (Away matches + k)) / A |
| defencestrengthhome | ((Home goals conceded + k * A) / (Home matches + k)) / A |
| defencestrengthaway | ((Away goals conceded + k * H) / (Away matches + k)) / H |

The current CSV uses **k = 3** for all teams and all four strengths. This is a
provisional setting, not a value selected through historical validation.
It adds three league-average matches separately to each home/away estimate.
For example, home attack = round(round((home goals + k * H) / (home matches + k), 2) / H, 2).
Attack above 1 means scoring above
the league venue average. Defence below 1 means conceding fewer goals than
average (a stronger defence). Home defence is compared against **away** scoring,
and away defence against **home** scoring.

The expected-goals calculation uses:

```text
home goals = home attack * visiting team's away defence * H
away goals = away attack * home team's home defence * A
```

`src/data/feature_engineering.py` uses H and A from the same snapshot. Update
those constants whenever refreshing the CSV. For example, Coventry scored no
goals in 2 home games: (0 + 3 * 1.57) / (2 + 3) = 0.942 smoothed goals per game.
Using the rounding convention, round(0.94 / 1.57, 2) = 0.60 home attack.

Only current-season Premier League matches are used, including for promoted
clubs. The paper's section 5 Championship-to-Premier-League adjustments are
not applied because these inputs were already recorded in the Premier League.
The section 9 Mac Allister transfer scenario is not applied: this snapshot
measures actual current squads, with no hypothetical goal transfers.

Smoothing moves each rating toward 1, with more observed matches reducing the
influence of the prior. Coventry's home attack is now 0.60, Nottingham's is 0.50,
and Hull's home defence is 0.60. All 80 strengths in this snapshot are positive.
The estimates remain uncertain with only two or three matches per venue.
Do not use this snapshot to backtest earlier matches; recompute ratings using
only pre-match results, and tune k on historical validation seasons.

The observed match counts and goal totals are saved in
`data/team_strength_inputs.json`, together with the source and cutoff. These
are the original inputs, so rerunning smoothing does not compound it.
To regenerate the CSV using the same snapshot and a chosen k:

```bash
python src/data/smooth_strengths.py --k 3
```

`--k 0` reproduces the unsmoothed IA calculation; `--output` selects another
CSV path for experiments. The script does not fetch new results. Changing k
alone does not change the league averages. If the source snapshot is refreshed,
update the league averages in both the snapshot and `feature_engineering.py`.

Existing team labels are retained where possible. Feed aliases map Newcastle
to Newcastle Utd, Nott'm Forest to Nottingham, and Spurs to Tottenham. Coventry,
Hull, Ipswich and Leeds use Coventry City, Hull City, Ipswich Town and Leeds United.
