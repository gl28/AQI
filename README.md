# AQI Finder

Enter your current location into the web app, and you'll be shown the 10 locations near you with the best air quality.

Try the live version at https://aqifinder.herokuapp.com

## How it works

The app is set to run a Python script each hour which requests the latest air quality data from the AirNow API. (AirNow data is updated on an hourly basis.) It stores this data in a Postgres database.

When a user inputs their location, this is converted to latitude/longitude using the Google Maps API. The app then finds all the locations within a specified range that have the best air quality and displays these on a map, also using the Google Maps API.
