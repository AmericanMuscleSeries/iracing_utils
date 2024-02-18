## League Support

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
If you are working within the AMS team, you can be added to our [ams project](
https://console.cloud.google.com/apis/credentials?project=american-muscle-series).
To get the required credentials json, goto the project and click `Credentials` under the `APIs & Services`, 
and click the download arrow on the AMS_Utils row under the `OAuth 2.0 Client IDs` section. 
This will bring up a dialog where you can download the json file.
Rename it `credentials.json` and place it in your working directory.

## Session Support

### Aussie Pursuit


