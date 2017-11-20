# Comprehensive Weather Alerts
This program is designed to work with a database of users and locations and send personalized weather forecast emails to those users.

## Getting Started


### Prerequisites

You should already have sqlite3 and Python3 on your system before starting the program.

You will need an API key from OpenWeatherMap.org. This will enable you to check the 5-day forecast necessary for the program.

You will also need the SMTP information for the email address you'd like to use to send the alerts.

### Installing

First, run setup.py to initialize your database.

Add your OpenWeatherMap API key and SMTP information to the appropriate places in SAMPLEconfigInfo.py and rename the file to configInfo.py.

If you'd like a table of all the OpenWeatherMap locations, run allLocations.py to create and fill that table.

## Adding Users

You can add a user to the users table by running newUser.py and adding the appropriate information.
If the user has multiple email addresses they want the same forecast sent to, separate the email addresses by a ",".

Locations should be either a zip code or a city ID from OpenWeatherMap. The program has logic to tell these two apart and use the appropriate pull request.
If the user has multiple locations they want forecast data for, separate the locations by a ",".

The "hours" setting is for the timeframe a user wants their forecast to include. Some users will only care about the times when they are going to be awake and possibly out of the house. Others will want a full forecast.
If the user wants a full forecast, leave this blank and the program will interpret that as a full forecast.

## Deployment

Once you have users in the database, you can run main.py on a regular basis (once a day is probably the most frequent you'd want) to send regular forecast updates.

## Authors

* [Morgan S Hertz](http://mohertz.com/)

## License

This project is licensed under the CDDL-1.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to May for encouraging me to create this project in the first place.
* Thanks to Maxie for troubleshooting, brainstorming, and input.
