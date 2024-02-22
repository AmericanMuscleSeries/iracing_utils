# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import trueskill
from pathlib import Path
from trueskill import Rating
from iracingdataapi.client import irDataClient

from google.protobuf import json_format, text_format
from league.objects_pb2 import *

from league.objects import Group, SerializationFormat, SortBy, League
from league.sheets import GDrive


_ams_logger = logging.getLogger('ams')


class ScoringSystem:
    __slots__ = ["pole_position",
                 "fastest_lap",
                 "laps_lead"
                 ]

    def __init__(self):
        self.pole_position = 0
        self.fastest_lap = 0
        self.laps_lead = 0


class LinearDecentScoring(ScoringSystem):
    __slots__ = ["top_score"]

    def __init__(self):
        super().__init__()
        self.top_score = 0


class AssignmentScoring(ScoringSystem):
    __slots__ = ["assignments"]

    def __init__(self):
        super().__init__()
        self.assignments = dict()


class CarNumberRange:
    __slots__ = ["min_car_number",
                 "max_car_number"]

    def __init__(self, min_car_number: int, max_car_number: int):
        self.min_car_number = min_car_number
        self.max_car_number = max_car_number


class TimePenalty:
    __slots__ = ["_race",
                 "_cust_id",
                 "_seconds"]

    def __init__(self, race: int, cust_id: int, seconds: int):
        self._race = race
        self._cust_id = cust_id
        self._seconds = seconds

    @property
    def race(self): return self._race

    @property
    def cust_id(self): return self._cust_id

    @property
    def seconds(self): return self._seconds


class GoogleSheet:
    __slots__ = ["_key",
                 "_group_tabs"
                 ]

    def __init__(self, key: str, group_tabs: dict):
        self._key = key
        self._group_tabs = group_tabs

    @property
    def key(self): return self._key

    @property
    def group_tabs(self): return self._group_tabs


class SeasonConfiguration:
    __slots__ = ["number",
                 "active",
                 "sort_by",
                 "scoring_system",
                 "num_drops",
                 "non_drivers",
                 "practice_sessions",
                 "time_penalties",
                 "group_rules",
                 "google_sheet"
                 ]

    def __init__(self, number: int):
        self.number = number
        self.active = False
        self.sort_by = SortBy.Earned
        self.scoring_system = None
        self.num_drops = 0
        self.non_drivers = list()
        self.practice_sessions = list()
        self.group_rules = dict()
        self.time_penalties = list()
        self.google_sheet = None

    def set_linear_decent_scoring(self, top_score: int):
        self.scoring_system = LinearDecentScoring()
        self.scoring_system.top_score = top_score
        return self.scoring_system

    def set_assignment_scoring(self, assignments: dict):
        self.scoring_system = AssignmentScoring()
        self.scoring_system.assignments = assignments
        return self.scoring_system

    def add_non_driver(self, cust_id: int):
        self.non_drivers.append(cust_id)

    def add_non_drivers(self, drivers: list):
        self.non_drivers.extend(drivers)

    def add_practice_session(self, race: int):
        self.practice_sessions.append(race)

    def add_practice_sessions(self, races: list):
        self.practice_sessions.extend(races)

    def add_group_rule(self, group: Group, number_range: CarNumberRange):
        self.group_rules[group] = number_range

    def add_time_penalty(self, race: int, cust_id: int, seconds: int):
        self.time_penalties.append(TimePenalty(race, cust_id, seconds))

    def add_google_sheet(self, key: str, group_tabs: dict):
        self.google_sheet = GoogleSheet(key, group_tabs)

    def get_group(self, car_number: int) -> Group:
        for group, rule in self.group_rules.items():
            if rule.min_car_number <= car_number <= rule.max_car_number:
                return group

        _ams_logger.error("No group rule found in season " + str(self.number) + " for car number " + str(car_number))
        return Group.Unknown


class LeagueConfiguration:
    __slots__ = ["_ir_id",
                 "_name",
                 "seasons"
                 ]

    def __init__(self, ir_id: int):
        self._ir_id = ir_id
        self._name = None
        self.seasons = dict()

    def as_dict(self) -> dict:
        string = serialize_league_configuration_to_string(self, SerializationFormat.JSON)
        return json.loads(string)

    @staticmethod
    def from_dict(d: dict):
        string = json.dumps(d)
        return serialize_league_configuration_from_string(string, SerializationFormat.JSON)

    @property
    def ir_id(self): return self._ir_id

    @property
    def name(self): return self._name

    def get_season(self, number: int):
        if number not in self.seasons:
            self.seasons[number] = SeasonConfiguration(number)
        return self.seasons[number]

    def push_results_to_sheets(self, lg: League, credentials_filename: Path):
        gdrive = GDrive(str(credentials_filename))
        for season_num, season in self.seasons.items():
            if season.google_sheet is None:
                _ams_logger.warning(
                    "Not pushing season " + str(season_num) +
                    ". No sheet specified to push to. Check your configuration.")
                continue
            if lg.get_season(season_num) is None:
                _ams_logger.warning(
                    "Not pushing season " + str(season_num) + ". No results to push. Check your configuration.")
                continue
            _ams_logger.info("Pushing " + self._name + " season " + str(season_num) + " results to sheets")
            # TODO These two methods should probably be one
            gdrive.connect_to_results(season.google_sheet.key, season.google_sheet.group_tabs)
            cnt = gdrive.push_results(lg, season_num, list(season.google_sheet.group_tabs.keys()), season.sort_by)
            _ams_logger.info("Executed " + str(cnt) + " update calls")

    def fetch_and_score_league(self, username: str, password: str, specific_seasons: list = None) -> League:
        lg = League()
        # Pull everything from iracing
        idc = irDataClient(username, password)
        ir_league_info = idc.league_get(self._ir_id)
        self._name = ir_league_info["league_name"]
        _ams_logger.info("Extracting data from league: " + self._name)
        _ams_logger.info("There are " + str(len(ir_league_info["roster"])) + " members in this league")
        for ir_member in ir_league_info["roster"]:
            lg.add_member(ir_member["cust_id"], ir_member["display_name"], ir_member["nick_name"])

        ir_seasons = idc.league_seasons(self._ir_id, True)["seasons"]
        _ams_logger.info("Found " + str(len(ir_seasons)) + " seasons")
        for season_num, ir_season in enumerate(ir_seasons):
            season_num += 1  # We store data in dicts, and it's just more conventional to start at 1
            if specific_seasons is not None and season_num not in specific_seasons:
                continue
            season_cfg = self.get_season(season_num)

            _ams_logger.info("Pulling season " + str(season_num))
            season = lg.add_season(season_num)
            # TODO We could pull with results_only False to detect if we are in season or not
            ir_sessions = idc.league_season_sessions(self._ir_id, ir_season["season_id"], True)["sessions"]
            _ams_logger.info("There were " + str(len(ir_sessions)) + " sessions in season " + str(season_num))

            race_num = 0
            race_session_num = 0
            for session_num, ir_session in enumerate(ir_sessions):
                track_name = ir_session["track"]["track_name"]
                ir_subsession = idc.result(subsession_id=ir_session["subsession_id"])["session_results"]
                # Skip the session if there was no race
                ir_race_results = None
                for ir_event in ir_subsession:
                    if ir_event["simsession_type"] == 6:
                        ir_race_results = ir_event
                if ir_race_results is None:
                    _ams_logger.info("Session " + str(session_num) + " at " + track_name + " was not a race.")
                    continue

                # Check if this race event was a practice race
                race_session_num += 1
                if race_session_num in season_cfg.practice_sessions:
                    _ams_logger.info("Session " + str(session_num) + " at " + track_name +
                                     " was a practice race. Skipping it.")
                    continue

                #  This is an actual race we are going to score
                race_num += 1
                _ams_logger.info("Session " + str(session_num) + " was a race at " + track_name)
                _ams_logger.info("Processing it as race " + str(race_num))

                race = season.add_race(race_num, ir_session["launch_at"].split('T')[0], ir_session["track"]["track_name"])

                ir_car_results = ir_race_results["results"]
                # all_laps = idc.result_lap_chart_data(subsession_id=session["subsession_id"])
                ir_total_laps = ir_car_results[0]["laps_complete"]

                # Loop over every driver in this race
                for ir_car_result in ir_car_results:
                    cust_id = ir_car_result["cust_id"]
                    if cust_id in season_cfg.non_drivers:
                        _ams_logger.info("Skipping non-driver: "+lg.get_member(cust_id).nickname)
                        continue

                    # Pull driver from race and add to season list of drivers
                    # We keep updating the season drivers as we go to preserve any change of number/group
                    # The last race is the number/group that will be preserved in the structure
                    # _ams_logger.info("Processing driver: " + my_league.get_member(cust_id).nickname)
                    driver = season.add_driver(cust_id)
                    member = lg.get_member(cust_id)
                    if member is None:
                        driver._name = idc.member(cust_id)["members"][0]["display_name"]
                        # TODO should we mark previous members?
                        lg.add_member(cust_id, driver._name, None)
                        _ams_logger.info("Adding " + driver._name + " to members.")
                    else:
                        driver._name = member.name
                        # We only want to use the league number, if this season is an active season
                        if season_cfg.active:
                            for lg_member in ir_league_info["roster"]:
                                if lg_member["cust_id"] == cust_id:
                                    driver_car_number = int(lg_member["car_number"])
                                    driver.set_car_number(driver_car_number, season_cfg.get_group(driver_car_number))
                    if driver.car_number is None:
                        driver_car_number = int(ir_car_result["livery"]["car_number"])
                        driver.set_car_number(driver_car_number, season_cfg.get_group(driver_car_number))

                    # Just book keep, we will rack, stack, and score later
                    result = race.add_result(cust_id)
                    result._start_position = ir_car_result["starting_position"]+1
                    result._finish_position = ir_car_result["finish_position"]+1
                    result._interval = ir_car_result["interval"] * 0.0001
                    result._incidents = ir_car_result["incidents"]
                    result._laps_completed = ir_car_result["laps_complete"]
                    result._laps_lead = ir_car_result["laps_lead"]
                    result._clean_driver_points = 0
                    if result._laps_completed >= ir_total_laps*0.5:
                        if result._incidents == 0:
                            result._clean_driver_points = 3
                        elif result._incidents == 1:
                            result._clean_driver_points = 2
                        elif result._incidents <= 4:
                            result._clean_driver_points = 1

                    # Increment driver counters
                    driver._total_races += 1
                    driver._total_incidents += result._incidents
                    driver._total_laps_lead += result._laps_lead
                    driver._total_laps_complete += result._laps_completed
                    driver._clean_driver_points += result._clean_driver_points

                    # End of looping over every driver in a race

                # Apply any time penalties in this race
                race_penalty = False
                for time_penalty in season_cfg.time_penalties:
                    for rr in race.grid.values():
                        if time_penalty.race == race_num and time_penalty.cust_id == rr.cust_id:
                            if rr.interval < 0:
                                _ams_logger.error("Cannot apply a time penalty to " +
                                                  lg.get_member(rr.cust_id).nickname +
                                                  " since they did not finish on the lead lap.")
                                continue
                            race_penalty = True
                            rr._interval += time_penalty.seconds
                            _ams_logger.info("A " + str(time_penalty.seconds) + "s time penalty has been applied to " +
                                             lg.get_member(rr.cust_id).nickname)
                if race_penalty:  # Recalculate finish positions
                    # Penalties are added to the interval, and only to cars on the lead lap
                    # So we only need to update the finishing positions on lead lap cars
                    lead_laps = list()
                    for rr in race.grid.values():
                        if rr.interval >= 0:
                            lead_laps.append(rr)
                    # Sort the lead lap cars by interval
                    new_lead_laps = sorted(lead_laps, key=lambda x: x.interval)
                    for pos, rr in enumerate(new_lead_laps):
                        rr._finish_position = pos + 1

                # Start scoring this race
                if isinstance(season_cfg.scoring_system, LinearDecentScoring):
                    max_points = season_cfg.scoring_system.top_score
                    for rr in race.grid.values():
                        rr._points = max_points - rr._finish_position+1
                        if rr._points < 0:
                            rr._points = 0
                        if rr._laps_lead > 0:
                            rr._points += season_cfg.scoring_system.laps_lead
                elif isinstance(season_cfg.scoring_system, AssignmentScoring):
                    for rr in race.grid.values():
                        pos_pts = 0
                        if rr._finish_position in season_cfg.scoring_system.assignments:
                            pos_pts = season_cfg.scoring_system.assignments[rr._finish_position]
                        rr._points = pos_pts
                        if rr._laps_lead > 0:
                            rr._points += season_cfg.scoring_system.laps_lead
                else:
                    _ams_logger.fatal("Unknown scoring system provided")

                # End of looping over every race in a season

            # Rate each driver
            ratings = list()
            finishing_positions = list()
            for race in season.races.values():
                ratings.clear()
                finishing_positions.clear()
                for cust_id, my_driver in season.drivers.items():
                    result = race.get_result(cust_id)
                    if result is None:  # Not in this race
                        finishing_positions.append(-1)
                    else:
                        finishing_positions.append(result.finish_position)
                    ratings.append((Rating(driver._mu, driver._sigma),))
                new_ratings = trueskill.rate(ratings, finishing_positions)
                for idx, driver in enumerate(season.drivers.values()):
                    driver._mu = new_ratings[idx][0].mu
                    driver._sigma = new_ratings[idx][0].sigma
                    result = race.get_result(driver.cust_id)
                    if result is None:
                        continue  # The rating is propagated via the driver, not the result, so I think this is OK
                    result._mu = driver._mu
                    result._sigma = driver._sigma

            # Track group statistics after the season, since we don't know when the final groups are set
            # We will also compute trueskill ratings for each race based on finishing positions
            for race in season.races.values():
                # Find the fastest lap and pole position for every group

                for result in race.grid.values():
                    driver = season.get_driver(result.cust_id)
                    race_stats = race.get_stats(driver.group)
                    race_stats._num_drivers += 1
                    race_stats.check_if_pole_position(result.cust_id, result.start_position)
                    race_stats.check_if_fastest_lap(result.cust_id, result.fastest_lap)


                # Now push those stats back into the results and drivers
                for stat in race.stats.values():
                    rr = race.get_result(stat.fastest_lap_driver)
                    rr._fastest_lap = True
                    dvr = season.get_driver(stat.fastest_lap_driver)
                    dvr._total_fastest_laps += 1
                    if rr._fastest_lap:
                        rr._points += season_cfg.scoring_system.fastest_lap
                    rr = race.get_result(stat.pole_position_driver)
                    rr._pole_position = True
                    if rr._pole_position:
                        rr._points += season_cfg.scoring_system.pole_position
                    dvr._total_pole_positions += 1

            # Score each driver
            points = list()
            for cust_id, driver in season.drivers.items():
                season.get_driver(cust_id)
                points.clear()
                for race in season.races.values():
                    result = race.get_result(cust_id)
                    if result is None:  # Not in this race
                        points.append(0)
                    else:
                        points.append(result.points)
                driver._earned_points = sum(points)
                driver._drop_points = 0
                if 0 < season_cfg.num_drops < len(points):
                    driver._drop_points = sum(sorted(points)[:season_cfg.num_drops])

        # End of looping over every season

        return lg


def serialize_league_configuration_to_string(src: LeagueConfiguration, fmt: SerializationFormat) -> str:
    dst = LeagueConfigurationData()
    serialize_league_configuration_to_bind(src, dst)

    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        verbose = True if fmt == SerializationFormat.VERBOSE_JSON else False
        return json_format.MessageToJson(dst, verbose, verbose)
    elif fmt == SerializationFormat.TEXT:
        return text_format.MessageToString(dst)
    else:
        return dst.SerializeToString()


def serialize_league_configuration_to_bind(src: LeagueConfiguration, dst: LeagueConfigurationData):
    dst.iRacingID = src.ir_id
    if src.name is not None:
        dst.Name = src.name

    for season_number, season in src.seasons.items():
        season_data = dst.Seasons[season_number]

        if isinstance(season.scoring_system, LinearDecentScoring):
            season_data.ScoringSystem.LinearDecent.TopScore = season.scoring_system.top_score
            season_data.ScoringSystem.LinearDecent.Base.PolePosition = season.scoring_system.pole_position
            season_data.ScoringSystem.LinearDecent.Base.FastestLap = season.scoring_system.fastest_lap
            season_data.ScoringSystem.LinearDecent.Base.LapsLead = season.scoring_system.laps_lead
        elif isinstance(season.scoring_system, AssignmentScoring):
            for pos, pts in season.scoring_system.assignments.items():
                season_data.ScoringSystem.Assignment.PositionScore[pos] = pts
            season_data.ScoringSystem.Assignment.Base.PolePosition = season.scoring_system.pole_position
            season_data.ScoringSystem.Assignment.Base.FastestLap = season.scoring_system.fastest_lap
            season_data.ScoringSystem.Assignment.Base.LapsLead = season.scoring_system.laps_lead

        season_data.Active = season.active
        season_data.NumDrops = season.num_drops

        for cust_id in season.non_drivers:
            season_data.NonDrivers.append(cust_id)

        for session_number in season.practice_sessions:
            season_data.PracticeSessions.append(session_number)

        for group, car_number_range in season.group_rules.items():
            gr = GroupRuleData()
            gr.MinCarNumber = car_number_range.min_car_number
            gr.MaxCarNumber = car_number_range.max_car_number
            gr.Group = group.value
            season_data.GroupRules.GroupRule.append(gr)

        for tp in season.time_penalties:
            tpd = TimePenaltyData()
            tpd.Race = tp.race
            tpd.Driver = tp.cust_id
            tpd.Seconds = tp.seconds
            season_data.TimePenalty.append(tpd)

        season_data.GoogleSheets.Key = season.google_sheet.key
        for group, name in season.google_sheet.group_tabs.items():
            group_tab_data = GoogleTabData()
            group_tab_data.Group = group.value
            group_tab_data.TabName = name
            season_data.GoogleSheets.GroupTab.append(group_tab_data)

        season_data.SortBy = season.sort_by.value


def serialize_league_configuration_from_string(src: str, fmt: SerializationFormat) -> LeagueConfiguration:
    lrd = LeagueConfigurationData()
    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        json_format.Parse(src, lrd)
    elif fmt == SerializationFormat.TEXT:
        text_format.Parse(src, lrd)
    else:
        lrd.ParseFromString(src)
    dst = LeagueConfiguration(lrd.iRacingID)
    serialize_league_configuration_from_bind(lrd, dst)
    return dst


def serialize_league_configuration_from_bind(src: LeagueConfigurationData, dst: LeagueConfiguration):
    dst._name = src.Name

    for season_num, season_data in src.Seasons.items():
        season = dst.get_season(season_num)
        system = season_data.ScoringSystem.WhichOneof("System")
        # data = getattr(season_data.ScoringSystem, season_data.ScoringSystem.WhichOneof("System"))
        if system == "LinearDecent":
            scoring = season.set_linear_decent_scoring(season_data.ScoringSystem.LinearDecent.TopScore)
            scoring.pole_position = season_data.ScoringSystem.LinearDecent.Base.PolePosition
            scoring.laps_lead = season_data.ScoringSystem.LinearDecent.Base.LapsLead
            scoring.fastest_lap = season_data.ScoringSystem.LinearDecent.Base.FastestLap
        elif system == "Assignment":
            scoring = season.set_assignment_scoring(season_data.ScoringSystem.Assignment.PositionScore)
            scoring.pole_position = season_data.ScoringSystem.Assignment.Base.PolePosition
            scoring.laps_lead = season_data.ScoringSystem.Assignment.Base.LapsLead
            scoring.fastest_lap = season_data.ScoringSystem.Assignment.Base.FastestLap

        season.active = season_data.Active
        season.num_drops = season_data.NumDrops

        season.add_non_drivers(season_data.NonDrivers)

        season.add_practice_sessions(season_data.PracticeSessions)

        for group_rule_data in season_data.GroupRules.GroupRule:
            season.add_group_rule(Group(group_rule_data.Group),
                                  CarNumberRange(group_rule_data.MinCarNumber,
                                                 group_rule_data.MaxCarNumber))

        for time_penalty_data in season_data.TimePenalty:
            season.add_time_penalty(time_penalty_data.Race,
                                    time_penalty_data.Driver,
                                    time_penalty_data.Seconds)

        if season_data.GoogleSheets is not None:
            group_tabs = dict()
            for group_tab_data in season_data.GoogleSheets.GroupTab:
                group_tabs[Group(group_tab_data.Group)] = group_tab_data.TabName
            season.add_google_sheet(season_data.GoogleSheets.Key, group_tabs)

        season.sort_by = SortBy(season_data.SortBy)

    return dst

