# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: objects.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\robjects.proto\x12\x16\x61merican_muscle_series\"j\n\rGroupRuleData\x12\x14\n\x0cMinCarNumber\x18\x01 \x01(\x05\x12\x14\n\x0cMaxCarNumber\x18\x02 \x01(\x05\x12-\n\x05Group\x18\x03 \x01(\x0e\x32\x1e.american_muscle_series.eGroup\"J\n\x0eGroupRulesData\x12\x38\n\tGroupRule\x18\x01 \x03(\x0b\x32%.american_muscle_series.GroupRuleData\"@\n\x0fTimePenaltyData\x12\x0c\n\x04Race\x18\x01 \x01(\x05\x12\x0e\n\x06\x44river\x18\x02 \x01(\x05\x12\x0f\n\x07Seconds\x18\x03 \x01(\x05\"O\n\x11ScoringSystemData\x12\x14\n\x0cPolePosition\x18\x01 \x01(\x05\x12\x12\n\nFastestLap\x18\x02 \x01(\x05\x12\x10\n\x08LapsLead\x18\x03 \x01(\x05\"d\n\x17LinearDecentScoringData\x12\x37\n\x04\x42\x61se\x18\x01 \x01(\x0b\x32).american_muscle_series.ScoringSystemData\x12\x10\n\x08TopScore\x18\x02 \x01(\x05\"\xdf\x01\n\x15\x41ssignmentScoringData\x12\x37\n\x04\x42\x61se\x18\x01 \x01(\x0b\x32).american_muscle_series.ScoringSystemData\x12W\n\rPositionScore\x18\x02 \x03(\x0b\x32@.american_muscle_series.AssignmentScoringData.PositionScoreEntry\x1a\x34\n\x12PositionScoreEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\"\xae\x01\n\x14\x41nyScoringSystemData\x12G\n\x0cLinearDecent\x18\x01 \x01(\x0b\x32/.american_muscle_series.LinearDecentScoringDataH\x00\x12\x43\n\nAssignment\x18\x02 \x01(\x0b\x32-.american_muscle_series.AssignmentScoringDataH\x00\x42\x08\n\x06System\"O\n\rGoogleTabData\x12-\n\x05Group\x18\x01 \x01(\x0e\x32\x1e.american_muscle_series.eGroup\x12\x0f\n\x07TabName\x18\x02 \x01(\t\"X\n\x10GoogleSheetsData\x12\x0b\n\x03Key\x18\x01 \x01(\t\x12\x37\n\x08GroupTab\x18\x02 \x03(\x0b\x32%.american_muscle_series.GoogleTabData\"\x99\x03\n\x17SeasonConfigurationData\x12\x0e\n\x06\x41\x63tive\x18\x01 \x01(\x08\x12\x43\n\rScoringSystem\x18\x02 \x01(\x0b\x32,.american_muscle_series.AnyScoringSystemData\x12\x10\n\x08NumDrops\x18\x03 \x01(\x05\x12\x12\n\nNonDrivers\x18\x04 \x03(\x05\x12\x18\n\x10PracticeSessions\x18\x05 \x03(\x05\x12:\n\nGroupRules\x18\x06 \x01(\x0b\x32&.american_muscle_series.GroupRulesData\x12<\n\x0bTimePenalty\x18\x07 \x03(\x0b\x32\'.american_muscle_series.TimePenaltyData\x12>\n\x0cGoogleSheets\x18\x08 \x01(\x0b\x32(.american_muscle_series.GoogleSheetsData\x12/\n\x06SortBy\x18\t \x01(\x0e\x32\x1f.american_muscle_series.eSortBy\"\xea\x01\n\x17LeagueConfigurationData\x12\x11\n\tiRacingID\x18\x01 \x01(\x05\x12\x0c\n\x04Name\x18\x02 \x01(\t\x12M\n\x07Seasons\x18\x03 \x03(\x0b\x32<.american_muscle_series.LeagueConfigurationData.SeasonsEntry\x1a_\n\x0cSeasonsEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12>\n\x05value\x18\x02 \x01(\x0b\x32/.american_muscle_series.SeasonConfigurationData:\x02\x38\x01\"\xb8\x02\n\nLeagueData\x12@\n\x07Members\x18\x01 \x03(\x0b\x32/.american_muscle_series.LeagueData.MembersEntry\x12@\n\x07Seasons\x18\x02 \x03(\x0b\x32/.american_muscle_series.LeagueData.SeasonsEntry\x1aR\n\x0cMembersEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.MemberData:\x02\x38\x01\x1aR\n\x0cSeasonsEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.SeasonData:\x02\x38\x01\",\n\nMemberData\x12\x0c\n\x04Name\x18\x01 \x01(\t\x12\x10\n\x08Nickname\x18\x02 \x01(\t\"\xb0\x02\n\nSeasonData\x12@\n\x07\x44rivers\x18\x01 \x03(\x0b\x32/.american_muscle_series.SeasonData.DriversEntry\x12<\n\x05Races\x18\x02 \x03(\x0b\x32-.american_muscle_series.SeasonData.RacesEntry\x1aR\n\x0c\x44riversEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.DriverData:\x02\x38\x01\x1aN\n\nRacesEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12/\n\x05value\x18\x02 \x01(\x0b\x32 .american_muscle_series.RaceData:\x02\x38\x01\"\xf6\x02\n\nDriverData\x12\x0c\n\x04Name\x18\x01 \x01(\t\x12\x11\n\tOldRating\x18\x02 \x01(\x05\x12\x11\n\tNewRating\x18\x03 \x01(\x05\x12\x11\n\tCarNumber\x18\x04 \x01(\x05\x12-\n\x05Group\x18\x05 \x01(\x0e\x32\x1e.american_muscle_series.eGroup\x12\x14\n\x0c\x45\x61rnedPoints\x18\x06 \x01(\x05\x12\x12\n\nDropPoints\x18\x07 \x01(\x05\x12\x19\n\x11\x43leanDriverPoints\x18\x08 \x01(\x05\x12\x18\n\x10TotalFastestLaps\x18\t \x01(\x05\x12\x16\n\x0eTotalIncidents\x18\n \x01(\x05\x12\x19\n\x11TotalLapsComplete\x18\x0b \x01(\x05\x12\x15\n\rTotalLapsLead\x18\x0c \x01(\x05\x12\x1a\n\x12TotalPolePositions\x18\r \x01(\x05\x12\x12\n\nTotalRaces\x18\x0e \x01(\x05\x12\n\n\x02Mu\x18\x0f \x01(\x02\x12\r\n\x05Sigma\x18\x10 \x01(\x02\"\xb2\x01\n\x0eGroupStatsData\x12-\n\x05Group\x18\x01 \x01(\x0e\x32\x1e.american_muscle_series.eGroup\x12\r\n\x05\x43ount\x18\x02 \x01(\x05\x12\x1a\n\x12PolePositionDriver\x18\x03 \x01(\x05\x12\x14\n\x0cPolePosition\x18\x04 \x01(\x05\x12\x18\n\x10\x46\x61stestLapDriver\x18\x05 \x01(\x05\x12\x16\n\x0e\x46\x61stestLapTime\x18\x06 \x01(\x02\"\xee\x01\n\x08RaceData\x12\x0c\n\x04\x44\x61te\x18\x01 \x01(\t\x12\r\n\x05Track\x18\x02 \x01(\t\x12\x38\n\x04Grid\x18\x03 \x03(\x0b\x32*.american_muscle_series.RaceData.GridEntry\x12:\n\nGroupStats\x18\x04 \x03(\x0b\x32&.american_muscle_series.GroupStatsData\x1aO\n\tGridEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.ResultData:\x02\x38\x01\"\xf9\x01\n\nResultData\x12\x14\n\x0cPolePosition\x18\x01 \x01(\x08\x12\x12\n\nFastestLap\x18\x02 \x01(\x08\x12\x15\n\rStartPosition\x18\x03 \x01(\x05\x12\x16\n\x0e\x46inishPosition\x18\x04 \x01(\x05\x12\x0e\n\x06Points\x18\x05 \x01(\x05\x12\x19\n\x11\x43leanDriverPoints\x18\x06 \x01(\x05\x12\x10\n\x08Interval\x18\x07 \x01(\x02\x12\x11\n\tIncidents\x18\x08 \x01(\x05\x12\x15\n\rLapsCompleted\x18\t \x01(\x05\x12\x10\n\x08LapsLead\x18\n \x01(\x05\x12\n\n\x02Mu\x18\x0b \x01(\x02\x12\r\n\x05Sigma\x18\x0c \x01(\x02\"\xdc\x01\n\tEventData\x12\x0c\n\x04Name\x18\x01 \x01(\t\x12\x11\n\tNumSplits\x18\x02 \x01(\x05\x12\x14\n\x0cIsMulticlass\x18\x03 \x01(\x08\x12?\n\x07Results\x18\x04 \x03(\x0b\x32..american_muscle_series.EventData.ResultsEntry\x1aW\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x36\n\x05value\x18\x02 \x01(\x0b\x32\'.american_muscle_series.EventResultData:\x02\x38\x01\"\x85\x05\n\x0f\x45ventResultData\x12\x17\n\x0fStrengthOfField\x18\x01 \x01(\x05\x12\x0b\n\x03URL\x18\x02 \x01(\t\x12[\n\x12StrengthOfCategory\x18\x03 \x03(\x0b\x32?.american_muscle_series.EventResultData.StrengthOfCategoryEntry\x12U\n\x0fNumCategoryCars\x18\x04 \x03(\x0b\x32<.american_muscle_series.EventResultData.NumCategoryCarsEntry\x12U\n\x0fNumCategoryLaps\x18\x05 \x03(\x0b\x32<.american_muscle_series.EventResultData.NumCategoryLapsEntry\x12\x41\n\x05Teams\x18\x06 \x03(\x0b\x32\x32.american_muscle_series.EventResultData.TeamsEntry\x1a\x39\n\x17StrengthOfCategoryEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\x1a\x36\n\x14NumCategoryCarsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\x1a\x36\n\x14NumCategoryLapsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\x1aS\n\nTeamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x34\n\x05value\x18\x02 \x01(\x0b\x32%.american_muscle_series.EventTeamData:\x02\x38\x01\"\xeb\x03\n\rEventTeamData\x12\x0c\n\x04Name\x18\x01 \x01(\t\x12\x10\n\x08\x43\x61tegory\x18\x02 \x01(\t\x12\x0b\n\x03\x43\x61r\x18\x03 \x01(\t\x12\x11\n\tReasonOut\x18\x04 \x01(\t\x12\x16\n\x0e\x46inishPosition\x18\x05 \x01(\x05\x12\x1d\n\x15\x46inishPositionInClass\x18\x06 \x01(\x05\x12\x16\n\x0eTotalIncidents\x18\x07 \x01(\x05\x12\x19\n\x11TotalLapsComplete\x18\x08 \x01(\x05\x12\x43\n\x07\x44rivers\x18\t \x03(\x0b\x32\x32.american_muscle_series.EventTeamData.DriversEntry\x12\x43\n\x07Members\x18\n \x03(\x0b\x32\x32.american_muscle_series.EventTeamData.MembersEntry\x1aR\n\x0c\x44riversEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.DriverData:\x02\x38\x01\x1aR\n\x0cMembersEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12\x31\n\x05value\x18\x02 \x01(\x0b\x32\".american_muscle_series.MemberData:\x02\x38\x01*&\n\x06\x65Group\x12\x0b\n\x07Unknown\x10\x00\x12\x07\n\x03Pro\x10\x01\x12\x06\n\x02\x41m\x10\x02*&\n\x07\x65SortBy\x12\n\n\x06\x45\x61rned\x10\x00\x12\x0f\n\x0b\x46orcedDrops\x10\x01\x42\x02H\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'objects_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'H\001'
  _ASSIGNMENTSCORINGDATA_POSITIONSCOREENTRY._options = None
  _ASSIGNMENTSCORINGDATA_POSITIONSCOREENTRY._serialized_options = b'8\001'
  _LEAGUECONFIGURATIONDATA_SEASONSENTRY._options = None
  _LEAGUECONFIGURATIONDATA_SEASONSENTRY._serialized_options = b'8\001'
  _LEAGUEDATA_MEMBERSENTRY._options = None
  _LEAGUEDATA_MEMBERSENTRY._serialized_options = b'8\001'
  _LEAGUEDATA_SEASONSENTRY._options = None
  _LEAGUEDATA_SEASONSENTRY._serialized_options = b'8\001'
  _SEASONDATA_DRIVERSENTRY._options = None
  _SEASONDATA_DRIVERSENTRY._serialized_options = b'8\001'
  _SEASONDATA_RACESENTRY._options = None
  _SEASONDATA_RACESENTRY._serialized_options = b'8\001'
  _RACEDATA_GRIDENTRY._options = None
  _RACEDATA_GRIDENTRY._serialized_options = b'8\001'
  _EVENTDATA_RESULTSENTRY._options = None
  _EVENTDATA_RESULTSENTRY._serialized_options = b'8\001'
  _EVENTRESULTDATA_STRENGTHOFCATEGORYENTRY._options = None
  _EVENTRESULTDATA_STRENGTHOFCATEGORYENTRY._serialized_options = b'8\001'
  _EVENTRESULTDATA_NUMCATEGORYCARSENTRY._options = None
  _EVENTRESULTDATA_NUMCATEGORYCARSENTRY._serialized_options = b'8\001'
  _EVENTRESULTDATA_NUMCATEGORYLAPSENTRY._options = None
  _EVENTRESULTDATA_NUMCATEGORYLAPSENTRY._serialized_options = b'8\001'
  _EVENTRESULTDATA_TEAMSENTRY._options = None
  _EVENTRESULTDATA_TEAMSENTRY._serialized_options = b'8\001'
  _EVENTTEAMDATA_DRIVERSENTRY._options = None
  _EVENTTEAMDATA_DRIVERSENTRY._serialized_options = b'8\001'
  _EVENTTEAMDATA_MEMBERSENTRY._options = None
  _EVENTTEAMDATA_MEMBERSENTRY._serialized_options = b'8\001'
  _globals['_EGROUP']._serialized_start=4781
  _globals['_EGROUP']._serialized_end=4819
  _globals['_ESORTBY']._serialized_start=4821
  _globals['_ESORTBY']._serialized_end=4859
  _globals['_GROUPRULEDATA']._serialized_start=41
  _globals['_GROUPRULEDATA']._serialized_end=147
  _globals['_GROUPRULESDATA']._serialized_start=149
  _globals['_GROUPRULESDATA']._serialized_end=223
  _globals['_TIMEPENALTYDATA']._serialized_start=225
  _globals['_TIMEPENALTYDATA']._serialized_end=289
  _globals['_SCORINGSYSTEMDATA']._serialized_start=291
  _globals['_SCORINGSYSTEMDATA']._serialized_end=370
  _globals['_LINEARDECENTSCORINGDATA']._serialized_start=372
  _globals['_LINEARDECENTSCORINGDATA']._serialized_end=472
  _globals['_ASSIGNMENTSCORINGDATA']._serialized_start=475
  _globals['_ASSIGNMENTSCORINGDATA']._serialized_end=698
  _globals['_ASSIGNMENTSCORINGDATA_POSITIONSCOREENTRY']._serialized_start=646
  _globals['_ASSIGNMENTSCORINGDATA_POSITIONSCOREENTRY']._serialized_end=698
  _globals['_ANYSCORINGSYSTEMDATA']._serialized_start=701
  _globals['_ANYSCORINGSYSTEMDATA']._serialized_end=875
  _globals['_GOOGLETABDATA']._serialized_start=877
  _globals['_GOOGLETABDATA']._serialized_end=956
  _globals['_GOOGLESHEETSDATA']._serialized_start=958
  _globals['_GOOGLESHEETSDATA']._serialized_end=1046
  _globals['_SEASONCONFIGURATIONDATA']._serialized_start=1049
  _globals['_SEASONCONFIGURATIONDATA']._serialized_end=1458
  _globals['_LEAGUECONFIGURATIONDATA']._serialized_start=1461
  _globals['_LEAGUECONFIGURATIONDATA']._serialized_end=1695
  _globals['_LEAGUECONFIGURATIONDATA_SEASONSENTRY']._serialized_start=1600
  _globals['_LEAGUECONFIGURATIONDATA_SEASONSENTRY']._serialized_end=1695
  _globals['_LEAGUEDATA']._serialized_start=1698
  _globals['_LEAGUEDATA']._serialized_end=2010
  _globals['_LEAGUEDATA_MEMBERSENTRY']._serialized_start=1844
  _globals['_LEAGUEDATA_MEMBERSENTRY']._serialized_end=1926
  _globals['_LEAGUEDATA_SEASONSENTRY']._serialized_start=1928
  _globals['_LEAGUEDATA_SEASONSENTRY']._serialized_end=2010
  _globals['_MEMBERDATA']._serialized_start=2012
  _globals['_MEMBERDATA']._serialized_end=2056
  _globals['_SEASONDATA']._serialized_start=2059
  _globals['_SEASONDATA']._serialized_end=2363
  _globals['_SEASONDATA_DRIVERSENTRY']._serialized_start=2201
  _globals['_SEASONDATA_DRIVERSENTRY']._serialized_end=2283
  _globals['_SEASONDATA_RACESENTRY']._serialized_start=2285
  _globals['_SEASONDATA_RACESENTRY']._serialized_end=2363
  _globals['_DRIVERDATA']._serialized_start=2366
  _globals['_DRIVERDATA']._serialized_end=2740
  _globals['_GROUPSTATSDATA']._serialized_start=2743
  _globals['_GROUPSTATSDATA']._serialized_end=2921
  _globals['_RACEDATA']._serialized_start=2924
  _globals['_RACEDATA']._serialized_end=3162
  _globals['_RACEDATA_GRIDENTRY']._serialized_start=3083
  _globals['_RACEDATA_GRIDENTRY']._serialized_end=3162
  _globals['_RESULTDATA']._serialized_start=3165
  _globals['_RESULTDATA']._serialized_end=3414
  _globals['_EVENTDATA']._serialized_start=3417
  _globals['_EVENTDATA']._serialized_end=3637
  _globals['_EVENTDATA_RESULTSENTRY']._serialized_start=3550
  _globals['_EVENTDATA_RESULTSENTRY']._serialized_end=3637
  _globals['_EVENTRESULTDATA']._serialized_start=3640
  _globals['_EVENTRESULTDATA']._serialized_end=4285
  _globals['_EVENTRESULTDATA_STRENGTHOFCATEGORYENTRY']._serialized_start=4031
  _globals['_EVENTRESULTDATA_STRENGTHOFCATEGORYENTRY']._serialized_end=4088
  _globals['_EVENTRESULTDATA_NUMCATEGORYCARSENTRY']._serialized_start=4090
  _globals['_EVENTRESULTDATA_NUMCATEGORYCARSENTRY']._serialized_end=4144
  _globals['_EVENTRESULTDATA_NUMCATEGORYLAPSENTRY']._serialized_start=4146
  _globals['_EVENTRESULTDATA_NUMCATEGORYLAPSENTRY']._serialized_end=4200
  _globals['_EVENTRESULTDATA_TEAMSENTRY']._serialized_start=4202
  _globals['_EVENTRESULTDATA_TEAMSENTRY']._serialized_end=4285
  _globals['_EVENTTEAMDATA']._serialized_start=4288
  _globals['_EVENTTEAMDATA']._serialized_end=4779
  _globals['_EVENTTEAMDATA_DRIVERSENTRY']._serialized_start=2201
  _globals['_EVENTTEAMDATA_DRIVERSENTRY']._serialized_end=2283
  _globals['_EVENTTEAMDATA_MEMBERSENTRY']._serialized_start=1844
  _globals['_EVENTTEAMDATA_MEMBERSENTRY']._serialized_end=1926
# @@protoc_insertion_point(module_scope)
