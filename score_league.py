# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import argparse
import copy
import csv
import json
import logging
import os
import re
import sys
from pathlib import Path

from core.league import LeagueConfiguration, LeagueResult
from core.sheets import GDrive, SheetsDisplay

_logger = logging.getLogger('log')


def score_league(cfgs: list[LeagueConfiguration], sheets_display: SheetsDisplay, active: bool = True):
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', filename="ams.log", filemode="w")
    logging.getLogger('ams').setLevel(logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    parser = argparse.ArgumentParser(description="Pull league results and rack and stack them for presentation")
    parser.add_argument(
        "username",
        type=str,
        help="iracing user name."
    )
    parser.add_argument(
        "password",
        type=str,
        help="iracing password."
    )
    parser.add_argument(
        "-cr", "--credentials",
        default="./credentials.json",
        type=Path,
        help="Credentials file for connecting to google sheets."
    )
    opts = parser.parse_args()

    for cfg in cfgs:
        league = cfg.fetch_and_score_league(opts.username, opts.password, active)

        # print_debug_stats(league, 609455)
        # print_debug_stats(league, 120570)

        results_dir = Path("./results")
        results_dir.mkdir(exist_ok=True)
        filename = results_dir / f"{cfg.name} {cfg.season}.json"
        print(f"Writing league to {filename}")
        # Convert the League class to a python dict
        d = league.as_dict()  # Work with data in a native python format instead of our classes
        # Dump the dict to json
        with open(filename, 'w') as fp:
            json.dump(d, fp, indent=2)
        broadcast_standings(filename, cfg, league, results_dir)

        # Push our results up to our sheets
        if opts.credentials.exists():
            try:
                _logger.info("Pushing " + cfg.name + " season " + str(cfg.season) + " results to sheets")
                GDrive.push_results_to_sheets(league, list(cfg.group_rules.keys()), sheets_display, opts.credentials)
            except Exception as e:
                print("Failed to upload to google sheets", e)
                if "Token" in str(e) and "expired" in str(e):
                    # if this craps out about an expired token, I will need to delete your authorized_user.json file
                    # ex. C:\Users\aaron.bray\AppData\Roaming\gspread\authorized_user.json
                    # The user authorization token you get only lasts 7 days
                    # Then you can rerun the program
                    authorized_user_file = Path(os.getenv('APPDATA') + "/gspread/authorized_user.json")
                    print("I have deleted your google sheets authorization file: " + str(authorized_user_file))
                    print("Please select your gmail login in your browser again")
                    authorized_user_file.unlink()
                    GDrive.push_results_to_sheets(league, list(cfg.group_rules.keys()), sheets_display, opts.credentials)
                    # TODO change up the auth type so we don't need to do this
        else:
            print("Could not find credentials file. Not pushing to sheets.")


def broadcast_standings(results_filename: Path, cfg: LeagueConfiguration, lg: LeagueResult, out_dir: Path):

    headers = [
        "First name", "Last name", "Suffix", "Multicar team name", "Club name", "iRacing ID", "Car number",
        "Multicar team background color", "iRacing car color", "iRacing car number color", "iRacing car number color 2",
        "iRacing car number color 3", "iRacing car number font ID", "iRacing car number style",
        "Points before weekend", "Points earned", "Bonus points", "Points after weekend"
    ]
    data = ["First name", "Last name", "", "", "", "iRacindID", "CarNumber",
            "Transparent", "Transparent", "Transparent", "Transparent", "Transparent",
            "0", "0", "0", "0", "0", "0"]

    def pull_class(c: str, lr: LeagueResult):
        class_standings = []
        for iRid, driver in lr.drivers.items():
            if driver.group != c:
                continue

            # Split name, and remove numbers
            clean_name = re.sub(r"\d+", "", driver.name)
            names = clean_name.split(" ")

            d = copy.deepcopy(data)
            d[0] = names[0]
            d[1] = names[-1]
            d[5] = iRid
            d[6] = driver.car_number
            d[14] = driver.earned_points
            d[17] = driver.earned_points
            class_standings.append(d)
        class_standings.sort(key=lambda x: x[-1], reverse=True)
        class_standings.insert(0, headers)
        return class_standings

    for group in cfg.group_rules.keys():
        standings = pull_class(group, lg)
        filename = out_dir / f"{cfg.name} {cfg.season} {group}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(standings)
