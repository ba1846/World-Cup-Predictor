# Importing the CSV Library
import csv

# Dictionary for Weights, how important is each value to the overall rating
WEIGHTS = {
    "qual_gd":          0.10, # Goal differential through World Cup Qualifiers
    "qual_ga_per_mp":   0.10, # Goals Allowed per match in Qualifiers
    "tournament_score": 0.14, # Personal variable where I alloted a certain score based on the tournament and placement for each team
    "podium_bonus":     0.15, # Added bonus points for teams who finished 1-4th in their respective major tournament
    "fifa_rank":        0.21, # FIFA rankings off the website, ranked 1-48 and dropped the teams that didn't qualify
    "star_rating":      0.25, # Personal rating based on team strength 1-5
    "gk_form":          0.05, # Personal rating based on a goalkeepers strength 1-3, especially important for penalties
}

## Helper Functions
# Takes a value and tries to convert it to a number
def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError): # If it fails it returns 0 instead of crashing
        return default

# Takes a list of numbers and scales them from 0-1
def normalize(values):
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]

# Reads the CSV file by row so each teams data stays together
def main():
    with open("wc2026_ratings.csv", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    teams = [] # Loop to build the team data
    for row in rows:
        teams.append({
            "row":              row,
            "name":             row["Team"].strip(),
            "qual_gd":          safe_float(row.get("Qual GD")),
            "qual_ga_per_mp":   safe_float(row.get("Qual GA/MP")),
            "tournament_score": safe_float(row.get("Tournament Score")),
            "podium_bonus":     safe_float(row.get("Podium Bonus")),
            "fifa_rank":        safe_float(row.get("FIFA Rank")),
            "star_rating":      safe_float(row.get("Star Rating")),
            "gk_form":          safe_float(row.get("GK Form")),
        })

    # Normalizes the columns for all teams so that the ratings are compared to other teams
    def norm_col(key, invert=False):
        vals = [t[key] for t in teams]
        normed = normalize(vals)
        if invert:
            normed = [1 - v for v in normed]
        for t, v in zip(teams, normed):
            t[f"{key}_norm"] = v

    norm_col("qual_gd")
    norm_col("qual_ga_per_mp", invert=True)
    norm_col("tournament_score")
    norm_col("podium_bonus")
    norm_col("fifa_rank", invert=True)
    norm_col("star_rating")
    norm_col("gk_form")

    # Multiply the weights by the teams individual values to make the composite scores
    for t in teams:
        score = (
            WEIGHTS["qual_gd"]          * t["qual_gd_norm"]          +
            WEIGHTS["qual_ga_per_mp"]   * t["qual_ga_per_mp_norm"]   +
            WEIGHTS["tournament_score"] * t["tournament_score_norm"] +
            WEIGHTS["podium_bonus"]     * t["podium_bonus_norm"]     +
            WEIGHTS["fifa_rank"]        * t["fifa_rank_norm"]        +
            WEIGHTS["star_rating"]      * t["star_rating_norm"]      +
            WEIGHTS["gk_form"]          * t["gk_form_norm"]
        )
        t["composite"] = score

    # Scaling composite scores from 0-100
    composites = [t["composite"] for t in teams]
    mn, mx = min(composites), max(composites)
    for t in teams:
        t["rating_100"] = round((t["composite"] - mn) / (mx - mn) * 100, 2)

    fieldnames = list(rows[0].keys())
    if "Rating (0-100)" not in fieldnames:
        fieldnames.append("Rating (0-100)")

    team_lookup = {t["name"]: t for t in teams}

    # Writing the team score 0-100 back to the CSV file
    with open("wc2026_ratings.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            name = row["Team"].strip()
            if name in team_lookup:
                row["Rating (0-100)"] = team_lookup[name]["rating_100"]
            writer.writerow(row)

    # Printing the final scores in the terminal
    ranked = sorted(teams, key=lambda t: t["rating_100"], reverse=True)
    print(f"\n{'Rank':<5} {'Team':<28} {'Rating':>8}")
    print("-" * 45)
    for i, t in enumerate(ranked, 1):
        print(f"{i:<5} {t['name']:<28} {t['rating_100']:>8.2f}")

    print(f"\nUpdated wc2026_ratings.csv with new ratings.")

main()