# Comprehensive Weather Alerts
This program is designed to work with a database of users and locations and send personalized weather forecast emails to those users. It is configured to send emails once a day with a custom run command.

## UPDATE

This program stopped working with Python 3.7. Current research indicates that is due to Python 3.7 not being backwards compatible with Django 1.11. Version 2.0.0 is in progress to update to Django 2.0 and hopefully fix this problem.

## Getting Started


### Prerequisites

You should already have Django 1.11, sqlite3, and Python3 on your system before starting the program.

You will need an API key from OpenWeatherMap.org. This will enable you to check the 5-day forecast necessary for the program.

You will also need the SMTP information for the email address you'd like to use to send the alerts.

### Installing

Install basic requirements:
```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```
You'll also need to install the requirements in requirements/local.txt for local debug requirements.

Then run migrations as usual in Django.

## Deployment

### Running the Forecasts

This program comes with a custom command to run all the forecasts.
```python
python manage.py runallforecasts
```
or
```python
python3 manage.py runallforecasts
```

Use the above command to check all forecasts that haven't been checked in the same day and send relevant emails.
A scheduled cron job or other task manager can run this on a regular basis.

## Settings and Other Information

The program is set up to use environment variables for the sensitive information. See env.sample for the settings that will need to go in your environment variables. You can also use a .env file for these settings.

The account management system and basic template comes from [cookiecutter-django](https://github.com/pydanny/cookiecutter-django). If you want to use AWS to serve static files or use Celery, or any of the other options available in the cookiecutter, you can see the settings in the original and add them back into the program settings.

## Authors

* [Morgan S Hertz](http://mohertz.com/)

## License

This project is licensed under the CDDL-1.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to May for encouraging me to create this project in the first place.
* Thanks to Maxie for troubleshooting, brainstorming, and input.
