# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import logging
from enum import Enum

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules, PositionValue, LeagueMain
from core.objects import Driver, LeagueResult
from core.sheets import SheetsDisplay, SortBy

_log = logging.getLogger('log')

_ff = 9555
_fv = 6956
_srf = 1566
_ecr = 6236


class LeagueType(Enum):
    FF = 0
    FV = 1
    SRF = 2
    WW = 3
    ECR = 4


class SteveRay(LeagueMain):
    __slots__ = ["_lt"]

    def __init__(self, log_filename: str):
        self._lt = LeagueType.FF
        super().__init__(log_filename)

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument(
            "-lg", "--league",
            help="Which league to score. valid tokens: FF, FV, SRF, ECR, WW\n"
                 "WW will score all 3 weekend warrior leagues: FF, FV, and SRF"
        )

    def process_args(self, args):
        super().process_args(args)
        if args.league is not None:
            if args.league == "FF":
                self._lt = LeagueType.FF
            elif args.league == "FV":
                self._lt = LeagueType.FV
            elif args.league == "SRF":
                self._lt = LeagueType.SRF
            elif args.league == "WW":
                self._lt = LeagueType.WW
            elif args.league == "ECR":
                self._lt = LeagueType.ECR
            else:
                self._lt = None
                _log.error(f"Unknown league: {args.league}")

    def score_league(self):
        # TODO 3 ways to specify what to score: json, filename tokens, league token
        # Should only 1 be allowed, or allow a big mix? Cull duplicates?
        if len(self.configs) == 0:
            self.gen_configs()
        for cfg in self.configs:
            score_league(self, cfg, RaySheets(cfg.google_sheet))

    def gen_configs(self):

        if self._lt is None:
            return

        if self._lt == LeagueType.ECR:
            s = [("Season 2 Group 1A SMX", "1A SMX"),
                 ("Season 2 Group 1B SRF", "1B SRF"),
                 ("Season 2 Group 2A Mustang", "2A Mustang"),
                 ("Season 2 Group 2B SM", "2B SM"),
                 ("Season 2 Group 3A FV", "3A FV"),
                 ("Season 2 Group 3B FF1600", "3B FF1600"),
                 ("Season 2 Group 4 GT4", "4 GT4"),
                 ("Season 2 Group 5A Jetta", "5A Jetta"),
                 ("Season 2 Group 5B TCR", "5B TCR")]
            for season_group in s:
                self._get_ecr_configurations(season_group[0], season_group[1])
            return

        legacy = []
        leagues = []
        if self._lt == LeagueType.FF or self._lt == LeagueType.WW:
            legacy.append((_ff, "2025 S1 FF Weekend Warriors", "1YsYm0TRjSjIR1r0EBxUCKq6yyRBgpHFe8F1dXhQAv0k"))
            legacy.append((_ff, "2025 S2", "121Fx4vKQ2t5Urdzueq5LWqdhv_ksKIt0S4b9_wTlw2s"))
            legacy.append((_ff, "2025S3 WW FF1600", "1CNixnEGEtJyIRNzUD-84NIlFv7Ef2oCQFJ6lGByT5Cc"))
            legacy.append((_ff, "2025S4 WW FF1600", "1vaalgnOjVqw-wJxVBIyfguVCZQBtRTAm6OaTZqPM7TU"))
            legacy.append((_ff, "2026S1 FF Weekend Warriors", "1GPX_aoxihNMd6qwcjCb0MmMhZgmPQ_l0ngSA-ETvN_A"))
            s = (_ff, "2026S2 FF Weekend Warriors", "1SvmByQhBSYt_42-9sPQ6LSxuKEwdl38SIrCROb8BBfQ")
            leagues.append(s)
        if self._lt == LeagueType.FV or self._lt == LeagueType.WW:
            legacy.append((_fv, "WW FV 2025 S1", "1W3gXY5wZzrYDoUL6_xbaK65KWI0dE_O_Ca-XRluq240"))
            legacy.append((_fv, "WW FV 2025 S2", "1bFBGHBxaN6CdNBy3t-I_AByVmaZIB--_SF1wWbJgM4U"))
            legacy.append((_fv, "WW FV 2025 S3", "1vAODigWsOreSP0hAVZZdx3BaRyiJniAD82zcUuiBPfk"))
            legacy.append((_fv, "WW FV 2025 S4", "1NfwzTzXWI4EewIY36YhLi-k48w8OJJlTHIYFSwLerIo"))
            legacy.append((_fv, "WW FV 2026 S1", "1Z50uG4J5VTqHSfIfm3FmJxFFEcZNCCHSuWVJKY0iHdk"))
            s = (_fv, "WW FV 2026 S2", "1HroBF2GEXefCzlIucG03-VLVnOD5sqKtSkmOPX1bG-k")
            leagues.append(s)
        if self._lt == LeagueType.SRF or self._lt == LeagueType.WW:
            legacy.append((_srf, "2025 S1 SRF Weekend Warriors", "1yFPSQoAYfz5gch9TQgv7AIU6pvHLnElHZPIIqhs0KfU"))
            legacy.append((_srf, "2025 S2", "1MbgV4Iwz2TPYMN5ZHiP0eXwltdvN1ML_zhZhOyp7cbk"))
            legacy.append((_srf, "2025 S3 SRF WW", "1Zfig0SYlfPvbhCOAA5ekQYgpfDlCQeGm8DbpUH3-mTo"))
            legacy.append((_srf, "2025S4 WW SRF 10yr Anniversary season", "1fOaE9Afo0DtdSbY7SoTP7MnrUSRGgp9AE2IqCExFXmA"))
            legacy.append((_srf, "2026S1 WW SRF", "1FNH5qaUKaMWGf_J96NKLqff_MTZwQA7NErieO0fQ9KA"))
            s = (_srf, "2026S2 WW SRF", "1UI842BVIf_eIBbyxIVZPzVCeBFLgG56t1qAau_0XmhU")
            leagues.append(s)
        for league in leagues:
            self._get_ww_configurations(league[0], league[1], league[2])

        """
        # Pull ALL legacy results (Don't push)
        league_id = __srf
        all_seasons = fetch_all_season_names(league_id)
        for season in all_seasons:
            all_cfg = LeagueConfiguration(iracing_id=league_id, season=season)
            all_cfg.add_group_rule("All Drivers", GroupRules(0, 999, num_drops))
            _setup_scoring(all_cfg)
            expected_filename = Path(f"./results/SRF Weekend Warriors {all_cfg.season}.json")
            if not expected_filename.exists():
                score_league(all_cfg, broadcast=False)
        """

        """
        # Pull legacy results (Don't push)
        for league in legacy:
            cfgs = _get_ww_configurations(league[0], league[1], 0)
            for cfg in cfgs:
                score_league(cfg, broadcast=False)
        """

    @staticmethod
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

    @staticmethod
    def _scca_scoring(cfg: LeagueConfiguration):
        scoring = cfg.set_assignment_scoring(assignments={1: 25, 2: 21, 3: 18, 4: 17, 5: 16,
                                                          6: 15, 7: 14, 8: 13, 9: 12, 10: 11,
                                                          11: 10, 12: 9, 13: 8, 14: 7, 15: 6,
                                                          16: 5, 17: 4, 18: 3, 19: 2, 20: 1},
                                             separate_pool=False,
                                             position_value=PositionValue.Overall)
        scoring.minimum_race_distance = 0.5
        scoring.pole_position = 0
        scoring.lead_a_lap.points = 1
        scoring.lead_a_lap.minimum_requirement = 0.8
        scoring.fastest_lap.points = 0
        scoring.fastest_lap.minimum_requirement = 0
        scoring.most_laps_lead.points = 3
        scoring.most_laps_lead.minimum_requirement = 0
        scoring.clean_driver.point_map = {0: 5,
                                          1: 5,
                                          2: 2,
                                          3: 2,
                                          4: 2}
        scoring.clean_driver.minimum_requirement = 0.85
        scoring.clean_driver.separate_points = False
        scoring.finish_race.points = 2
        scoring.finish_race.minimum_requirement = 0.85

    def _pull_all_seasons(self, league_id: int) -> list:
        return LeagueConfiguration.fetch_all_season_names(self.idc, league_id)

    def _get_ww_configurations(self, league_id: int, season: str, gsheet: str):

        def apply_penalties(cfg: LeagueConfiguration):
            if league_id == _ff:
                if season == "2026S2 FF Weekend Warriors":
                    # Did not perform required pit stop
                    cfg.add_time_penalty(6, 998259, 180)  # Williams
                    cfg.add_time_penalty(6, 679942, 180)  # Moran
                    cfg.add_time_penalty(6, 85279, 180)   # Nomm
            elif league_id == _fv:
                # Apply Penalties
                if season == "WW FV 2025 S4":
                    cfg.add_time_penalty(1, 284039, 30)  # Degasis (927)
            elif league_id == _srf:
                if season == "2025S4 WW SRF 10yr Anniversary season":
                    cfg.add_disqualification(1, 59267)  # Perry (97)

        num_drops = 3
        num_races = 12
        min_races_for_drops = num_races - num_drops
        all_cfg = LeagueConfiguration(name="All", iracing_id=league_id, season=season, num_races=num_races)
        all_cfg.google_sheet = gsheet
        all_cfg.add_group_rule("All Drivers", GroupRules(0, 999, num_drops, min_races_for_drops))
        SteveRay._setup_scoring(all_cfg)
        apply_penalties(all_cfg)

        class_config = LeagueConfiguration(name="Group", iracing_id=league_id, season=season, num_races=num_races)
        class_config.google_sheet = gsheet
        class_config.add_group_rule("S1 Drivers", GroupRules(0, 199, num_drops, min_races_for_drops))
        class_config.add_group_rule("S2 Drivers", GroupRules(200, 899, num_drops, min_races_for_drops))
        class_config.add_group_rule("Masters Drivers", GroupRules(900, 999, num_drops, min_races_for_drops))
        SteveRay._setup_scoring(class_config)
        apply_penalties(class_config)

        self.configs.append(all_cfg)
        self.configs.append(class_config)

    def _get_ecr_configurations(self, season: str, group: str):
        num_drops = 1
        num_races = 6
        cfg = LeagueConfiguration(name="ECR", iracing_id=_ecr, season=season, num_races=num_races)
        cfg.google_sheet = "1HzKe8K5kYwb50WLppZjsSUgxWlQr_zSiBzKIhil_bFY"
        cfg.add_group_rule(group, GroupRules(0, 999, num_drops))
        SteveRay._scca_scoring(cfg)

        if season == "Season 2 Group 5A Jetta" and group == "5A Jetta":
            # Jumping before end of session
            cfg.override_finish_order(race=3, order=[114175,   # Pendergrass
                                                     407295,   # Robertson
                                                     543002,   # Hayes
                                                     449980,   # Spoelman
                                                     920078,   # Weaver
                                                     173130,   # Justice
                                                     903073,   # Yankee
                                                     251760,   # Brewster
                                                     1155903,  # Miller
                                                     186201,   # Lebano
                                                     260841,   # Love
                                                     180474,   # Sanchinelli
                                                     136838,   # Key
                                                     453077,   # Buttermore
                                                     67948,    # Effinger
                                                     1153773,  # Daniel
                                                     511982]   # Cicchetti
                                      )

        self.configs.append(cfg)


class RaySheets(SheetsDisplay):

    def __init__(self, sheet_id: str):
        super().__init__(sheet_id)
        self.sort_by = SortBy.ForcedDrops

    def create_row(self, cust_id: int, driver: Driver, lgr: LeagueResult) -> list:
        row = list()  # Make a list per driver row
        # These 4 should always be the same between SheetsDisplays
        row.append(driver.name)
        row.append(driver.car_number)
        row.append(driver.earned_points)
        row.append(driver.earned_points - driver.drop_points)
        row.append(driver.total_completed_races)

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


def main():
    ray = SteveRay(log_filename="steve-ray.log")
    ray.score_league()


if __name__ == "__main__":
    main()
