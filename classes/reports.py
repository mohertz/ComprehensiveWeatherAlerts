# need to update to pull email type and number of days in forecast
# if number of days is null, default to full 5 days


import pytz
import sqlite3
import urllib.request, urllib.parse, urllib.error
import json
import datetime
import configInfo
from classes import possibleConditions


conn = sqlite3.connect("data.sqlite3")


class Person:

    freezingThresh = 33
    possAlerts = ["Freezing","Projected Lows","Projected Highs","Rain","Snow"]

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
        self.email_subj = None
        self.email_body = None

    def addEmailTo(self):
        cur = conn.cursor()
        cur.execute("SELECT email_to FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            email_str = cur.fetchone()[0]
        except:
            quit()
        try:
            email_list = email_str.split(",")
            for i in email_list:
                self.EMAIL_TO.append(i)
        except:
            self.EMAIL_TO.append(email_str)
        cur.close()

    def addEmailType(self):
        cur = conn.cursor()
        cur.execute("SELECT email_type FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            self.email_type = cur.fetchone()[0]
        except:
            self.email_type = "email"
        cur.close()

    def addLocations(self):
        cur = conn.cursor()
        cur.execute("SELECT locations FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            locations_str = cur.fetchone()[0]
        except:
            pass
        try:
            locations_list = locations_str.split(",")
            for i in locations_list:
                self.locations.append(i)
        except:
            self.locations.append(locations_str)
        cur.close()

    def adjustHours(self):
        cur = conn.cursor()
        cur.execute("SELECT time FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            time_str = cur.fetchone()[0]
        except:
            quit()
        try:
            time_list = time_str.split(",")
            self.hours["Start"] = time_list[0]
            self.hours["End"] = time_list[1]
        except:
            pass
        if len(self.hours["Start"]) == 2:
            self.hours["Start"] = self.hours["Start"]+":00"
        if len(self.hours["End"]) == 2:
            self.hours["End"] = self.hours["End"]+":00"
        cur.close()

    def setAlerts(self):
        cur = conn.cursor()
        cur.execute("SELECT alerts FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            alerts_str = cur.fetchone()[0]
        except:
            pass
        try:
            alerts_list = alerts_str.split(",")
            for i in alerts_list:
                if i in self.possAlerts:
                    self.alerts.append(i)
                else:
                    continue
        except:
            if i in self.possAlerts:
                self.alerts.append(alerts_str)
            else:
                pass
        cur.close()

    def setDays(self):
        cur = conn.cursor()
        cur.execute("SELECT forecast_days FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            self.forecast_days = int(cur.fetchone()[0])
        except:
            if self.email_type.lower() == "sms":
                self.forecast_days = 1
            else:
                self.forecast_days = 5

    def setTZ(self):
        cur = conn.cursor()
        cur.execute("SELECT tz FROM Users WHERE id = :id",{"id": self.user_id})
        try:
            tz = cur.fetchone()[0]
        except:
            quit()
        if tz in pytz.all_timezones:
            self.tz = pytz.timezone(tz)
        else:
            self.tz = "UTC"
        cur.close()

    def populatePerson(self):
        self.addEmailTo()
        self.addEmailType()
        self.addLocations()
        self.adjustHours()
        self.setAlerts()
        self.setDays()
        self.setTZ()

    def updateForecast(self,fData):
        # below cursor connection is to pull the human-readable city from the location table
        cur = conn.cursor()
        cur.execute("SELECT name FROM Locations WHERE id = :id",{"id": fData.location})
        try:
            locName = cur.fetchone()[0]
        except:
            locName = fData.location
        cur.close()

        for daytime in fData.parsed_forecast:
            UTCdt = datetime.datetime.utcfromtimestamp(daytime).replace(tzinfo=pytz.utc)
            forecastDayTime = UTCdt.astimezone(self.tz)
            forecastDayTimeStr = forecastDayTime.strftime("%Y-%m-%d %H:%M")
            forecastDay = forecastDayTime.strftime("%Y-%m-%d")
            forecastTime = forecastDayTime.strftime("%H:%M")
            if forecastTime < self.hours["Start"] or forecastTime > self.hours["End"]:
                continue
            else:
                if forecastDay not in self.forecast:
                    self.forecast[forecastDay] = {locName: {"Low": fData.parsed_forecast[daytime]["Low"], "High": fData.parsed_forecast[daytime]["High"], "CondCode": [], "Cond": [], "Conditions": []}}
                    self.forecast[forecastDay][locName]["CondCode"].append((forecastTime, fData.parsed_forecast[daytime]["CondCode"]))
                    self.forecast[forecastDay][locName]["Cond"].append((forecastTime, fData.parsed_forecast[daytime]["Cond"]))
                    self.forecast[forecastDay][locName]["Conditions"].append((forecastTime, fData.parsed_forecast[daytime]["Conditions"]))
                else:
                    condCodeLast = len(self.forecast[forecastDay][locName]["CondCode"])-1
                    condLast = len(self.forecast[forecastDay][locName]["Cond"])-1
                    condDescLast = len(self.forecast[forecastDay][locName]["Conditions"])-1
                    if fData.parsed_forecast[daytime]["Low"] < self.forecast[forecastDay][locName]["Low"]:
                        self.forecast[forecastDay][locName]["Low"] = fData.parsed_forecast[daytime]["Low"]
                    if fData.parsed_forecast[daytime]["High"] > self.forecast[forecastDay][locName]["High"]:
                        self.forecast[forecastDay][locName]["High"] = fData.parsed_forecast[daytime]["High"]
                    if fData.parsed_forecast[daytime]["CondCode"] != self.forecast[forecastDay][locName]["CondCode"][condCodeLast][1]:
                        self.forecast[forecastDay][locName]["CondCode"].append((forecastTime, fData.parsed_forecast[daytime]["CondCode"]))
                    if fData.parsed_forecast[daytime]["Cond"] != self.forecast[forecastDay][locName]["Cond"][condLast][1]:
                        self.forecast[forecastDay][locName]["Cond"].append((forecastTime, fData.parsed_forecast[daytime]["Cond"]))
                    if fData.parsed_forecast[daytime]["Conditions"] != self.forecast[forecastDay][locName]["Conditions"][condDescLast][1]:
                        self.forecast[forecastDay][locName]["Conditions"].append((forecastTime, fData.parsed_forecast[daytime]["Conditions"]))

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

    def checkForecastLocal(self):
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
                self.checkForecastRemote()
        elif forecast_data is None or len(forecast_data) < 1:
            self.inDB = False
            self.checkForecastRemote()
        else:
            self.checkForecastRemote()
        cur.close()

    def checkForecastRemote(self):
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
            js = None

        if js is not None:
            self.forecast = js
            if self.inDB == True:
                cur.execute("UPDATE ForecastData SET last_update = :update, forecast = :fore WHERE location = :loc",{"update": self.today, "fore": str(self.forecast), "loc": self.location})
                conn.commit()
            else:
                cur.execute("INSERT OR IGNORE INTO ForecastData (location, last_update, forecast) VALUES (:loc, :update, :fore)", {"loc": self.location, "update": self.today, "fore": str(self.forecast)})
                conn.commit()
        cur.close()

    def readForecast(self):
        for item in self.forecast["list"]:
            forecast_daytime = item["dt"]
            projLow = item["main"]["temp_min"]
            projHigh = item["main"]["temp_max"]
            projCondCode = item["weather"][0]["id"]
            projCond = item["weather"][0]["main"]
            projCondDesc = item["weather"][0]["description"]
            self.parsed_forecast[forecast_daytime] = {"Low": projLow, "High": projHigh,"CondCode": projCondCode, "Cond": projCond, "Conditions": projCondDesc}
