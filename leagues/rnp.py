# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import logging

from pathlib import Path

from score_league import score_league, InitializeSheets
from core.league import LeagueConfiguration, GroupRules

__league_id = 10236
_log = logging.getLogger('log')


def main():

    args = InitializeSheets(log_filename="rnp.log")
    tc = LeagueConfiguration.fetch_track_count(args, league_id=__league_id)

    def _season_str(seasons: set):
        abbr = []
        for s in seasons:
            if "Season" in s:
                abbr.append(s.replace("Season ", "S"))
            elif "Summer" in s:
                abbr.append("Summer")
            elif "Special" in s:
                abbr.append("Special")
            else:
                abbr.append(s)
        return ",".join(abbr)

    for track, stats in dict(sorted(tc.items())).items():
        _log.info(f"{track} - {stats['count']}x in [{_season_str(stats['seasons'])}]")

    # Pull ALL legacy results (Don't push)
    all_seasons = LeagueConfiguration.fetch_all_season_names(__league_id)
    for season in all_seasons:
        cfg = LeagueConfiguration(iracing_id=__league_id, season=season)
        cfg.add_group_rule("All Drivers", GroupRules(0, 999, 0))
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
        expected_filename = Path(f"./results/Road n' Plate {cfg.season}.json")
        if not expected_filename.exists():
            score_league(cfg, broadcast=False)


if __name__ == "__main__":
    main()
