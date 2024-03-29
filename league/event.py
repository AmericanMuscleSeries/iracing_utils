# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import sys
import time
import logging
import textwrap
import pandas as pd
import dataframe_image as dfi
from league.markdown import *
from league.league import League
from league.objects import Event
from iracingdataapi.client import irDataClient

_ams_logger = logging.getLogger('ams')


def list_events(username: str, password: str, year: int):
    idc = irDataClient(username, password)
    ir_series_stats = idc.series_stats()
    for ir_series in ir_series_stats:
        if ir_series["seasons"][0]["season_year"] == 2024:
            print(ir_series["series_name"] + "-" + ir_series["category"])


def pull_event(username: str, password: str, name: str, log: bool = False) -> Event:
    idc = irDataClient(username, password)
    ir_series_stats = idc.series_stats()
    event_series = None
    for ir_series in ir_series_stats:
        if ir_series["series_name"] == name and ir_series["seasons"][0]["season_year"] == 2024:
            event_series = ir_series

    if event_series is None:
        _ams_logger.error("Unable to find series: " + name)
        return None
    ir_races = idc.result_season_results(event_series["seasons"][0]["season_id"], 5)

    # Grab all the event data we need from iracing
    _ams_logger.info(f"Pulling {name} data from iracing...")
    splits = []
    for ir_result in ir_races["results_list"]:
        # Get the event race result
        ir_subsession = idc.result(subsession_id=ir_result["subsession_id"])["session_results"]
        ir_race_results = None
        for ir_event in ir_subsession:
            if ir_event["simsession_type"] == 6:
                ir_race_results = ir_event
        if ir_race_results is None:
            _ams_logger.error("Session " + ir_result["subsession_id"] + " did not have a race.")
            continue
        splits.append((ir_result["event_strength_of_field"], ir_result, ir_race_results))

    event = Event(name)
    event._is_multiclass = len(event_series["seasons"][0]["car_classes"]) > 1
    event._num_splits = len(splits)
    # Sort splits by sof
    splits.sort(key=lambda tup: tup[0], reverse=True)
    _ams_logger.info("There were " + str(event.num_splits) + " splits.")

    split = 0
    pull_team_roster = False

    for sof, ir_result, ir_race_results in splits:
        split += 1
        num_teams = len(ir_race_results["results"])
        _ams_logger.info(f"Pulling the members from {num_teams} teams for split {split}")
        result = event.add_result(split, ir_result["event_strength_of_field"],
                                  "https://members.iracing.com/membersite/member/EventResult.do?subsessionid=" +
                                  str(ir_result["subsession_id"]))
        for car_class in ir_result["car_classes"]:
            result.add_category(car_class["short_name"], car_class["strength_of_field"])
        if log:
            _ams_logger.info(f"SOF: {result.sof}")
        for ir_team_result in ir_race_results["results"]:
            result.count_cars_and_laps(ir_team_result["car_class_short_name"], ir_team_result["laps_complete"])
            team = result.add_team(ir_team_result["team_id"],
                                   ir_team_result["car_class_short_name"],
                                   ir_team_result["display_name"],
                                   ir_team_result["car_name"])
            team._reason_out = ir_team_result["reason_out"]
            team._finish_position = ir_team_result["finish_position"]+1
            team._finish_position_in_class = ir_team_result["finish_position_in_class"]+1
            team._total_laps_complete = ir_team_result["laps_complete"]
            team._total_incidents = ir_team_result["incidents"]
            if log:
                _ams_logger.info(f"\tTeam: {team.name}, Class: {team.category}, Car: {team.car}")
            # Add team members
            # Only drivers that have driven laps are listed here,
            for ir_team_member in ir_team_result["driver_results"]:
                driver = team.add_driver(ir_team_member["cust_id"], ir_team_member["display_name"])
                driver._old_irating = ir_team_member["oldi_rating"]
                driver._new_irating = ir_team_member["newi_rating"]
                # if irating is < 0, pretty sure that means that car Did Not Start
                driver._total_laps_complete = ir_team_member["laps_complete"]
                driver._total_laps_lead = ir_team_member["laps_lead"]
                driver._total_incidents = ir_team_member["incidents"]
                if log:
                    team.get_driver()
                    _ams_logger.info(f"\t\t{driver.name} : {driver.cust_id}")
            if pull_team_roster:
                # If they crash and quit before all scheduled drivers drove a lap,
                # They will not be in the driver list
                # So we also pull the official team member list, which can be very long...
                time.sleep(0.1)  # So many calls makes iracing mad...
                ir_team = idc.team(ir_team_result["team_id"])
                for ir_member in ir_team["roster"]:
                    team.add_member(ir_member["cust_id"], ir_member["display_name"])
    return event


def fetch_and_report_league(event: Event, league: League, img_name_postfix: str = ""):
    fetch_and_report_drivers(event, league.members.keys(), img_name_postfix)


def fetch_and_report_drivers(event: Event, drivers: list, img_name_postfix: str = ""):
    # Written to allow a driver to participate in more than 1 team in the same split
    data = []
    if event.is_multiclass:
        headings = [event.name,
                    f"Split / {event.num_splits}",
                    "Team",
                    "#Drivers",
                    "Class",
                    "Car",
                    "Finish (Class)",
                    "Finish (Overall)",
                    "Laps Driven",
                    "Laps Behind (Class)",
                    "Laps Behind (Overall)",
                    "Final",
                    "iRating"
                    ]
        # Map the indexes in data for each heading
        fields = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    else:
        headings = [event.name,
                    f"Split / {event.num_splits}",
                    "Team",
                    "#Drivers",
                    "Car",
                    "Finish",
                    "Laps Driven",
                    "Laps Behind",
                    "Final",
                    "iRating"
                    ]
        # Map the indexes in data for each heading
        fields = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    for cust_id in drivers:
        split_results = event.get_driver_team_results(cust_id)
        for split, teams in split_results.items():
            result = event.get_result(split)
            for team in teams:
                driver = team.get_driver(cust_id)
                total_cars = result.total_cars
                total_class_cars = result.num_cars(team.category)
                laps_behind_class_leader = result.num_laps(team.category) - team.total_laps_complete
                laps_behind_race_leader = result.total_laps - team.total_laps_complete

                final_ir_sign = "" if driver.new_irating < driver.old_irating else "+"
                final_ir = " "+str(driver.new_irating)+" ("+final_ir_sign+str(driver.new_irating-driver.old_irating)+")"
                if event.is_multiclass:
                    data.append((f"{driver.name} ({driver.old_irating})",
                                 split,
                                 team.name,
                                 team.num_drivers,
                                 f"{team.category} ({result.strength_of_category(team.category)})",
                                 team.car,
                                 f"{team.finish_position_in_class}/{total_class_cars}",
                                 f"{team.finish_position}/{total_cars}",
                                 f"{driver.total_laps_complete}/{team.total_laps_complete}",
                                 laps_behind_class_leader,
                                 laps_behind_race_leader,
                                 team.reason_out,
                                 final_ir
                                 ))
                else:
                    data.append((f"{driver.name} ({driver.old_irating})",
                                 split,
                                 team.name,
                                 team.num_drivers,
                                 team.car,
                                 f"{team.finish_position}/{total_cars}",
                                 f"{driver.total_laps_complete}/{team.total_laps_complete}",
                                 laps_behind_race_leader,
                                 team.reason_out,
                                 final_ir
                                 ))
    # Sort our results
    data = sorted(data, key=lambda element: (element[1], element[4]))
    align = []
    for i in range(len(fields)):
        align.append(('^', '^'))
    table(sys.stdout, data, fields, headings, align)

    # Write out table as png
    wrapped_headers = ["<br>".join(textwrap.wrap(h, width=20)) for h in headings]
    df = pd.DataFrame(data, columns=wrapped_headers)
    df.style.format(escape="html")  # Actually wrap column names
    df_styler = df.style.hide(axis="index") \
        .set_properties(subset=wrapped_headers[1:], **{'text-align': 'center'}) \
        .set_properties(subset=[wrapped_headers[0]], **{'text-align': 'left'}, overwrite=False) \
        .set_properties(**{'border': '1px black solid'})
    df_styler.set_table_styles([
        {'selector': 'th.col_heading', 'props': 'text-align: center; border: 1px black solid;'},
    ], overwrite=False)
    img_filename = f"{event.name}{img_name_postfix}.png"
    _ams_logger.info(f"Writing {img_filename}")
    dfi.export(df_styler, img_filename)
