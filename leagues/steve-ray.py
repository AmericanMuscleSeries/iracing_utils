# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import logging

from enum import Enum

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules, PositionValue
from core.objects import Driver, LeagueResult
from core.sheets import SheetsDisplay, SortBy

__ff = 9555
__fv = 6956
__srf = 1566
__ecr = 6236


class LeagueType(Enum):
    FF = 0
    FV = 1
    SRF = 2
    WW = 3
    ECR = 4


def main():
    cfgs = []
    lt = LeagueType.SRF

    if lt == LeagueType.FF or lt == LeagueType.WW:
        # s = ["2025 S1 FF Weekend Warriors", "1YsYm0TRjSjIR1r0EBxUCKq6yyRBgpHFe8F1dXhQAv0k"]
        s = ["2025 S2", "121Fx4vKQ2t5Urdzueq5LWqdhv_ksKIt0S4b9_wTlw2s"]
        cfgs.extend(_get_ww_configurations(__ff, s[0]))
    if lt == LeagueType.FV or lt == LeagueType.WW:
        # s = ["WW FV 2025 S1", "1W3gXY5wZzrYDoUL6_xbaK65KWI0dE_O_Ca-XRluq240"]
        s = ["WW FV 2025 S2", "1bFBGHBxaN6CdNBy3t-I_AByVmaZIB--_SF1wWbJgM4U"]
        cfgs.extend(_get_ww_configurations(__fv, s[0]))
    if lt == LeagueType.SRF or lt == LeagueType.WW:
        # s = ["2025 S1 SRF Weekend Warriors", "1yFPSQoAYfz5gch9TQgv7AIU6pvHLnElHZPIIqhs0KfU"]
        s = ["2025 S2", "1MbgV4Iwz2TPYMN5ZHiP0eXwltdvN1ML_zhZhOyp7cbk"]
        cfgs.extend(_get_ww_configurations(__srf, s[0]))
    if lt == LeagueType.ECR:
        s = [[("RES CRL FV Season 1", "FV"),
              #("RES CRL GT4 Season 1", "GT4"),
              ("RES CRL Miatas Season 1", "Miatas"),
              ("RES CRL SRF Season 1", "SRF"),
              ("RES CRL TCR Season 1", "TCR")],
             "1WgL6EExoj1nvSCml5S2htuGmKej7FMSC8eNQ3LGEBy0"]
        cfgs = _get_ecr_configurations(__ecr, s[0])

    score_league(cfgs, RaySheets(s[1]))


def _setup_scoring(cfg: LeagueConfiguration):
    scoring = cfg.set_assignment_scoring(assignments={1: 100, 2: 90, 3: 83, 4: 78, 5: 74,
                                                      6: 71, 7: 68, 8: 66, 9: 64, 10: 62,
                                                      11: 61, 12: 60, 13: 59, 14: 58, 15: 57,
                                                      16: 56, 17: 55, 18: 54, 19: 53, 20: 52,
                                                      21: 51, 22: 50, 23: 49, 24: 48, 25: 47,
                                                      26: 46, 27: 45, 28: 44, 29: 43, 30: 42,
                                                      31: 41, 32: 40, 33: 39, 34: 38, 35: 37,
                                                      36: 36, 37: 35, 38: 34, 39: 33, 40: 32,
                                                      41: 31, 42: 30, 43: 29, 44: 28, 45: 27,
                                                      46: 26, 47: 25, 48: 24, 49: 23, 50: 22,
                                                      51: 21, 52: 20, 53: 19, 54: 18, 55: 17,
                                                      56: 16, 57: 15, 58: 14, 59: 13, 60: 12},
                                         separate_pool=False,
                                         position_value=PositionValue.Overall)
    scoring.minimum_race_distance = 0.5
    scoring.pole_position = 0
    scoring.lead_a_lap.points = 1
    scoring.lead_a_lap.minimum_requirement = 0.9
    scoring.fastest_lap.points = 1
    scoring.fastest_lap.minimum_requirement = 0.5
    scoring.most_laps_lead.points = 3
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 4,
                                      1: 2}
    scoring.clean_driver.minimum_requirement = 0.75
    scoring.clean_driver.separate_points = False
    scoring.finish_race.points = 2
    scoring.finish_race.minimum_requirement = 0.8


class RaySheets(SheetsDisplay):

    def __init__(self, sheet_id: str):
        super().__init__(sheet_id)
        self.sort_by = SortBy.Earned

    def create_row(self, cust_id: int, driver: Driver, lgr: LeagueResult) -> list:
        row = list()  # Make a list per driver row
        # These 4 should always be the same between SheetsDisplays
        row.append(driver.name)
        row.append(driver.car_number)
        row.append(driver.earned_points)
        row.append(driver.earned_points - driver.drop_points)

        row.append(driver.total_incidents)
        row.append(driver.total_wins)
        row.append(driver.total_race_starts)
        row.append("{:.1f}".format(driver.average_finish))
        row.append(driver.race_finish_points)
        row.append(driver.most_laps_lead_points)
        row.append(driver.lead_a_lap_points)
        row.append(driver.fastest_lap_points)
        row.append(driver.completed_race_points)
        row.append(driver.clean_driver_points)
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
                row.append("Y" if result.most_laps_lead else "")
                row.append("Y" if result.laps_lead > 0 else "")
                row.append("Y" if result.fastest_lap > 0 else "")
                row.append("Y" if result.completed_race_points else "")
                row.append("Y" if result.clean_driver_points else "")
                row.append(result.incidents)
                row.append(result.laps_completed)
                row.append(result.laps_lead)
                row.append("{:.2f}".format(result.mu))
                row.append("{:.2f}".format(result.sigma))
        return row

    @property
    def num_race_cells(self): return 13

    @property
    def race_start_column(self): return 'Q'


def _get_ww_configurations(league_id: int, season: str) -> list[LeagueConfiguration]:

    def apply_penalties(cfg: LeagueConfiguration):
        if league_id == __ff:
            pass
        elif league_id == __fv:
            pass
        elif league_id == __srf:
            cfg.add_time_penalty(9, 16630, 180)  # Simoes

    all_cfg = LeagueConfiguration(iracing_id=league_id, season=season)
    all_cfg.add_group_rule("All Drivers", GroupRules(0, 999, 3))
    _setup_scoring(all_cfg)
    apply_penalties(all_cfg)

    class_config = LeagueConfiguration(iracing_id=league_id, season=season)
    class_config.add_group_rule("S1 Drivers", GroupRules(0, 199, 3))
    class_config.add_group_rule("S2 Drivers", GroupRules(200, 899, 3))
    class_config.add_group_rule("Masters Drivers", GroupRules(900, 999, 3))
    _setup_scoring(class_config)
    apply_penalties(all_cfg)

    return [all_cfg, class_config]


def _get_ecr_configurations(league_id: int, seasons: list[(str, str)]) -> list[LeagueConfiguration]:
    cfgs = []
    for season in seasons:
        cfg = LeagueConfiguration(iracing_id=league_id, season=season[0])
        cfg.add_group_rule(season[1], GroupRules(0, 999, 3))
        _setup_scoring(cfg)
        cfgs.append(cfg)

    return cfgs


if __name__ == "__main__":
    main()
