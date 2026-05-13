# FIFA World Cup 2026 Tournament Simulator

A Python-based Monte Carlo simulator that models the 2026 FIFA World Cup using a composite team-rating system, Poisson-distributed match outcomes, and the official FIFA Annex C bracket structure. Built to estimate each team's probability of winning the tournament over thousands of simulated runs.

## Overview

The 2026 World Cup is the first 48-team tournament in FIFA history, featuring 12 groups of 4 teams, a Round of 32, and a bracket structure governed by a 495-row lookup table for assigning best third-place teams. This project simulates the full tournament end-to-end and aggregates results across many simulations to produce championship probabilities.

In 10,000 simulations, France and Spain emerged as the clearest favorites (~13.9% and ~11.7% respectively), with Argentina, England, and Portugal rounding out the top 5. Realistic upset frequencies were preserved — Saudi Arabia, for instance, won the tournament 0.01% of the time, mirroring real-world rare-event possibility.

## How it Works

### 1. Team Ratings (0-100 composite score)

Each of the 48 qualified teams is rated using 7 weighted predictors:

| Predictor | Weight | Description |
|---|---|---|
| FIFA Rank | 21% | Inverted — rank 1 scores highest |
| Star Rating | 25% | 1-5 squad quality rating |
| Tournament Score | 14% | Continental tournament performance |
| Qualifying GD | 10% | Goal difference in WC qualifying |
| Podium Bonus | 15% | WC22 finish bonus |
| Qual Goals Against/Match | 10% | Defensive solidity (inverted) |
| GK Form | 5% | Goalkeeper rating |

Weights and inputs can be tuned in `score_teams.py`. Ratings are min-max normalized to a 0-100 scale where the strongest team in the field = 100 and the weakest = 0.

### 2. Match Simulation (Poisson Model)

Each match produces a scoreline using the following process:

1. **Expected goals** are computed for both teams using the formula:
   ```
   λ = base_goals × sqrt(team_rating / opponent_rating)
   ```
   The square root softens extreme rating gaps to prevent unrealistic blowouts.

2. **Game-day variance** is added by multiplying λ by a random factor:
   - Group stage: 0.7-1.3 (wider variance, more upsets)
   - Knockout rounds: 0.9-1.2 (tighter, favorites lean slightly more)

3. **Goal counts** are drawn from a Poisson distribution centered on λ (the standard distribution for soccer scoring).

### 3. Group Stage Logic

The simulator implements real motivation dynamics for matchday 3:

- **Safe teams** (already qualified) playing weaker opponents apply a 0.7× multiplier — they're cruising
- **Eliminated teams** play at 0.8× — going through the motions
- **Must-win teams** apply a 1.3× multiplier (favorites) or 1.2× (underdogs leaving more space at the back)

This produces realistic results like Spain easing off in their final group game after qualifying, rather than running up the score.

### 4. Form Boost

Teams that win matches gain a small rating boost based on the quality of their opponent:

```
boost = (opponent_rating / 100) × 5%
```

Capped at +3% accumulated. Resets to 0 on any loss. Beating Spain gives a meaningful bump; beating Bosnia barely moves the needle.

### 5. Round of 32 Bracket

The simulator uses the **official FIFA Annex C** lookup table (495 rows) to assign best third-place teams to specific R32 matches based on which 8 of 12 groups produce qualifying third-place teams. This mirrors exactly what FIFA does after the group stage finishes — no approximation.

The 8 predetermined matchups (winner vs runner-up, runner-up vs runner-up) follow the published bracket structure.

### 6. Knockout Rounds

Knockout matches must produce a winner. If tied after regulation, the simulator runs a penalty shootout where each team has a 40-60% win probability based on relative rating (penalties are heavily random in real life).

## Project Structure

```
World Cup 2026/
├── simulator.py           # Main simulator and Monte Carlo runner
├── score_teams.py         # Composite rating calculator
├── wc2026_ratings.csv     # Team data + composite ratings
├── fifa_annex_c.csv       # Official FIFA 495-scenario lookup
└── README.md
```

## Usage

### Run a single tournament (verbose)
Uncomment the print statements in `simulate_knockout_round` and `simulate_tournament`, then run:
```bash
python simulator.py
```
You'll see every match result from R32 to the final, ending with a champion.

### Run 10,000 simulations (Monte Carlo)
With prints commented out (default), running `python simulator.py` produces aggregated stats:
- Each team's win probability
- Each team's average goals scored per campaign
- Ranked output table

### Recalculate team ratings
After editing `wc2026_ratings.csv` (changing FIFA ranks, Star Ratings, etc.):
```bash
python score_teams.py
```
This rewrites the Rating (0-100) column in the CSV.

## Sample Results (10,000 Simulations)

| Rank | Team | Win % | Avg Goals/Campaign |
|---|---|---|---|
| 1 | France | 13.9% | 12.69 |
| 2 | Spain | 11.7% | 15.30 |
| 3 | Argentina | 10.2% | 11.37 |
| 4 | England | 10.1% | 13.18 |
| 5 | Portugal | 7.6% | 11.32 |
| 6 | Morocco | 5.9% | 20.48 |
| 7 | Germany | 5.1% | 12.13 |
| 8 | Netherlands | 4.7% | 9.85 |
| 9 | Brazil | 4.3% | 18.95 |
| 10 | Belgium | 4.1% | 9.91 |

Notable observations:
- **Morocco's 20.48 avg goals** but only 5.9% wins reflects deep runs that end in late rounds — consistent with their 2022 semifinal pattern
- **Brazil's 18.95 avg goals** on only 4.3% wins suggests they win their group convincingly but face elite competition in knockouts
- **Bottom-tier teams** (Haiti, Curaçao, Cape Verde) win 0.0% — consistent with debutant tournament reality

## Methodology Notes & Limitations

**What this model does well:**
- Uses real qualifying data, not invented stats
- Applies FIFA's actual bracket logic for R32 third-place assignments
- Produces realistic upset frequencies via Poisson randomness
- Tracks tournament-long form and momentum effects

**What it doesn't model (yet):**
- Player injuries or suspensions during the tournament
- Specific tactical matchups (e.g., a team that struggles vs high-press systems)
- Player-specific star effects beyond the squad's overall Star Rating
- Fatigue across extra-time knockout games
- Home advantage for USA, Mexico, Canada (intentionally excluded after testing showed minimal impact)

**Data sources:**
- FIFA qualifying campaign stats (goals, GD)
- Continental tournament results (EURO 2024, Copa America 2024, AFCON 2023/2025, Asian Cup 2023, Gold Cup 2025)
- FIFA World Rankings (April 2026)
- Subjective Star Rating and GK Form (1-5 / 1-3 scales)

## Built With

- **Python 3.13** (no external dependencies — uses only `csv`, `random`, `math`)
- **VS Code** for development
- **Google Sheets** for data entry

## About

Built as a senior-year portfolio project by Bernard Abousleiman, Data Science major at UC Santa Barbara. The project combines tournament structure, statistical modeling, and Monte Carlo simulation — applying analytics methods used in sports betting, fantasy sports modeling, and broadcast analytics.
