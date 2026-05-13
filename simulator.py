# 1. Imports
import csv # To access the csv file
import random  # For randomness in simulation

# 2. Constants and config (things that don't change)
base_goals = 1.4 # Baseline for simulation
rating_floor = 10 # Blocks absurd blowouts
from math import exp, factorial # For poisson math
from math import sqrt

# Groups
# Pot order for each group (top seed first, lowest seed last)
GROUP_POT_ORDER = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Côte d'Ivoire", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}


# 3. Helper functions (small reusable pieces)
def load_teams(): # No argument func, to load teams
    """Read teams from CSV and return as a dictionary keyed by team name."""
    teams = {} # Empty dictionary
    with open("wc2026_ratings.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Team"].strip()
            teams[name] = {
                "name": name,
                "group": row["Group"],
                "rating": float(row["Rating (0-100)"]),
            }
    return teams

def expected_goals(team_a, team_b, knockout=False, motivation_a=1.0, motivation_b=1.0):
    # Apply form bonus to ratings
    rating_a = team_a["rating"] * (1 + team_a.get("form_bonus", 0))
    rating_b = team_b["rating"] * (1 + team_b.get("form_bonus", 0))
    
    lambda_a = base_goals * sqrt(rating_a / rating_b)
    lambda_b = base_goals * sqrt(rating_b / rating_a)
    
    lambda_a *= motivation_a
    lambda_b *= motivation_b
    
    if knockout:
        lambda_a *= random.uniform(0.9, 1.1)
        lambda_b *= random.uniform(0.9, 1.1)
    else:
        lambda_a *= random.uniform(0.8, 1.2)
        lambda_b *= random.uniform(0.8, 1.2)
    
    return lambda_a, lambda_b

def poisson_sample(lam):
    """Draw a random goal count from a Poisson distribution with mean lam."""
    # Using the Knuth algorithm — simple and built-in math
    L = exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def build_group_schedule(group_teams):
    """Builds the 3 matchday schedule for each respective group"""
    t = group_teams

    schedule = [
        # MD1 1v2, 3v4
        [(t[0], t[1]), (t[2], t[3])],
        # MD2 1v3, 2v4
        [(t[0], t[2]), (t[1], t[3])],
        # MD3 1v4, 2v3
        [(t[0], t[3]), (t[1], t[2])]
    ]
    
    return schedule

def update_form_bonus(team_a, team_b, goals_a, goals_b):
    """Winner gets boost based on opponent quality (max 3% accumulated). Loser resets."""
    if "form_bonus" not in team_a:
        team_a["form_bonus"] = 0
    if "form_bonus" not in team_b:
        team_b["form_bonus"] = 0
    
    if goals_a > goals_b:
        boost = (team_b["rating"] / 100) * 0.05
        team_a["form_bonus"] = min(team_a["form_bonus"] + boost, 0.03)
        team_b["form_bonus"] = 0
    elif goals_b > goals_a:
        boost = (team_a["rating"] / 100) * 0.05
        team_b["form_bonus"] = min(team_b["form_bonus"] + boost, 0.03)
        team_a["form_bonus"] = 0



def update_match_stats(stats, team_a, team_b, goals_a, goals_b):
    stats[team_a["name"]]["played"] += 1
    stats[team_b["name"]]["played"] += 1
    stats[team_a["name"]]["goals_for"] += goals_a
    stats[team_a["name"]]["goals_against"] += goals_b
    stats[team_b["name"]]["goals_for"] += goals_b
    stats[team_b["name"]]["goals_against"] += goals_a
    
    if goals_a > goals_b:
        stats[team_a["name"]]["wins"] += 1
        stats[team_a["name"]]["points"] += 3
        stats[team_b["name"]]["losses"] += 1
    elif goals_b > goals_a:
        stats[team_b["name"]]["wins"] += 1
        stats[team_b["name"]]["points"] += 3
        stats[team_a["name"]]["losses"] += 1
    else:
        stats[team_a["name"]]["draws"] += 1
        stats[team_a["name"]]["points"] += 1
        stats[team_b["name"]]["draws"] += 1
        stats[team_b["name"]]["points"] += 1

# 4. Main logic
def simulate_match(team_a, team_b, knockout=False, motivation_a=1.0, motivation_b=1.0):
    lambda_a, lambda_b = expected_goals(team_a, team_b, knockout, motivation_a, motivation_b)
    goals_a = poisson_sample(lambda_a)
    goals_b = poisson_sample(lambda_b)
    return goals_a, goals_b

def simulate_group(group_teams):
    schedule = build_group_schedule(group_teams)
    
    stats = {}
    for team in group_teams:
        stats[team["name"]] = {
            "team": team,
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_for": 0, "goals_against": 0, "points": 0,
        }
    
    # Matchdays 1 and 2 — normal play
    for matchday in schedule[:2]:
        for team_a, team_b in matchday:
            goals_a, goals_b = simulate_match(team_a, team_b)
            update_match_stats(stats, team_a, team_b, goals_a, goals_b)
            update_form_bonus(team_a, team_b, goals_a, goals_b)
    
    # Matchday 3 — apply motivation
    matchday_3 = schedule[2]
    for team_a, team_b in matchday_3:
        motivation_a, motivation_b = get_motivation(stats, team_a, team_b)
        goals_a, goals_b = simulate_match(team_a, team_b, motivation_a=motivation_a, motivation_b=motivation_b)
        update_match_stats(stats, team_a, team_b, goals_a, goals_b)
        update_form_bonus(team_a, team_b, goals_a, goals_b)
    
    for team_stats in stats.values():
        team_stats["gd"] = team_stats["goals_for"] - team_stats["goals_against"]
    
    standings = sorted(
        stats.values(),
        key=lambda x: (x["points"], x["gd"], x["goals_for"]),
        reverse=True
    )
    
    return standings

def simulate_group_stage(teams):
    """Simulate all 12 groups."""
    winners = []
    runners_up = []
    third_place_teams = []
    group_goals = {}
    
    for letter in sorted(GROUP_POT_ORDER.keys()):
        group_teams = [teams[name] for name in GROUP_POT_ORDER[letter]]
        standings = simulate_group(group_teams)
        
        for s in standings:
            s["group_letter"] = letter
            group_goals[s["team"]["name"]] = s["goals_for"]
        
        winners.append(standings[0])
        runners_up.append(standings[1])
        third_place_teams.append(standings[2])
    
    return winners, runners_up, third_place_teams, group_goals

def get_best_thirds(third_place_teams, n=8):
    """Get the best 8 third-place teams."""
    sorted_thirds = sorted(
        third_place_teams,
        key=lambda x: (x["points"], x["gd"], x["goals_for"]),
        reverse=True,
    )
    return sorted_thirds[:n]

def get_third_place_matchups(best_thirds):
    """Get the best 8 third-place teams to move on to knockout stage"""
     # Get the 8 group letters and sort alphabetically to build the key
    qualifying_letters = sorted([t["group_letter"] for t in best_thirds])
    key = "".join(qualifying_letters)
    
    # Look it up in the Annex C table
    annex_c = load_annex_c()
    
    if key not in annex_c:
        raise ValueError(f"Combination {key} not found in Annex C table!")
    
    return annex_c[key]

def load_annex_c():
    """
    Load FIFA's Annex C lookup table.
    Returns a dict mapping qualifying group letters string → matchup dict.
    """
    table = {}
    with open("fifa_annex_c.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["Qualifying Groups"].strip()
            
            # Each value is like "3E" — strip the "3" to get just the group letter
            matchups = {}
            for col in ["1A vs", "1B vs", "1D vs", "1E vs", "1G vs", "1I vs", "1K vs", "1L vs"]:
                winner_id = col.replace(" vs", "")  # "1A vs" → "1A"
                third_place_group = row[col].strip().replace("3", "")  # "3E" → "E"
                matchups[winner_id] = third_place_group
            
            table[key] = matchups
    
    return table

def get_motivation(stats, team_a, team_b):
    """
    Determine motivation multipliers for matchday 3.
    Simple rules based on current points and ratings.
    """
    a_stats = stats[team_a["name"]]
    b_stats = stats[team_b["name"]]
    
    a_points = a_stats["points"]
    b_points = b_stats["points"]
    rating_gap = team_a["rating"] - team_b["rating"]
    
    def get_status(points):
        if points >= 6:
            return "safe"      # locked top 2
        if points == 0:
            return "eliminated"  # going through motions
        if points <= 3:
            return "must_win"    # need a win
        return "neutral"          # 4-5 points, situation depends on others
    
    a_status = get_status(a_points)
    b_status = get_status(b_points)
    
    motivation_a = 1.0
    motivation_b = 1.0
    
    if a_status == "safe" and rating_gap > 30:
        motivation_a = 0.7
    elif a_status == "eliminated":
        motivation_a = 0.8
    elif a_status == "must_win":
        motivation_a = 1.3 if rating_gap >= 0 else 1.2
    
    if b_status == "safe" and rating_gap < -30:
        motivation_b = 0.7
    elif b_status == "eliminated":
        motivation_b = 0.8
    elif b_status == "must_win":
        motivation_b = 1.3 if rating_gap <= 0 else 1.2
    
    return motivation_a, motivation_b

def build_r32_matchups(winners, runners_up, best_thirds, third_place_matchups):
    """
    Build all 16 Round of 32 matchups based on FIFA bracket structure.
    Returns a list of (team_a, team_b, match_number) tuples.
    """
    # Helpers to look up teams by group letter
    def get_winner(letter):
        return next(w["team"] for w in winners if w["group_letter"] == letter)
    
    def get_runner_up(letter):
        return next(r["team"] for r in runners_up if r["group_letter"] == letter)
    
    def get_third(letter):
        return next(t["team"] for t in best_thirds if t["group_letter"] == letter)
    
    # Map from group winner ID → match number (from FIFA bracket)
    third_place_match_numbers = {
        "1A": 79,
        "1B": 85,
        "1D": 81,
        "1E": 74,
        "1G": 82,
        "1I": 77,
        "1K": 87,
        "1L": 80,
    }
    
    matchups = []
    
    # The 8 matchups involving 3rd-place teams
    for winner_id, third_letter in third_place_matchups.items():
        match_num = third_place_match_numbers[winner_id]
        winner_letter = winner_id[1]  # "1A" → "A"
        team_a = get_winner(winner_letter)
        team_b = get_third(third_letter)
        matchups.append((team_a, team_b, match_num))
    
    # The 8 predetermined matchups (winner vs runner-up, runner-up vs runner-up)
    predetermined = [
        (73, get_runner_up("A"), get_runner_up("B")),
        (75, get_winner("F"), get_runner_up("C")),
        (76, get_winner("C"), get_runner_up("F")),
        (78, get_runner_up("E"), get_runner_up("I")),
        (83, get_runner_up("K"), get_runner_up("L")),
        (84, get_winner("H"), get_runner_up("J")),
        (86, get_winner("J"), get_runner_up("H")),
        (88, get_runner_up("D"), get_runner_up("G")),
    ]
    
    for match_num, team_a, team_b in predetermined:
        matchups.append((team_a, team_b, match_num))
    
    # Sort by match number so they're in order
    matchups.sort(key=lambda m: m[2])
    
    return matchups

def simulate_knockout_round(matchups, round_name):
    # print(f"\n=== {round_name} ===") Prints knockout round name in terminal
    results = []
    
    for team_a, team_b, match_num in matchups:
        winner, goals_a, goals_b, went_to_pens = simulate_knockout_match(team_a, team_b)
        update_form_bonus(team_a, team_b, goals_a, goals_b)  # ← add this line
        pens_text = " (penalties)" if went_to_pens else ""
        # print(f"Match {match_num}: {team_a['name']} {goals_a} - {goals_b} {team_b['name']}{pens_text} → {winner['name']}")
        results.append((winner, match_num))
    
    return results

def simulate_knockout_round_tracked(matchups, round_name, goals_by_team):
    """Like simulate_knockout_round but tracks goals."""
    results = []
    for team_a, team_b, match_num in matchups:
        winner, goals_a, goals_b, went_to_pens = simulate_knockout_match(team_a, team_b)
        update_form_bonus(team_a, team_b, goals_a, goals_b)
        goals_by_team[team_a["name"]] += goals_a
        goals_by_team[team_b["name"]] += goals_b
        results.append((winner, match_num))
    return results

def build_next_round_matchups(prev_round_results, starting_match_num):
    """
    Pair up winners from the previous round into the next round's matchups.
    prev_round_results is a list of (winner, match_num) tuples.
    starting_match_num is the first match number in the next round.
    Returns a list of (team_a, team_b, match_num) tuples.
    """
    # Sort by match number to make sure pairings are in bracket order
    prev_round_results.sort(key=lambda r: r[1])
    
    matchups = []
    new_match_num = starting_match_num
    
    # Pair them up: (M73 winner vs M74 winner), (M75 vs M76), etc.
    for i in range(0, len(prev_round_results), 2):
        team_a = prev_round_results[i][0]
        team_b = prev_round_results[i + 1][0]
        matchups.append((team_a, team_b, new_match_num))
        new_match_num += 1
    
    return matchups

def simulate_knockout_match(team_a, team_b):
    """
    Simulate a knockout match. Must produce a winner (penalties if drawn).
    Returns (winner, goals_a, goals_b, went_to_pens).
    """
    goals_a, goals_b = simulate_match(team_a, team_b, knockout=True)
    went_to_pens = False
    
    if goals_a == goals_b:
        went_to_pens = True
        rating_a = (team_a["rating"])
        rating_b = (team_b["rating"])
        win_prob_a = 0.4 + 0.2 * (rating_a / (rating_a + rating_b))
        
        if random.random() < win_prob_a:
            winner = team_a
        else:
            winner = team_b
    else:
        winner = team_a if goals_a > goals_b else team_b
    
    return winner, goals_a, goals_b, went_to_pens

def simulate_tournament(teams):
    """Run the entire tournament and return the champion + goals per team."""
    # Track goals for every team
    goals_by_team = {name: 0 for name in teams}
    
    # Group stage
    winners, runners_up, thirds, group_goals = simulate_group_stage(teams)
    for name, goals in group_goals.items():
        goals_by_team[name] += goals
    
    best_thirds = get_best_thirds(thirds)
    third_place_matchups = get_third_place_matchups(best_thirds)
    
    # Round of 32
    r32_matchups = build_r32_matchups(winners, runners_up, best_thirds, third_place_matchups)
    r32_results = simulate_knockout_round_tracked(r32_matchups, "ROUND OF 32", goals_by_team)
    
    # Round of 16
    r16_matchups = build_next_round_matchups(r32_results, 89)
    r16_results = simulate_knockout_round_tracked(r16_matchups, "ROUND OF 16", goals_by_team)
    
    # Quarterfinals
    qf_matchups = build_next_round_matchups(r16_results, 97)
    qf_results = simulate_knockout_round_tracked(qf_matchups, "QUARTERFINALS", goals_by_team)
    
    # Semifinals
    sf_matchups = build_next_round_matchups(qf_results, 101)
    sf_results = simulate_knockout_round_tracked(sf_matchups, "SEMIFINALS", goals_by_team)
    
    # Final
    final_matchups = build_next_round_matchups(sf_results, 104)
    final_results = simulate_knockout_round_tracked(final_matchups, "FINAL", goals_by_team)
    
    champion = final_results[0][0]
    # print(f"\n🏆 CHAMPION: {champion['name']} 🏆")
    return champion, goals_by_team

def monte_carlo(teams, num_sims=100):
    """Run the tournament many times and aggregate statistics."""
    # Initialize trackers for each team
    tracker = {}
    for name in teams:
        tracker[name] = {
            "wins": 0,
            "total_goals": 0,
        }
    
    print(f"Running {num_sims} simulations...")
    
    for i in range(num_sims):
        # Reset form bonuses between simulations
        for team in teams.values():
            team["form_bonus"] = 0
        
        # Run one tournament
        champion, goals_by_team = simulate_tournament(teams)
        
        # Record results
        tracker[champion["name"]]["wins"] += 1
        for name, goals in goals_by_team.items():
            tracker[name]["total_goals"] += goals
        
        # Progress indicator every 10 sims
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{num_sims}")
    
    # Calculate averages and percentages
    results = []
    for name, stats in tracker.items():
        results.append({
            "name": name,
            "win_pct": (stats["wins"] / num_sims) * 100,
            "avg_goals": stats["total_goals"] / num_sims,
            "wins": stats["wins"],
        })
    
    # Sort by win percentage
    results.sort(key=lambda x: (x["win_pct"], x["avg_goals"]), reverse=True)
    
    # Print results table
    print(f"\n=== RESULTS AFTER {num_sims} SIMULATIONS ===")
    print(f"{'Rank':<5} {'Team':<28} {'Wins':>5} {'Win %':>8} {'Avg Goals':>10}")
    print("-" * 62)
    for i, r in enumerate(results, 1):
        print(f"{i:<5} {r['name']:<28} {r['wins']:>5} {r['win_pct']:>7.1f}% {r['avg_goals']:>10.2f}")
    
    return results

def main():
    teams = load_teams()
    monte_carlo(teams, num_sims=10000)

# 5. The actual call to run everything
main()