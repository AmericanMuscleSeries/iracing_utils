# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import logging

from enum import Enum

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules, PositionValue
from core.objects import Driver, LeagueResult
from core.sheets import SheetsDisplay

__league_id = 1566


class LeagueType(Enum):
    FF = 0
    FV = 1
    SRF = 2

# Seasons scored:
# FF
#    2025 S1 FF Weekend Warriors - 1YsYm0TRjSjIR1r0EBxUCKq6yyRBgpHFe8F1dXhQAv0k
#    2025 S2
# FV
#    WW FV 2025 S1 - 1W3gXY5wZzrYDoUL6_xbaK65KWI0dE_O_Ca-XRluq240
#    WW FV 2025 S2
# SRF
#    2025 S1 SRF Weekend Warriors - 1yFPSQoAYfz5gch9TQgv7AIU6pvHLnElHZPIIqhs0KfU
#    2025 S2


def main():
    ww = WeekendWarriors(LeagueType.SRF)
    score_league(ww.get_configurations(), ww)


class WeekendWarriors(SheetsDisplay):
    __slots__ = ["_league_type", "_league_id", "_season"]

    def __init__(self, league_type: LeagueType):
        self._league_type = league_type
        if league_type == LeagueType.FF:
            super().__init__("1YsYm0TRjSjIR1r0EBxUCKq6yyRBgpHFe8F1dXhQAv0k")
            self._season = "2025 S1 FF Weekend Warriors"
            self._league_id = 9555
        elif league_type == LeagueType.FV:
            super().__init__("1W3gXY5wZzrYDoUL6_xbaK65KWI0dE_O_Ca-XRluq240")
            self._season = "WW FV 2025 S1"
            self._league_id = 6956
        elif league_type == LeagueType.SRF:
            super().__init__("1yFPSQoAYfz5gch9TQgv7AIU6pvHLnElHZPIIqhs0KfU")
            self._season = "2025 S1 SRF Weekend Warriors"
            self._league_id = 1566
        else:
            raise ValueError("Unsupported League Type")

    def get_configurations(self) -> list[LeagueConfiguration]:

        all_cfg = LeagueConfiguration(iracing_id=self._league_id, season=self._season)
        all_cfg.add_group_rule("All Drivers", GroupRules(0, 999, 3))
        self._setup_scoring(all_cfg)

        class_config = LeagueConfiguration(iracing_id=self._league_id, season=self._season)
        class_config.add_group_rule("S1 Drivers", GroupRules(0, 199, 3))
        class_config.add_group_rule("S2 Drivers", GroupRules(200, 899, 3))
        class_config.add_group_rule("Masters Drivers", GroupRules(900, 999, 3))
        self._setup_scoring(class_config)

        return [all_cfg, class_config]

    def _setup_scoring(self, cfg: LeagueConfiguration):
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

        # Penalties
        if self._league_type == LeagueType.FF:
            pass
        elif self._league_type == LeagueType.FV:
            pass
        elif self._league_type == LeagueType.SRF:
            cfg.add_time_penalty(9, 16630, 180)  # Simoes

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


if __name__ == "__main__":
    main()
