# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import sys
import logging
import argparse
import statistics
from league.objects import Driver
from iracingdataapi.client import irDataClient

_ams_logger = logging.getLogger('ams')


class DriverLaps(Driver):
    __slots__ = ["lap_times_s", "_car_class", "_ai",
                 "_average_lap_time_s", "_hold_time_s"]

    def __init__(self, cust_id: int, name: str, car_number: int, car_class: str, ai: bool):
        super().__init__(cust_id)
        self._ai = ai
        self._name = name
        if self._ai:
            self._name += "*"
        self._car_number = car_number
        self._car_class = car_class
        self.lap_times_s = list()
        self._average_lap_time_s = None
        self._hold_time_s = None

    def is_ai(self): return self._ai

    @property
    def car_class(self): return self._car_class

    @property
    def average_lap_time_s(self): return self._average_lap_time_s

    @property
    def hold_time_s(self): return self._hold_time_s

    @staticmethod
    def valid_lap_time(fastest_s: float, test_lap_s: float) -> bool:
        return test_lap_s < (fastest_s * 1.07)

    def calculate_average_lap_time(self):
        """
        Calculate the fastest average lap time using the fastest 3 laps, if 3 laps are provided
        Laps must be within 107% of the fastest laps, or they don't count
        :return: None
        """
        _ams_logger.info("Calculating average lap time for " + self.name + "...")
        laps = list()  # list of laps we will average into a time for our hold calculation
        laps.append(self.lap_times_s[0])
        if len(self.lap_times_s) >= 2:
            if self.valid_lap_time(self.lap_times_s[0], self.lap_times_s[1]):
                laps.append(self.lap_times_s[1])
            else:
                _ams_logger.info("Ignoring lap 2, as it was too slow (> 107% of the fastest lap)")
        if len(self.lap_times_s) >= 3:
            if self.valid_lap_time(self.lap_times_s[0], self.lap_times_s[2]):
                laps.append(self.lap_times_s[2])
            else:
                _ams_logger.info("Ignoring lap 3, as it was too slow (> 107% of the fastest lap)")
        self._average_lap_time_s = statistics.mean(laps)
        _ams_logger.info("The average lap time for " + self.name + " is " + str(self._average_lap_time_s) + "s.")

    def calculate_hold_time(self, estimated_race_time_s: float, num_laps: int) -> float:
        my_estimated_race_time_s = self._average_lap_time_s * num_laps
        self._hold_time_s = estimated_race_time_s - my_estimated_race_time_s

    def use_fastest_ai_average_lap_time(self, drivers: dict):
        """
        If a driver has not set a valid lap time,
        Get the fastest average lap time from the fastest AI driver for their car class, and take off 2s
        :param drivers: all the drivers in the session
        :return: None
        """
        if self.is_ai():
            _ams_logger.error("Cannot use_fastest_ai_average_lap_time on an ai driver.")
            return
        _ams_logger.info(self.name + " did not set any valid laps.")
        _ams_logger.info("Using the fastest average lap time from a bot in the " + self.car_class + ".")
        fastest_bot = None
        self._average_lap_time_s = 1000
        for driver in drivers.values():
            if driver.is_ai() and driver.car_class == self.car_class:
                if driver.average_lap_time_s < self._average_lap_time_s:
                    fastest_bot = driver
                    self._average_lap_time_s = driver.average_lap_time_s
        _ams_logger.info("Bot " + fastest_bot.name +
                         " had the fastest average lap time of " + str(fastest_bot.average_lap_time_s))
        # Human driver is expected to go 2s faster than the fastest bot
        self._average_lap_time_s -= 2
        _ams_logger.info("Setting " + self.name + "'s average lap time to " + str(self._average_lap_time_s))


def calculate_black_flags(username: str, password: str, subsession_id: int, num_laps: int):
    idc = irDataClient(username, password)

    # Race is always 0
    # -1 is expected to be a warmup practice session, while black flags are entered
    # -2 is Qualification
    # -3 is the initial practice
    simsession_numbers = [-3, -2]
    drivers = dict()
    # Figure out what cars were driven by whom
    ir_subsession = idc.result(subsession_id=subsession_id)["session_results"]

    for ir_event in ir_subsession:
        if ir_event["simsession_number"] in simsession_numbers:
            for result in ir_event["results"]:
                driver = DriverLaps(result["cust_id"],
                                    result["display_name"],
                                    result["livery"]["car_number"],
                                    result["car_class_short_name"],
                                    result["ai"])
                drivers[driver.cust_id] = driver

    for simsession_number in simsession_numbers:
        all_laps = idc.result_lap_chart_data(subsession_id=subsession_id, simsession_number=simsession_number)
        if all_laps is None:
            _ams_logger.info("Could not find simsession_number " + str(simsession_number))
            continue

        for lap in all_laps:
            lap_time_s = lap["lap_time"] * 0.0001
            if lap_time_s <= 0:
                continue  # Skip invalid laps
            drivers[lap["cust_id"]].lap_times_s.append(lap_time_s)

    # Sort our lap times
    for driver in drivers.values():
        driver.lap_times_s.sort()
        _ams_logger.info(driver.name + " : " + str(driver.lap_times_s))

    # Calculate the average lap time of each driver
    # Find the slowest average lap time and multiply by the number of laps we want
    slowest_driver = None
    slowest_average_lap_time_s = 0
    for cust_id, driver in drivers.items():
        if len(driver.lap_times_s) > 0:
            driver.calculate_average_lap_time()
            if slowest_average_lap_time_s < driver.average_lap_time_s:
                slowest_driver = driver
                slowest_average_lap_time_s = driver.average_lap_time_s
    slowest_race_time_s = slowest_average_lap_time_s * num_laps
    # This is our estimate of how long the race should last
    _ams_logger.info("\n")
    _ams_logger.info("The slowest driver is " + slowest_driver.name +
                     ", with an average lap time of " + str(slowest_driver.average_lap_time_s))
    _ams_logger.info("A " + str(num_laps) + " lap race is expected to run for "+str(slowest_race_time_s)+"s.\n\n")

    for cust_id, driver in drivers.items():
        if len(driver.lap_times_s) == 0:
            driver.use_fastest_ai_average_lap_time(drivers)
        driver.calculate_hold_time(slowest_race_time_s, num_laps)
        _ams_logger.info(driver.name + " is averaging " +
                         str(driver.average_lap_time_s) + "s laps and should be held for " +
                         str(driver.hold_time_s) + " seconds.\n")


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
    parser.add_argument(
        "-s", "--session",
        default=None,
        type=str,
        help="Session id to monitor."
    )
    parser.add_argument(
        "-l", "--laps",
        default=20,
        type=int,
        help="Number of race laps to calculate for."
    )
    opts = parser.parse_args()

    calculate_black_flags(opts.username, opts.password, "65859026", opts.laps)
    # calculate_black_flags(opts.username, opts.password, "64508370", opts.laps)
