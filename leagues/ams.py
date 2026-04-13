# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

from score_league import score_league
from core.clients import Client
from core.league import (LeagueConfiguration, GroupRules,
                         serialize_league_configuration_to_string, serialize_league_configuration_from_string)
from core.objects import Driver, LeagueResult, PositionValue, SerializationFormat
from core.sheets import SheetsDisplay

__league_id = 6810
__league_name = "American Muscle Series"


def main():
    args = Client(log_filename="ams.log")

    """
    legacy = [get_season_1_cfg(),
              get_season_2_cfg(),
              get_season_3_cfg(),
              get_season_4_cfg(),
              get_season_5_cfg(),
              get_season_6_cfg(),
              get_season_7_cfg(),
              get_season_8_cfgs(),
              get_season_9_cfgs()]
    for cfgs in legacy:
        for cfg in cfgs:
            score_league(cfg, active=False)
    """

    cfgs = get_season_10_cfgs()
    for cfg in cfgs:
        score_league(args, cfg, AMSSheetsDisplay("1gONBb0VYbYOmyw0xUWbHS7hrOYu1XBnMzUrru18B9ho"))
        json = serialize_league_configuration_to_string(cfg, SerializationFormat.JSON)
        with open("example.txt", "w") as file:
            file.write(json)
        serialize_league_configuration_from_string(json, SerializationFormat.JSON)


class AMSSheetsDisplay(SheetsDisplay):
    __slots__ = ["handicap"]

    def __init__(self, sheet_id: str):
        super().__init__(sheet_id)
        self.handicap = False

    def create_row(self, cust_id: int, driver: Driver, lgr: LeagueResult) -> list:
        row = list()  # Make a list per driver row
        # These 4 should always be the same between SheetsDisplays
        row.append(driver.name)
        row.append(driver.car_number)
        row.append(driver.earned_points)
        if self.handicap:
            row.append(driver.handicap_points)
        else:
            row.append(driver.earned_points - driver.drop_points)

        row.append(driver.clean_driver_points)
        row.append(driver.total_incidents)
        row.append(driver.total_wins)
        row.append(driver.total_race_starts)
        row.append("{:.1f}".format(driver.average_finish))
        row.append(driver.race_finish_points)
        row.append(driver.pole_position_points)
        row.append(driver.lead_a_lap_points)
        row.append(driver.most_laps_lead_points)
        row.append(driver.fastest_lap_points)
        row.append("{:.2f}".format(driver.mu))
        row.append("{:.2f}".format(driver.sigma))

        for race_number in range(len(lgr.races)):
            result = lgr.get_race(race_number + 1).get_result(cust_id)
            if result is None:
                for i in range(self.num_race_cells):
                    row.append("")
            else:
                row.append(result.start_position)
                row.append(result.finish_position)
                row.append(result.points)
                row.append("Y" if result.pole_position else "")
                row.append("Y" if result.laps_lead > 0 else "")
                row.append("Y" if result.fastest_lap else "")
                if self.handicap:
                    row.append(result.handicap_points)  # HCP
                row.append(result.incidents)
                row.append(result.clean_driver_points)
                row.append(result.laps_completed)
                row.append(result.laps_lead)
                row.append("{:.2f}".format(result.mu))
                row.append("{:.2f}".format(result.sigma))
        return row

    @property
    def num_race_cells(self):
        if self.handicap:
            return 13
        return 12

    @property
    def race_start_column(self): return 'R'


def get_season_10_cfgs() -> list[LeagueConfiguration]:
    cfgs = []
    num_races = 14
    num_drops = 3
    num_races_for_drops = 7
    for i in range(2):
        if i == 0:
            cfg = LeagueConfiguration(__league_name+" All", iracing_id=__league_id, season="Season 10", num_races=num_races)
            scoring = cfg.set_linear_decent_scoring(40, hcp=False)
            cfg.add_group_rule("All Drivers", GroupRules(0, 299, num_drops, num_races_for_drops))
        elif i == 1:
            cfg = LeagueConfiguration(__league_name, iracing_id=__league_id, season="Season 10", num_races=num_races)
            scoring = cfg.set_assignment_scoring(assignments={1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                              6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                              11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                              16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                              21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                              26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                              31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                              36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                              41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                              46: 1},
                                                 separate_pool=True,
                                                 position_value=PositionValue.Overall)
            cfg.add_group_rule("Pro Drivers", GroupRules(0, 99, num_drops, num_races_for_drops))
            cfg.add_group_rule("Ch Drivers", GroupRules(100, 199, num_drops, num_races_for_drops))
            cfg.add_group_rule("Am Drivers", GroupRules(200, 299, num_drops, num_races_for_drops))
        else:
            raise IndexError("Unknown configuration")

        if scoring:
            scoring.pole_position = 1
            scoring.fastest_lap.points = 1
            scoring.fastest_lap.minimum_requirement = 0
            scoring.lead_a_lap.points = 1
            scoring.lead_a_lap.minimum_requirement = 0
            scoring.most_laps_lead.points = 0
            scoring.most_laps_lead.minimum_requirement = 0
            scoring.clean_driver.point_map = {0: 3,
                                              1: 2,
                                              2: 1,
                                              3: 1,
                                              4: 1}
            scoring.clean_driver.minimum_requirement = 0.5
            scoring.clean_driver.separate_points = True

        # Add non drivers like race control and media personalities
        cfg.add_non_driver(295683)  # Richey
        cfg.add_non_driver(345352)  # McGrew

        # Ignore practice races
        cfg.add_practice_sessions([1])

        # Apply Penalties
        cfg.add_time_penalty(7, 511982, 5)   # Cicchetti (211)
        cfg.add_time_penalty(7, 143379, 20)  # Belant (21)
        cfg.add_time_penalty(7, 142499, 10)  # Fensch (42)

        # Bathurst pit entry line is after the start finish, so you can gain time unfairly on your in lap
        cfg.override_fastest_lap(8, from_id=143379, to_id=1012907)  # From Belant (21) to Schnackel (23)

        cfgs.append(cfg)

    return cfgs


def get_season_9_cfgs() -> list[LeagueConfiguration]:
    cfgs = []
    scoring = None
    for i in range(2):
        cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 9")
        if i == 0:
            scoring = cfg.set_linear_decent_scoring(40, hcp=False)
            cfg.add_group_rule("All Drivers", GroupRules(0, 299, 2))
        elif i == 1:
            scoring = cfg.set_assignment_scoring(assignments={1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                              6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                              11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                              16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                              21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                              26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                              31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                              36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                              41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                              46: 1},
                                                 separate_pool=True,
                                                 position_value=PositionValue.Overall)
            cfg.add_group_rule("Pro Drivers", GroupRules(0, 99, 2))
            cfg.add_group_rule("Ch Drivers", GroupRules(100, 199, 2))
            cfg.add_group_rule("Am Drivers", GroupRules(200, 299, 2))

        if scoring:
            scoring.pole_position = 1
            scoring.fastest_lap.points = 1
            scoring.fastest_lap.minimum_requirement = 0
            scoring.lead_a_lap.points = 1
            scoring.lead_a_lap.minimum_requirement = 0
            scoring.most_laps_lead.points = 0
            scoring.most_laps_lead.minimum_requirement = 0
            scoring.clean_driver.point_map = {0: 3,
                                              1: 2,
                                              2: 1,
                                              3: 1,
                                              4: 1}
            scoring.clean_driver.minimum_requirement = 0.5
            scoring.clean_driver.separate_points = True
            # Double up points for race 12
            multiplier = scoring.add_race_multiplier(race=12)
            multiplier.position = 2
            multiplier.pole_position = 2
            multiplier.fastest_lap = 2
            multiplier.lead_a_lap = 2

        # Add non drivers like race control and media personalities
        cfg.add_non_driver(295683)  # Richey
        cfg.add_non_driver(345352)  # McGrew

        # Ignore practice races

        # Apply Penalties
        cfg.add_time_penalty(5, 326705, 20)   # Henriquez (6)
        cfg.add_time_penalty(5, 1012907, 20)  # Schnackel (23)
        cfg.add_time_penalty(5, 563709, 10)   # Weant     (228)
        cfg.add_time_penalty(5, 67967, 5)     # Brooks    (299)
        cfg.add_time_penalty(7, 410773, 5)    # Price     (298)
        cfg.add_time_penalty(8, 565548, 20)   # Powell    (103)
        # Could not clear some black flags fast enough
        cfg.override_finish_order(race=12, order=[197, 13, 133, 297, 34, 139, 99, 53, 152, 2, 24, 41, 103, 129, 199,
                                                  144, 277, 35, 163, 6, 181, 21, 278, 180, 48, 299, 100, 229, 104, 157,
                                                  228, 83, 218, 69, 23, 136])
        cfg.override_laps_lead(12, 480781, 0)  # Thompson (133)
        cfg.override_laps_lead(12, 528770, 1)  # Smith (197)

        cfgs.append(cfg)

    return cfgs


def get_season_8_cfgs() -> list[LeagueConfiguration]:
    cfgs = []
    scoring = None
    for i in range(2):
        cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 8")
        if i == 0:
            scoring = cfg.set_linear_decent_scoring(40, hcp=False)
            cfg.add_group_rule("All Drivers", GroupRules(0, 299, 2))
        elif i == 1:
            scoring = cfg.set_assignment_scoring(assignments={1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                              6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                              11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                              16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                              21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                              26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                              31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                              36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                              41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                              46: 1},
                                                 separate_pool=True,
                                                 position_value=PositionValue.Overall)
            cfg.add_group_rule("Pro Drivers", GroupRules(0, 99, 2))
            cfg.add_group_rule("Ch Drivers", GroupRules(100, 199, 2))
            cfg.add_group_rule("Am Drivers", GroupRules(200, 299, 2))

        if scoring:
            scoring.pole_position = 1
            scoring.fastest_lap.points = 1
            scoring.fastest_lap.minimum_requirement = 0
            scoring.lead_a_lap.points = 1
            scoring.lead_a_lap.minimum_requirement = 0
            scoring.most_laps_lead.points = 0
            scoring.most_laps_lead.minimum_requirement = 0
            scoring.clean_driver.point_map = {0: 3,
                                              1: 2,
                                              2: 1,
                                              3: 1,
                                              4: 1}
            scoring.clean_driver.minimum_requirement = 0.5
            scoring.clean_driver.separate_points = True

        # Add non drivers like race control and media personalities
        cfg.add_non_driver(295683)  # Richey
        cfg.add_non_driver(345352)  # McGrew

        # Ignore practice races
        cfg.add_practice_sessions([1, 2])

        # Apply Penalties
        cfg.add_time_penalty(5, 417105, 20)   # Hosea
        cfg.add_time_penalty(5, 920078, 10)   # Weaver
        cfg.add_time_penalty(5, 71668, 5)     # Buchholz
        cfg.add_time_penalty(10, 88930, 5)    # Kemp
        cfg.add_time_penalty(11, 511982, 20)  # Cicchetti

        cfgs.append(cfg)

    return cfgs


def get_season_7_cfg() -> list[LeagueConfiguration]:
    cfgs = []
    scoring = None
    for i in range(2):
        cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 7")
        if i == 0:
            scoring = cfg.set_linear_decent_scoring(40, hcp=False)
            cfg.add_group_rule("All Drivers", GroupRules(0, 299, 2))
        elif i == 1:
            scoring = cfg.set_assignment_scoring(assignments={1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                              6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                              11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                              16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                              21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                              26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                              31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                              36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                              41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                              46: 1},
                                                 separate_pool=True,
                                                 position_value=PositionValue.Overall)
            cfg.add_group_rule("Pro Drivers", GroupRules(0, 99, 2))
            cfg.add_group_rule("Ch Drivers", GroupRules(100, 199, 2))
            cfg.add_group_rule("Am Drivers", GroupRules(200, 299, 2))

        if scoring:
            scoring.pole_position = 1
            scoring.fastest_lap.points = 1
            scoring.fastest_lap.minimum_requirement = 0
            scoring.lead_a_lap.points = 1
            scoring.lead_a_lap.minimum_requirement = 0
            scoring.most_laps_lead.points = 0
            scoring.most_laps_lead.minimum_requirement = 0
            scoring.clean_driver.point_map = {0: 3,
                                              1: 2,
                                              2: 1,
                                              3: 1,
                                              4: 1}
            scoring.clean_driver.minimum_requirement = 0.5
            scoring.clean_driver.separate_points = True

        # Ignore practice races
        cfg.add_practice_sessions([1, 2, 3])

        # Apply Penalties

        cfg.add_time_penalty(1, 459211, 10)  # Pucyk
        # Spa
        cfg.add_time_penalty(2, 821509, 60)  # Sudenga
        cfg.add_time_penalty(2, 481375, 30)  # Campbell
        # Homestead
        cfg.add_time_penalty(3, 71668, 10)  # Buchholz
        cfg.add_time_penalty(3, 342356, 10)  # Royce
        # Sebring
        cfg.add_time_penalty(4, 459211, 15)  # Pucyk
        cfg.add_time_penalty(4, 342356, 15)  # Royce
        cfg.add_time_penalty(4, 345352, 20)  # McFinger
        # Brands Hatch
        cfg.add_time_penalty(5, 823724, 10)  # Parrish
        # Nurburgring
        cfg.add_time_penalty(6, 88930, 5)  # Kemp
        # Barcelona
        cfg.add_time_penalty(9, 360361, 3)  # Moore

        cfgs.append(cfg)

    return cfgs


def get_season_6_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 6")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True

    # Set up our grouping rules per season
    cfg.add_group_rule("Pro", GroupRules(0, 99, 2))
    cfg.add_group_rule("Am", GroupRules(100, 199, 2))

    # Ignore practice races
    cfg.add_practice_sessions([1, 2])

    # Apply Penalties
    cfg.add_time_penalty(2, 310239, 10)
    cfg.add_time_penalty(6, 189468, 10)
    cfg.add_time_penalty(7, 85279, 5)
    cfg.add_time_penalty(10, 71668, 5)
    return [cfg]


def get_season_5_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 5")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True
    # Add non drivers like race control and media personalities
    cfg.add_non_driver(295683)
    cfg.add_non_driver(366513)

    # Set up our grouping rules per season
    cfg.add_group_rule("Pro", GroupRules(0, 99, 2))
    cfg.add_group_rule("Am", GroupRules(100, 199, 2))

    # Let's ignore practice sessions
    # This will result in the third race session as being race 1
    # NOTE: This is the number of the league race sessions
    cfg.add_practice_sessions([1, 2])

    # Apply Penalties
    cfg.add_time_penalty(2, 821509, 5)
    cfg.add_time_penalty(3, 823724, 5)
    # You can only apply a time penalty on drivers that finish on the lead lap, an error will be logged
    # lr.add_time_penalty(5, 1, 413722, 5)  # This driver did not finish on lead lap

    return [cfg]


def get_season_4_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 4")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    return [cfg]


def get_season_3_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 3")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    return [cfg]


def get_season_2_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 2")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    return [cfg]


def get_season_1_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 1")
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 0
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 3,
                                      1: 2,
                                      2: 1,
                                      3: 1,
                                      4: 1}
    scoring.clean_driver.minimum_requirement = 0.5
    scoring.clean_driver.separate_points = True
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    return [cfg]


if __name__ == "__main__":
    main()
