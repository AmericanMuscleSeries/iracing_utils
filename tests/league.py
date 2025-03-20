# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

def test_league_configuration_serialization():
    # Save our league configuration to a json file.
    # Convert the LeagueConfiguration class to a python dict
    d = cfg.as_dict()  # Use this to work with data in a native python format instead of our classes
    # Dump the dict to json
    with open("configuration.json", 'w') as fp:
        json.dump(d, fp, indent=2)

    r = open(opts.configuration)
    d = json.load(r)
    lr = LeagueConfiguration.from_dict(d)
    d = lr.as_dict()
    season = None
    if opts.season is not None:
        season = [opts.season]

    testing = True
    if testing:
        # Testing that our serialization is consistent
        r = open('configuration.json')
        d = json.load(r)
        cfg = LeagueConfiguration.from_dict(d)
        d = cfg.as_dict()

        with open("configuration2.json", 'w') as fp:
            json.dump(d, fp, indent=2)