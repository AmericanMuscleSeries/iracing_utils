# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import sys
import json
import logging
import argparse
from pathlib import Path

from league.event import pull_event, fetch_and_report_drivers, fetch_and_report_league, list_events
from league.league import LeagueConfiguration
from league.objects import Event

_ams_logger = logging.getLogger('ams')

if __name__ == "__main__":
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

    list_events(opts.username, opts.password, 2024)

    def load_event(name: str) -> Event:
        fp = Path(f"./{name}.json")
        if fp.exists():
            _ams_logger.info(f"Reading event file for : {name}")
            r = open(f"{name}.json")
            d = json.load(r)
            event = Event.from_dict(d)
        else:
            event = pull_event(opts.username, opts.password, name, False)
            if event is None:
                raise Exception(f"Could not find the event: {name}")
            _ams_logger.info(f"Writing event file for : {name}")
            e = event.as_dict()
            with open(f"{name}.json", 'w') as fp:
                json.dump(e, fp, indent=2)
        return event

    events = [load_event("Daytona 24"), load_event("Bathurst 12 Hour")]

    cfg = LeagueConfiguration(6810)
    lg = cfg.fetch_league(opts.username, opts.password)

    # Discord registration
    discord = []
    registrations = Path("./registrations.json")
    if registrations.exists():
        r = open("./registrations.json")
        d = json.load(r)
        for key, driver in d.items():
            discord.append(int(driver["iracing_id"]))

    for event in events:
        fetch_and_report_league(event, lg, "-AMS")
        fetch_and_report_drivers(event, discord, "-Discord")

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
        fetch_and_report_drivers(event, streamers, "-Streamers")
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
        ]
        fetch_and_report_drivers(event, drivers, "-Pros")





