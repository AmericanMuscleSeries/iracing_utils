# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules, IncidentPoints
from core.objects import Driver, LeagueResult, PositionValue
from core.sheets import SheetsDisplay

__league_id = 6810


def main():
    cfgs = get_season_8_cfg()
    score_league(cfgs, AMSSheetsDisplay("1n2Vmbsn_V16n3TtlgSTjJobyqLbTjpz3MGlPrGXw4T8"))


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


def get_season_8_cfg() -> list[LeagueConfiguration]:
    cfgs = []
    scoring = None
    for i in range(2):
        cfg = LeagueConfiguration(iracing_id=__league_id, season=8)
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
        cfg.add_time_penalty(5, 417105, 20)  # Hosea
        cfg.add_time_penalty(5, 920078, 10)  # Weaver
        cfg.add_time_penalty(5, 71668, 5)    # Buchholz
        cfgs.append(cfg)

    return cfgs

"""
def get_season_7_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=7)
    season.sort_by = SortBy.ForcedDrops
    # Separate point pool between classes and use overall position value relative to class winner
    season_7_scoring_mode = 1
    if season_7_scoring_mode == 1:
        sheet = "1SZSIvtBNU4n94vmcQFFTNErxr6uUVKz9lHVfySHWxFI"
        scoring = season.set_assignment_scoring({1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                 6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                 11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                 16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                 21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                 26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                 31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                 36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                 41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                 46: 1},
                                                separate_pool=True, position_value=PositionValue.Overall)
        season.add_group_rule(Group.Pro, GroupRules(0, 99, 0))
        season.add_group_rule(Group.Ch, GroupRules(100, 199, 2))
        season.add_group_rule(Group.Am, GroupRules(200, 299, 2))
        season.add_google_sheet(sheet,
                                {Group.Pro: "Pro Drivers", Group.Ch: "Ch Drivers", Group.Am: "Am Drivers"})
    elif season_7_scoring_mode == 2:
        sheet = "1SZSIvtBNU4n94vmcQFFTNErxr6uUVKz9lHVfySHWxFI"
        scoring = season.set_linear_decent_scoring(40, hcp=False)
        season.add_group_rule(Group.Pro, GroupRules(0, 299, 3))
        season.add_google_sheet(sheet, {Group.Pro: "All Drivers"})
    # Let's give points for these as well, default is 0 points
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 1
    scoring.most_laps_lead = 0

    # Ignore practice races
    season.add_practice_sessions([1, 2, 3])

    # Apply Penalties
    #
    season.add_time_penalty(1, 459211, 10)  # Pucyk
    # Spa
    season.add_time_penalty(2, 821509, 60)  # Sudenga
    season.add_time_penalty(2, 481375, 30)  # Campbell
    # Homestead
    season.add_time_penalty(3, 71668, 10)  # Buchholz
    season.add_time_penalty(3, 342356, 10)  # Royce
    # Seabring
    season.add_time_penalty(4, 459211, 15)  # Pucyk
    season.add_time_penalty(4, 342356, 15)  # Royce
    season.add_time_penalty(4, 345352, 20)  # McFinger
    # Brands Hatch
    season.add_time_penalty(5, 823724, 10)  # Parrish
    # Nurburgring
    season.add_time_penalty(6, 88930, 5)  # Kemp
    # Barcelona
    season.add_time_penalty(9, 360361, 3)  # Moore
    return [cfg]


def get_season_6_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              name=__league_name,
                              season=6)
    cfg.sort_by = SortBy.ForcedDrops
    for i in range(5):
        if i == 0:
            # Official
            sheet = "1qdMBFll_eZxTF7G9DkaliJ6tm8sADqhHHFhKT8fIy1c"
            scoring = cfg.set_linear_decent_scoring(40, hcp=False)
        elif i == 1:
            # Separate point pool between classes and use overall position value relative to class winner
            sheet = "1Qi8n5HlUkW5AsDkaKk5uRbFz-8axQGeE2G7pODwCLvA"
            # scoring = season.set_linear_decent_scoring(40, hcp=False,
            #                                            separate_pool=True, position_value=PositionValue.Overall)
            scoring = cfg.set_assignment_scoring({1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                     6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                     11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                     16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                     21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                     26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                     31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                     36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                     41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                     46: 1},
                                                    separate_pool=True, position_value=PositionValue.Overall)
    elif case == 3:
        # True multiclass
        # Separate point pool between classes and use class position value for points
        sheet = "1EqQjR9UM-Ds_bQ5mCdh3raCKnE5i4MgRLIXm5GRYajw"
        # scoring = season.set_linear_decent_scoring(40, hcp=False,
        #                                            separate_pool=True, position_value=PositionValue.Class)
        scoring = season.set_assignment_scoring({1: 50, 2: 47, 3: 45, 4: 43, 5: 42,
                                                 6: 41, 7: 40, 8: 39, 9: 38, 10: 37,
                                                 11: 36, 12: 35, 13: 34, 14: 33, 15: 32,
                                                 16: 31, 17: 30, 18: 29, 19: 28, 20: 27,
                                                 21: 26, 22: 25, 23: 24, 24: 23, 25: 22,
                                                 26: 21, 27: 20, 28: 19, 29: 18, 30: 17,
                                                 31: 16, 32: 15, 33: 14, 34: 13, 35: 12,
                                                 36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
                                                 41: 6, 42: 5, 43: 4, 44: 3, 45: 2,
                                                 46: 1},
                                                separate_pool=True, position_value=PositionValue.Class)
    elif case == 4:
        # IndyCar Style
        sheet = "1mawS71Na0yUpAoXT1Oid-skL1GIzHkxUTYURTodCu5o"
        scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                 6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                 11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                 16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                 21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                 26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                 31: 5, 32: 5, 33: 5})
    elif case == 5:
        # IndyCar Style
        sheet = "1p8qO5ruVhaUBXx7oC72MdrzjvBAYkgXWG_UNY8qPOUo"
        scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                 6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                 11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                 16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                 21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                 26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                 31: 5, 32: 5, 33: 5},
                                                separate_pool=True, position_value=PositionValue.Overall)
    elif case == 6:
        # IndyCar Style
        sheet = "1HnIyOt6CKtXHbcQpUqcjPjAjqSyRc0hO3z6d0i9jTjc"
        scoring = season.set_assignment_scoring({1: 50, 2: 40, 3: 35, 4: 32, 5: 30,
                                                 6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
                                                 11: 19, 12: 18, 13: 17, 14: 16, 15: 15,
                                                 16: 14, 17: 13, 18: 12, 19: 11, 20: 10,
                                                 21: 9, 22: 8, 23: 7, 24: 6, 25: 5,
                                                 26: 5, 27: 5, 28: 5, 29: 5, 30: 5,
                                                 31: 5, 32: 5, 33: 5},
                                                separate_pool=True, position_value=PositionValue.Class)

    # Let's give points for these as well, default is 0 points
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0

    # Ignore practice races
    season.add_practice_sessions([1, 2])

    if scoring.handicap:
        season.num_drops = 0
        season.add_group_rule(Group.Pro, GroupRules(0, 199, 0))
        season.add_google_sheet("1bjNJevXmU3godoJuPZjHnMHWdwdLmMimxcdOm38XsBk", {Group.Pro: "Drivers"})
    else:
        # Set up our grouping rules per season
        season.add_group_rule(Group.Pro, GroupRules(0, 99, 2))
        season.add_group_rule(Group.Am, GroupRules(100, 199, 2))
        season.add_google_sheet(sheet, {Group.Pro: "Pro Drivers", Group.Am: "Am Drivers"})

    # Apply Penalties
    season.add_time_penalty(2, 310239, 10)
    season.add_time_penalty(6, 189468, 10)
    season.add_time_penalty(7, 85279, 5)
    season.add_time_penalty(10, 71668, 5)
    return [cfg]
"""


def get_season_5_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=5)
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0
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

    # [Optional] Provide a Google Sheet, for each season, where we can push results to
    # Where is it and what are the group tab names of the Google sheet to push results to
    cfg.add_google_sheet("1jlybjNg8sQGFuwSPrnNvQRq5SrIX73QUbISNVIp3Clk", ["Pro", "Am"])
    return [cfg]


def get_season_4_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=4)
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    cfg.add_google_sheet("1IJOA3c5k6r9IUq0tqgDJPQxaSwZ3xW4y-gknGRD8QjE", ["Drivers"])
    return [cfg]


def get_season_3_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=3)
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    cfg.add_google_sheet("1Smo-G7BlUEaFxudOn6FZ83mrSzu3u2eFFwH1dOyYBtY", ["Drivers"])
    return [cfg]


def get_season_2_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=2)
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    cfg.add_google_sheet("1Rh7X5lLh2C68dG-NjyFbgjn9shsrartGrR0PAyDol2o", ["Drivers"])
    return [cfg]


def get_season_1_cfg() -> list[LeagueConfiguration]:
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              season=1)
    scoring = cfg.set_linear_decent_scoring(40)
    scoring.pole_position = 1
    scoring.laps_lead = 1
    scoring.fastest_lap = 0
    scoring.most_laps_lead = 0
    cfg.add_group_rule("Drivers", GroupRules(0, 999, 2))
    cfg.add_google_sheet("1-u35u7rVazBkJOwpk1MGeafRksC0jc-zkJ2PamU1p1o", ["Drivers"])
    return [cfg]


if __name__ == "__main__":
    main()
