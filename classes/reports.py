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
        self.email_subj = "Upcoming Forecast"
        self.email_body = None
        self.freezing = False
        self.rain = False
        self.snow = False
        self.extreme = False

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
            if len(time_list[0]) > 0:
                self.hours["Start"] = time_list[0]
            else:
                pass
            if len(time_list[1]) > 0:
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
                if i in self.possAlerts:
                    self.alerts.append(a)
                else:
                    continue
        except:
            if full[5] is not None and full[5] in self.possAlerts:
                self.alerts.append(full[5])
            else:
                self.alerts = "all"

        # populate days in forecast for user
        if full[6] is not None and int(full[6]) < 6:
            self.forecast_days = int(full[6])
        elif int(full[6]) > 5:
            self.forecast_days = 5
        else:
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
        # below cursor connection is to pull the human-readable city from the location table
        cur = conn.cursor()
        cur.execute("SELECT name FROM Locations WHERE id = :id",{"id": fData.location})
        try:
            locName = cur.fetchone()[0]
        except:
            locName = fData.location
        cur.close()

        d = 0
        for daytime in fData.parsed_forecast:
            UTCdt = datetime.datetime.utcfromtimestamp(daytime).replace(tzinfo=pytz.utc)
            forecastDayTime = UTCdt.astimezone(self.tz)
            forecastDay = forecastDayTime.strftime("%Y-%m-%d")
            forecastTime = forecastDayTime.strftime("%H:%M")
            if forecastTime < self.hours["Start"] or forecastTime > self.hours["End"]:
                continue
            else:
                if forecastDay not in self.forecast:

                    # below checks to see how many days are in the forecast and ends if it's surpassed user's preference
                    # since it would be foolish to send an email with an alert for a day they don't want to know about yet
                    d += 1
                    if d > self.forecast_days:
                        break

                    else:
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
                        # below checks for freezing temps
                        if fData.parsed_forecast[daytime]["Low"] < self.freezingThresh and self.freezing == False:
                            self.freezing = True

                    if fData.parsed_forecast[daytime]["High"] > self.forecast[forecastDay][locName]["High"]:
                        self.forecast[forecastDay][locName]["High"] = fData.parsed_forecast[daytime]["High"]

                    if fData.parsed_forecast[daytime]["CondCode"] != self.forecast[forecastDay][locName]["CondCode"][condCodeLast][1]:
                        self.forecast[forecastDay][locName]["CondCode"].append((forecastTime, fData.parsed_forecast[daytime]["CondCode"]))

                        # below checks for extreme weather, rain, and snow
                        if fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllExtreme:
                            self.extreme = True
                        elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.AllRain:
                            self.rain = True
                        elif fData.parsed_forecast[daytime]["CondCode"] in possibleConditions.Snow:
                            self.snow = True

                    if fData.parsed_forecast[daytime]["Cond"] != self.forecast[forecastDay][locName]["Cond"][condLast][1]:
                        self.forecast[forecastDay][locName]["Cond"].append((forecastTime, fData.parsed_forecast[daytime]["Cond"]))
                    if fData.parsed_forecast[daytime]["Conditions"] != self.forecast[forecastDay][locName]["Conditions"][condDescLast][1]:
                        self.forecast[forecastDay][locName]["Conditions"].append((forecastTime, fData.parsed_forecast[daytime]["Conditions"]))


    def composeEmail(self):
        self.email_body = ""
        for d in self.forecast:
            self.email_body = self.email_body + d + "\r\n"
            for l in self.forecast[d]:
                self.email_body = self.email_body + "==" + l + "==\r\n"
                for item in self.forecast[d][l]:
                    if item == "CondCode" or item == "Cond":
                        continue
                    elif type(self.forecast[d][l][item]) is list:
                        self.email_body = self.email_body + "  " + item + ":\r\n"
                        for i in range(len(self.forecast[d][l][item])):
                            self.email_body = self.email_body + "   - " + str(self.forecast[d][l][item][i]) + "\r\n"
                    else:
                        self.email_body = self.email_body + "  " + item + ": " + str(self.forecast[d][l][item]) + "\r\n"
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
                cur.execute("INSERT INTO ForecastData (location, last_update, forecast) VALUES (:loc, :update, :fore)", {"loc": self.location, "update": self.today, "fore": str(self.forecast)})
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
