# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
from pathlib import Path
from trueskill import TrueSkill

from core.objects import LeagueResult


def assess_seasons(season_filenames: list) -> dict:
    league_ratings = {}
    for season_filename in season_filenames:
        assess_season(season_filename, league_ratings)
    # Sort the league_ratings by rating mu
    driver_rankings = sorted(list(league_ratings.values()), key=lambda d: d["rating"].mu, reverse=True)
    for idx, driver in enumerate(driver_rankings):
        driver["league_rank"] = idx+1
    return league_ratings


def assess_season(season_filename: Path, league_ratings: dict):
    print(f"Assessing {season_filename}")
    with open(season_filename, 'r') as file:
        league_ledger = LeagueResult.from_dict(json.load(file))

    env = TrueSkill()  # uses default settings

    num_races = len(league_ledger.races)
    print(f"There are {num_races} races")

    for r in range(1, num_races+1):
        race = league_ledger.get_race(r)
        results = race.get_results()
        if len(results) == 0:
            continue
        driver_ratings = []
        for result in results:
            if result[0] not in league_ratings:
                league_ratings[result[0]] = {"name": league_ledger.get_driver(result[0]).name,
                                             "rating": env.create_rating(),
                                             "starts": 0,
                                             "league_rank": None,
                                             "season_rank": None}
            driver_ratings.append((league_ratings[result[0]]["rating"],))
        new_driver_ratings = env.rate(driver_ratings)
        # Push the new driver ratings into our league_ratings
        for i, result in enumerate(results):
            league_ratings[result[0]]["rating"] = new_driver_ratings[i][0]

    for cust_id, items in league_ratings.items():
        driver = league_ledger.get_driver(cust_id)
        if driver:
            items["starts"] += driver.total_race_starts

    return league_ratings


# Trim the given league ratings to only the drivers in the given season file
def trim(league_ratings: dict, season_filename: Path):
    season_ratings = {}
    with open(season_filename, 'r') as file:
        season_ledger = LeagueResult.from_dict(json.load(file))
    for cust_id in season_ledger.drivers.keys():
        season_ratings[cust_id] = league_ratings[cust_id]
    # Sort the league_ratings by rating mu
    driver_rankings = sorted(list(season_ratings.values()), key=lambda d: d["rating"].mu, reverse=True)
    for idx, driver in enumerate(driver_rankings):
        driver["season_rank"] = idx + 1
    return season_ratings


def write_ratings_file(league_ratings: dict, rating_filename: Path, sigma_threshold: float = None):
    league_order = []
    for cust_id, items in league_ratings.items():
        if sigma_threshold and items["rating"].sigma > sigma_threshold:
            continue
        j_items = items.copy()
        j_items["mu"] = j_items["rating"].mu
        j_items["sigma"] = j_items["rating"].sigma
        del j_items["rating"]
        league_order.append(j_items)
    sorted_ratings = sorted(league_order, key=lambda x: x["mu"], reverse=True)

    if rating_filename.suffix == ".txt":
        with open(rating_filename, 'w', encoding='utf-8') as file:
            for idx, p in enumerate(sorted_ratings):
                file.write(f"{idx+1}. {p['name']} ({p['league_rank']}) {p['mu']} ({p['sigma']}) {p['starts']} starts\n")
    elif rating_filename.suffix == ".json":
        with open(rating_filename, 'w') as file:
            json.dump(sorted_ratings, file, indent=2)


def main():
    out_dir = Path("./ratings")
    todo = ["ww-srf"]

    def write_ratings(name: str, season_files: list, dst: Path):
        ratings = assess_seasons(season_files)
        dst.mkdir(exist_ok=True, parents=True)
        write_ratings_file(ratings, dst/f"{name} League Ratings.txt")
        write_ratings_file(ratings, dst/f"{name} League Ratings.json")
        write_ratings_file(ratings, dst/f"{name} Trimmed League Ratings.txt", sigma_threshold=2.0)
        current_ratings = trim(ratings, season_files[-1])
        write_ratings_file(current_ratings, dst/f"{name} Current Ratings.txt")

    for lg in todo:
        if lg == "ams":
            seasons = [Path("./results/American Muscle Series Season 1.json"),
                       Path("./results/American Muscle Series Season 2.json"),
                       Path("./results/American Muscle Series Season 3.json"),
                       Path("./results/American Muscle Series Season 4.json"),
                       Path("./results/American Muscle Series Season 5.json"),
                       Path("./results/American Muscle Series Season 6.json"),
                       Path("./results/American Muscle Series Season 7.json"),
                       Path("./results/American Muscle Series Season 8.json"),
                       Path("./results/American Muscle Series Season 9.json")]
            write_ratings(name="American Muscle Series", season_files=seasons, dst=out_dir/f"{lg}")
            continue

        if lg == "ww-ff":
            seasons = [Path("./results/FF Weekend Warriors 2025 S1 FF Weekend Warriors.json"),
                       Path("./results/FF Weekend Warriors 2025 S2.json"),
                       Path("./results/FF Weekend Warriors 2025S3 WW FF1600.json"),
                       Path("./results/FF Weekend Warriors 2025S4 WW FF1600.json")]
            write_ratings(name="Weekend Warriors FF", season_files=seasons, dst=out_dir/f"{lg}")
            continue

        if lg == "ww-fv":
            seasons = [Path("./results/FV Weekend Warriors WW FV 2025 S1.json"),
                       Path("./results/FV Weekend Warriors WW FV 2025 S2.json"),
                       Path("./results/FV Weekend Warriors WW FV 2025 S3.json"),
                       Path("./results/FV Weekend Warriors WW FV 2025 S4.json")]
            write_ratings(name="Weekend Warriors FV", season_files=seasons, dst=out_dir/f"{lg}")
            continue

        if lg == "ww-srf":
            seasons = [Path("./results/SRF Weekend Warriors 2025 S1 SRF Weekend Warriors.json"),
                       Path("./results/SRF Weekend Warriors 2025 S2.json"),
                       Path("./results/SRF Weekend Warriors 2025 S3 SRF WW.json"),
                       Path("./results/SRF Weekend Warriors 2025S4 WW SRF 10yr Anniversary season.json")]
            #  seasons = list(Path("./results").glob("SRF*.json"))
            write_ratings(name="Weekend Warriors SRF", season_files=seasons, dst=out_dir/f"{lg}")
            continue


if __name__ == "__main__":
    main()
