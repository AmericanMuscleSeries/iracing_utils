# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import math
import trueskill

from datetime import datetime, timedelta
from dateutil import tz
from google.protobuf import json_format, text_format
from iracingdataapi.client import irDataClient
from trueskill import Rating

from core.clients import Client
from core.garage61 import Garage61Client
from core.objects import GroupRules, LeagueResult, PositionValue, SerializationFormat, serialize_to_string, \
    percent_difference, time2str
from core.objects_pb2 import (GroupRulesData, LeagueConfigurationData, PointsMultiplierData,
                              PenaltyData, TimePenaltyData, PointsThresholdData, IncidentPointsData)

_logger = logging.getLogger('log')

# Note, for our API, use 1 based counting
# The first race is race 1, not race 0
# The first season is season 1, not season 0


class PointsThreshold:
    __slots__ = ["minimum_requirement",
                 "points"]

    def __init__(self,):
        self.points = 0
        self.minimum_requirement = 0

    def satisfied(self, laps_completed: int, race_laps: int) -> bool:
        if self.minimum_requirement < 1:
            # min requirement is a percent of the race
            return laps_completed >= race_laps * self.minimum_requirement
        elif self.minimum_requirement >= 1:
            # min requirement is number of laps
            return laps_completed > (race_laps - self.minimum_requirement)


class LapThreshold:
    __slots__ = ["num_laps",
                 "points"]

    def __init__(self,):
        self.points = 0
        self.num_laps = 0


class FastLapThreshold(LapThreshold):
    __slots__ = ["time_percent"]

    def __init__(self):
        super().__init__()
        self.time_percent = 0


class IncidentPoints:
    __slots__ = ["point_map",
                 "minimum_requirement",
                 "separate_points"]

    def __init__(self):
        self.point_map = {}
        self.minimum_requirement = 0
        self.separate_points = False

    def satisfied(self, laps_completed: int, race_laps: int) -> bool:
        if self.minimum_requirement < 1:
            # min requirement is a percent of the race
            return laps_completed >= race_laps * self.minimum_requirement
        elif self.minimum_requirement >= 1:
            # min requirement is number of laps
            return laps_completed > (race_laps - self.minimum_requirement)


class PointsMultiplier:
    __slots__ = ["_race",
                 "position",
                 "clean_driver",
                 "fastest_lap",
                 "finish_race",
                 "lead_a_lap",
                 "most_laps_lead",
                 "pole_position"]

    def __init__(self, race: int):
        self._race = race
        self.position = 1
        self.clean_driver = 1
        self.fastest_lap = 1
        self.finish_race = 1
        self.pole_position = 1
        self.lead_a_lap = 1
        self.most_laps_lead = 1

    @property
    def race(self): return self._race


class ScoringSystem:
    __slots__ = ["minimum_race_distance",
                 "pole_position",
                 "clean_laps",
                 "fast_clean_laps",
                 "fastest_lap",
                 "lead_a_lap",
                 "most_laps_lead",
                 "finish_race",
                 "clean_driver",
                 "separate_pool",
                 "position_value",
                 "_handicap",
                 "_multipliers"
                 ]

    def __init__(self):
        self.minimum_race_distance = 0
        self.pole_position = 0
        self.clean_laps = LapThreshold()
        self.fast_clean_laps = FastLapThreshold()
        self.fastest_lap = PointsThreshold()
        self.lead_a_lap = PointsThreshold()
        self.most_laps_lead = PointsThreshold()
        self.finish_race = PointsThreshold()
        self.clean_driver = IncidentPoints()
        self.separate_pool = False
        self.position_value = PositionValue.Overall
        self._handicap = False
        self._multipliers = {}

    @property
    def handicap(self): return self._handicap

    def add_race_multiplier(self, race: int):
        return self.get_race_multiplier(race)

    def get_race_multiplier(self, race: int):
        if race not in self._multipliers:
            self._multipliers[race] = PointsMultiplier(race)
        return self._multipliers[race]


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


class Penalty:
    __slots__ = ["_race",
                 "_cust_id"]

    def __init__(self, race: int, cust_id: int):
        self._race = race
        self._cust_id = cust_id

    @property
    def race(self): return self._race

    @property
    def cust_id(self): return self._cust_id


class TimePenalty(Penalty):
    __slots__ = ["_seconds"]

    def __init__(self, race: int, cust_id: int, seconds: int):
        super().__init__(race, cust_id)
        self._seconds = seconds

    @property
    def seconds(self): return self._seconds


class LeagueConfiguration:
    __slots__ = ["_iracing_id",
                 "_g61_id",
                 "_name",
                 "_season",
                 "scoring_system",
                 "non_drivers",
                 "practice_sessions",
                 "group_rules",
                 "time_penalties",
                 "disqualifications",
                 "_fast_laps_override",
                 "_finish_override",
                 "_laps_lead_override",
                 "_manual_sessions"
                 ]

    def __init__(self, iracing_id: int, g61_id: str="", season: str = ""):
        self._iracing_id = iracing_id
        self._g61_id = g61_id
        self._name = None
        self._season = season
        self.scoring_system = None
        self.non_drivers = list()
        self.practice_sessions = list()
        self.group_rules = dict()
        self.time_penalties = list()
        self.disqualifications = list()
        self._fast_laps_override = dict()
        self._finish_override = dict()
        self._laps_lead_override = dict()
        self._manual_sessions = dict()

    def as_dict(self) -> dict:
        string = serialize_league_configuration_to_string(self, SerializationFormat.JSON)
        return json.loads(string)

    @staticmethod
    def from_dict(d: dict):
        string = json.dumps(d)
        return serialize_league_configuration_from_string(string, SerializationFormat.JSON)

    @property
    def iracing_id(self): return self._iracing_id

    @property
    def g61_id(self): return self._g61_id

    @property
    def name(self): return self._name

    @property
    def season(self): return self._season

    def set_linear_decent_scoring(self, top_score: int,
                                  hcp: bool = False,
                                  separate_pool: bool = False,
                                  position_value: PositionValue = PositionValue.Overall):
        self.scoring_system = LinearDecentScoring()
        self.scoring_system.top_score = top_score
        self.scoring_system.separate_pool = separate_pool
        self.scoring_system.position_value = position_value
        self.scoring_system._handicap = hcp
        return self.scoring_system

    def set_assignment_scoring(self, assignments: dict, hcp: bool = False,
                               separate_pool: bool = False,
                               position_value: PositionValue = PositionValue.Overall):
        self.scoring_system = AssignmentScoring()
        self.scoring_system.assignments = assignments
        self.scoring_system._handicap = hcp
        self.scoring_system.separate_pool = separate_pool
        self.scoring_system.position_value = position_value
        return self.scoring_system

    def add_non_driver(self, cust_id: int):
        self.non_drivers.append(cust_id)

    def add_non_drivers(self, drivers: list):
        self.non_drivers.extend(drivers)

    def add_practice_session(self, race: int):
        self.practice_sessions.append(race)

    def add_practice_sessions(self, races: list):
        self.practice_sessions.extend(races)

    def add_group_rule(self, group: str, rules: GroupRules):
        self.group_rules[group] = rules

    def get_group_rules(self, group: str):
        return self.group_rules[group]

    def add_time_penalty(self, race: int, cust_id: int, seconds: int):
        self.time_penalties.append(TimePenalty(race, cust_id, seconds))

    def add_disqualification(self, race: int, cust_id: int):
        self.disqualifications.append(Penalty(race, cust_id))

    def override_fastest_lap(self, race: int, from_id: int, to_id: int):
        if race not in self._fast_laps_override:
            self._fast_laps_override[race] = {}
        self._fast_laps_override[race][from_id] = to_id

    def override_finish_order(self, race: int, order: list):
        if len(order) != len(set(order)):
            raise ValueError("override_finish_order given an order that has duplicates.")
        self._finish_override[race] = order

    def override_laps_lead(self, race: int, cust_id: int, num: int):
        if race not in self._laps_lead_override:
            self._laps_lead_override[race] = {}
        self._laps_lead_override[race][cust_id] = num

    def get_group(self, car_number: int) -> str:
        for group, rule in self.group_rules.items():
            if rule.min_car_number <= car_number <= rule.max_car_number:
                return group

        _logger.error("No group rule found in season " + str(self.season) + " for car number " + str(car_number))
        return "Unknown"

    def add_session(self, number: int, session: dict):
        self._manual_sessions[number] = session

    def fetch_league_members(self, idc: irDataClient):
        lg = LeagueResult()
        # Pull everything from iracing
        ir_league_info = idc.league_get(self._iracing_id)
        self._name = ir_league_info["league_name"]
        _logger.info("Extracting data from league: " + self._name)
        _logger.info("There are " + str(len(ir_league_info["roster"])) + " members in this league")
        for ir_member in ir_league_info["roster"]:
            lg.add_member(ir_member["cust_id"], ir_member["display_name"], ir_member["nick_name"])
        return lg

    @staticmethod
    def _get_league_number(cust_id, roster):
        for member in roster:
            if member["cust_id"] == cust_id:
                if not member["car_number"]:
                    return None
                else:
                    return int(member["car_number"])

    @staticmethod
    def fetch_all_season_names(idc: irDataClient, league_id: int) -> list:
        ir_league_info = idc.league_get(league_id)  # TODO replace with lg below
        ir_seasons = idc.league_seasons(league_id, True)["seasons"]
        names = []
        for ir_season in ir_seasons:
            names.append(ir_season["season_name"])
        return names

    @staticmethod
    def fetch_track_count(idc: irDataClient, league_id: int):
        tracks = dict()
        ir_seasons = idc.league_seasons(league_id, True)["seasons"]
        _logger.info("Found " + str(len(ir_seasons)) + " seasons")
        for ir_season in ir_seasons:
            ir_sessions = idc.league_season_sessions(league_id, ir_season["season_id"], False)["sessions"]
            for ir_session in ir_sessions:
                ir_track = ir_session['track']
                track = f"{ir_track['track_name']}"
                if "config_name" in ir_track:
                    track = f"{track} {ir_track['config_name']}"
                if track not in tracks:
                    tracks[track] = {"count": 0, "seasons": set()}
                tracks[track]["count"] += 1
                tracks[track]["seasons"].add(ir_season["season_name"])
        return tracks

    def fetch_and_score_league(self, idc: irDataClient, active: bool = True) -> LeagueResult:
        lg = self.fetch_league_members(idc)

        ir_league_info = idc.league_get(self._iracing_id)  # TODO replace with lg below
        ir_seasons = idc.league_seasons(self._iracing_id, True)["seasons"]
        _logger.info("Found " + str(len(ir_seasons)) + " seasons")
        scoring = self.scoring_system  # alias to shorten lines
        for ir_season in ir_seasons:
            if self._season != ir_season['season_name']:
                continue

            _logger.info(f"Pulling season {ir_season['season_name']}")
            # TODO We could pull with results_only False to detect if we are in season or not
            ir_sessions = idc.league_season_sessions(self._iracing_id, ir_season["season_id"], False)["sessions"]
            _logger.info("There are " + str(len(ir_sessions)) + " sessions in season ")

            completed_races = 0
            race_num = 0
            race_session_num = 0
            for session_num, ir_session in enumerate(ir_sessions):
                track_name = ir_session["track"]["track_name"]

                # Check if this is a practice only session
                if ir_session["qualify_laps"] == 0 and ir_session["qualify_length"] == 0:
                    _logger.info("Session " + str(session_num) + " at " + track_name + " was a practice session.")
                    continue

                # Check if this race event was a practice race
                race_session_num += 1
                if race_session_num in self.practice_sessions:
                    _logger.info("Session " + str(session_num) + " at " + track_name +
                                 " was a practice race. Skipping it.")
                    continue

                # Check to see if its run yet
                subsession_id = 0
                if "subsession_id" not in ir_session:
                    _logger.info("\tSession " + str(race_num) + " at " + track_name + " has not occurred yet.")
                else:
                    subsession_id = ir_session["subsession_id"]

                # Sessions are in UTC time, convert to local
                utc = datetime.strptime(ir_session["launch_at"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.tzutc())
                est = str(utc.astimezone(tz.gettz('America/New_York'))).split(' ')[0]
                # No subsession means no results, so create an empty race and move on
                # TODO if this session has heats... how would we know that?
                if subsession_id == 0:
                    race_num += 1
                    lg.add_race(race_num,
                                est,
                                ir_session["track"]["track_name"], subsession_id)
                    continue

                try:
                    ir_subsession = idc.result(subsession_id=subsession_id)
                except RuntimeError:
                    _logger.error(f"\tRace {race_num} on {est} at {track_name} is currently running?")
                    continue

                ir_subsession_results = ir_subsession["session_results"]
                ir_race_results = None
                for ir_event in ir_subsession_results:
                    if ir_event["simsession_type"] == 6:
                        #  This is an actual race we are going to score
                        race_num += 1
                        _logger.info(f"Session {session_num} on {est} at {track_name} has race {race_num}")
                        ir_race_results = ir_event
                        race = lg.add_race(race_num,
                                           est,
                                           ir_session["track"]["track_name"], subsession_id)
                    else:
                        continue

                    if ir_subsession["event_laps_complete"] == 0:
                        _logger.info(f"\tRace {race_num} on {est} at {track_name} had no laps run, skipping.")
                        continue

                    completed_races += 1
                    ir_car_results = ir_race_results["results"]
                    ir_total_laps = ir_car_results[0]["laps_complete"]
                    multiplier = scoring.get_race_multiplier(race.number)

                    subsession_drivers = set()  # All drivers that started the race
                    # Figure out the class leader for every lap
                    group_lap_leaders = {}
                    for group in self.group_rules.keys():
                        laps = {}
                        for i in range(ir_total_laps):
                            laps[i+1] = {"cust_id": -1, "position": 999}
                        group_lap_leaders[group] = laps
                    all_laps = idc.result_lap_chart_data(subsession_id=ir_session["subsession_id"],
                                                         simsession_number=ir_event["simsession_number"])
                    for lap in all_laps:
                        lap_number = lap["lap_number"]
                        if lap_number == 0:
                            continue
                        cust_id = lap["cust_id"]
                        subsession_drivers.add(cust_id)
                        if cust_id in self.non_drivers:
                            continue
                        position = lap["lap_position"]
                        car_number = None
                        if active:
                            car_number = self._get_league_number(lap["cust_id"], ir_league_info["roster"])
                        if car_number is None:
                            # Must be brand spanking new
                            car_number = int(lap["car_number"])
                        group = self.get_group(car_number)
                        leader = group_lap_leaders[group][lap_number]
                        if position < leader["position"]:
                            leader["position"] = position
                            leader["cust_id"] = cust_id
                    # Now count up how many laps each driver lead
                    laps_lead = {}
                    for group, laps in group_lap_leaders.items():
                        for lap in laps.values():
                            if lap["cust_id"] not in laps_lead:
                                laps_lead[lap["cust_id"]] = 0
                            laps_lead[lap["cust_id"]] += 1

                    # Check to see if we have a laps lead overrides for this race
                    if race_num in self._laps_lead_override:
                        for cust_id, new_laps_lead in self._laps_lead_override[race_num].items():
                            laps_lead[cust_id] = new_laps_lead

                    # Check to see if we have a finish override for this race
                    finish_overrides = None
                    if race_num in self._finish_override:
                        finish_overrides = self._finish_override[race_num]

                    # Loop over every driver in this race
                    for ir_car_result in ir_car_results:
                        cust_id = ir_car_result["cust_id"]
                        if cust_id in self.non_drivers or (cust_id not in subsession_drivers and
                                                           ir_car_result["incidents"] == 0 and
                                                           (ir_car_result["reason_out_id"] == 0 or
                                                            ir_car_result["reason_out_id"] == 34)):
                            non_driver = lg.get_member(cust_id)
                            if non_driver is None:
                                _logger.info(f"Skipping non-driver: {cust_id}")
                            else:
                                _logger.info("Skipping non-driver: " + lg.get_member(cust_id).nickname)
                            continue

                        # Pull driver from race and add to season list of drivers
                        # We keep updating the season drivers as we go to preserve any change of number/group
                        # The last race is the number/group that will be preserved in the structure
                        # _ams_logger.info("Processing driver: " + my_league.get_member(cust_id).nickname)
                        driver = lg.add_driver(cust_id)
                        member = lg.get_member(cust_id)
                        if member is None:
                            driver._name = idc.member(cust_id)["members"][0]["display_name"]
                            # TODO should we mark previous members?
                            lg.add_member(cust_id, driver._name, None)
                            _logger.info("Adding " + driver._name + " to members.")
                        else:
                            driver._name = member.name
                            # We only want to use the league number, if this season is an active season
                            if active:
                                driver_car_number = self._get_league_number(cust_id, ir_league_info["roster"])
                                if driver_car_number is not None:
                                    driver.set_car_number(driver_car_number, self.get_group(driver_car_number))
                        if driver.car_number is None:
                            # Must be brand spanking new
                            driver_car_number = int(ir_car_result["livery"]["car_number"])
                            driver.set_car_number(driver_car_number, self.get_group(driver_car_number))

                        # Don't add dq'd drivers to the race, just promote everyone
                        dq_driver = False
                        for dq in self.disqualifications:
                            if race_num == dq.race and cust_id == dq.cust_id:
                                dq_driver = True
                                driver._total_race_starts += 1
                                _logger.info(f"\t{lg.get_member(dq.cust_id).nickname} ({driver.car_number}) disqualified\n"
                                             f"\t\tRemoving them from the race.")
                                break
                        if dq_driver:
                            continue  # Not adding this driver to the race result

                        # Just book keep, we will rack, stack, and score later
                        result = race.add_result(cust_id)
                        result._start_position = ir_car_result["starting_position"]+1
                        result._finish_position = ir_car_result["finish_position"]+1
                        if finish_overrides is not None:
                            if min(finish_overrides) > 1000:
                                result._finish_position = finish_overrides.index(driver.cust_id)+1
                            else:
                                result._finish_position = finish_overrides.index(driver.car_number)+1
                        result._interval = ir_car_result["interval"] * 0.0001
                        result._incidents = ir_car_result["incidents"]
                        result._laps_completed = ir_car_result["laps_complete"]
                        result._laps_lead = 0
                        result._fastest_lap_time = 9999999
                        result._clean_driver_points = 0
                        result._completed_race_points = 0
                        result._met_minimum_distance = False

                        # Get all the laps associated with this cust_id
                        for race_lap in all_laps:
                            if race_lap["cust_id"] == cust_id:
                                lap = result.add_lap()
                                lap._cust_id = cust_id
                                lap._position = race_lap["lap_position"]
                                lap._number = race_lap["lap_number"]
                                lap._time = race_lap["lap_time"]
                                # lap._time_stamp = race_lap["session_time"] # TODO g61 vs iracing formats
                            """ Counts all car contacts
                            for event in lap["lap_events"]:
                                if "contact" in event:
                                    if driver.name not in contacts:
                                        contacts[driver.name] = 0
                                    contacts[driver.name] += 1
                            """

                        if result._laps_completed/ir_total_laps >= scoring.minimum_race_distance:
                            driver._total_completed_races += 1
                            result._met_minimum_distance = True

                            if scoring.lead_a_lap.satisfied(result._laps_completed, ir_total_laps):
                                result._laps_lead = 0 if cust_id not in laps_lead else laps_lead[cust_id]

                            if scoring.fastest_lap.satisfied(result._laps_completed, ir_total_laps):
                                result._fastest_lap_time = ir_car_result["best_lap_time"]

                            if scoring.clean_driver.satisfied(result._laps_completed, ir_total_laps):
                                if result._incidents in scoring.clean_driver.point_map:
                                    result._clean_driver_points = scoring.clean_driver.point_map[result._incidents]
                                    result._clean_driver_points *= multiplier.clean_driver

                            if scoring.finish_race.satisfied(result._laps_completed, ir_total_laps):
                                result._completed_race_points = scoring.finish_race.points * multiplier.finish_race

                            if result._laps_lead > 0:
                                driver._total_lead_a_lap += 1
                                driver._lead_a_lap_points += scoring.lead_a_lap.points * multiplier.lead_a_lap

                        # Increment driver counters
                        driver._total_race_starts += 1
                        driver._total_incidents += result._incidents
                        driver._total_laps_complete += result._laps_completed
                        driver._clean_driver_points += result._clean_driver_points
                        driver._completed_race_points += result._completed_race_points
                        driver._total_lead_a_lap += result._laps_lead
                    # End of looping over every driver in a race

                    # reorder the race.grid with the new order (logic below depends on this being ordered by race finish)
                    if finish_overrides:
                        new_finish_order = sorted(race.grid.items(), key=lambda item: item[1].finish_position)
                        race.grid = {}
                        for t in new_finish_order:
                            race.grid[t[0]] = t[1]

                    # If we removed any driver from the result, make sure finishing positions are right
                    if len(ir_car_results) != len(race.grid):
                        finish_order = sorted(list(race.grid.values()), key=lambda car: car.finish_position)
                        for idx, result in enumerate(finish_order):
                            result._finish_position = idx+1

                    race_penalty = False
                    for time_penalty in self.time_penalties:
                        for rr in race.grid.values():
                            if time_penalty.race == race_num and time_penalty.cust_id == rr.cust_id:
                                driver = lg.get_driver(rr.cust_id)
                                if rr.interval < 0:
                                    _logger.error(f"Cannot apply a time penalty to {lg.get_member(rr.cust_id).nickname}"
                                                  f"({driver.car_number}) since they did not finish on the lead lap.")
                                    continue
                                race_penalty = True
                                rr._interval += time_penalty.seconds
                                _logger.info(f"A {time_penalty.seconds}s time penalty has been applied to "
                                             f"{lg.get_member(rr.cust_id).nickname}({driver.car_number})")

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

                    # Gather up some race statistics
                    # TODO do we want to save this out?
                    final_group_order = {}
                    group_overall_winning_position = {}
                    for rr in race.grid.values():
                        driver = lg.get_driver(rr.cust_id)
                        if driver.group not in group_overall_winning_position:
                            final_group_order[driver.group] = []
                            group_overall_winning_position[driver.group] = rr._finish_position
                        final_group_order[driver.group].append(driver.car_number)

                    # Start scoring this race
                    if isinstance(scoring, LinearDecentScoring):
                        max_points = scoring.top_score
                        for rr in race.grid.values():
                            driver = lg.get_driver(rr.cust_id)
                            if not rr.met_minimum_distance:
                                rr._points = 0
                                continue

                            if not scoring.separate_pool:
                                rr._points = (max_points - rr._finish_position+1)
                            else:
                                if scoring.position_value == PositionValue.Overall:
                                    rr._points = (max_points -
                                                  (rr._finish_position - group_overall_winning_position[driver.group]))

                                elif scoring.position_value == PositionValue.Class:
                                    rr._points = (max_points - final_group_order[driver.group].index(driver.car_number))
                            rr._points = int(rr._points * multiplier.position)

                            if rr._points < 0:
                                rr._points = 0
                            driver._race_finish_points += rr._points  # Points without bonuses

                            if rr.laps_lead > 0:
                                rr._points += scoring.lead_a_lap.points * multiplier.lead_a_lap
                            # Allow leagues to add or separate clean driver points to the race points
                            if not scoring.clean_driver.separate_points:
                                rr._points += rr._clean_driver_points
                            if scoring.finish_race:
                                rr._points += rr._completed_race_points

                    elif isinstance(scoring, AssignmentScoring):
                        for rr in race.grid.values():
                            rr._points = 0
                            driver = lg.get_driver(rr.cust_id)
                            if not rr.met_minimum_distance:
                                rr._points = 0
                                continue

                            if not scoring.separate_pool:
                                if rr._finish_position in scoring.assignments:
                                    rr._points = scoring.assignments[rr._finish_position]
                            else:
                                scoring_position = 100
                                if scoring.position_value == PositionValue.Overall:
                                    scoring_position = rr._finish_position - group_overall_winning_position[driver.group]
                                elif scoring.position_value == PositionValue.Class:
                                    scoring_position = final_group_order[driver.group].index(driver.car_number)
                                scoring_position += 1  # Position assignment start at 1, not 0

                                if scoring_position in scoring.assignments:
                                    rr._points = scoring.assignments[scoring_position]
                            rr._points = int(rr._points * multiplier.position)
                            driver._race_finish_points += rr._points  # Points without bonuses

                            if rr.laps_lead > 0:
                                rr._points += scoring.lead_a_lap.points * multiplier.lead_a_lap
                            # Allow leagues to add or separate clean driver points to the race points
                            if not scoring.clean_driver.separate_points:
                                rr._points += rr._clean_driver_points
                            if scoring.finish_race:
                                rr._points += rr._completed_race_points

                    else:
                        _logger.fatal("Unknown scoring system provided")

                    # End of looping over every race in a season

                if ir_race_results is None:
                    _logger.info("\tRace " + str(race_num) + " at " + track_name + " has not completed yet.")
                    continue

            # Rate each driver
            ratings = list()
            finishing_positions = list()
            for race in lg.races.values():
                if race.grid_size == 0:
                    continue
                ratings.clear()
                finishing_positions.clear()
                for cust_id, my_driver in lg.drivers.items():
                    result = race.get_result(cust_id)
                    if result is None:  # Not in this race
                        finishing_positions.append(-1)
                    else:
                        finishing_positions.append(result.finish_position)
                    ratings.append((Rating(my_driver._mu, my_driver._sigma),))
                new_ratings = trueskill.rate(ratings, finishing_positions)
                for idx, driver in enumerate(lg.drivers.values()):
                    driver._mu = new_ratings[idx][0].mu
                    driver._sigma = new_ratings[idx][0].sigma
                    result = race.get_result(driver.cust_id)
                    if result is None:
                        continue  # The rating is propagated via the driver, not the result, so I think this is OK
                    result._mu = driver._mu
                    result._sigma = driver._sigma

            # Track group statistics after the season, since we don't know when the final groups are set
            # We will also compute trueskill ratings for each race based on finishing positions
            for race in lg.races.values():
                multiplier = scoring.get_race_multiplier(race.number)
                # Find the fastest lap and pole position for every group

                for result in race.grid.values():
                    driver = lg.get_driver(result.cust_id)
                    if driver.group == "Unknown":
                        _logger.fatal(f"You should add {result.cust_id} as a non driver")
                        exit(1)
                    race_stats = race.get_stats(driver.group)
                    race_stats._num_drivers += 1

                    race_stats.check_if_pole_position(result.cust_id, result.start_position)
                    if not result.met_minimum_distance:
                        continue  # I think you should still get your pole position point if you don't finish the race
                    race_stats.check_if_fastest_lap(result.cust_id, result.fastest_lap_time)
                    race_stats.check_if_winner(result.cust_id, result.finish_position)
                    race_stats.check_if_most_laps_lead(result.cust_id, result.laps_lead)
                    if result.laps_lead > 0:
                        race_stats.lead_a_lap_drivers.append(result.cust_id)

                # Now push those stats back into the results and drivers
                for grp, stat in race.stats.items():
                    if grp == "Unknown":
                        _logger.fatal(f"How did we get an Unknown group?")
                        exit(1)

                    dvr = lg.get_driver(stat.winning_driver)
                    dvr._total_wins += 1

                    rr = race.get_result(stat.pole_position_driver)
                    rr._pole_position = True
                    rr._points += self.scoring_system.pole_position * multiplier.pole_position
                    dvr = lg.get_driver(stat.pole_position_driver)
                    dvr._total_pole_positions += 1
                    dvr._pole_position_points += self.scoring_system.pole_position * multiplier.pole_position

                    if race.number in self._fast_laps_override:
                        if stat.fastest_lap_driver in self._fast_laps_override[race.number]:
                            new_fast_lap_id = self._fast_laps_override[race.number][stat.fastest_lap_driver]
                            _logger.info(f"Overriding fasting lap for race {race.number} from "
                                         f"{lg.get_driver(stat.fastest_lap_driver).name} to "
                                         f"{lg.get_driver(new_fast_lap_id).name}")
                            stat._fastest_lap_driver = new_fast_lap_id
                    rr = race.get_result(stat.fastest_lap_driver)
                    if rr is None:
                        _logger.warning("No fastest lap for race")
                        # You can have a race where noone sets a legal lap....
                    else:
                        rr._fastest_lap = True
                        rr._points += self.scoring_system.fastest_lap.points * multiplier.fastest_lap
                        dvr = lg.get_driver(stat.fastest_lap_driver)
                        dvr._total_fastest_laps += 1
                        dvr._fastest_lap_points += self.scoring_system.fastest_lap.points * multiplier.fastest_lap

                    if stat.most_laps_lead_driver is None:
                        print("most_laps_lead_driver is None")
                    rr = race.get_result(stat.most_laps_lead_driver)
                    rr._most_laps_lead = True
                    rr._points += self.scoring_system.most_laps_lead.points * multiplier.most_laps_lead
                    dvr = lg.get_driver(stat.most_laps_lead_driver)
                    dvr._total_most_laps_lead += 1
                    dvr._most_laps_lead_points += self.scoring_system.most_laps_lead.points * multiplier.most_laps_lead

            # Score each driver
            points = list()
            for cust_id, driver in lg.drivers.items():
                if driver.group == "Unknown":
                    continue
                lg.get_driver(cust_id)
                points.clear()
                num_races = 0
                hcp_points = []
                finishing_positions = []
                for race in lg.races.values():
                    result = race.get_result(cust_id)
                    if result is None:  # Not in this race
                        points.append(0)
                        hcp_points.append(0)
                    else:
                        num_races += 1
                        finishing_positions.append(result.finish_position)
                        result._handicap_points = 0
                        points.append(result.points)
                        # Apply a handicap if requested
                        if self.scoring_system.handicap:
                            # N = average points per race
                            # points added = 0.9 * (30 - N)
                            n = (sum(points) + sum(hcp_points)) / num_races
                            hcp = math.floor(0.90 * ((max_points * 0.75) - n))
                            result._handicap_points = hcp if hcp > 0 else 0
                            hcp_points.append(result._handicap_points)
                driver._earned_points = sum(points)
                driver._handicap_points = sum(points) + sum(hcp_points)
                driver._drop_points = 0
                races_counted = self.get_group_rules(driver.group).races_counted
                if len(points) > races_counted:
                    num_drops = len(points) - races_counted
                    driver._drop_points = sum(sorted(points)[:num_drops])
                if driver.total_completed_races > 0:
                    driver._average_finish = sum(finishing_positions) / len(finishing_positions)

        # End of looping over every season
        # print(dict(sorted(contacts.items(), key=lambda item: item[1])))
        return lg

    def fetch_and_score_hot_lap_league(self, idc: irDataClient, g61: Garage61Client, g612ir: dict) -> LeagueResult:
        lg = self.fetch_league_members(idc)

        def lap2str(_lap: dict):
            return f"\t{_lap['driver']['slug']} {time2str(_lap['lapTime'])} on {_lap['startTime']}"

        ir_league_info = idc.league_get(self._iracing_id)  # TODO replace with lg below
        ir_seasons = idc.league_seasons(self._iracing_id, True)["seasons"]
        _logger.info("Found " + str(len(ir_seasons)) + " seasons")
        scoring = self.scoring_system  # alias to shorten lines
        for ir_season in ir_seasons:
            if self._season != ir_season['season_name']:
                continue

            _logger.info(f"Pulling season {ir_season['season_name']}")
            # TODO We could pull with results_only False to detect if we are in season or not
            ir_sessions = idc.league_season_sessions(self._iracing_id, ir_season["season_id"], False)["sessions"]

            if len(self._manual_sessions) > 0:
                for idx, session in self._manual_sessions.items():
                    ir_sessions.insert(idx, session)

            _logger.info("There are " + str(len(ir_sessions)) + " sessions in season ")

            completed_races = 0
            race_num = 0
            race_session_num = 0
            for session_num, ir_session in enumerate(ir_sessions):
                race_num += 1
                track_name = ir_session["track"]["track_name"]
                track_config = None
                if "config_name" in ir_session["track"]:
                    track_config = ir_session["track"]["config_name"]
                track_id = ir_session["track"]["track_id"]
                weather = ir_session["weather"]
                car_ids = []
                for car in ir_session["cars"]:
                    car_ids.append(car["car_id"])
                session_launch = datetime.strptime(ir_session["launch_at"], '%Y-%m-%dT%H:%M:%SZ')
                utc = session_launch.replace(tzinfo=tz.tzutc())

                subsession_id = 0
                if "subsession_id" in ir_session:
                    subsession_id = ir_session["subsession_id"]

                _logger.info("\tSession " + str(race_num) + " at " + track_name)

                # Convert iRacing units to g61 units
                air_temp_c = (weather["temp_value"] - 32) * 0.555
                wind_m_per_s = weather["wind_value"] * 0.44704
                rel_humidity = weather["rel_humidity"] * 0.01

                window_start = session_launch - timedelta(days=7)  # TODO Make this delta a cfg variable
                window_end = session_launch + timedelta(minutes=ir_session["time_limit"])

                # https://garage61.net/developer
                all_g61_laps = g61.laps(teams=self._g61_id,
                                        cars=car_ids,
                                        tracks=track_id,
                                        group="none",
                                        include_unclean=True,
                                        date_after=window_start
                                        )
                # Apply filters (API filters don't work when getting all laps (??))
                """
                                # min_cond_track_usage=0,
                                # max_cond_track_usage=0,
                                min_cond_track_wetness=weather["track_water"],
                                max_cond_track_wetness=weather["track_water"],
                                # min_cond_track_temp=0,
                                # max_cond_track_temp=0,
                                min_cond_air_temp=air_temp_c,
                                max_cond_air_temp=air_temp_c,
                                min_cond_wind_vel=wind_m_per_s,
                                max_cond_wind_vel=wind_m_per_s,
                                min_cond_relative_humidity=weather["rel_humidity"],
                                max_cond_relative_humidity=weather["rel_humidity"],
                                min_cond_fog_level=weather["fog"],
                                max_cond_fog_level=weather["fog"],
                                min_cond_precipitation=weather["precip_option"],
                                max_cond_precipitation=weather["precip_option"],
                                # min_cond_cloud=weather["skies"],
                                # max_cond_cloud=weather["skies"],
                                cond_wind_dir=weather["wind_dir"],
                                # rounding="englishStandard"
                                )
                """

                race = lg.add_race(race_num,
                                   str(utc.astimezone(tz.gettz('America/New_York'))).split(' ')[0],
                                   ir_session["track"]["track_name"], subsession_id)
                # Sort laps
                lap_counts = {}
                for g61_lap in all_g61_laps:

                    driver_name = g61_lap["driver"]["firstName"] + " " + g61_lap["driver"]["lastName"]
                    cust_id = lg.get_cust_id(driver_name, clean_nums=True)
                    #if "Bast" in driver_name:
                    #    continue
                    #  if session_num == 3 and "Aaron" in driver_name:
                    #     print("Here")

                    # Time window check
                    lap_datetime = datetime.strptime(g61_lap["startTime"],
                                                     '%Y-%m-%dT%H:%M:%SZ')
                    if lap_datetime < window_start or lap_datetime > window_end:
                        _logger.info(f"Invalid Lap: Out of acceptable time window")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue

                    # There should not be a session id, since these should be done solo
                    # But it can be the league session
                    # Assuming its setup properly as solo quali, only laps from that quali session will be used
                    if g61_lap["session"] != 0 and g61_lap["session"] != subsession_id:
                        _logger.info(f"Invalid Lap: Not a TestDrive lap. Lap from session {g61_lap['session']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue
                    # Ensure this lap matches defined parameters
                    if percent_difference(air_temp_c, g61_lap["airTemp"]) > 0.25:
                        _logger.info(f"Invalid Lap: Failed Air Temp. Expected: {air_temp_c}, Lap {g61_lap['airTemp']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue
                    if percent_difference(wind_m_per_s, g61_lap["windVel"]) > 0.25:
                        _logger.info(
                            f"Invalid Lap: Failed Wind. Expected: {wind_m_per_s}, Lap {g61_lap['airTemp']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue
                    if percent_difference(rel_humidity, g61_lap["relativeHumidity"]) > 0.25:
                        _logger.info(
                            f"Invalid Lap: Failed Humidity. "
                            f"Expected: {rel_humidity}, Lap {g61_lap['relativeHumidity']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue
                    # Sky/Cloud values seem to be off by 1
                    if weather["skies"]+1 != g61_lap["clouds"]:
                        # TODO Sky mapping is weird between iR and g61... they just don't seem to match
                        _logger.info(
                            f"Invalid Lap: Failed Clouds. "
                            f"Expected: {weather['skies']+1}, Lap {g61_lap['clouds']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        #continue
                    if (weather["track_water"] == 0 and g61_lap["trackWetness"] != 0) or \
                       (weather["track_water"] == 3 and (67 < g61_lap["trackWetness"] < 50)):
                        _logger.info(
                            f"Invalid Lap: Failed wetness. "
                            f"Expected: {weather['track_water']}, Lap {g61_lap['trackWetness']}")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue

                    if g61_lap["joker"]:
                        _logger.info(
                            f"Invalid Lap: Joker lap.")
                        _logger.info(f"\t{lap2str(g61_lap)}")
                        continue

                    if cust_id is None:
                        if driver_name in g612ir:
                            cust_id = lg.get_cust_id(g612ir[driver_name], clean_nums=True)
                        if cust_id is None:
                            raise ValueError(f"Cannot find g61 driver {driver_name} in league")
                    driver = lg.add_driver(cust_id)
                    member = lg.get_member(cust_id)
                    if member is None:
                        driver._name = driver_name
                        lg.add_member(cust_id, driver._name, None)
                        _logger.info("Driver " + driver._name + " is not a league member. Ask them to join the league!")
                    else:
                        driver._name = member.name

                    if driver.car_number is None:
                        # Must be brand spanking new
                        driver_car_number = self._get_league_number(cust_id, ir_league_info["roster"])
                        if not driver_car_number:
                            driver_car_number = 42  # TODO Ensure league has numbers set?
                        driver.set_car_number(driver_car_number, self.get_group(driver_car_number))

                    if cust_id not in lap_counts:
                        lap_counts[cust_id] = 0
                    lap_counts[cust_id] += 1

                    result = race.add_result(cust_id)
                    result._laps_completed += 1
                    result._car = g61_lap["car"]["name"]
                    lap = result.add_lap()
                    lap._cust_id = cust_id
                    lap._position = 0
                    lap._number = lap_counts[cust_id]
                    lap._time = g61_lap["lapTime"]
                    lap._time_stamp = g61_lap["startTime"]
                    if not g61_lap["clean"] or g61_lap["offtrack"] or g61_lap["discontinuity"] or g61_lap["joker"] or \
                            g61_lap["incomplete"] or g61_lap["pitlane"] or g61_lap["pitIn"] or g61_lap["pitOut"]:
                        lap._clean = False
                        result._incidents += 1
                    else:
                        lap._clean = True
                        result._clean_laps += 1
                        # Add this time to our clean lap times
                        if not result.fastest_lap_time or lap.time < result.fastest_lap_time:
                            result._fastest_lap_time = lap._time
                            result._fastest_lap_time_stamp = lap._time_stamp

                # Sort and score fastest laps
                position = 0
                fastest_laps = []
                for cust_id, result in race.grid.items():
                    if result.fastest_lap_time:
                        fastest_laps.append((cust_id, result.fastest_lap_time))
                        # Loop over our laps and count how many fast clean laps we got
                        max_bonus_time = result.fastest_lap_time * scoring.fast_clean_laps.time_percent * 0.01
                        for lap in result.laps:
                            if not lap.clean:
                                continue
                            if lap.time <= max_bonus_time:
                                result._fast_clean_laps += 1
                        result._fast_clean_laps -= 1  # Take away the fast lap
                fastest_laps.sort(key=lambda item: item[1])
                for t in fastest_laps:
                    position += 1
                    rr = race.get_result(t[0])
                    rr._start_position = position
                    rr._finish_position = position
                    if isinstance(scoring, LinearDecentScoring):
                        pass
                    elif isinstance(scoring, AssignmentScoring):
                        if not scoring.separate_pool:
                            if rr._finish_position in scoring.assignments:
                                rr._points = scoring.assignments[rr._finish_position]
                        else:
                            raise Exception("Unsupported scoring configuration")

                # Increment driver stats
                finishings = {}
                for cust_id, result in race.grid.items():
                    driver = lg.get_driver(result.cust_id)
                    if result.cust_id not in finishings:
                        finishings[result.cust_id] = []
                    driver._race_finish_points += result._points
                    # Add in bonus points
                    result._clean_laps_points = int(result.clean_laps / scoring.clean_laps.num_laps) * scoring.clean_laps.points
                    result._fast_clean_laps_points = int(result.fast_clean_laps / scoring.fast_clean_laps.num_laps) * scoring.fast_clean_laps.points
                    result._points += result.clean_laps_points
                    result._points += result.fast_clean_laps_points
                    # Track some driver stats
                    driver._total_race_starts += 1
                    if result.finish_position == 1:
                        driver._total_wins += 1
                    driver._earned_points += result._points
                    driver._total_fast_clean_laps += result.fast_clean_laps
                    driver._fast_clean_laps_points += result.fast_clean_laps_points
                    driver._total_clean_laps += result.clean_laps
                    driver._clean_laps_points += result.fast_clean_laps_points
                    driver._total_incidents += result.incidents
                    driver._total_laps_complete += result.laps_completed
                    finishings[result.cust_id].append(result.finish_position)
                for cust_id, positions in finishings.items():
                    driver = lg.get_driver(cust_id)
                    # TODO Include races that driver did not participate in?
                    driver._average_finish = sum(positions) / len(positions)

        return lg


def serialize_points_threshold_to_bind(src: PointsThreshold, dst: PointsThresholdData):
    dst.MinimumRequirement = src.minimum_requirement
    dst.Points = src.points


def serialize_incident_points_to_bind(src: IncidentPoints, dst: IncidentPointsData):
    for num, value in src.point_map.items():
        dst.PointMap[num] = value
    dst.MinimumRequirement = src.minimum_requirement
    dst.SeparatePoints = src.separate_points


def serialize_league_configuration_to_string(src: LeagueConfiguration, fmt: SerializationFormat) -> str:
    dst = LeagueConfigurationData()
    serialize_league_configuration_to_bind(src, dst)
    return serialize_to_string(dst, fmt)


def serialize_league_configuration_to_bind(src: LeagueConfiguration, dst: LeagueConfigurationData):
    dst.iRacingID = src.iracing_id
    dst.g61ID = src.g61_id
    dst.Name = src.name
    dst.Season = src.season

    dst_scoring_system = None
    if isinstance(src.scoring_system, LinearDecentScoring):
        dst_scoring_system = dst.ScoringSystem.LinearDecent
        dst_scoring_system.TopScore = src.scoring_system.top_score
        dst_scoring_system.Handicap = src.scoring_system.handicap
    elif isinstance(src.scoring_system, AssignmentScoring):
        dst_scoring_system = dst.ScoringSystem.Assignment
        for pos, pts in src.scoring_system.assignments.items():
            dst_scoring_system.PositionScore[pos] = pts
    dst_scoring_system.Base.MinimumRaceDistance = src.scoring_system.minimum_race_distance
    dst_scoring_system.Base.PolePosition = src.scoring_system.pole_position
    serialize_points_threshold_to_bind(src.scoring_system.fastest_lap, dst_scoring_system.Base.FastestLap)
    serialize_points_threshold_to_bind(src.scoring_system.lead_a_lap, dst_scoring_system.Base.LeadALap)
    serialize_points_threshold_to_bind(src.scoring_system.most_laps_lead, dst_scoring_system.Base.MostLapsLead)
    serialize_points_threshold_to_bind(src.scoring_system.finish_race, dst_scoring_system.Base.FinishRace)
    serialize_incident_points_to_bind(src.scoring_system.clean_driver, dst_scoring_system.Base.CleanDriver)
    dst_scoring_system.Base.SeparatePool = src.scoring_system.separate_pool
    dst_scoring_system.Base.PositionValue = src.scoring_system.position_value.value
    for m in src.scoring_system._multipliers.values():
        rm = PointsMultiplierData()
        rm.Race = m.race
        rm.Position = m.position
        rm.CleanDriver = m.clean_driver
        rm.FastestLap = m.fastest_lap
        rm.FinishRace = m.finish_race
        rm.LeadALap = m.lead_a_lap
        rm.MostLapsLead = m.most_laps_lead
        rm.PolePosition = m.pole_position
        dst_scoring_system.Base.RaceMultiplier.append(rm)

    for cust_id in src.non_drivers:
        dst.NonDrivers.append(cust_id)

    for session_number in src.practice_sessions:
        dst.PracticeSessions.append(session_number)

    for group, rule in src.group_rules.items():
        gr = GroupRulesData()
        gr.Group = group
        gr.MinCarNumber = rule.min_car_number
        gr.MaxCarNumber = rule.max_car_number
        gr.RacesCounted = rule.races_counted
        dst.GroupRule.append(gr)

    for dq in src.disqualifications:
        pd = PenaltyData()
        pd.Race = dq.race
        pd.Driver = dq.cust_id
        dst.Disqualification.append(pd)

    for tp in src.time_penalties:
        tpd = TimePenaltyData()
        tpd.Base.Race = tp.race
        tpd.Base.Driver = tp.cust_id
        tpd.Seconds = tp.seconds
        dst.TimePenalty.append(tpd)


def serialize_points_threshold_from_bind(src: PointsThresholdData, dst: PointsThreshold):
    dst.minimum_requirement = src.MinimumRequirement
    dst.points = src.Points


def serialize_incident_points_from_bind(src: IncidentPointsData, dst: IncidentPoints):
    for num, value in src.PointMap.items():
        dst.point_map[num] = value
    dst.minimum_requirement = src.MinimumRequirement
    dst.separate_points = src.SeparatePoints


def serialize_league_configuration_from_string(src: str, fmt: SerializationFormat) -> LeagueConfiguration:
    lrd = LeagueConfigurationData()
    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        json_format.Parse(src, lrd)
    elif fmt == SerializationFormat.TEXT:
        text_format.Parse(src, lrd)
    else:
        lrd.ParseFromString(src)
    dst = LeagueConfiguration(lrd.iRacingID, lrd.g61ID)
    serialize_league_configuration_from_bind(lrd, dst)
    return dst


def serialize_league_configuration_from_bind(src: LeagueConfigurationData, dst: LeagueConfiguration):
    dst._name = src.Name
    dst._season = src.Season

    scoring = None
    scoring_base = None
    scoring_system = src.ScoringSystem.WhichOneof("System")
    if scoring_system == "LinearDecent":
        scoring_base = src.ScoringSystem.LinearDecent.Base
        scoring = dst.set_linear_decent_scoring(src.ScoringSystem.LinearDecent.TopScore,
                                                src.ScoringSystem.LinearDecent.Handicap)
    elif scoring_system == "Assignment":
        scoring_base = src.ScoringSystem.Assignment.Base
        scoring = dst.set_assignment_scoring(src.ScoringSystem.Assignment.PositionScore)
    scoring.minimum_race_distance = scoring_base.MinimumRaceDistance
    scoring.pole_position = scoring_base.PolePosition
    serialize_points_threshold_from_bind(scoring_base.FastestLap, scoring.fastest_lap)
    serialize_points_threshold_from_bind(scoring_base.LeadALap, scoring.lead_a_lap)
    serialize_points_threshold_from_bind(scoring_base.MostLapsLead, scoring.most_laps_lead)
    serialize_points_threshold_from_bind(scoring_base.FinishRace, scoring.finish_race)
    serialize_incident_points_from_bind(scoring_base.CleanDriver, scoring.clean_driver)
    scoring.separate_pool = scoring_base.SeparatePool
    scoring.position_value = PositionValue(scoring_base.PositionValue)
    for m_data in scoring_base.RaceMultiplier:
        m = scoring.add_race_multiplier(m_data.Race)
        m.position = m_data.Position
        m.clean_driver = m_data.CleanDriver
        m.fastest_lap = m_data.FastestLap
        m.finish_race = m_data.FinishRace
        m.lead_a_lap = m_data.LeadALap
        m.most_laps_lead = m_data.MostLapsLead
        m.pole_position = m_data.PolePosition

    dst.add_non_drivers(src.NonDrivers)

    dst.add_practice_sessions(src.PracticeSessions)

    for group_rule_data in src.GroupRule:
        dst.add_group_rule(group_rule_data.Group, GroupRules(group_rule_data.MinCarNumber,
                                                             group_rule_data.MaxCarNumber,
                                                             group_rule_data.RacesCounted))

    for dq_data in src.Disqualification:
        dst.add_disqualification(dq_data.Race, dq_data.Driver)

    for time_penalty_data in src.TimePenalty:
        dst.add_time_penalty(time_penalty_data.Base.Race,
                             time_penalty_data.Base.Driver,
                             time_penalty_data.Seconds)

    return dst
