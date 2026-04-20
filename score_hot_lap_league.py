# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import os
from pathlib import Path

from core.clients import ClientMain
from core.league import LeagueConfiguration
from core.sheets import GDrive, SheetsDisplay

_logger = logging.getLogger('log')


def score_league(client: ClientMain,
                 cfg: LeagueConfiguration,
                 g612ir: dict,
                 sheets_display: SheetsDisplay):
    league = cfg.fetch_and_score_hot_lap_league(client.idc, client.g61, g612ir)

    results_dir = Path("./results")
    results_dir.mkdir(exist_ok=True)
    filename = results_dir / f"{cfg.name} {cfg.season}.json"
    print(f"Writing league to {filename}")
    # Convert the League class to a python dict
    d = league.as_dict()  # Work with data in a native python format instead of our classes
    # Dump the dict to json
    with open(filename, 'w') as fp:
        json.dump(d, fp, indent=2)

    # Push our results up to our sheets
    if sheets_display is not None and client.google_credentials_filename.exists():
        try:
            _logger.info("Pushing " + cfg.name + " season " + str(cfg.season) + " results to sheets")
            GDrive.push_results_to_sheets(league,
                                          list(cfg.group_rules.keys()),
                                          sheets_display,
                                          client.google_credentials_filename)
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
                GDrive.push_results_to_sheets(league,
                                              list(cfg.group_rules.keys()),
                                              sheets_display,
                                              client.google_credentials_filename)
                # TODO change up the auth type so we don't need to do this
    else:
        print("Could not find credentials file. Not pushing to sheets.")


