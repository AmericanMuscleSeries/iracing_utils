# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import logging
import trueskill
from trueskill import Rating
from iracingdataapi.client import irDataClient

from google.protobuf import json_format, text_format
from league.objects_pb2 import *

from league.objects import Group, SerializationFormat, League


_ams_logger = logging.getLogger('ams')


class GroupRule:
    __slots__ = ["_min_car_number",
                 "_max_car_number",
                 "_group"
                 ]

    def __init__(self, min_car_number: int, max_car_number: int, group: Group):
        self._min_car_number = min_car_number
        self._max_car_number = max_car_number
        self._group = group

    @property
    def min_car_number(self): return self._min_car_number

    @property
    def max_car_number(self): return self._max_car_number

    @property
    def group(self): return self._group


class SeasonRace:
    __slots__ = ["_season",
                 "_race"
                 ]

    def __init__(self, season: int, race: int):
        self._season = season
        self._race = race

    @property
    def season(self): return self._season

    @property
    def race(self): return self._race


class TimePenalty(SeasonRace):
    __slots__ = ["_cust_id",
                 "_seconds"
                 ]

    def __init__(self, season: int, race: int, cust_id: int, seconds: int):
        super().__init__(season, race)
        self._cust_id = cust_id
        self._seconds = seconds

    @property
    def cust_id(self): return self._cust_id

    @property
    def seconds(self): return self._seconds


class LeagueResource:
    __slots__ = ["_ir_id",
                 "num_drops",
                 "non_drivers",
                 "practice_races",
                 "time_penalties",
                 "group_rules"
                 ]

    def __init__(self, ir_id: int):
        self._ir_id = ir_id
        self.num_drops = 0
        self.non_drivers = list()
        self.practice_races = list()
        self.group_rules = dict()
        self.time_penalties = list()

    def as_dict(self) -> dict:
        string = serialize_league_resource_to_string(self, SerializationFormat.JSON)
        return json.loads(string)

    @staticmethod
    def from_dict(d: dict):
        string = json.dumps(d)
        return serialize_league_resource_from_string(string, SerializationFormat.JSON)

    @property
    def ir_id(self): return self._ir_id

    def add_non_driver(self, cust_id: int):
        self.non_drivers.append(cust_id)

    def add_practice_race(self, season: int, race: int):
        self.practice_races.append(SeasonRace(season, race))

    def add_group_rule(self, season: int, rule: GroupRule):
        if season not in self.group_rules:
            self.group_rules[season] = list()
        self.group_rules[season].append(rule)

    def add_time_penalty(self, season: int, race: int, cust_id: int, seconds: int):
        self.time_penalties.append(TimePenalty(season, race, cust_id, seconds))

    def get_group(self, season: int, car_number: int) -> Group:
        if season not in self.group_rules:
            _ams_logger.error("No group rule found for season " + str(season))
            return Group.Unknown

        for rule in self.group_rules[season]:
            if rule.min_car_number <= car_number <= rule.max_car_number:
                return rule.group

        _ams_logger.error("No group rule found in season " + str(season) + " for car number " + str(car_number))
        return Group.Unknown

    def fetch_and_score_league(self, username: str, password: str, specific_seasons: list = None) -> League:
        my_league = League()
        # Pull everything from iracing
        idc = irDataClient(username, password)
        league_info = idc.league_get(self._ir_id)
        _ams_logger.info("Extracting data from league: " + league_info["league_name"])
        _ams_logger.info("There are " + str(len(league_info["roster"])) + " members in this league")
        for member in league_info["roster"]:
            my_league.add_member(member["cust_id"], member["display_name"], member["nick_name"])

        seasons = idc.league_seasons(self._ir_id, True)["seasons"]
        _ams_logger.info("Found " + str(len(seasons)) + " seasons")
        for season_num, season in enumerate(seasons):
            season_num += 1  # We store data in dicts, and it's just more conventional to start at 1
            if specific_seasons is not None and season_num not in specific_seasons:
                continue

            _ams_logger.info("Pulling season " + str(season_num))
            my_season = my_league.add_season(season_num)
            sessions = idc.league_season_sessions(self._ir_id, season["season_id"], True)["sessions"]
            _ams_logger.info("There were " + str(len(sessions)) + " sessions in season " + str(season_num))

            race_num = 0
            race_event = 0
            for session_num, session in enumerate(sessions):
                subsession = idc.result(subsession_id=session["subsession_id"])["session_results"]
                # Skip the session if there was no race
                race_results = None
                for event in subsession:
                    if event["simsession_type"] == 6:
                        race_results = event
                if race_results is None:
                    _ams_logger.info("Session " + str(session_num) + " was not a race.")
                    continue

                # Check if this race event was a practice race
                race_event += 1
                is_practice_race = False
                for practice_race in self.practice_races:
                    if practice_race.season == season_num and practice_race.race == race_event:
                        is_practice_race = True
                        break
                if is_practice_race:
                    _ams_logger.info("Session " + str(session_num) + " was a practice race. Skipping it.")
                    continue

                #  This is an actual race we are going to score
                race_num += 1
                _ams_logger.info("Session " + str(session_num) + " was a race!")
                _ams_logger.info("Processing it as race " + str(race_num))

                my_race = my_season.add_race(race_num, session["launch_at"].split('T')[0], session["track"]["track_name"])

                car_results = race_results["results"]
                # all_laps = idc.result_lap_chart_data(subsession_id=session["subsession_id"])

                # Loop over every driver in this race
                for car_result in car_results:
                    cust_id = car_result["cust_id"]
                    if cust_id in self.non_drivers:
                        _ams_logger.info("Skipping non-driver: "+my_league.get_member(cust_id).nickname)
                        continue

                    # Pull driver from race and add to season list of drivers
                    # We keep updating the season drivers as we go to preserve any change of number/group
                    # The last race is the number/group that will be preserved in the structure
                    # _ams_logger.info("Processing driver: " + my_league.get_member(cust_id).nickname)
                    my_driver = my_season.add_driver(cust_id)
                    driver_car_number = int(car_result["livery"]["car_number"])
                    my_driver.set_car_number(driver_car_number, self.get_group(season_num, driver_car_number))

                    # Just book keep, we will rack, stack, and score later
                    my_result = my_race.add_result(cust_id)
                    my_result._start_position = car_result["starting_position"]+1
                    my_result._finish_position = car_result["finish_position"]+1
                    my_result._interval = car_result["interval"] * 0.0001
                    my_result._incidents = car_result["incidents"]
                    my_result._laps_completed = car_result["laps_complete"]
                    my_result._laps_lead = car_result["laps_lead"]

                    # Increment driver counters
                    my_driver._total_races += 1
                    my_driver._total_incidents += my_result._incidents
                    my_driver._total_laps_lead += my_result._laps_lead
                    my_driver._total_laps_complete += my_result._laps_completed

                    # End of looping over every driver in a race

                # Apply any time penalties in this race
                race_penalty = False
                for time_penalty in self.time_penalties:
                    for rr in my_race.grid.values():
                        if time_penalty.season == season_num and \
                                time_penalty.race == race_num and \
                                time_penalty.cust_id == rr.cust_id:
                            if rr.interval < 0:
                                _ams_logger.error("Cannot apply a time penalty to " +
                                                  my_league.get_member(rr.cust_id).nickname +
                                                  " since they did not finish on the lead lap.")
                                continue
                            race_penalty = True
                            rr._interval += time_penalty.seconds
                            _ams_logger.info("A " + str(time_penalty.seconds) + "s time penalty has been applied to " +
                                             my_league.get_member(rr.cust_id).nickname)
                if race_penalty:  # Recalculate finish positions
                    # Penalties are added to the interval, and only to cars on the lead lap
                    # So we only need to update the finishing positions on lead lap cars
                    lead_laps = list()
                    for rr in my_race.grid.values():
                        if rr.interval >= 0:
                            lead_laps.append(rr)
                    # Sort the lead lap cars by interval
                    new_lead_laps = sorted(lead_laps, key=lambda x: x.interval)
                    for pos, rr in enumerate(new_lead_laps):
                        rr._finish_position = pos + 1

                # Start scoring this race
                max_points = 40
                for rr in my_race.grid.values():
                    rr._points = max_points - rr._finish_position+1
                    if rr._points < 0:
                        rr._points = 0
                    if rr._laps_lead > 0:
                        rr._points += 1
                    if rr._pole_position:
                        rr._points += 1
                    #if rr._fastest_lap:
                    #    rr._points += 1

                # End of looping over every race in a season

            # Score each driver
            my_points = list()
            for cust_id, my_driver in my_season.drivers.items():
                my_season.get_driver(cust_id)
                my_points.clear()
                for my_race in my_season.races.values():
                    my_result = my_race.get_result(cust_id)
                    if my_result is None:  # Not in this race
                        my_points.append(0)
                    else:
                        my_points.append(my_result.points)
                for drops in range(self.num_drops):
                    my_points.remove(min(my_points))
                my_driver._points = sum(my_points)

            # Rate each driver
            my_ratings = list()
            my_finishing_positions = list()
            for my_race in my_season.races.values():
                my_ratings.clear()
                my_finishing_positions.clear()
                for cust_id, my_driver in my_season.drivers.items():
                    my_result = my_race.get_result(cust_id)
                    if my_result is None:  # Not in this race
                        my_finishing_positions.append(-1)
                    else:
                        my_finishing_positions.append(my_result.finish_position)
                    my_ratings.append((Rating(my_driver._mu, my_driver._sigma),))
                new_ratings = trueskill.rate(my_ratings, my_finishing_positions)
                for idx, my_driver in enumerate(my_season.drivers.values()):
                    my_driver._mu = new_ratings[idx][0].mu
                    my_driver._sigma = new_ratings[idx][0].sigma
                    my_result = my_race.get_result(my_driver.cust_id)
                    if my_result is None:
                        continue  # The rating is propagated via the driver, not the result, so I think this is OK
                    my_result._mu = my_driver._mu
                    my_result._sigma = my_driver._sigma

            # Track group statistics after the season, since we don't know when the final groups are set
            # We will also compute trueskill ratings for each race based on finishing positions
            for my_race in my_season.races.values():
                # Find the fastest lap and pole position for every group

                for my_result in my_race.grid.values():
                    my_driver = my_season.get_driver(my_result.cust_id)
                    my_race_stats = my_race.get_stats(my_driver.group)
                    my_race_stats._num_drivers += 1
                    my_race_stats.check_if_pole_position(my_result.cust_id, my_result.start_position)
                    my_race_stats.check_if_fastest_lap(my_result.cust_id, my_result.fastest_lap)


                # Now push those stats back into the results and drivers
                for stat in my_race.stats.values():
                    rr = my_race.get_result(stat.fastest_lap_driver)
                    rr._fastest_lap = True
                    dvr = my_season.get_driver(stat.fastest_lap_driver)
                    dvr._total_fastest_laps += 1
                    rr = my_race.get_result(stat.pole_position_driver)
                    rr._pole_position = True
                    dvr._total_pole_positions += 1

        # End of looping over every season

        return my_league


def serialize_league_resource_to_string(src: LeagueResource, fmt: SerializationFormat) -> str:
    dst = LeagueResourceData()
    serialize_league_resource_to_bind(src, dst)

    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        verbose = True if fmt == SerializationFormat.VERBOSE_JSON else False
        return json_format.MessageToJson(dst, verbose, verbose)
    elif fmt == SerializationFormat.TEXT:
        return text_format.MessageToString(dst)
    else:
        return dst.SerializeToString()


def serialize_league_resource_to_bind(src: LeagueResource, dst: LeagueResourceData):
    dst.iRacingID = src.ir_id
    dst.NumDrops = src.num_drops

    for cust_id in src.non_drivers:
        dst.NonDrivers.append(cust_id)

    for pr in src.practice_races:
        srd = SeasonRaceData()
        srd.Season = pr.season
        srd.Race = pr.race
        dst.PracticeRace.append(srd)

    for season, group_rules in src.group_rules.items():
        for group_rule in group_rules:
            gr = GroupRuleData()
            gr.MinCarNumber = group_rule.min_car_number
            gr.MaxCarNumber = group_rule.max_car_number
            gr.Group = group_rule.group.value
            dst.SeasonGroupRules[season].GroupRule.append(gr)

    for tp in src.time_penalties:
        tpd = TimePenaltyData()
        tpd.SeasonRace.Season = tp.season
        tpd.SeasonRace.Race = tp.race
        tpd.Driver = tp.cust_id
        tpd.Seconds = tp.seconds
        dst.TimePenalty.append(tpd)


def serialize_league_resource_from_string(src: str, fmt: SerializationFormat) -> LeagueResource:
    lrd = LeagueResourceData()
    if fmt == SerializationFormat.JSON or fmt == SerializationFormat.VERBOSE_JSON:
        json_format.Parse(src, lrd)
    elif fmt == SerializationFormat.TEXT:
        text_format.Parse(src, lrd)
    else:
        lrd.ParseFromString(src)
    dst = LeagueResource(lrd.iRacingID)
    dst.num_drops = lrd.NumDrops
    for cust_id in lrd.NonDrivers:
        dst.add_non_driver(cust_id)
    for sr in lrd.PracticeRace:
        dst.add_practice_race(sr.Season, sr.Race)
    for season, grs in lrd.SeasonGroupRules.items():
        for gr in grs.GroupRule:
            dst.add_group_rule(season,
                               GroupRule(gr.MinCarNumber,
                                         gr.MaxCarNumber,
                                         Group(gr.Group))
                               )
    for tp in lrd.TimePenalty:
        dst.add_time_penalty(tp.SeasonRace.Season,
                             tp.SeasonRace.Race,
                             tp.Driver,
                             tp.Seconds)
    return dst

