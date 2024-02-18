# AMS Utilities
The projects within this repo contain utilities for managing the American Muscle Series league in iRacing.

## Driver Ratings
`driver-ratings` contains a system for calculating driver ratings based on the TrueSkill algorithm.

## Discord Bot
`discord-bot` contains a bot for Discord named Jessica Rabbot. This bot conatins commands for drivers to register for the league, manage some of their registration info, claim a number, and admin functions.

## League
`league` contains various algorithms using data pulled from iracing.

Provided drivers (To use any of these drivers, pip install the requirements.txt in the league directory)

`aussie_pursuit.py` - Uses the iRacing API to analyze a provided session id to calculate penalty times for all cars.
An aussie pursuit race is a multiclass race where each driver gets a penalty time based on their lap time.
The intent of the penalties is to time them so that all drivers in all cars all have the ability to cross the finish line at the same time.

`score_league.py` - Pull all data associated with a iRacing league and score one or more seasons using our scoring methodology.
This also provides a mechanism for publishing scores to a Google sheet.