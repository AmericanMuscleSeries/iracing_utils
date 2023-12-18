from trueskill import *
import random


def populate_ffa(roster):
    updated = []
    for x in range(0,30):
        updated.append((roster[x],))

    return updated


def convert_ratings(results):
    updated = []
    for x in range(0,30):
        rating, = results[x]
        updated.append(rating)

    return updated


#
# run results with random rankings
#
roster = [Rating() for _ in range(0,30)]

for _ in range(0,10):
    ranks = [x for x in range(0,30)]
    random.shuffle(ranks)
    results = rate(populate_ffa(roster), ranks=ranks)
    roster = convert_ratings(results)

roster = sorted(roster, key=lambda x: x.mu, reverse=True)

for x in range(0,30):
    print(roster[x])

