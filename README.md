The old scoring system we used had a driver rating system implementing a C# library for TrueSkill. I found a pretty clean Python library. I threw this together. It'll take a roster in a weird format (driver ID, mu, sigma, finishing positions..). Mu and sigma are related to the skill grading, mu being the rating and sigma being the confidence level.

You'll need to install trueskill.

`pip install trueskill`

Notes:
`-1` used for a finishing position for a missed race
CSV gets rewritten in place, sorted by mu high-to-low
runs on my install of Python 3.10.11
poc.py was me sandboxing the library
takes input from `roster/test-roster.csv`
`roster/test-roster.csv.small` was my original test data set
`roster/test-roster.csv.sanity` is a sanity-check test set that has no missing races and the same finishing order each race
`roster/test-roster.csv.s5` is a test set using the season 5 data
