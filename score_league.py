# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import argparse
from pathlib import Path

from league.config import LeagueConfiguration, Group, GroupRule
from league.objects import print_debug_stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.getLogger('ams').setLevel(logging.INFO)

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
        "-c", "--configuration",
        default=None,
        type=Path,
        help="League configuration json file to process. If none is provided, we will score an ams season."
    )
    parser.add_argument(
        "-s", "--season",
        default=None,
        type=int,
        help="Seasons to score (1 based indexing!). If none is provided, we will pull and score all league seasons."
    )
    parser.add_argument(
        "-l", "--league_filename",
        default="./league.json",
        type=Path,
        help="A json file of the the scored league."
    )
    parser.add_argument(
        "-cr", "--credentials",
        default="./credentials.json",
        type=Path,
        help="Credentials file for connecting to google sheets."
    )
    opts = parser.parse_args()

    if opts.configuration is not None:
        if opts.configuration.exists():
            r = open(opts.configuration)
            d = json.load(r)
            lr = LeagueConfiguration.from_dict(d)
            d = lr.as_dict()
            season = None
            if opts.season is not None:
                season = [opts.season]
            league = lr.fetch_and_score_league(opts.username, opts.password, season)
        else:
            print("Unable to load specified configuration: " + str(opts.configuration))
    else:
        # Pull an AMS season and score it

        # Note, for our API, use 1 based counting
        # The first race is race 1, not race 0
        # The first season is season 1, not season 0
        lr = LeagueConfiguration(6810)

        # Set the number of drop rounds
        lr.num_drops = 2

        # Set our scoring system
        scoring = lr.set_linear_decent_scoring(40)
        # This will provide the winner with 40 points, and 1 less point for each subsequent driver

        # You could do formula 1 style scoring
        # scoring = lr.set_assignment_scoring({1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        #                                     6: 8, 7: 6, 8: 4, 9: 2, 10: 1})

        # Let's give points for these as well, default is 0 points
        scoring.pole_position = 1
        scoring.laps_lead = 1
        scoring.fastest_lap = 0

        # Add non drivers like race control and media personalities
        lr.add_non_driver(295683)
        lr.add_non_driver(366513)

        # Set up our grouping rules per season
        lr.add_group_rule(5, GroupRule(0, 99, Group.Pro))
        lr.add_group_rule(5, GroupRule(100, 199, Group.Am))

        # Let's ignore practice races
        # This will result in the third race session as being race 1
        lr.add_practice_race(5, 1)
        lr.add_practice_race(5, 2)

        # Apply Penalties
        lr.add_time_penalty(5, 2, 821509, 5)
        lr.add_time_penalty(5, 3, 823724, 5)
        # You can only apply a time penalty on drivers that finish on the lead lap, an error will be logged
        # lr.add_time_penalty(5, 1, 413722, 5)  # This driver did not finish on lead lap

        # [Optional] Provide a Google Sheet, for each season, where we can push results to
        # Where is it and what are the group tab names of the Google sheet to push results to
        lr.add_google_sheet(5,
                            "1jlybjNg8sQGFuwSPrnNvQRq5SrIX73QUbISNVIp3Clk",
                            {Group.Pro: "Pro Drivers", Group.Am: "Am Drivers"})

        # Save our league resource to a json file.
        # Convert the LeagueResource class to a python dict
        d = lr.as_dict()  # Use this if you would rather work with data in a native python format instead of our classes
        # Dump the dict to json
        with open("configuration.json", 'w') as fp:
            json.dump(d, fp, indent=2)

        testing = False
        if testing:
            # Testing that our serialization is consistent
            r = open('configuration.json')
            d = json.load(r)
            lr = LeagueConfiguration.from_dict(d)
            d = lr.as_dict()

            with open("configuration2.json", 'w') as fp:
                json.dump(d, fp, indent=2)

        # Let's just fetch and score season 5
        # If you do not provide a season array, all seasons will be pulled and scored
        league = lr.fetch_and_score_league(opts.username, opts.password, [5])

        print_debug_stats(league, 120570)
        print_debug_stats(league, 609455)

    print("Writing league to "+str(opts.league_filename))
    # Convert the League class to a python dict
    d = league.as_dict()  # Use this if you would rather work with data in a native python format instead of our classes
    # Dump the dict to json
    with open(opts.league_filename, 'w') as fp:
        json.dump(d, fp, indent=2)

    # Push our results up to our sheets
    if opts.credentials.exists():
        lr.push_results_to_sheets(league, opts.credentials)
    else:
        print("Could not find credentials file. Not pushing to sheets.")





