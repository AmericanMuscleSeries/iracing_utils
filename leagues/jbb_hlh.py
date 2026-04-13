# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

from datetime import datetime
from dateutil import tz

from score_hot_lap_league import score_league
from core.clients import Client
from core.league import LeagueConfiguration, GroupRules, PositionValue, \
    serialize_league_configuration_to_string, serialize_league_configuration_from_string
from core.objects import Driver, LeagueResult, SerializationFormat, time2str
from core.sheets import SheetsDisplay, SortBy

__league_id = 13594
__team_id = "01KBR3TPYHYHEDS7BHQ99FCPG5"
__team_name = "jbb-hot-lap-heroes"


def main():
    client = Client(log_filename="jbb_hlh.log")

    # Map of g61 driver names to ir driver names
    # Only need to add names that are different
    g612ir = {
        "Jeff Schnackel": "Jeffrey Schnackel",
        "Ed Sanchinelli": "Edgar Sanchinelli",
        "James Moore": "Jimmy R Moore",
        "Michael McCoy": "Michael C McCoy",
        "Kevin Parrish": "Kevin M Parrish"
    }

    cfg, sheet = get_season_2_cfg()
    score_league(client, cfg, g612ir, HLHSheetsDisplay(sheet))
    json = serialize_league_configuration_to_string(cfg, SerializationFormat.JSON)
    serialize_league_configuration_from_string(json, SerializationFormat.JSON)


class HLHSheetsDisplay(SheetsDisplay):

    def __init__(self, sheet_id: str):
        super().__init__(sheet_id)
        self._sort_idx = 1

    def create_row(self, cust_id: int, driver: Driver, lgr: LeagueResult) -> list:
        row = list()  # Make a list per driver row
        row.append(driver.name)
        row.append(driver.earned_points)
        row.append(driver.total_race_starts)

        row.append(driver.total_wins)
        row.append(driver.race_finish_points)
        row.append(driver.fast_clean_laps_points)
        row.append(driver.clean_laps_points)
        row.append(driver.total_clean_laps)
        row.append(driver.total_laps_complete)
        row.append(driver.average_finish)

        for race_number in range(len(lgr.races)):
            result = lgr.get_race(race_number + 1).get_result(cust_id)
            if result is None:
                for i in range(self.num_race_cells):
                    row.append("")
            else:
                row.append(result.car)
                if result.fastest_lap_time:
                    row.append(time2str(result.fastest_lap_time))
                else:
                    row.append("None")
                if result.fastest_lap_time_stamp:
                    lap_time_stamp = (datetime.strptime(result.fastest_lap_time_stamp, '%Y-%m-%dT%H:%M:%SZ')
                                      .replace(tzinfo=tz.tzutc()).astimezone().strftime("%b %d, %Y %I:%M%p"))
                    row.append(lap_time_stamp)
                else:
                    row.append("None")
                row.append(result.points)
                row.append(result.fast_clean_laps_points)
                row.append(result.clean_laps_points)
                row.append(result.clean_laps)
                row.append(result.laps_completed)
        return row

    @property
    def num_race_cells(self):
        return 8

    @property
    def race_start_column(self): return 'L'


def get_season_2_cfg() -> (LeagueConfiguration, str):
    cfg = LeagueConfiguration(name="JBB_HLH",
                              iracing_id=__league_id,
                              g61_id=__team_name,
                              num_races=6,
                              season="Hot Lap Heroes S2")
    scoring = cfg.set_assignment_scoring(assignments={1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
                                                      6: 8, 7: 6, 8: 4, 9: 2, 10: 1},
                                         separate_pool=False,
                                         position_value=PositionValue.Overall)
    # X points for every Y laps
    scoring.clean_laps.num_laps = 5
    scoring.clean_laps.points = 1
    # X points for every Y clean laps within Z% of each driver's fastest lap
    scoring.fast_clean_laps.num_laps = 5
    scoring.fast_clean_laps.points = 1
    scoring.fast_clean_laps.time_percent = 107
    cfg.add_group_rule("All Drivers", GroupRules(0, 999, 0))

    return cfg, "13hp05oNdM-Uf9eDpPRioqvfTqV7VndsVgjqExscZVJ8"


def get_season_1_cfg() -> (LeagueConfiguration, str):
    cfg = LeagueConfiguration(iracing_id=__league_id,
                              g61_id=__team_name,
                              season="Hot Lap Heroes S1")
    scoring = cfg.set_assignment_scoring(assignments={1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
                                                      6: 8, 7: 6, 8: 4, 9: 2, 10: 1},
                                         separate_pool=False,
                                         position_value=PositionValue.Overall)
    cfg.add_group_rule("All Drivers", GroupRules(0, 999, 0))

    # Jay deleted a session, recreate it
    daytona = {"track": {"track_name": "Daytona International Speedway", "track_id": 192},
               "cars": [{"car_id": 170},   # Acura GTP
                        {"car_id": 159},   # BMW GTP
                        {"car_id": 168},   # Cadillac GTP
                        {"car_id": 196},   # Ferrari GTP
                        {"car_id": 174}],  # Porsche GTP
               "launch_at": "2026-01-12T05:00:00Z",
               "time_limit": 240,
               "subsession_id": 0,
               "weather": {"temp_value": 69.0,
                           "wind_value": 2.0,
                           "rel_humidity": 45,
                           "skies": 2,
                           "track_water": 0}}
    cfg.add_session(3, daytona)

    return cfg, "19wm2JSt4w5ivfXwovRWVeW7UNSGbaaI5UyWcK3ld2-I"


if __name__ == "__main__":
    main()
