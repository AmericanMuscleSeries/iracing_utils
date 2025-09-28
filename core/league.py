# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import math
import trueskill

from datetime import datetime
from dateutil import tz
from google.protobuf import json_format, text_format
from iracingdataapi.client import irDataClient
from trueskill import Rating

from core.objects import GroupRules, LeagueResult, PositionValue, SerializationFormat, serialize_to_string
from core.objects_pb2 import (GroupRulesData, LeagueConfigurationData,
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


class ScoringSystem:
    __slots__ = ["minimum_race_distance",
                 "pole_position",
                 "fastest_lap",
                 "lead_a_lap",
                 "most_laps_lead",
                 "finish_race",
                 "clean_driver",
                 "separate_pool",
                 "position_value",
                 "_handicap",
                 ]

    def __init__(self):
        self.minimum_race_distance = 0
        self.pole_position = 0
        self.fastest_lap = PointsThreshold()
        self.lead_a_lap = PointsThreshold()
        self.most_laps_lead = PointsThreshold()
        self.finish_race = PointsThreshold()
        self.clean_driver = IncidentPoints()
        self.separate_pool = False
        self.position_value = PositionValue.Overall
        self._handicap = False

    @property
    def handicap(self): return self._handicap


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
                 "_name",
                 "_season",
                 "scoring_system",
                 "non_drivers",
                 "practice_sessions",
                 "group_rules",
                 "time_penalties",
                 "disqualifications"
                 ]

    def __init__(self, iracing_id: int, season: str = ""):
        self._iracing_id = iracing_id
        self._name = None
        self._season = season
        self.scoring_system = None
        self.non_drivers = list()
        self.practice_sessions = list()
        self.group_rules = dict()
        self.time_penalties = list()
        self.disqualifications = list()

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

    def get_group(self, car_number: int) -> str:
        for group, rule in self.group_rules.items():
            if rule.min_car_number <= car_number <= rule.max_car_number:
                return group

        _logger.error("No group rule found in season " + str(self.season) + " for car number " + str(car_number))
        return "Unknown"

    def fetch_league_members(self, username: str, password: str):
        lg = LeagueResult()
        # Pull everything from iracing
        idc = irDataClient(username, password)
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
    def fetch_all_season_names(username: str, password: str, league_id: int) -> list:
        idc = irDataClient(username, password)
        ir_league_info = idc.league_get(league_id)  # TODO replace with lg below
        ir_seasons = idc.league_seasons(league_id, True)["seasons"]
        names = []
        for ir_season in ir_seasons:
            names.append(ir_season["season_name"])
        return names

    def fetch_and_score_league(self, username: str, password: str, active: bool = True) -> LeagueResult:
        lg = self.fetch_league_members(username, password)

        idc = irDataClient(username, password)
        ir_league_info = idc.league_get(self._iracing_id)  # TODO replace with lg below
        ir_seasons = idc.league_seasons(self._iracing_id, True)["seasons"]
        _logger.info("Found " + str(len(ir_seasons)) + " seasons")
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

                #  This is an actual race we are going to score
                race_num += 1
                _logger.info("Session " + str(session_num) + " at " + track_name + " is race " + str(race_num))

                # Sessions are in UTC time, convert to local
                utc = datetime.strptime(ir_session["launch_at"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.tzutc())
                race = lg.add_race(race_num,
                                   str(utc.astimezone(tz.gettz('America/New_York'))).split(' ')[0],
                                   ir_session["track"]["track_name"])

                # Check to see if its run yet
                if "subsession_id" not in ir_session:
                    _logger.info("\tRace " + str(race_num) + " at " + track_name + " has not run yet.")
                    continue
                try:
                    ir_subsession = idc.result(subsession_id=ir_session["subsession_id"])
                except RuntimeError:
                    _logger.error("\tRace " + str(race_num) + " at " + track_name + " is currently running?")
                    continue
                ir_subsession_results = ir_subsession["session_results"]
                ir_race_results = None
                for ir_event in ir_subsession_results:
                    if ir_event["simsession_type"] == 6:
                        ir_race_results = ir_event
                if ir_race_results is None:
                    _logger.info("\tRace " + str(race_num) + " at " + track_name + " has not completed yet.")
                    continue

                if ir_subsession["event_laps_complete"] == 0:
                    _logger.info("\tRace " + str(race_num) + " at " + track_name + " had no laps run, skipping.")
                    continue

                completed_races += 1
                ir_car_results = ir_race_results["results"]
                ir_total_laps = ir_car_results[0]["laps_complete"]

                # Figure out the class leader for every lap
                group_lap_leaders = {}
                for group in self.group_rules.keys():
                    laps = {}
                    for i in range(ir_total_laps):
                        laps[i+1] = {"cust_id": -1, "position": 999}
                    group_lap_leaders[group] = laps
                all_laps = idc.result_lap_chart_data(subsession_id=ir_session["subsession_id"])
                for lap in all_laps:
                    lap_number = lap["lap_number"]
                    if lap_number == 0:
                        continue
                    cust_id = lap["cust_id"]
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

                # Loop over every driver in this race
                for ir_car_result in ir_car_results:
                    cust_id = ir_car_result["cust_id"]
                    if cust_id in self.non_drivers:
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

                    """ Counts all car contacts
                    all_laps = idc.result_lap_data(subsession_id=ir_session["subsession_id"], cust_id=cust_id)
                    for lap in all_laps:
                        for event in lap["lap_events"]:
                            if "contact" in event:
                                if driver.name not in contacts:
                                    contacts[driver.name] = 0
                                contacts[driver.name] += 1
                    """

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
                    result._interval = ir_car_result["interval"] * 0.0001
                    result._incidents = ir_car_result["incidents"]
                    result._laps_completed = ir_car_result["laps_complete"]
                    result._laps_lead = 0
                    result._fastest_lap_time = 9999999
                    result._clean_driver_points = 0
                    result._completed_race_points = 0
                    result._met_minimum_distance = False

                    if result._laps_completed/ir_total_laps >= self.scoring_system.minimum_race_distance:
                        driver._total_completed_races += 1
                        result._met_minimum_distance = True

                        if self.scoring_system.lead_a_lap.satisfied(result._laps_completed, ir_total_laps):
                            result._laps_lead = 0 if cust_id not in laps_lead else laps_lead[cust_id]

                        if self.scoring_system.fastest_lap.satisfied(result._laps_completed, ir_total_laps):
                            result._fastest_lap_time = ir_car_result["best_lap_time"]

                        if self.scoring_system.clean_driver.satisfied(result._laps_completed, ir_total_laps):
                            if result._incidents in self.scoring_system.clean_driver.point_map:
                                result._clean_driver_points = self.scoring_system.clean_driver.point_map[result._incidents]

                        if self.scoring_system.finish_race.satisfied(result._laps_completed, ir_total_laps):
                            result._completed_race_points = self.scoring_system.finish_race.points

                        if result._laps_lead > 0:
                            driver._total_lead_a_lap += 1
                            driver._lead_a_lap_points += self.scoring_system.lead_a_lap.points

                    # Increment driver counters
                    driver._total_race_starts += 1
                    driver._total_incidents += result._incidents
                    driver._total_laps_complete += result._laps_completed
                    driver._clean_driver_points += result._clean_driver_points
                    driver._completed_race_points += result._completed_race_points
                    driver._total_lead_a_lap += result._laps_lead
                # End of looping over every driver in a race

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
                if isinstance(self.scoring_system, LinearDecentScoring):
                    max_points = self.scoring_system.top_score
                    for rr in race.grid.values():
                        driver = lg.get_driver(rr.cust_id)
                        if not rr.met_minimum_distance:
                            rr._points = 0
                            continue

                        if not self.scoring_system.separate_pool:
                            rr._points = max_points - rr._finish_position+1
                        else:
                            if self.scoring_system.position_value == PositionValue.Overall:
                                rr._points = (max_points -
                                              (rr._finish_position - group_overall_winning_position[driver.group]))

                            elif self.scoring_system.position_value == PositionValue.Class:
                                rr._points = (max_points - final_group_order[driver.group].index(driver.car_number))

                        if rr._points < 0:
                            rr._points = 0
                        driver._race_finish_points += rr._points  # Points without bonuses
                        if rr.laps_lead > 0:
                            rr._points += self.scoring_system.lead_a_lap.points
                        # Allow leagues to add or separate clean driver points to the race points
                        if not self.scoring_system.clean_driver.separate_points:
                            rr._points += rr._clean_driver_points
                        if self.scoring_system.finish_race:
                            rr._points += rr._completed_race_points

                elif isinstance(self.scoring_system, AssignmentScoring):
                    for rr in race.grid.values():
                        rr._points = 0
                        driver = lg.get_driver(rr.cust_id)
                        if not rr.met_minimum_distance:
                            rr._points = 0
                            continue

                        if not self.scoring_system.separate_pool:
                            if rr._finish_position in self.scoring_system.assignments:
                                rr._points = self.scoring_system.assignments[rr._finish_position]
                        else:
                            scoring_position = 100
                            if self.scoring_system.position_value == PositionValue.Overall:
                                scoring_position = rr._finish_position - group_overall_winning_position[driver.group]
                            elif self.scoring_system.position_value == PositionValue.Class:
                                scoring_position = final_group_order[driver.group].index(driver.car_number)
                            scoring_position += 1  # Position assignment start at 1, not 0

                            if scoring_position in self.scoring_system.assignments:
                                rr._points = self.scoring_system.assignments[scoring_position]

                        driver._race_finish_points += rr._points  # Points without bonuses
                        if rr.laps_lead > 0:
                            rr._points += self.scoring_system.lead_a_lap.points
                        # Allow leagues to add or separate clean driver points to the race points
                        if not self.scoring_system.clean_driver.separate_points:
                            rr._points += rr._clean_driver_points
                        if self.scoring_system.finish_race:
                            rr._points += rr._completed_race_points

                else:
                    _logger.fatal("Unknown scoring system provided")

                # End of looping over every race in a season

            # Rate each driver
            ratings = list()
            finishing_positions = list()
            for race in lg.races.values():
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
                    rr._points += self.scoring_system.pole_position
                    dvr = lg.get_driver(stat.pole_position_driver)
                    dvr._total_pole_positions += 1
                    dvr._pole_position_points += self.scoring_system.pole_position

                    rr = race.get_result(stat.fastest_lap_driver)
                    if rr is None:
                        _logger.warning("No fastest lap for race")
                        # You can have a race where noone sets a legal lap....
                    else:
                        rr._fastest_lap = True
                        rr._points += self.scoring_system.fastest_lap.points
                        dvr = lg.get_driver(stat.fastest_lap_driver)
                        dvr._total_fastest_laps += 1
                        dvr._fastest_lap_points += self.scoring_system.fastest_lap.points

                    rr = race.get_result(stat.most_laps_lead_driver)
                    rr._most_laps_lead = True
                    rr._points += self.scoring_system.most_laps_lead.points
                    dvr = lg.get_driver(stat.most_laps_lead_driver)
                    dvr._total_most_laps_lead += 1
                    dvr._most_laps_lead_points += self.scoring_system.most_laps_lead.points

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
                num_drops = self.get_group_rules(driver.group).num_drops
                if 0 < num_drops and completed_races >= len(points)/2:
                    num_drops = len(points) - completed_races + num_drops
                    driver._drop_points = sum(sorted(points)[:num_drops])
                if driver.total_completed_races > 0:
                    driver._average_finish = sum(finishing_positions) / len(finishing_positions)

        # End of looping over every season
        # print(dict(sorted(contacts.items(), key=lambda item: item[1])))
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

    for cust_id in src.non_drivers:
        dst.NonDrivers.append(cust_id)

    for session_number in src.practice_sessions:
        dst.PracticeSessions.append(session_number)

    for group, rule in src.group_rules.items():
        gr = GroupRulesData()
        gr.Group = group
        gr.MinCarNumber = rule.min_car_number
        gr.MaxCarNumber = rule.max_car_number
        gr.NumberOfDrops = rule.num_drops
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
    dst = LeagueConfiguration(lrd.iRacingID)
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

    dst.add_non_drivers(src.NonDrivers)

    dst.add_practice_sessions(src.PracticeSessions)

    for group_rule_data in src.GroupRule:
        dst.add_group_rule(group_rule_data.Group, GroupRules(group_rule_data.MinCarNumber,
                                                             group_rule_data.MaxCarNumber,
                                                             group_rule_data.NumberOfDrops))

    for dq_data in src.Disqualification:
        dst.add_disqualification(dq_data.Race, dq_data.Driver)

    for time_penalty_data in src.TimePenalty:
        dst.add_time_penalty(time_penalty_data.Base.Race,
                             time_penalty_data.Base.Driver,
                             time_penalty_data.Seconds)

    return dst
