# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import gspread
import argparse
from operator import itemgetter

from league.objects import League, Group

_ams_logger = logging.getLogger('ams')


class GDrive:
    __slots__ = ["_gc",
                 "_results_key", "_results_xls", "_result_sheets",
                 "_driver_key", "_drivers_xls", "_driver_sheets"]

    def __init__(self, credentials_filename: str):
        self._gc = None
        self._results_key = None
        self._results_xls = None
        self._result_sheets = dict()
        self._driver_key = None
        self._drivers_xls = None
        self._driver_sheets = dict()
        self._gc = gspread.oauth(
            credentials_filename=credentials_filename)

    def connect_to_results(self, key: str, sheets: dict) -> None:
        self._results_key = key
        self._results_xls = self._gc.open_by_key(self._results_key)
        for group, sheet in sheets.items():
            self._result_sheets[group] = self._results_xls.worksheet(sheet)

    def push_results(self, lg: League, season: int, groups: list) -> int:
        count = 0 # Keeping track of sheet update calls, you only get 60/min with free projects
        # gsheets takes a list(list())
        season_values = list()

        dates = list()
        tracks = list()

        season = lg.get_season(season)
        for group in groups:
            season_values.clear()

            dates.clear()
            tracks.clear()
            for race_number in range(len(season.races)):
                race = season.get_race(race_number + 1)
                track_name = race.track
                if track_name.count(' ') > 2:
                    split_at = track_name.find(' ', track_name.find(' ') + 1)
                    track_name = race.track[:split_at] + '\n' + race.track[split_at:]
                for i in range(11):
                    tracks.append(track_name)
                    dates.append(race.date)
                date_values = list().append(dates)
                track_values = list().append(tracks)
            date_values = list().append(dates)
            track_values = list().append(tracks)
            self._result_sheets[group].update(range_name="M2", values=date_values)
            self._result_sheets[group].update(range_name="M3", values=track_values)
            count += 2

            for cust_id, driver in season.drivers.items():
                if driver.group != group:
                    continue
                row = list()  # Make a list per driver row
                row.append(driver.name)
                row.append(driver.car_number)
                row.append(driver.points)
                row.append(driver.total_races)
                row.append(driver.total_incidents)
                row.append(driver.total_pole_positions)
                row.append(driver.total_laps_complete)
                row.append(driver.total_laps_lead)
                row.append(driver.total_fastest_laps)
                row.append(driver.mu)
                row.append(driver.sigma)

                for race_number in range(len(season.races)):
                    result = season.get_race(race_number+1).get_result(cust_id)
                    if result is None:
                        for i in range(11):
                            row.append("")
                    else:
                        row.append(result.start_position)
                        row.append(result.finish_position)
                        row.append(result.points)
                        row.append("Y" if result.pole_position else "")
                        row.append("Y" if result.laps_lead > 0 else "")
                        row.append("Y" if result.fastest_lap else "")
                        row.append(result.incidents)
                        row.append(result.laps_completed)
                        row.append(result.laps_lead)
                        row.append(result.mu)
                        row.append(result.sigma)
                season_values.append(row)

            season_values = sorted(season_values, key=itemgetter(2), reverse=True)
            # Pad the rest with blanks
            max_racers = 35
            if len(season_values) < max_racers:
                for extra_rows in range(max_racers - len(season_values)):
                    row = list()
                    for i in range(33):
                        row.append("")
                    season_values.append(row)
            # Push to the sheets
            self._result_sheets[group].update(range_name="B5", values=season_values)
            count += 1
        return count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.getLogger('ams').setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="Pull league results and rack and stack them for presentation")
    parser.add_argument(
        "league",
        type=str,
        help="League json file."
    )
    # opts = parser.parse_args()

    # TODO properly utilize arguments

    r = open("./league.json")
    d = json.load(r)
    league = League.from_dict(d)

    gdrive = GDrive("./credentials.json")
    gdrive.connect_to_results("1jlybjNg8sQGFuwSPrnNvQRq5SrIX73QUbISNVIp3Clk",
                              {Group.Pro: "Pro Drivers", Group.Am: "Am Drivers"})
    gdrive.push_results(league, 5, [Group.Pro, Group.Am])
