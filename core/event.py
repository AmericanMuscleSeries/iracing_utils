# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import dataframe_image as dfi
import json
import logging
import pandas as pd
import pickle
import sys
import time

from pathlib import Path

from iracingdataapi.client import irDataClient

from core.markdown import *
from core.objects import Event, EventTeam

_logger = logging.getLogger('log')


def list_events(idc: irDataClient, year: int):
    ir_series_stats = idc.series_stats()
    for ir_series in ir_series_stats:
        print(f"{ir_series['series_name']}")
        # if "THE" in ir_series['series_name']:
        #    print("here")
        for season in ir_series["seasons"]:
            if season["season_year"] == year:
                print(f"\t{season['season_name']}")


def pull_event(idc: irDataClient, series_name: str, year: int, detailed_team: bool = False, log: bool = False) -> Event:

    event_ir_directory = Path(f"./events/{year}_{series_name}_iR")
    teams_directory = event_ir_directory / "teams"
    teams_directory.mkdir(exist_ok=True, parents=True)

    # Find the event
    ir_series_stats = idc.series_stats()
    event_season = None
    for ir_series in ir_series_stats:
        if ir_series["series_name"] == series_name:
            for season in ir_series["seasons"]:
                if season["season_year"] == year:
                    event_season = season
                    break
    if event_season is None:
        _logger.error(f"Unable to find series: {series_name} in year {year}")
        return None

    # Grab all the event data we need from iracing, cache for quicker rerunning
    ir_races = idc.result_season_results(event_season["season_id"], 5)
    event_splits_filename = event_ir_directory / "splits.json"
    if not event_splits_filename.exists():
        _logger.info(f"Pulling {series_name} data from iracing...")
        splits = []
        for ir_result in ir_races["results_list"]:
            # Get the event race result
            ir_subsession = idc.result(subsession_id=ir_result["subsession_id"])["session_results"]
            ir_race_results = None
            for ir_event in ir_subsession:
                if ir_event["simsession_type"] == 6:
                    ir_race_results = ir_event
            if ir_race_results is None:
                _logger.error("Session " + ir_result["subsession_id"] + " did not have a race.")
                continue
            splits.append((ir_result["event_strength_of_field"], ir_result, ir_race_results))
        # Sort splits by sof
        splits.sort(key=lambda tup: tup[0], reverse=True)
        with open(event_splits_filename, 'w') as fp:
            json.dump(splits, fp, indent=2)
    else:
        with open(event_splits_filename) as fp:
            splits = json.load(fp)

    event = Event(series_name, year)
    event._is_multiclass = len(event_season["car_classes"]) > 1
    event._num_splits = len(splits)
    _logger.info(f"There were {len(splits)} splits.")

    split = 0
    for sof, ir_result, ir_race_results in splits:
        split += 1
        num_teams = len(ir_race_results["results"])
        _logger.info(f"Pulling results for split {split} that had {num_teams} teams")
        result = event.add_result(split, ir_result["event_strength_of_field"], ir_result["subsession_id"])

        for car_class in ir_result["car_classes"]:
            result.add_category(car_class["short_name"], car_class["strength_of_field"])
        if log:
            _logger.info(f"SOF: {result.sof}")
        for ir_team_result in ir_race_results["results"]:
            result.count_cars_and_laps(ir_team_result["car_class_short_name"], ir_team_result["laps_complete"])
            team = result.add_team(ir_team_result["team_id"] if "team_id" in ir_team_result else ir_team_result["cust_id"],
                                   ir_team_result["car_class_short_name"],
                                   ir_team_result["display_name"],
                                   ir_team_result["car_name"],
                                   int(ir_team_result["livery"]["car_number"]))
            team._reason_out = ir_team_result["reason_out"]
            team._finish_position = ir_team_result["finish_position"]+1
            team._finish_position_in_class = ir_team_result["finish_position_in_class"]+1
            team._total_laps_complete = ir_team_result["laps_complete"]
            team._total_incidents = ir_team_result["incidents"]

            if log:
                _logger.info(f"\tTeam: {team.name}, Class: {team.category}, Car: {team.car}")
            # Add team members
            ir_team_members = ir_team_result["driver_results"] if "driver_results" in ir_team_result \
                else [ir_team_result]
            # Only drivers that have driven laps are listed here,
            for ir_team_member in ir_team_members:
                driver = team.add_driver(ir_team_member["cust_id"], ir_team_member["display_name"])
                driver._old_irating = ir_team_member["oldi_rating"]
                driver._new_irating = ir_team_member["newi_rating"]
                # if irating is < 0, pretty sure that means that car Did Not Start
                driver._total_laps_complete = ir_team_member["laps_complete"]
                driver._total_lead_a_lap = ir_team_member["laps_lead"]
                driver._total_incidents = ir_team_member["incidents"]
                if log:
                    team.get_driver()
                    _logger.info(f"\t\t{driver.name} : {driver.cust_id}")

            if detailed_team and "driver_results" in ir_team_result:
                # If they crash and quit before all scheduled drivers drove a lap,
                # They will not be in the driver list
                # So we also pull the official team member list, which can be very long...
                # So we cache team members to a separate file, so we don't have to pull as much
                save_json = False
                team_filename = teams_directory / f"{ir_team_result['team_id']}.json"
                if team_filename.exists():
                    with open(team_filename) as fp:
                        ir_team = json.load(fp)
                else:
                    save_json = True
                    time.sleep(0.01)  # So many calls makes iracing mad...
                    _logger.info(f"Pulling team members for {ir_team_result['display_name']}")
                    ir_team = idc.team(ir_team_result["team_id"])
                    ir_team = {k: ir_team[k] for k in ["owner_id", "roster"] if k in ir_team}
                    ir_team["display_name"] = ir_team_result['display_name']

                team._owner = ir_team["owner_id"]
                if not team._owner:
                    _logger.error(f"Team {ir_team_result['display_name']} has no owner?")
                for ir_member in ir_team["roster"]:
                    if save_json:
                        del ir_member["helmet"]
                    team.add_member(ir_member["cust_id"], ir_member["display_name"])

                if save_json:
                    with open(team_filename, 'w') as fp:
                        json.dump(ir_team, fp, indent=2)
    return event


def add_lap_data(idc: irDataClient, event: Event, splits: list):

    event_ir_directory = Path(f"./events/{event.year}_{event.name}_iR")
    laps_directory = event_ir_directory / "laps"
    laps_directory.mkdir(exist_ok=True, parents=True)

    for split in splits:
        result = event.get_result(split)

        ir_laps_filename = laps_directory / f"{result.subsession_id}.pkl"
        if not ir_laps_filename.exists():
            ir_lap_chart = idc.result_lap_chart_data(subsession_id=result.subsession_id)
            with open(ir_laps_filename, 'wb') as fp:
                pickle.dump(ir_lap_chart, fp)
        else:
            with open(laps_directory / f"{result.subsession_id}.pkl", 'rb') as fp:
                ir_lap_chart = pickle.load(fp)
        for ir_race_lap in ir_lap_chart:
            team = result.get_team(ir_race_lap["group_id"])
            lap = team.add_lap()
            lap._cust_id = ir_race_lap["cust_id"]
            lap._position = ir_race_lap["lap_position"]
            lap._number = ir_race_lap["lap_number"]
            lap._time = ir_race_lap["lap_time"]
            lap._session_time = ir_race_lap["session_time"]


def _create_report(basename: Path, data, fields, headings, widths=None):
    if widths is None:
        widths = []
    align = []
    for i in range(len(fields)):
        align.append(('^', '^'))
    table(sys.stdout, data, fields, headings, align)

    # Write out table as png
    wrapped_headers = headings  # ["<br>".join(textwrap.wrap(h, width=20)) for h in headings]
    df = pd.DataFrame(data, columns=wrapped_headers)
    df.style.format(escape="html")  # Actually wrap column names
    df_styler = df.style.hide(axis="index") \
        .set_properties(subset=wrapped_headers[1:], **{'text-align': 'center'}) \
        .set_properties(subset=[wrapped_headers[0]], **{'text-align': 'left'}) \
        .set_properties(**{'border': '1px black solid'})
    for i, width in enumerate(widths):
        df_styler = df_styler.set_properties(subset=wrapped_headers[i], **{'width': width})
    df_styler.set_table_styles(table_styles=[
        {'selector': 'th.col_heading', 'props': 'text-align: center; border: 1px black solid;'},
    ], overwrite=False)
    img_filename = str(basename) + ".png"
    _logger.info(f"Writing {img_filename}")
    dfi.export(df_styler, img_filename, table_conversion='playwright', dpi=300, max_rows=200)


def report_splits(event: Event, output_dir: Path = "./"):
    data = []
    owners = {}
    headings = [f"Split / {event.num_splits}",
                "SOF",
                "Classes",
                "Class Strength",
                "Class Count",
                "Class Laps",
                "Podium<br> team (# drivers) [owner]"
                ]
    # Map the indexes in data for each heading
    fields = [0, 1, 2, 3, 4, 5, 6]

    def get_team_description(team: EventTeam):
        #if team.owner not in owners:
        #    owner = idc.member_profile(team.owner)
        #    owners[team.owner] = owner['member_info']['display_name']
        return f"{team.name} ({team.num_drivers})"# [{owners[team.owner]}]"

    _logger.info(f"There were {event.num_splits} splits in this event")
    for num in range(event.num_splits):
        r = event.get_result(num+1)
        _logger.info(f"Pulling Split {num+1}")

        e_cat = ""
        e_soc = ""
        e_count = ""
        e_laps = ""
        e_podium = ""
        for c in r.get_categories():
            e_cat += f"{c}<br>"
            soc = r.strength_of_category(c)
            e_soc += f"{soc}<br>"
            count = r.num_cars(c)
            e_count += f"{count}<br>"
            laps = r.num_laps(c)
            e_laps += f"{laps}<br>"
            order = r.get_finish_order(c)
            p1 = get_team_description(order[1])
            p2 = get_team_description(order[2])
            p3 = get_team_description(order[3])
            e_podium += f"{p1}<br>{p2}<br>{p3}<br><br>"
        data.append((num+1,
                     r.sof,
                     e_cat,
                     e_soc,
                     e_count,
                     e_laps,
                     e_podium))

    output_dir.mkdir(exist_ok=True)
    _create_report(basename=output_dir / f"{event.year}_{event.name}_Splits", data=data, fields=fields, headings=headings)


def fetch_and_report_drivers(event: Event, drivers: list, img_name_postfix: str = "", output_dir: Path = "./"):
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
                    "Incidents",
                    "iRating"
                    ]
        # Map the indexes in data for each heading
        fields = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
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
                    "Incidents",
                    "iRating"
                    ]
        # Map the indexes in data for each heading
        fields = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
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
                                 f"{team.name} ({team.owner})",
                                 team.num_drivers,
                                 f"{team.category} ({result.strength_of_category(team.category)})",
                                 team.car,
                                 f"{team.finish_position_in_class}/{total_class_cars}",
                                 f"{team.finish_position}/{total_cars}",
                                 f"{driver.total_laps_complete}/{team.total_laps_complete}",
                                 laps_behind_class_leader,
                                 laps_behind_race_leader,
                                 team.reason_out,
                                 driver.total_incidents,
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
                                 driver.total_incidents,
                                 final_ir
                                 ))
    # Sort our results
    data = sorted(data, key=lambda element: (element[1], element[4]))
    output_dir.mkdir(exist_ok=True)
    _create_report(basename=output_dir/f"{event.year}_{event.name}{img_name_postfix}",
                   data=data, fields=fields, headings=headings)


def report_owner_events(idc: irDataClient, owner_id: int, event: Event, output_dir: Path):
    if owner_id not in event.team_owners:
        _logger.info(f"Team owner, {owner_id}, did not have any teams participate in provided events")
        return

    data = []
    owner = idc.member_profile(owner_id)
    owner_name = owner['member_info']['display_name']
    _logger.info(f"Gather events from team owner: {owner_name}")
    headings = [owner['member_info']['display_name'],
                f"Split",
                "Team",
                "Drivers<br>(laps) (inc) (ir)",
                "Class",
                "Car",
                "Finish (Class)",
                "Laps Behind (Class)",
                "Finish (Overall)",
                "Laps Behind (Overall)",
                "Final"
                ]
    widths = ["200",
              "85",
              "600",
              "1600",
              "400",
              "300",
              "50",
              "50",
              "50",
              "50",
              "50"]
    # Map the indexes in data for each heading
    fields = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    for team_id in event.team_owners[owner_id]:
        team_results = event.get_team_results(team_id)
        for split, team_result in team_results.items():
            event_split = event.get_result(split)
            # Generate driver list
            drivers = ""
            for driver_id, driver_stats in team_result._drivers.items():
                drivers += (f"{driver_stats.name} "
                            f"{driver_stats.total_laps_complete}/{team_result.total_laps_complete} "
                            f"{driver_stats.total_incidents}x "
                            f"{driver_stats.new_irating}({driver_stats.new_irating-driver_stats.old_irating})<br>")
            data.append((f"{event.name}",
                         f"{split}/{event.num_splits}",
                         team_result.name,
                         f"{drivers}",
                         f"{team_result.category} ({event_split.strength_of_category(team_result.category)})",
                         team_result.car,
                         f"{team_result.finish_position_in_class}/{event_split.num_cars(team_result.category)}",
                         f"{event_split.num_laps(team_result.category) - team_result.total_laps_complete}",
                         f"{team_result.finish_position}/{event_split.total_cars}",
                         f"{event_split.total_laps - team_result.total_laps_complete}",
                         team_result.reason_out
                         ))
    _create_report(basename=output_dir/f"{owner_name}_{event.year}-{event.name}",
                   data=data, fields=fields, headings=headings, widths=widths)
