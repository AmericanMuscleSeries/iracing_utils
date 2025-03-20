# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.


import gspread
import logging

from abc import abstractmethod
from enum import Enum
from operator import itemgetter
from pathlib import Path

from core.objects import Driver, LeagueResult

_logger = logging.getLogger('log')


class SortBy(Enum):
    Earned = 0
    ForcedDrops = 1


class SheetsDisplay:
    __slots__ = ["_id", "sort_by"]

    def __init__(self, sheet_id: str):
        self._id = sheet_id
        self.sort_by = SortBy.ForcedDrops

    @property
    def id(self): return self._id

    @property
    @abstractmethod
    def num_race_cells(self): pass

    @property
    @abstractmethod
    def race_start_column(self): pass

    @abstractmethod
    def create_row(self, cust_id: int, driver: Driver, lgr: LeagueResult) -> list:
        pass


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

    @staticmethod
    def push_results_to_sheets(lg: LeagueResult, groups: list[str],
                               sheets_display: SheetsDisplay, credentials_filename: Path):
        gdrive = GDrive(str(credentials_filename))
        if sheets_display is None:
            _logger.warning(
                "Not pushing. No sheet specified to push to. Check your configuration.")
            return

        # TODO These two methods should probably be one
        gdrive.connect_to_results(sheets_display.id, groups)
        cnt = gdrive.push_results(lg,
                                  groups,
                                  sheets_display)
        _logger.info("Executed " + str(cnt) + " update calls")

    def connect_to_results(self, key: str, groups: list[str]) -> None:
        self._results_key = key
        self._results_xls = self._gc.open_by_key(self._results_key)
        for group in groups:  # Should be a tab for each group named the same thing
            self._result_sheets[group] = self._results_xls.worksheet(group)

    def push_results(self, lg: LeagueResult, groups: list, sheets_display: SheetsDisplay) -> int:
        count = 0  # Keeping track of sheet update calls, you only get 60/min with free projects
        # gsheets takes a list(list())
        season_values = list()

        dates = list()
        date_values = list()
        tracks = list()
        track_values = list()

        # How many cells of data for each race are we pushing?
        num_race_cells = sheets_display.num_race_cells

        for race_number in range(len(lg.races)):
            race = lg.get_race(race_number + 1)
            track_name = race.track
            if track_name.count(' ') > 2:
                split_at = track_name.find(' ', track_name.find(' ') + 1)
                track_name = race.track[:split_at] + '\n' + race.track[split_at:]
            for i in range(num_race_cells):
                tracks.append(track_name)
                dates.append(race.date)
        date_values.append(dates)
        track_values.append(tracks)

        for group in groups:
            season_values.clear()
            # Push Race Dates and Tracks
            self._result_sheets[group].update(range_name=f"{sheets_display.race_start_column}2", values=date_values)
            self._result_sheets[group].update(range_name=f"{sheets_display.race_start_column}3", values=track_values)
            count += 2

            for cust_id, driver in lg.drivers.items():
                if driver.group != group:
                    continue
                row = sheets_display.create_row(cust_id, driver, lg)
                season_values.append(row)

            sort_idx = 2 if sheets_display.sort_by == SortBy.Earned else 3
            season_values = sorted(season_values, key=itemgetter(sort_idx), reverse=True)
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
