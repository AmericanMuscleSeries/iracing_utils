# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules, PositionValue, \
    serialize_league_configuration_to_string, serialize_league_configuration_from_string
from core.clients import ClientMain
from core.objects import Driver, LeagueResult, SerializationFormat
from core.sheets import SheetsDisplay

__league_id = 8928


def main():
    client = ClientMain(log_filename="ruf.log")

    cfg = get_season_3_cfg()
    score_league(client, cfg, RUFSheetsDisplay("1CucR19IMBRjEeNsIgMfdaSqtwTmt-IasZyTTrgUJsPU"))
    json = serialize_league_configuration_to_string(cfg, SerializationFormat.JSON)
    serialize_league_configuration_from_string(json, SerializationFormat.JSON)


class RUFSheetsDisplay(SheetsDisplay):
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
                row.append("Y" if result.most_laps_lead > 0 else "")
                row.append("Y" if result.fastest_lap else "")
                row.append(result.incidents)
                row.append(result.clean_driver_points)
                row.append(result.laps_completed)
                row.append(result.laps_lead)
                row.append("{:.2f}".format(result.mu))
                row.append("{:.2f}".format(result.sigma))
        return row

    @property
    def num_race_cells(self):
        return 12

    @property
    def race_start_column(self): return 'R'


def get_season_3_cfg() -> LeagueConfiguration:
    cfg = LeagueConfiguration(iracing_id=__league_id, season="Season 3 (Rocky Road)")
    scoring = cfg.set_assignment_scoring(assignments={1: 350, 2: 320, 3: 300, 4: 280, 5: 260,
                                                      6: 250, 7: 240, 8: 230, 9: 220, 10: 210,
                                                      11: 200, 12: 190, 13: 180, 14: 170, 15: 160,
                                                      16: 150, 17: 140, 18: 130, 19: 120, 20: 110,
                                                      21: 100, 22: 90, 23: 80, 24: 70, 25: 60,
                                                      26: 50, 27: 40},
                                         separate_pool=False,
                                         position_value=PositionValue.Overall)
    cfg.add_group_rule("All Drivers", GroupRules(0, 999, 2))

    scoring.pole_position = 10
    scoring.fastest_lap.points = 10
    scoring.fastest_lap.minimum_requirement = 0
    scoring.lead_a_lap.points = 0
    scoring.lead_a_lap.minimum_requirement = 0
    scoring.most_laps_lead.points = 10
    scoring.most_laps_lead.minimum_requirement = 0
    scoring.clean_driver.point_map = {0: 10,
                                      1: 10,
                                      2: 5,
                                      3: 5,
                                      4: 5}
    scoring.clean_driver.minimum_requirement = 0
    scoring.clean_driver.separate_points = True
    for r in [2, 4, 6, 8, 10, 12]:
        multiplier = scoring.add_race_multiplier(race=r)
        multiplier.position = 1
        multiplier.pole_position = 0
        multiplier.fastest_lap = 1
        multiplier.lead_a_lap = 1

    # Post race derby started before the race ended....
    cfg.override_finish_order(race=4, order=[920078,  # Weaver
                                             480781,  # Thompson
                                             186201,  # Lebano
                                             609455,  # Bray
                                             528770,  # Smith
                                             298491,  # Cohn
                                             511982,  # Cicchetti
                                             563709,  # Weant
                                             451461,  # Guzenda
                                             180474,  # Sanchinelli
                                             511528]  # Besnard
                              )

    return cfg


if __name__ == "__main__":
    main()
