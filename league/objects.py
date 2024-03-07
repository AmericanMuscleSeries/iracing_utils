# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
from enum import Enum
from collections import OrderedDict

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


class SortBy(Enum):
    Earned = 0
    ForcedDrops = 1


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

    def add_member(self, cust_id: int, name: str, nickname: str = None):
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

    def __init__(self, cust_id: int, name: str, nickname: str = None):
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
            driver._earned_points = 0
            driver._drop_points = 0
            driver._clean_driver_points = 0
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
                 "_old_irating",
                 "_new_irating",
                 "_car_number",  # Can change in season
                 "_group",  # Can change in season
                 "_earned_points",
                 "_drop_points",
                 "_clean_driver_points",
                 "_total_fastest_laps",
                 "_total_incidents",
                 "_total_laps_complete",
                 "_total_laps_lead",
                 "_total_pole_positions",
                 "_total_races",
                 "_mu", "_sigma"]

    def __init__(self, cust_id: int, name: str = None):
        self._cust_id = cust_id
        self._name = name
        self._old_irating = 0
        self._new_irating = 0
        self._car_number = None
        self._group = None
        self._earned_points = None
        self._drop_points = None
        self._clean_driver_points = None
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
    def old_irating(self): return self._old_irating

    @property
    def new_irating(self): return self._new_irating

    @property
    def group(self): return self._group

    @property
    def car_number(self): return self._car_number

    @property
    def earned_points(self): return self._earned_points

    @property
    def drop_points(self): return self._drop_points

    @property
    def clean_driver_points(self): return self._clean_driver_points

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
                 "_clean_driver_points",
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
        self._clean_driver_points = None
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
    def clean_driver_points(self): return self._clean_driver_points

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


class Event:
    __slots__ = ["_name", "_is_multiclass", "_num_splits", "_results"]

    def __init__(self, name: str):
        self._name = name
        self._num_splits = 0
        self._is_multiclass = None
        self._results = OrderedDict()

    def as_dict(self):
        string = serialize_event_to_string(self, SerializationFormat.JSON)
        return json.loads(string)

    @staticmethod
    def from_dict(d: dict):
        string = json.dumps(d)
        return serialize_event_from_string(string, SerializationFormat.JSON)

    @property
    def name(self): return self._name

    @property
    def num_splits(self): return self._num_splits

    @property
    def is_multiclass(self): return self._is_multiclass

    def add_result(self, split: int, sof: int, url: str):
        if split in self._results:
            # Two splits with the exact same sof!?!
            _ams_logger.error(f"There is already results for split {split}")
        result = EventResult(sof, url)
        self._results[split] = result
        return result

    def get_result(self, split: int):
        return self._results[split]

    def get_driver_team_results(self, cust_id: int):
        teams = {}
        for split, result in self._results.items():
            result_teams = result.get_driver_teams(cust_id)
            if len(result_teams) > 0:
                teams[split] = result_teams
        return teams


class EventResult:
    __slots__ = ["_sof", "_url", "_num_cars", "_num_laps", "_teams"]

    def __init__(self, sof: int, url: str):
        self._sof = sof
        self._url = url
        self._num_cars = {}
        self._num_laps = {}
        self._teams = {}

    def add_team(self, team_id: str, category: str, name: str, car: str):
        if team_id in self._teams:
            return self._teams[team_id]
        team = EventTeam(team_id, category, name, car)
        self._teams[team_id] = team
        return team

    def get_driver_teams(self, cust_id: int):
        teams = []
        for team_id, team in self._teams.items():
            driver = team.get_driver(cust_id)
            if driver is not None:
                teams.append(team)
        return teams

    def count_cars_and_laps(self, category: str, num_laps):
        if category not in self._num_cars:
            self._num_cars[category] = 0
        if category not in self._num_laps:
            self._num_laps[category] = 0

        self._num_cars[category] += 1
        if num_laps > self._num_laps[category]:
            self._num_laps[category] = num_laps

    @property
    def sof(self): return self._sof

    @property
    def url(self): return self._url

    def num_cars(self, category: str):
        return self._num_cars[category]

    @property
    def total_cars(self): return sum(self._num_cars.values())

    def num_laps(self, category: str):
        return self._num_laps[category]

    @property
    def total_laps(self):
        return max(self._num_laps.values())


class EventTeam:
    __slots__ = ["_team_id", "_category", "_name", "_car", "_reason_out",
                 "_finish_position", "_finish_position_in_class",
                 "_total_laps_complete", "_total_incidents",
                 "_drivers", "_members"]

    def __init__(self, team_id: str, category: str, name: str, car: str):
        self._team_id = team_id
        self._category = category
        self._name = name
        self._car = car
        self._reason_out = None
        self._finish_position = None
        self._finish_position_in_class = None
        self._total_laps_complete = 0
        self._total_incidents = 0
        self._drivers = dict()
        self._members = dict()

    def add_driver(self, cust_id: int, name: str) -> Driver:
        self.add_member(cust_id, name)
        if cust_id not in self._drivers:
            self._drivers[cust_id] = Driver(cust_id, name)
        else:
            _ams_logger.warning(f"Driver {cust_id} already exists.")
        return self._drivers[cust_id]

    def add_member(self, cust_id: int, name: str) -> None:
        if cust_id not in self._members:
            self._members[cust_id] = Member(cust_id, name)

    def get_driver(self, cust_id: int) -> Driver:
        if cust_id not in self._drivers:
            return None
        return self._drivers[cust_id]

    @property
    def name(self): return self._name

    @property
    def num_drivers(self): return len(self._drivers)

    @property
    def car(self): return self._car

    @property
    def category(self): return self._category

    @property
    def reason_out(self): return self._reason_out

    @property
    def finish_position(self): return self._finish_position

    @property
    def finish_position_in_class(self): return self._finish_position_in_class

    @property
    def total_incidents(self): return self._total_incidents

    @property
    def total_laps_complete(self): return self._total_laps_complete


def serialize_league_to_string(src: League, fmt: SerializationFormat) -> str:
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
            driver_data.OldRating = driver.old_irating
            driver_data.NewRating = driver.new_irating
            driver_data.CarNumber = driver.car_number
            driver_data.Group = driver.group.value
            driver_data.EarnedPoints = driver.earned_points
            driver_data.DropPoints = driver.drop_points
            driver_data.CleanDriverPoints = driver.clean_driver_points
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
                results_data.CleanDriverPoints = result.clean_driver_points
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
    serialize_league_data_from_bind(league_data, dst)
    return dst


def serialize_league_data_from_bind(src: LeagueData, dst: League):
    for cust_id, member_data in src.Members.items():
        dst.add_member(cust_id, member_data.Name, member_data.Nickname)

    for season_num, season_data in src.Seasons.items():
        season = dst.add_season(season_num)
        for cust_id, driver_data in season_data.Drivers.items():
            driver = season.add_driver(cust_id)
            driver._name = driver_data.Name
            driver._old_irating = driver.OldRating
            driver._new_irating = driver.NewRating
            driver._group = Group(driver_data.Group)
            driver._car_number = driver_data.CarNumber
            driver._earned_points = driver_data.EarnedPoints
            driver._drop_points = driver_data.DropPoints
            driver._clean_driver_points = driver.CleanDriverPoints
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
                result._clean_driver_points = result_data.CleanDriverPoints
                result._interval = result_data.Interval
                result._incidents = result_data.Incidents
                result._laps_completed = result_data.LapsCompleted
                result._laps_lead = result_data.LapsLead
                result._mu = result_data.Mu
                result._sigma = result_data.Sigma


def serialize_event_to_string(src: Event, fmt: SerializationFormat) -> str:
    dst = EventData()
    dst.Name = src.name
    dst.IsMulticlass = src.is_multiclass
    dst.NumSplits = src.num_splits

    for split, result in src._results.items():
        result_data = dst.Results[split]
        result_data.StrengthOfField = result.sof
        result_data.URL = result.url

        for category, num_cars in result._num_cars.items():
            result_data.NumCategoryCars[category] = num_cars
        for category, num_laps in result._num_laps.items():
            result_data.NumCategoryLaps[category] = num_laps

        for team_id, team in result._teams.items():
            team_data = result_data.Teams[team_id]
            team_data.Name = team.name
            team_data.Category = team.category
            team_data.Car = team.car
            team_data.ReasonOut = team.reason_out
            team_data.FinishPosition = team.finish_position
            team_data.FinishPositionInClass = team.finish_position_in_class
            team_data.TotalIncidents = team.total_incidents
            team_data.TotalLapsComplete = team.total_laps_complete

            for cust_id, driver in team._drivers.items():
                driver_data = team_data.Drivers[cust_id]
                driver_data.Name = driver.name
                driver_data.OldRating = driver.old_irating
                driver_data.NewRating = driver.new_irating
                driver_data.TotalIncidents = driver.total_incidents
                driver_data.TotalLapsComplete = driver.total_laps_complete
                driver_data.TotalLapsLead = driver.total_laps_lead

            for cust_id, member in team._members.items():
                member_data = team_data.Members[cust_id]
                member_data.Name = member.name

    return json_format.MessageToJson(dst, True, True)


def serialize_event_from_string(src: str, fmt: SerializationFormat) -> Event:
    event_data = EventData()
    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        json_format.Parse(src, event_data)
    elif fmt == SerializationFormat.TEXT:
        text_format.Parse(src, event_data)
    else:
        event_data.ParseFromString(src)
    dst = Event(event_data.Name)
    serialize_event_data_from_bind(event_data, dst)
    return dst


def serialize_event_data_from_bind(src: EventData, dst: Event):
    dst._num_splits = src.NumSplits
    dst._is_multiclass = src.IsMulticlass

    for split, result_data in src.Results.items():
        result = dst.add_result(split, result_data.StrengthOfField, result_data.URL)

        for category, num_cars in result_data.NumCategoryCars.items():
            result._num_cars[category] = num_cars
        for category, num_laps in result_data.NumCategoryLaps.items():
            result._num_laps[category] = num_laps

        for team_id, team_data in result_data.Teams.items():
            team = result.add_team(team_id, team_data.Category, team_data.Name, team_data.Car)
            team._reason_out = team_data.ReasonOut
            team._finish_position = team_data.FinishPosition
            team._finish_position_in_class = team_data.FinishPositionInClass
            team._total_incidents = team_data.TotalIncidents
            team._total_laps_complete = team_data.TotalLapsComplete

            for cust_id, driver_data in team_data.Drivers.items():
                driver = team.add_driver(cust_id, driver_data.Name)
                driver._old_irating = driver_data.OldRating
                driver._new_irating = driver_data.NewRating
                driver._total_incidents = driver_data.TotalIncidents
                driver._total_laps_complete = driver_data.TotalLapsComplete
                driver._total_laps_lead = driver_data.TotalLapsLead

            for cust_id, member_data in team_data.Members.items():
                team.add_member(cust_id, member_data.Name)


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
