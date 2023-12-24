# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import argparse

from league.utils import LeagueResource, Group, GroupRule
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
        "-r", "--resource",
        default=None,
        type=str,
        help="League resource json file to process. If none is provided, we will score an ams season."
    )
    parser.add_argument(
        "-s", "--season",
        default=None,
        type=str,
        help="Seasons to score (1 based indexing!). If none is provided, we will pull and score all league seasons."
    )
    parser.add_argument(
        "-o", "--outfile",
        default=None,
        type=str,
        help="A json of the the scored league."
    )
    opts = parser.parse_args()

    # Note, for our API, use 1 based counting
    # The first race is race 1, not race 0
    # The first season is season 1, not season 0
    lr = LeagueResource(6810)

    # Set the number of drop rounds
    lr.num_drops = 2

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

    # Add a few penalties for punting (for testing purposes, we have only the cleanest of drivers)
    lr.add_time_penalty(5, 1, 823724, 5)  # This should knock Kevin to 3rd
    lr.add_time_penalty(5, 2, 120570, 5)  # This should knock Malone to 4th
    # You can only apply a time penalty on drivers that finish on the lead lap, an error will be logged
    lr.add_time_penalty(5, 1, 413722, 5)  # This driver did not finish on lead lap


    # Save our league resource to a json file.
    # Convert the LeagueResource class to a python dict
    d = lr.as_dict()  # Use this if you would rather work with data in a native python format instead of our classes
    # Dump the dict to json
    with open("resource.json", 'w') as fp:
        json.dump(d, fp, indent=2)

    testing = False
    if testing:
        # Testing that our serialization is consistent
        r = open('resource.json')
        d = json.load(r)
        lr = LeagueResource.from_dict(d)
        d = lr.as_dict()

        with open("resource2.json", 'w') as fp:
            json.dump(d, fp, indent=2)

    # Let's just fetch and score season 5
    # If you do not provide a season array, all seasons will be pulled and scored
    league = lr.fetch_and_score_league(opts.username, opts.password, [5])

    print_debug_stats(league, 120570)
    print_debug_stats(league, 609455)

    print("Writing league to league.json")
    # Convert the League class to a python dict
    d = league.as_dict()  # Use this if you would rather work with data in a native python format instead of our classes
    # Dump the dict to json
    with open("league.json", 'w') as fp:
        json.dump(d, fp, indent=2)

