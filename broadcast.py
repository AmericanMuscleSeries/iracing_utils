# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json

# set filename from .env instead
_points = './results/American Muscle Series Season 8.json'


def get_points(drops: bool = True) -> dict:
    r = open(_points)
    raw = json.load(r)

    # remove season completely and just grab top level object
    driver_points = {}

    # use 'Members' instead of 'Drivers'
    for iracing_id, driver in raw['Drivers'].items():
        points = driver['EarnedPoints']

        if drops:
            points = points - driver['DropPoints']

        driver_points[str(iracing_id)] = points

    return driver_points


if __name__ == "__main__":
    print(f"{get_points()}")
