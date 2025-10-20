# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import json
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

from core.objects import serialize_league_result_from_file, LeagueResult, serialize_event_from_file


def get_lap_positions(lg: LeagueResult, race: int):
    car_positions = []
    results = lg.get_race(race).get_results()
    for r, t in enumerate(results):
        num = f"{lg.get_driver(t[0]).car_number}"
        # if num == "228":
        #     print("here")
        lap_positions = []
        for i, lap in enumerate(t[1].laps):
            if i == 0 and lap.position == 0:
                lap_positions.append(r+1)
            else:
                lap_positions.append((i, lap.position))
        if lap_positions[-1][1] != t[1].finish_position:
            lap_positions.append((lap_positions[-1][0], t[1].finish_position))
        car_positions.append((num, lap_positions))

    return car_positions


def plot_position_changes(car_positions: list, to: Path, figsize=(16, 8)):

    matplotlib.rcParams['font.family'] = 'monospace'
    fig, ax = plt.subplots(figsize=figsize)

    # Add lines to our plt
    max_laps = -1

    # Create y-axis labels
    # The left side is the starting position and car number
    # The right side is the finishing position and car number

    start_labels = []
    finish_labels = []
    for t in car_positions:
        num = t[0]

        n_pad = ""
        sp_pad = ""
        fp_pad = ""

        start_position = t[1][0][1]
        finish_position = t[1][-1][1]

        if len(num) == 0:
            if start_position >= 10:
                sp_pad = "      "
            else:
                sp_pad = "       "
            start_labels.append((start_position, f"P{start_position}{sp_pad}"))
            if finish_position >= 10:
                fp_pad = "    "
            else:
                fp_pad = "     "
            finish_labels.append((finish_position, f"P{finish_position}{fp_pad}"))
        else:
            if len(num) == 1:
                n_pad = "  "
            elif len(num) == 2:
                n_pad = " "
            if start_position < 10:
                sp_pad = " "
            start_labels.append((start_position, f"P{start_position}{sp_pad} - {n_pad}{num}"))
            if finish_position < 10:
                fp_pad = " "
            finish_labels.append((finish_position, f"P{finish_position}{fp_pad} - {n_pad}{num}"))

            # Add a line for this car to the plot
            ax.plot([item[0] for item in t[1]], [item[1] for item in t[1]])

            # Find the most number of laps a car ran (i.e. the highest position car)
            num_laps = len(t[1])
            if num_laps > max_laps:
                max_laps = num_laps

    for t in car_positions:
        num = t[0]
        if len(num) != 0:
            # If you were not on the last lap and did not crash on the first lap, add a position label to the last point
            if t[1][-1][0] != max_laps-1 and t[1][-1][0] != 0:
                if t[1][-1][0] != t[1][-2][0]:
                    ax.text(t[1][-1][0], t[1][-1][1], f"P{t[1][-1][1]}", ha='left', va='center')
                else:
                    ax.text(t[1][-1][0], t[1][-1][1], f"P{t[1][-1][1]}", ha='left', va='top')

    left_y_labels = [tup[1] for tup in sorted(start_labels, key=lambda x: x[0])]
    right_y_labels = [tup[1] for tup in sorted(finish_labels, key=lambda x: x[0])]

    field_size = len(car_positions)
    ax.set_ylim([field_size + 0.5, 0.5])
    ax.set_yticks(list(range(1, field_size+1)), left_y_labels)
    fin_ax = ax.secondary_yaxis('right')
    fin_ax.set_yticks(list(range(1, field_size + 1)), right_y_labels)
    ax.set_xticks(list(range(0, max_laps)))
    ax.set_xlabel('Lap')
    ax.set_ylabel('Position')
    ax.legend().set_visible(False)



    plt.xticks(range(max_laps))  # add loads of ticks
    plt.gca().margins(x=0)
    plt.gcf().canvas.draw()
    tl = plt.gca().get_xticklabels()
    maxsize = max([t.get_window_extent().width for t in tl])
    m = 5  # inch margin (orig = 0.2)
    s = maxsize / plt.gcf().dpi * max_laps + 2 * m
    margin = m / plt.gcf().get_size_inches()[0]
    plt.gcf().subplots_adjust(left=float(margin), right=float(1. - margin))
    plt.gcf().set_size_inches(s, float(plt.gcf().get_size_inches()[1]))

    #plt.grid()
    plt.tight_layout()
    print(f"Writing image file {to}")
    fig.savefig(to)

    plt.close('all')
    plt.clf()


def main():

    # Plotting an event race
    nix_keys = []
    e_filename = Path("./events/Ed Petit Le Mans.json")
    event = serialize_event_from_file(e_filename)
    for split, result in event._results.items():
        owner_teams = result.get_owner_teams(cust_id=180474)
        if len(owner_teams) > 0:
            print(f"Plotting position changes for split {split}")
            categories = set()
            for team in owner_teams:
                category = team.category
                if category in categories:
                    continue  # Already plotted
                categories.add(category)
                print(f"\tPlotting category {category}")
                car_positions = []
                for team_id, category_team in result._teams.items():
                    num = ""
                    if category_team.category == category:
                        num = f"{category_team.car_number}"
                    lap_positions = []
                    started = True
                    for i, lap in enumerate(category_team.laps):
                        if lap.position == 0:
                            started = False
                            print("hmmmm")
                        else:
                            lap_positions.append((i, lap.position))
                    if len(lap_positions) > 0 and lap_positions[-1][1] != category_team.finish_position:
                        lap_positions.append((lap_positions[-1][0], category_team.finish_position))
                    if started:
                        car_positions.append((num, lap_positions))
                img_filename = e_filename.parent / f"{e_filename.stem} Split {split} {category}.png"
                plot_position_changes(sorted(car_positions, key=lambda x: x[1][0]), img_filename, figsize=(144.0, 8.0))
    """
        else:
            del event._results[split +1]
    with open(f"./events/Ed Petit Le Mans.json", 'w') as fp:
        json.dump(event.as_dict(), fp, indent=2)
    """

    # Plotting a league race
    lg_filename = Path("./results/American Muscle Series Season 9.json")
    race = 11
    lg = serialize_league_result_from_file(lg_filename)
    car_positions = get_lap_positions(lg, race)
    img_filename = lg_filename.parent / f"{lg_filename.stem} Race {race}.png"
    plot_position_changes(car_positions, img_filename)


if __name__ == "__main__":
    main()
