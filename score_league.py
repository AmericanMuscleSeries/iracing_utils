# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import os
import sys
import json
import logging
import argparse
from pathlib import Path

from league.league import LeagueConfiguration, Group, GroupRules, SortBy
from league.objects import PositionValue
from league.objects import print_debug_stats

if __name__ == "__main__":
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
        "-c", "--configuration",
        default=None,
        type=Path,
        help="League configuration json file to process. If none is provided, we will score an ams season."
    )
    parser.add_argument(
        "-s", "--season",
        default=7,
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
        cfg = LeagueConfiguration(6810)

        if opts.season == 1 or opts.season is None:
            # Season 1
            season = cfg.get_season(1)
            scoring = season.set_linear_decent_scoring(40)
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0
            season.add_group_rule(Group.Unknown, GroupRules(0, 999, 2))
            season.add_google_sheet("1-u35u7rVazBkJOwpk1MGeafRksC0jc-zkJ2PamU1p1o",
                                    {Group.Unknown: "Drivers"})

        if opts.season == 2 or opts.season is None:
            # Season 2
            season = cfg.get_season(2)
            scoring = season.set_linear_decent_scoring(40)
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0
            season.add_group_rule(Group.Unknown, GroupRules(0, 999, 2))
            season.add_google_sheet("1Rh7X5lLh2C68dG-NjyFbgjn9shsrartGrR0PAyDol2o",
                                    {Group.Unknown: "Drivers"})

        if opts.season == 3 or opts.season is None:
            # Season 3
            season = cfg.get_season(3)
            scoring = season.set_linear_decent_scoring(40)
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0
            season.add_group_rule(Group.Unknown, GroupRules(0, 999, 2))
            season.add_google_sheet("1Smo-G7BlUEaFxudOn6FZ83mrSzu3u2eFFwH1dOyYBtY",
                                    {Group.Unknown: "Drivers"})

        if opts.season == 4 or opts.season is None:
            # Season 4
            season = cfg.get_season(4)
            scoring = season.set_linear_decent_scoring(40)
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0
            season.add_group_rule(Group.Unknown, GroupRules(0, 999, 2))
            season.add_google_sheet("1IJOA3c5k6r9IUq0tqgDJPQxaSwZ3xW4y-gknGRD8QjE",
                                    {Group.Unknown: "Drivers"})

        if opts.season == 5 or opts.season is None:
            # Season 5
            season = cfg.get_season(5)
            scoring = season.set_linear_decent_scoring(40)

            # You could do formula 1 style scoring
            # scoring = season.set_assignment_scoring({1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
            #                                          6: 8, 7: 6, 8: 4, 9: 2, 10: 1})

            # Let's give points for these as well, default is 0 points
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0

            # Add non drivers like race control and media personalities
            season.add_non_driver(295683)
            season.add_non_driver(366513)

            # Set up our grouping rules per season
            season.add_group_rule(Group.Pro, GroupRules(0, 99, 2))
            season.add_group_rule(Group.Am, GroupRules(100, 199, 2))

            # Let's ignore practice sessions
            # This will result in the third race session as being race 1
            # NOTE: This is the number of the league race sessions
            season.add_practice_sessions([1, 2])

            # Apply Penalties
            season.add_time_penalty(2, 821509, 5)
            season.add_time_penalty(3, 823724, 5)
            # You can only apply a time penalty on drivers that finish on the lead lap, an error will be logged
            # lr.add_time_penalty(5, 1, 413722, 5)  # This driver did not finish on lead lap

            # [Optional] Provide a Google Sheet, for each season, where we can push results to
            # Where is it and what are the group tab names of the Google sheet to push results to
            season.add_google_sheet("1jlybjNg8sQGFuwSPrnNvQRq5SrIX73QUbISNVIp3Clk",
                                    {Group.Pro: "Pro Drivers", Group.Am: "Am Drivers"})

        if opts.season == 6 or opts.season is None:
            # Season 6
            season = cfg.get_season(6)
            season.active = True  # Use this to use current league assigned numbers for all cars instead of race numbers
            season.sort_by = SortBy.ForcedDrops
            case = 6
            if case == 1:
                # Official
                sheet = "1qdMBFll_eZxTF7G9DkaliJ6tm8sADqhHHFhKT8fIy1c"
                scoring = season.set_linear_decent_scoring(40, hcp=False)
            elif case == 2:
                # Separate point pool between classes and use overall position value relative to class winner
                sheet = "1Qi8n5HlUkW5AsDkaKk5uRbFz-8axQGeE2G7pODwCLvA"
                # scoring = season.set_linear_decent_scoring(40, hcp=False,
                #                                            separate_pool=True, position_value=PositionValue.Overall)
                scoring = season.set_assignment_scoring({1:  50, 2:  47, 3:  45, 4:  43, 5:  42,
                                                         6:  41, 7:  40, 8:  39, 9:  38, 10: 37,
                                                         11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                         16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                         21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                         26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                         31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                         36: 11, 37: 10, 38:  9, 39:  8, 40:  7,
                                                         41:  6, 42:  5, 43:  4, 44:  3, 45:  2,
                                                         46:  1},
                                                        separate_pool=True, position_value=PositionValue.Overall)
            elif case == 3:
                # True multiclass
                # Separate point pool between classes and use class position value for points
                sheet = "1EqQjR9UM-Ds_bQ5mCdh3raCKnE5i4MgRLIXm5GRYajw"
                # scoring = season.set_linear_decent_scoring(40, hcp=False,
                #                                            separate_pool=True, position_value=PositionValue.Class)
                scoring = season.set_assignment_scoring({1:  50, 2:  47, 3:  45, 4:  43, 5:  42,
                                                         6:  41, 7:  40, 8:  39, 9:  38, 10: 37,
                                                         11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                         16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                         21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                         26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                         31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                         36: 11, 37: 10, 38:  9, 39:  8, 40:  7,
                                                         41:  6, 42:  5, 43:  4, 44:  3, 45:  2,
                                                         46:  1},
                                                        separate_pool=True, position_value=PositionValue.Class)
            elif case == 4:
                # IndyCar Style
                sheet = "1mawS71Na0yUpAoXT1Oid-skL1GIzHkxUTYURTodCu5o"
                scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                         6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                         11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                         16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                         21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                         26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                         31: 5, 32: 5, 33: 5})
            elif case == 5:
                # IndyCar Style
                sheet = "1p8qO5ruVhaUBXx7oC72MdrzjvBAYkgXWG_UNY8qPOUo"
                scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                         6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                         11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                         16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                         21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                         26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                         31: 5, 32: 5, 33: 5},
                                                        separate_pool=True, position_value=PositionValue.Overall)
            elif case == 6:
                # IndyCar Style
                sheet = "1HnIyOt6CKtXHbcQpUqcjPjAjqSyRc0hO3z6d0i9jTjc"
                scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                         6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                         11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                         16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                         21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                         26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                         31: 5, 32: 5, 33: 5},
                                                        separate_pool=True, position_value=PositionValue.Class)

            # Let's give points for these as well, default is 0 points
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 0
            scoring.most_laps_lead = 0

            # Ignore practice races
            season.add_practice_sessions([1, 2])

            if scoring.handicap:
                season.num_drops = 0
                season.add_group_rule(Group.Pro, GroupRules(0, 199, 0))
                season.add_google_sheet("1bjNJevXmU3godoJuPZjHnMHWdwdLmMimxcdOm38XsBk", {Group.Pro: "Drivers"})
            else:
                # Set up our grouping rules per season
                season.add_group_rule(Group.Pro, GroupRules(0, 99, 2))
                season.add_group_rule(Group.Am, GroupRules(100, 199, 2))
                season.add_google_sheet(sheet, {Group.Pro: "Pro Drivers", Group.Am: "Am Drivers"})

            # Apply Penalties
            season.add_time_penalty(2, 310239, 10)
            season.add_time_penalty(6, 189468, 10)
            season.add_time_penalty(7, 85279, 5)
            season.add_time_penalty(10, 71668, 5)

        if opts.season == 7 or opts.season is None:
            # Season 7
            season = cfg.get_season(7)
            season.active = True  # Use this to use current league assigned numbers for all cars instead of race numbers
            season.sort_by = SortBy.Earned
            # Separate point pool between classes and use overall position value relative to class winner
            season_7_scoring_mode = 2
            if season_7_scoring_mode == 1:
                sheet = "1SZSIvtBNU4n94vmcQFFTNErxr6uUVKz9lHVfySHWxFI"
                scoring = season.set_assignment_scoring({1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                         6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                         11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                         16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                         21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                         26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                         31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                         36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                         41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                         46: 1},
                                                        separate_pool=True, position_value=PositionValue.Overall)
                season.add_group_rule(Group.Pro, GroupRules(0, 99, 0))
                season.add_group_rule(Group.Ch, GroupRules(100, 199, 2))
                season.add_group_rule(Group.Am, GroupRules(200, 299, 2))
                season.add_google_sheet(sheet,
                                        {Group.Pro: "Pro Drivers", Group.Ch: "Ch Drivers", Group.Am: "Am Drivers"})
            elif season_7_scoring_mode == 2:
                sheet = "1SZSIvtBNU4n94vmcQFFTNErxr6uUVKz9lHVfySHWxFI"
                scoring = season.set_linear_decent_scoring(40, hcp=False)
                season.add_group_rule(Group.Pro, GroupRules(0, 299, 0))
                season.add_google_sheet(sheet, {Group.Pro: "All Drivers"})
            # Let's give points for these as well, default is 0 points
            scoring.pole_position = 1
            scoring.laps_lead = 1
            scoring.fastest_lap = 1
            scoring.most_laps_lead = 0

            # Ignore practice races
            season.add_practice_sessions([1, 2, 3])

            # Apply Penalties
            season.add_time_penalty(1, 459211, 10)

        # Save our league configuration to a json file.
        # Convert the LeagueConfiguration class to a python dict
        d = cfg.as_dict()  # Use this to work with data in a native python format instead of our classes
        # Dump the dict to json
        with open("configuration.json", 'w') as fp:
            json.dump(d, fp, indent=2)

        testing = True
        if testing:
            # Testing that our serialization is consistent
            r = open('configuration.json')
            d = json.load(r)
            cfg = LeagueConfiguration.from_dict(d)
            d = cfg.as_dict()

            with open("configuration2.json", 'w') as fp:
                json.dump(d, fp, indent=2)

        # Let's just fetch and score season 5
        # If you do not provide a season array, all seasons will be pulled and scored
        lg = cfg.fetch_and_score_league(opts.username, opts.password, [opts.season])

        # print_debug_stats(league, 120570)
        # print_debug_stats(league, 609455)

    print("Writing league to "+str(opts.league_filename))
    # Convert the League class to a python dict
    d = lg.as_dict()  # Use this if you would rather work with data in a native python format instead of our classes
    # Dump the dict to json
    with open(opts.league_filename, 'w') as fp:
        json.dump(d, fp, indent=2)

    # Push our results up to our sheets
    if opts.credentials.exists():
        try:
            cfg.push_results_to_sheets(lg, opts.credentials)
        except Exception as e:
            print("Failed to upload to google sheets: %s", e)
            if "Token" in str(e) and "expired" in str(e):
                # if this craps out about an expired token, I will need to delete your authorized_user.json file
                # ex. C:\Users\aaron.bray\AppData\Roaming\gspread\authorized_user.json
                # The user authorization token you get only lasts 7 days
                # Then you can rerun the program
                authorized_user_file = Path(os.getenv('APPDATA')+"/gspread/authorized_user.json")
                print("I have deleted your google sheets authorization file: " + str(authorized_user_file))
                print("Please select your gmail login in your browser again")
                authorized_user_file.unlink()
                cfg.push_results_to_sheets(lg, opts.credentials)
                # TODO change up the auth type so we don't need to do this
    else:
        print("Could not find credentials file. Not pushing to sheets.")





