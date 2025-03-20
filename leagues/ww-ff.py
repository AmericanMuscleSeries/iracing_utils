# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

from score_league import score_league
from core.league import LeagueConfiguration, GroupRules

__league_id = 9555


def main():
    cfgs = get_season_1_cfg()
    score_league(cfgs)


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
