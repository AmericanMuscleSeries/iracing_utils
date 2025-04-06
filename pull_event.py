# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import sys
import json
import logging
import argparse
from pathlib import Path
from iracingdataapi.client import irDataClient

from core.event import pull_event, fetch_and_report_drivers, list_events, report_owner_events
from core.league import LeagueConfiguration
from core.objects import Event

_logger = logging.getLogger('log')


def load_event(idc: irDataClient, series_name: str, year: int) -> Event:
    fp = Path(f"./events/{series_name}.json")
    if fp.exists():
        _logger.info(f"Reading event file for : {series_name}")
        r = open(fp)
        d = json.load(r)
        event = Event.from_dict(d)
    else:
        event = pull_event(idc, series_name, year, False)
        if event is None:
            raise Exception(f"Could not find the event: {series_name}")
        _logger.info(f"Writing event file for : {series_name}")
        with open(f"./events/{series_name}.json", 'w') as fp:
            json.dump(event.as_dict(), fp, indent=2)
    # Fill out ownership info
    for split in range(event.num_splits):
        result = event.get_result(split+1)
        for team_id, team in result._teams.items():
            if team.owner not in event.team_owners:
                event.team_owners[team.owner] = list()
            owned_teams = event.team_owners[team.owner]
            if team_id not in owned_teams:
                owned_teams.append(team_id)
    return event


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', filename="ams.log", filemode="w")
    logging.getLogger('ams').setLevel(logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    parser = argparse.ArgumentParser(description="Pull league results and rack and stack them for presentation")
    parser.add_argument(
        "username",
        type=str,
        help="iracing user name."
    )
    parser.add_argument(
        "password",
        type=str,
        help="iracing password."
    )
    opts = parser.parse_args()
    idc = irDataClient(opts.username, opts.password)

    output_dir = Path("./events")
    output_dir.mkdir(exist_ok=True)

    year = 2025
    list_events(idc, year)
    events = [
        # load_event(idc, "Roar Before the 24", year),
        # load_event(idc, "Daytona 24", year),
        # load_event(idc, "Bathurst 12 Hour", year),
        load_event(idc, "12 Hours of Sebring", year),
        # load_event(idc, "Road America 500", year),
        # load_event(idc, "24 Hours of Nurburgring", year),
        # load_event(idc, "iRacing.com Indy 500", year),
        # load_event(idc, "6 Hours of the Glen", year),
        # load_event(idc, "24 Hours of Spa", year),
        # load_event(idc, "iRacing MX-500 - Fixed", year),
        # load_event(idc, "Indy 6 Hour", year),
        # load_event(idc, "Petit Le Mans", year),
        # load_event(idc, "Fuji 8 Hour", year),
        # load_event(idc, "SCCA Runoffs - Spec Racer Ford", year),
        # load_event(idc, "THE Production Car Challenge", year),
    ]

    for event in events:
        report_owner_events(idc, owner_id=180474, event=event, output_dir=output_dir)

    # AMS Drivers
    # Various Discord user lists
    ams = set()
    for s in ["07", "08"]:
        users = Path(f"./users/ams_users_{s}.json")
        if users.exists():
            r = open(users)
            d = json.load(r)
            for key, driver in d.items():
                ams.add(int(driver["iracing_id"]))
    cfg = LeagueConfiguration(6810)
    lg = cfg.fetch_league_members(opts.username, opts.password)
    for lgKey in lg.members.keys():
        ams.add(lgKey)

    for event in events:
        fetch_and_report_drivers(event, list(ams), "-AMS", output_dir=output_dir)

        # Make lists of notable iracers to report on
        streamers = [
            62396,  # Tyson Meier
            510501,  # Oliver Furnell
            # 3333,  # Pablo Lopez
            427834,  # Dan Suzuki
            444212,  # Tony Kanaan
            587856,  # Tony Kanaan
            169861,  # Daniel Gray10
            139694,  # Arjuna Kankipati2
            399713,  # Lyubov Ozeretskovskaya
            26144,  # Emily Jones
            150205,  # Christian Ortega
            120570,  # Matt Malone
            612494,  # Bel Wells
            392108,  # Marc Noske
            256046,  # Borja Zazo
            393940,  # David PJ Sampson
            # 3333,  # Javier Soto
            95469,  # Jimmy Broadbent
            635431,  # Dave Cam
            259565,  # Dave Cameron
            474576,  # Mac Evad
            33911,  # Jardier
            314220,  # Suellio Almeida
            652661,  # Suellio Almeida
            82554,  # Casey Kirwan
            334400,  # Scott Tuffey
            207175,  # Laurin Heinrich
            682327,  # Laurin Heinrich
            260872,  # Ayhancan Guven
            930486,  # Ayhancan Guven
            415944,  # Ayhancan Guven
            206066,  # Daniel Morad
        ]
        fetch_and_report_drivers(event, streamers, "-Streamers", output_dir=output_dir)
        drivers = [
            168966,  # Max Verstappen
            60271,   # Lewis Hamilton
            524549,  # Fernando Alonso
            382472,  # Alex Albon
            55278,   # Valtteri Bottas
            382734,  # Pierre Gasly
            429787,  # Antonio Giovinazzi
            59700,   # Heikki Kovalalinen
            254162,  # Robert Kubica
            452329,  # Nicholas Latifi
            342741,  # Charles Leclerc
            61121,   # Juan Pablo Montoya
            468871,  # Esteban Ocon
            444936,  # George Russell
            469000,  # Takuma Sato
            444211,  # Josef Newgarden
            445645,  # Romain Grosjean
            390695,  # Carlos Sainz
            183738,  # Liam Lawson
            115606,  # Louis Deletraz
            261898,  # Thomas Preining
            182409,  # Scott Bloomiquist
            206066,  # Daniel Morad
            27345,   # Corey Lewis
            46808,   # Nico Hulkenburg
            247748,  # Pascal Wehrlein
            185260,  # Nico Rosberg
            175518,  # Esteban Gutierrez
            188467,  # Sebastian Vettel
            196450,  # Sebastien Loeb
            111169,  # Danny Juncadella
            130979,  # Lando Norris
            87961,   # Rubens Barrichello
            191526,  # Daniel Serra
            224342,  # Alex Palou
            444212,  # Tony Kanaan
            587856,  # Tony Kanaan
            101152,  # Agustin Canapino
            66754,   # Tony Stewart
            80666,   # Fred Vervisch
            105433,  # Stoffel Vandoorne
            175611,  # Jose Maria Lopez
            24792,   # Connor Daly
            65972,   # Ed Carpenter
            138207,  # Felipe Massa
            26033,   # Raffaele Marciello
            119244,  # Cristopher Mies
            18926,   # Tommy Milner
            41073,   # Richard Westbrook
            33439,   # Simon Pagenaud
            27143,   # Will Power
            18410,   # Townsend Bell
            118560,  # Antonio Felix da Costa
            116060,  # Felix Rosenqvist
            172117,  # Nick Yelloly
            80696,   # Nick Tandy
            148769,  # Nick Tandy
            108036,  # Nicki Thiim
            119892,  # Christopher Haase
            92102,   # Laurens Vanthoor
            119218,  # Rene Rast
            62077,   # Kelvin van der Linde
            165802,  # Felipe Albuquerque
            122967,  # Earl Bamber
            90655,   # Matt Campbell
            118785,  # Philipp Eng
            74902,   # Jordan Pepper
            50433,   # Nicky Catsburg
            89404,   # Stevan McAleer
            421827,  # Mirko Bortolotti
        ]
        fetch_and_report_drivers(event, drivers, "-Pros", output_dir=output_dir)


if __name__ == "__main__":
    main()
