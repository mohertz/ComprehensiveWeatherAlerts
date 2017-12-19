import pytz
import sqlite3
import urllib.request, urllib.parse, urllib.error
import json
import datetime
import logging
import configInfo
from classes import possibleConditions


logging.basicConfig(filename="weatherlogs.log",format="%(asctime)s | %(filename)s , %(lineno)d| %(levelname)s: %(message)s",level=logging.DEBUG)
conn = sqlite3.connect("data.sqlite3")


class Person:

    freezingThresh = 33
    possAlerts = ["FREEZING","PROJECTED LOWS","PROJECTED HIGHS","RAIN","SNOW","FULL DETAILS"]

    def __init__(self,user_id):
        self.user_id = user_id
        self.EMAIL_TO = []
        self.email_type = None
        self.locations = []
        self.tz = None
        self.hours = {"Start": "00:00", "End": "23:59"}
        self.alerts = []
        self.forecast_days = None
        self.forecast = {}
        self.email_subj = "Upcoming Forecast"
        self.email_body = None
        self.freezing = False
        self.rain = False
        self.snow = False
        self.extreme = False

        logging.info("Creating person instance: %s" % str(self.user_id))

        cur = conn.cursor()
        cur.execute("SELECT * FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            full = cur.fetchone()
        except:
            quit()

        # populate email address(es) for user
        try:
            email_list = full[1].split(",")
            for i in email_list:
                self.EMAIL_TO.append(i)
        except:
            if full[1] is not None:
                self.EMAIL_TO.append(full[1])
            else:
                quit()

        # populate type of email for user
        if full[2] is not None:
            self.email_type = full[2]
        else:
            self.email_type = "email"

        # populate location(s) for user
        try:
            locs_list = full[3].split(",")
            for l in locs_list:
                self.locations.append(l)
        except:
            if full[3] is not None:
                self.locations.append(full[3])
            else:
                quit()

        # populate timeframe for user
        try:
            time_list = full[4].split(",")
            if len(time_list[0]) > 0 and time_list[0] < time_list[1]:
                self.hours["Start"] = time_list[0]
            else:
                pass
            if len(time_list[1]) > 0 and time_list[1] > time_list[0]:
                self.hours["End"] = time_list[1]
            else:
                pass
        except:
            pass
        if len(self.hours["Start"]) == 2:
            self.hours["Start"] = self.hours["Start"]+":00"
        elif len(self.hours["Start"]) == 1:
            self.hours["Start"] = "0"+self.hours["Start"]+":00"
        if len(self.hours["End"]) == 2:
            self.hours["End"] = self.hours["End"]+":00"
        elif len(self.hours["End"]) == 1:
            self.hours["End"] = "0"+self.hours["End"]+":00"

        # populate alert(s) for user
        try:
            alerts_list = full[5].split(",")
            for a in alerts_list:
                if a.upper() in self.possAlerts:
                    self.alerts.append(a.upper)
                    logging.info("Alert in list: %s" % a)
                else:
                    logging.warning("Alert not in list: %s" % a)
                    continue
        except:
            if full[5] is not None and full[5] in self.possAlerts:
                self.alerts.append(full[5])
                logging.info("Only one alert and in list: %s" % full[5])
            else:
                self.alerts = "all"
                logging.info("No alerts in list. Adding all.")

        if self.alerts == "all" or "FULL DETAILS" in self.alerts or self.alerts is None or len(self.alerts) < 1:
            self.alerts = self.possAlerts
            logging.info("Populating all alerts.")

        # populate days in forecast for user
        if full[6] is not None and int(full[6]) < 6:
            self.forecast_days = int(full[6])
        elif int(full[6]) > 5:
            logging.warning("Number of days over 5 for user %s" % str(self.user_id))
            self.forecast_days = 5
        else:
            logging.warning("Number of days not set for user %s" % str(self.user_id))
            if self.email_type.lower() == "sms":
                self.forecast_days = 1
            else:
                self.forecast_days = 5

        # populate timezone for user
        if full[7] is not None:
            try:
                self.tz = pytz.timezone(full[7])
            except:
                self.tz = pytz.timezone("UTC")
        else:
            self.tz = pytz.timezone("UTC")

        cur.close()


    def updateForecast(self,fData):
        logging.info("Updating forecast: %s for %s" % (str(fData.location),str(self.user_id)))

        # below cursor connection is to pull the human-readable city from the location table
        cur = conn.cursor()
        cur.execute("SELECT name FROM Locations WHERE id = :id",{"id": fData.location})
        try:
            locName = cur.fetchone()[0]
        except:
            locName = fData.location
        cur.close()

        st = int(self.hours["Start"].split(":")[0])
        upper = st - 2
        if upper < 0:
            upper = 0
        end = int(self.hours["End"].split(":")[0])
        lower = end + 2
        if lower > 23:
            lower = 23

        d = 0
        for daytime in fData.parsed_forecast:
            condAdd = False
            UTCdt = datetime.datetime.utcfromtimestamp(daytime).replace(tzinfo=pytz.utc)
            forecastDayTime = UTCdt.astimezone(self.tz)
            forecastDay = forecastDayTime.strftime("%Y-%m-%d")
            forecastTime = forecastDayTime.strftime("%H:%M")

            fH = int(forecastTime.split(":")[0])

            # checking that forecast time is within user's preference
            if fH < upper or fH > lower:
                continue

            else:
                if forecastDay not in self.forecast:

                    # below checks to see how many days are in the forecast and ends if it's surpassed user's preference
                    # since it would be foolish to send an email with an alert for a day they don't want to know about yet
                    d += 1
                    if d > self.forecast_days:
                        break

                    else:
                        if fH < 12:
                            self.forecast[forecastDay] = {locName: {"AM Low": fData.parsed_forecast[daytime]["Low"],
                                                                    "PM Low": 999,
                                                                    "High": fData.parsed_forecast[daytime]["High"],
                                                                    "CondCode": [], "Cond": [], "Conditions": []}}
                        else:
                            self.forecast[forecastDay] = {locName: {"AM Low": 999,
                                                                    "PM Low": fData.parsed_forecast[daytime]["Low"],
                                                                    "High": fData.parsed_forecast[daytime]["High"],
                                                                    "CondCode": [], "Cond": [], "Conditions": []}}

                        # below checks for extreme weather, rain, and snow
                        if fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllExtreme:
                            self.extreme = True
                            condAdd = True
                        elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllRain and "Rain" in self.alerts:
                            self.rain = True
                            condAdd = True
                        elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.Snow and "Snow" in self.alerts:
                            self.snow = True
                            condAdd = True
                        elif "Full Details" in self.alerts:
                            condAdd = True

                        if condAdd == True:
                            self.forecast[forecastDay][locName]["Conditions"].append((forecastTime, fData.parsed_forecast[daytime]["Conditions"]))

                else:
                    condDescLast = len(self.forecast[forecastDay][locName]["Conditions"])-1

                    if fH < 12 and fData.parsed_forecast[daytime]["Low"] < self.forecast[forecastDay][locName]["AM Low"]:
                        self.forecast[forecastDay][locName]["AM Low"] = fData.parsed_forecast[daytime]["Low"]
                        # below checks for freezing temps
                        if fData.parsed_forecast[daytime]["Low"] < self.freezingThresh and self.freezing == False and "Freezing" in self.alerts:
                            self.freezing = True

                    elif fH >= 12 and fData.parsed_forecast[daytime]["Low"] < self.forecast[forecastDay][locName]["PM Low"]:
                        self.forecast[forecastDay][locName]["PM Low"] = fData.parsed_forecast[daytime]["Low"]
                        # below checks for freezing temps
                        if fData.parsed_forecast[daytime]["Low"] < self.freezingThresh and self.freezing == False and "Freezing" in self.alerts:
                            self.freezing = True

                    if fData.parsed_forecast[daytime]["High"] > self.forecast[forecastDay][locName]["High"]:
                        self.forecast[forecastDay][locName]["High"] = fData.parsed_forecast[daytime]["High"]

                    # below checks for extreme weather, rain, snow,
                    if fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllExtreme:
                        self.extreme = True
                        condAdd = True
                    elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllRain and "RAIN" in self.alerts:
                        self.rain = True
                        condAdd = True
                    elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.Snow and "SNOW" in self.alerts:
                        self.snow = True
                        condAdd = True
                    elif "FULL DETAILS" in self.alerts:
                        condAdd = True
                    else:
                        continue

                    if fData.parsed_forecast[daytime]["Conditions"] != self.forecast[forecastDay][locName]["Conditions"][condDescLast][1] and condAdd == True:
                        self.forecast[forecastDay][locName]["Conditions"].append((forecastTime, fData.parsed_forecast[daytime]["Conditions"]))


    def composeEmail(self):
        logging.info("Composing email for %s" % str(self.user_id))

        self.email_body = ""
        for d in self.forecast:
            self.email_body = self.email_body + d + "\r\n"
            for l in self.forecast[d]:
                self.email_body = self.email_body + "==" + l + "==\r\n"
                if "PROJECTED LOWS" in self.alerts:
                    if self.forecast[d][l]["AM Low"] < 999:
                        self.email_body = self.email_body + "  AM Low: " + str(self.forecast[d][l]["AM Low"]) + "\r\n"
                    if self.forecast[d][l]["PM Low"] < 999:
                        self.email_body = self.email_body + "  PM Low: " + str(self.forecast[d][l]["PM Low"]) + "\r\n"
                elif self.freezing == True:
                    if self.forecast[d][l]["AM Low"] < self.freezingThresh:
                        self.email_body = self.email_body + "  AM Low: " + str(self.forecast[d][l]["AM Low"]) + "\r\n"
                    if self.forecast[d][l]["PM Low"] < self.freezingThresh:
                        self.email_body = self.email_body + "  PM Low: " + str(self.forecast[d][l]["PM Low"]) + "\r\n"

                if "PROJECTED HIGHS" in self.alerts:
                    self.email_body = self.email_body + "  High: " + str(self.forecast[d][l]["High"]) + "\r\n"

                if len(self.forecast[d][l]["Conditions"]) > 0:
                    self.email_body = self.email_body + "  Conditions:\r\n"
                    for t in self.forecast[d][l]["Conditions"]:
                        self.email_body = self.email_body + "  - " + str(self.forecast[d][l]["Conditions"][t][0]) + ": " + self.forecast[d][l]["Conditions"][t][1] + "\r\n"

            self.email_body = self.email_body + "\r\n"
        if self.extreme == True:
            self.email_subj = "EXTREME WEATHER ALERT"
        if self.snow == True:
            self.email_subj = self.email_subj + " - SNOW DETECTED"
        if self.rain == True:
            self.email_subj = self.email_subj + " - RAIN DETECTED"
        if self.freezing == True:
            self.email_subj = self.email_subj + " - FREEZING TEMPS DETECTED"

        cur = conn.cursor()
        try:
            cur.execute("""INSERT INTO EmailArchive (recipient, subj, body, created, status) 
                        VALUES (:user, :subj, :body, :dayt, :stat)""",
                        {"user": self.user_id, "subj": self.email_subj, "body": self.email_body, "dayt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "stat": "pending"})
            conn.commit()
        except:
            print("Failed to insert email into table")

        cur.close()


    def dumpForecast(self):
        for d in self.forecast:
            print(d)
            for l in self.forecast[d]:
                print(l)
                for item in self.forecast[d][l]:
                    print(item, self.forecast[d][l][item])



class Forecast:

    serviceurl = "http://api.openweathermap.org/data/2.5/forecast?"
    urlend = "&units=imperial&APPID=" + configInfo.APIkey
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    def __init__(self,loc):
        self.location = loc
        self.inDB = True
        self.forecast = None
        self.parsed_forecast = {}
        if len(loc) == 5:
            self.location_type = "zip"
        else:
            self.location_type = "cid"
        logging.info("Creating forecast instance: %s" % str(self.location))

    def checkForecastLocal(self):
        logging.info("Checking forecast cache for %s" % str(self.location))

        cur = conn.cursor()
        cur.execute("SELECT * FROM ForecastData WHERE location = :loc", {"loc": self.location})
        try:
            forecast_data = cur.fetchone()
            try:
                last_update = forecast_data[2]
            except:
                last_update = None
        except:
            self.inDB = False
            forecast_data = None
            last_update = None
        if forecast_data is not None and last_update is not None and last_update == self.today:
            try:
                self.forecast = json.loads(forecast_data[1])
            except:
                logging.warning("Cannot load forecast data from database for %s" % str(self.location))
                self.checkForecastRemote()
        elif forecast_data is None or len(forecast_data) < 1:
            self.inDB = False
            logging.info("No forecast data found in database for %s" % str(self.location))
            self.checkForecastRemote()
        else:
            logging.info("No recent forecast data found in database for %s" % str(self.location))
            self.checkForecastRemote()
        cur.close()

    def checkForecastRemote(self):
        logging.info("Looking up forecast for %s" % str(self.location))

        cur = conn.cursor()
        if self.location_type == "zip":
            url_loc = "zip=" + self.location
        else:
            url_loc = "id=" + self.location
        url = self.serviceurl + url_loc + self.urlend
        uh = urllib.request.urlopen(url)
        data = uh.read().decode()

        try:
            js = json.loads(data)
        except:
            logging.warning("Unable to load JSON data for %s" % str(self.location))
            js = None

        if js is not None:
            self.forecast = js
            if self.inDB == True:
                cur.execute("UPDATE ForecastData SET last_update = :update, forecast = :fore WHERE location = :loc",{"update": self.today, "fore": str(data), "loc": self.location})
                conn.commit()
                logging.info("Updated forecast data for %s" % str(self.location))
            else:
                cur.execute("INSERT INTO ForecastData (location, last_update, forecast) VALUES (:loc, :update, :fore)", {"loc": self.location, "update": self.today, "fore": str(data)})
                conn.commit()
                logging.info("Added forecast data for %s to database" % str(self.location))
        cur.close()

    def readForecast(self):
        logging.info("Parsing forecast for %s" % str(self.location))

        for item in self.forecast["list"]:
            forecast_daytime = item["dt"]
            projLow = item["main"]["temp_min"]
            projHigh = item["main"]["temp_max"]
            projCondCode = item["weather"][0]["id"]
            projCond = item["weather"][0]["main"]
            projCondDesc = item["weather"][0]["description"]
            self.parsed_forecast[forecast_daytime] = {"Low": projLow, "High": projHigh,"CondCode": projCondCode, "Cond": projCond, "Conditions": projCondDesc}
