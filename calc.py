from Driver import Driver

import trueskill
import csv


def read_csv(path):
    drivers = []

    with open(path, mode='r') as file:
        reader = csv.reader(file)

        for row in reader:
            drivers.append(Driver(row))
    
    return drivers


def write_csv(path, drivers):
    drivers = sorted(drivers, key=lambda driver: driver.rating.mu, reverse=True)

    with open(path, mode='w') as file:
        for i in range(len(drivers)):
            if i != 0:
                file.write('\n')
            
            file.write(','.join(drivers[i].to_file()))


def calculate_race(entries, finishing_positions):
    grid = [(entry.rating,) for entry in entries]
    
    return trueskill.rate(grid, finishing_positions)


def calculate_races(path):
    roster = read_csv(path)

    for race_num in range(len(roster[0].finishes)):
        race_entries = list()
        finishing_positions = list()

        for entry in roster:
            finish = entry.finishes[race_num]

            if int(finish) > -1:
                race_entries.append(entry)
                finishing_positions.append(int(finish))

        result = calculate_race(race_entries, finishing_positions)

        for i in range(len(result)):
            race_entries[i].update(result[i][0])
    
    write_csv(path, roster)


path = 'roster/test-roster.csv'
calculate_races(path)
