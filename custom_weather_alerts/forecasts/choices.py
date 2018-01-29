import csv
from config.settings.base import ROOT_DIR


timezones = [
    ('US/Alaska','US/Alaska'),
    ('US/Arizona','US/Arizona'),
    ('US/Central','US/Central'),
    ('US/Eastern','US/Eastern'),
    ('US/Hawaii','US/Hawaii'),
    ('US/Mountain','US/Mountain'),
    ('US/Pacific','US/Pacific')
]
times = [
    (0,'12 am'),
    (1,'1 am'),
    (2,'2 am'),
    (3,'3 am'),
    (4,'4 am'),
    (5,'5 am'),
    (6,'6 am'),
    (7,'7 am'),
    (8,'8 am'),
    (9,'9 am'),
    (10,'10 am'),
    (11,'11 am'),
    (12,'12 pm'),
    (13,'1 pm'),
    (14,'2 pm'),
    (15,'3 pm'),
    (16,'4 pm'),
    (17,'5 pm'),
    (18,'6 pm'),
    (19,'7 pm'),
    (20,'8 pm'),
    (21,'9 pm'),
    (22,'10 pm'),
    (23,'11 pm')
]
forecastdays = [
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5')
]
alerts = [
    ("F",'Freezing'),
    ("L",'Projected Lows'),
    ("H",'Projected Highs'),
    ("R",'Rain'),
    ("S",'Snow'),
    ("A",'Full Forecast (This includes all of the above.)')
]


# !! COULD NOT MAKE THIS MANAGEABLE. SWITCHED BACK TO HAVING USERS ENTER ZIP CODES.!!
# There are over 39,000 locations. Trying to make this as easy as possible.
# lc_file_path = str(ROOT_DIR.path('forecasts/locationchoices.csv'))
# lc_file = open(lc_file_path)
# lc_reader = csv.reader(lc_file)
# locations = list(lc_reader)

