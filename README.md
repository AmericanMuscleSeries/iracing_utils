# iRacing Utilities
The main utilities provided by this repo are for:
  - Scoring iRacing leagues, and pushing up results to a Google Sheet
  - Pulling and creating reports of iRacing sessions

There are a few other scripts that may or may not work....

## League Support

`score_league.py` - Pull all data associated with a iRacing league and score one or more seasons using our scoring methodology.
This also provides a mechanism for publishing scores to a Google sheet.

### Implementation Notes

Using Protobuf to setup the data model
When updating the objects.proto, run (from this directory):
`protoc.exe --python_out=. objects.proto`

### Scoring

As part of our scoring system, we include the [TrueSkill library](
https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/?from=https://research.microsoft.com/en-us/projects/trueskill/&type=exact). 
Based on finishing positions, it calculates a mu and sigma for skill grading.
Mu being the rating and sigma being the confidence level.

#### Connection to Google Sheets

We are utilizing gspread to connect and publish scores to google sheets.
Here is an [example sheet](
https://docs.google.com/spreadsheets/d/1jlybjNg8sQGFuwSPrnNvQRq5SrIX73QUbISNVIp3Clk/edit?usp=sharing). 
If you would like to do this, you will need to make your own [google project](
https://docs.gspread.org/en/latest/oauth2.html#enable-api-access-for-a-project), and use a project oauth json file as your credentials.

Then you can [create your credential file](https://docs.gspread.org/en/latest/oauth2.html#) for your authentication type.
Ensure the proper gsheet api call is used in the sheets.py GDrive constructor.
Note the argparse section in clients.py for the default credentials filename.

If you are using OAuth, and it's been a while, and you are getting errors connecting
Delete this file %AppData%\Roaming\gspread\authorized_user.json

## Session Support

### Aussie Pursuit

`aussie_pursuit.py` - Uses the iRacing API to analyze a provided session id to calculate penalty times for all cars.
An aussie pursuit race is a multiclass race where each driver gets a penalty time based on their lap time.
The intent of the penalties is to time them so that all drivers in all cars all have the ability to cross the finish line at the same time.

## Creating an executable

Using pyinstaller
cd path/to/your/script/folder
pyinstaller --onefile your_script_name.py

