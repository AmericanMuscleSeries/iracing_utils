# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
from enum import Enum

from google.protobuf import json_format, text_format
from league.objects_pb2 import *

_ams_logger = logging.getLogger('ams')


class Group(Enum):
    Unknown = 0
    Pro = 1
    Am = 2


class SerializationFormat(Enum):
    JSON = 0
    BINARY = 1
    VERBOSE_JSON = 2
    TEXT = 3


class League:
    __slots__ = ["members", "seasons"]

    def __init__(self):
        self.members = dict()
        self.seasons = dict()

    def as_dict(self):
        string = serialize_league_to_string(self, SerializationFormat.JSON)
        return json.loads(string)

    @staticmethod
    def from_dict(d: dict):
        string = json.dumps(d)
        return serialize_league_from_string(string, SerializationFormat.JSON)

    def add_member(self, cust_id: int, name: str, nickname: str):
        if cust_id not in self.members:
            self.members[cust_id] = Member(cust_id, name, nickname)
        else:
            _ams_logger.warning("Member " + name + " already exists.")
        return self.members[cust_id]

    def get_member(self, cust_id: int):
        if cust_id not in self.members:
            return None
        return self.members[cust_id]

    def add_season(self, number: int):
        if number not in self.seasons:
            self.seasons[number] = Season(number)
        else:
            _ams_logger.warning("Season " + str(number) + " already exists.")
        return self.seasons[number]

    def get_season(self, number: int):
        if number not in self.seasons:
            return None
        return self.seasons[number]


class Member:
    __slots__ = ["_cust_id",
                 "_name",
                 "_nickname"]

    def __init__(self, cust_id: int, name: str, nickname: str):
        self._cust_id = cust_id
        self._name = name
        if nickname is None:
            self._nickname = ""
        else:
            self._nickname = nickname

    @property
    def cust_id(self):
        return self._cust_id

    @property
    def name(self):
        return self._name

    @property
    def nickname(self):
        return self._nickname


class Season:
    __slots__ = ["_number",
                 "drivers",
                 "races"]

    def __init__(self, number: int):
        self._number = number
        self.drivers = dict()
        self.races = dict()

    @property
    def number(self):
        return self._number

    def add_driver(self, cust_id: int):
        if cust_id not in self.drivers:
            driver = Driver(cust_id)
            driver._points = 0
            driver._total_fastest_laps = 0
            driver._total_incidents = 0
            driver._total_laps_complete = 0
            driver._total_laps_lead = 0
            driver._total_pole_positions = 0
            driver._total_races = 0
            self.drivers[cust_id] = driver
        return self.drivers[cust_id]

    def get_driver(self, cust_id: int):
        if cust_id not in self.drivers:
            return None
        return self.drivers[cust_id]

    def add_race(self, number: int, date: str, track: str):
        if number not in self.races:
            self.races[number] = Race(number, date, track)
        return self.races[number]

    def get_race(self, number: int):
        if number not in self.races:
            return None
        return self.races[number]


class Driver:
    __slots__ = ["_cust_id",
                 "_name",
                 "_car_number",  # Can change in season
                 "_group",  # Can change in season
                 "_points",
                 "_total_fastest_laps",
                 "_total_incidents",
                 "_total_laps_complete",
                 "_total_laps_lead",
                 "_total_pole_positions",
                 "_total_races",
                 "_mu", "_sigma"]

    def __init__(self, cust_id: int):
        self._cust_id = cust_id
        self._name = None
        self._car_number = None
        self._group = None
        self._points = None
        self._total_fastest_laps = None
        self._total_incidents = None
        self._total_laps_complete = None
        self._total_laps_lead = None
        self._total_pole_positions = None
        self._total_races = None
        self._mu = 25
        self._sigma = 0.83333

    @property
    def cust_id(self): return self._cust_id

    @property
    def name(self): return self._name

    @property
    def group(self): return self._group

    @property
    def car_number(self): return self._car_number

    @property
    def points(self): return self._points

    @property
    def total_fastest_laps(self): return self._total_fastest_laps

    @property
    def total_incidents(self): return self._total_incidents

    @property
    def total_laps_complete(self): return self._total_laps_complete

    @property
    def total_laps_lead(self): return self._total_laps_lead

    @property
    def total_pole_positions(self): return self._total_pole_positions

    @property
    def total_races(self): return self._total_races

    @property
    def mu(self): return self._mu

    @property
    def sigma(self): return self._sigma

    def set_car_number(self, car_number: int, group: Group):
        if self._car_number is None:
            self._car_number = car_number
            self._group = group
            return
        if self._car_number != car_number:
            _ams_logger.info("Updating car number from "+str(self.car_number)+" to "+str(car_number))
            self._car_number = car_number
            self._group = group


class GroupStats:
    __slots__ = ["_group",
                 "_num_drivers",
                 "_pole_position_driver",
                 "_pole_position",
                 "_fastest_lap_driver",
                 "_fastest_lap_time"]

    def __init__(self, group: Group):
        self._group = group
        self._num_drivers = 0
        self._pole_position_driver = None
        self._pole_position = 100
        self._fastest_lap_driver = None
        self._fastest_lap_time = 100

    def check_if_fastest_lap(self, cust_id: int, time_s: float):
        if time_s < self._fastest_lap_time:
            self._fastest_lap_time = time_s
            self._fastest_lap_driver = cust_id

    def check_if_pole_position(self, cust_id: int, position: int):
        if position < self._pole_position:
            self._pole_position = position
            self._pole_position_driver = cust_id

    @property
    def group(self): return self._group

    @property
    def num_drivers(self): return self._num_drivers

    @property
    def fastest_lap_driver(self): return self._fastest_lap_driver

    @property
    def fastest_lap_time(self): return self._fastest_lap_time

    @property
    def pole_position_driver(self): return self._pole_position_driver

    @property
    def pole_position(self): return self._pole_position


class Race:
    __slots__ = ["_number",
                 "_date",
                 "_track",
                 "stats",
                 "grid"]

    def __init__(self, number: int, date: str, track: str):
        self._number = number
        self._date = date
        self._track = track
        self.stats = dict()
        self.grid = dict()

    @property
    def number(self): return self._number

    @property
    def date(self): return self._date

    @property
    def track(self): return self._track

    def get_stats(self, group: Group):
        if group not in self.stats:
            self.stats[group] = GroupStats(group)
        return self.stats[group]

    def add_result(self, cust_id: int):
        if cust_id not in self.grid:
            result = Result(cust_id)
            self.grid[cust_id] = result
            return result
        return self.grid[cust_id]

    def get_result(self, cust_id: int):
        if cust_id not in self.grid:
            return None
        return self.grid[cust_id]


class Result:
    __slots__ = ["_cust_id",
                 "_pole_position",
                 "_fastest_lap",
                 "_start_position",
                 "_finish_position",
                 "_points",
                 "_interval",
                 "_incidents",
                 "_laps_completed",
                 "_laps_lead",
                 "_mu", "_sigma"]

    def __init__(self, cust_id: int):
        self._cust_id = cust_id
        self._pole_position = False
        self._fastest_lap = False
        self._start_position = None
        self._finish_position = None
        self._interval = None
        self._points = None
        self._incidents = None
        self._laps_completed = None
        self._laps_lead = None
        self._mu = 0
        self._sigma = 0

    @property
    def cust_id(self): return self._cust_id

    @property
    def pole_position(self): return self._pole_position

    @property
    def fastest_lap(self): return self._fastest_lap

    @property
    def start_position(self): return self._start_position

    @property
    def finish_position(self): return self._finish_position

    @property
    def interval(self): return self._interval

    @property
    def points(self): return self._points

    @property
    def incidents(self): return self._incidents

    @property
    def laps_completed(self): return self._laps_completed

    @property
    def laps_lead(self): return self._laps_lead

    @property
    def mu(self): return self._mu

    @property
    def sigma(self): return self._sigma


def serialize_league_to_string(src: League, fmt: SerializationFormat):
    dst = LeagueData()

    for cust_id, member in src.members.items():
        member_data = dst.Members[cust_id]
        member_data.Name = member.name
        if member.nickname is not None:
            member_data.Nickname = member.nickname

    for season_number, season in src.seasons.items():
        season_data = dst.Seasons[season_number]

        for cust_id, driver in season.drivers.items():
            driver_data = season_data.Drivers[cust_id]
            driver_data.Name = driver.name
            driver_data.CarNumber = driver.car_number
            driver_data.Group = driver.group.value
            driver_data.Points = driver.points
            driver_data.TotalFastestLaps = driver.total_fastest_laps
            driver_data.TotalIncidents = driver.total_incidents
            driver_data.TotalLapsComplete = driver.total_laps_complete
            driver_data.TotalLapsLead = driver.total_laps_lead
            driver_data.TotalPolePositions = driver.total_pole_positions
            driver_data.TotalRaces = driver.total_races
            driver_data.Mu = driver.mu
            driver_data.Sigma = driver.sigma


        for race_number, race in season.races.items():
            race_data = season_data.Races[race_number]
            race_data.Date = race.date
            race_data.Track = race.track

            for group, stats in race.stats.items():
                stats_data = GroupStatsData()
                stats_data.Group = stats.group.value
                stats_data.Count = stats.num_drivers
                stats_data.PolePositionDriver = stats.pole_position_driver
                stats_data.PolePosition = stats.pole_position
                stats_data.FastestLapDriver = stats.fastest_lap_driver
                stats_data.FastestLapTime = stats.fastest_lap_time
                race_data.GroupStats.append(stats_data)

            for cust_id, result in race.grid.items():
                results_data = race_data.Grid[cust_id]
                results_data.PolePosition = result.pole_position
                results_data.FastestLap = result.fastest_lap
                results_data.StartPosition = result.start_position
                results_data.FinishPosition = result.finish_position
                results_data.Points = result.points
                results_data.Interval = result.interval
                results_data.Incidents = result.incidents
                results_data.LapsCompleted = result.laps_completed
                results_data.LapsLead = result.laps_lead
                results_data.Mu = result.mu
                results_data.Sigma = result.sigma

    return json_format.MessageToJson(dst, True, True)


def serialize_league_from_string(src: str, fmt: SerializationFormat) -> League:
    league_data = LeagueData()
    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        json_format.Parse(src, league_data)
    elif fmt == SerializationFormat.TEXT:
        text_format.Parse(src, league_data)
    else:
        league_data.ParseFromString(src)
    dst = League()
    serialize_league_resource_from_bind(league_data, dst)
    return dst


def serialize_league_resource_from_bind(src: LeagueData, dst: League):
    for cust_id, member_data in src.Members.items():
        dst.add_member(cust_id, member_data.Name, member_data.Nickname)

    for season_num, season_data in src.Seasons.items():
        season = dst.add_season(season_num)
        for cust_id, driver_data in season_data.Drivers.items():
            driver = season.add_driver(cust_id)
            driver._name = driver_data.Name
            driver._group = Group(driver_data.Group)
            driver._car_number = driver_data.CarNumber
            driver._points = driver_data.Points
            driver._total_fastest_laps = driver_data.TotalFastestLaps
            driver._total_incidents = driver_data.TotalIncidents
            driver._total_laps_complete = driver_data.TotalLapsComplete
            driver._total_laps_lead = driver_data.TotalLapsLead
            driver._total_pole_positions = driver_data.TotalPolePositions
            driver._total_races = driver_data.TotalRaces
            driver._mu = driver_data.Mu
            driver._sigma = driver_data.Sigma

        for race_num, race_data in season_data.Races.items():
            race = season.add_race(race_num, race_data.Date, race_data.Track)

            for group_stats_data in race_data.GroupStats:
                stats = race.get_stats(group_stats_data.Group)
                stats._num_drivers = group_stats_data.Count
                stats._pole_position_driver = group_stats_data.Count
                stats._pole_position = group_stats_data.Count
                stats._fastest_lap_driver = group_stats_data.Count
                stats._fastest_lap_time = group_stats_data.Count

            for cust_id, result_data in race_data.Grid.items():
                result = race.add_result(cust_id)
                result._cust_id = cust_id
                result._pole_position = result_data.PolePosition
                result._fastest_lap = result_data.FastestLap
                result._start_position = result_data.StartPosition
                result._finish_position = result_data.FinishPosition
                result._points = result_data.Points
                result._interval = result_data.Interval
                result._incidents = result_data.Incidents
                result._laps_completed = result_data.LapsCompleted
                result._laps_lead = result_data.LapsLead
                result._mu = result_data.Mu
                result._sigma = result_data.Sigma


def print_debug_stats(lg: League, cust_id: int):
    print("Stats for " + lg.get_member(cust_id).nickname)
    for number, race in lg.get_season(5).races.items():
        result = race.get_result(cust_id)
        points = 0
        mu = 0
        sigma = 0
        if result is not None:
            points = result.points
            mu = result.mu
            sigma = result.sigma
        print("Race " + str(number) + " points: " + str(points) + " mu: " + str(mu) + " sigma: " + str(sigma))
