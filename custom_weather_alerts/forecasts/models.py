import urllib.request, urllib.parse, urllib.error
import json
import datetime
import pytz
import smtplib

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from email.mime.text import MIMEText

from custom_weather_alerts.users.models import User
from . import possibleConditions


class ForecastProfile(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
    nickname = models.CharField(_('Forecast Nickname'), max_length=25)
    locations = models.CharField(_('Forecast Locations'), max_length=125)
    timezone = models.CharField(_('Forecast Timezone'),max_length=25)
    start_time = models.PositiveSmallIntegerField(_('Forecast Start Time'))
    end_time = models.PositiveSmallIntegerField(_('Forecast End Time'))
    alerts = models.CharField(_('Forecast Alerts'), max_length=125)
    days_in_forecast = models.PositiveSmallIntegerField(_('Number of Days in Forecast'))
    last_updated = models.CharField(_('Last Time Forecast Was Run'),max_length=25, blank=True)


    def CheckForecast(self):
        if self.start_time < 2:
            upper = 0
        else:
            upper = self.start_time - 2
        if self.end_time > 21:
            lower = 23
        else:
            lower = self.end_time + 2
        alerts_d = {"E": False, "F": False, "R": False, "S": False}

        locs = self.locations.split()
        custom_forecast = {}

        for l in locs:
            try:           # Zip codes are not integers, but can be converted into them, as can all city IDs.
                int(l)     # Future updates will validate this data in the form.
            except:
                if len(locs) <= 1:
                    custom_forecast = False   # make note of this somewhere
                else:
                    continue   # Ignoring invalid entries if there is more than one entry
            try:
                lf = ForecastData.objects.get(location=l)
            except ObjectDoesNotExist:
                lf = ForecastData.objects.create(location=l)
                lf.save()
            lf.CheckCurrent()

            # Now process l.forecast_clean into custom_forecast
            fjs = json.loads(lf.forecast_clean)
            day_counter = 0
            for daytime in fjs:
                condadd = False
                UTCdt = datetime.datetime.utcfromtimestamp(int(daytime)).replace(tzinfo=pytz.utc)
                forecastDayTime = UTCdt.astimezone(pytz.timezone(self.timezone))
                forecastDay = forecastDayTime.strftime("%Y-%m-%d")
                forecastTime = forecastDayTime.strftime("%H:%M")
                fH = int(forecastDayTime.strftime("%H"))

                # checking that forecast time is within user's preference
                if fH < upper or fH > lower:
                    continue

                else:   # Only processing data within time preference

                    # This is a new day
                    if forecastDay not in custom_forecast:
                        day_counter += 1

                        if day_counter > self.days_in_forecast:
                            break

                        # This day isn't over the user's threshold
                        else:
                            custom_forecast[forecastDay] = {}


                    # This is an existing day
                    else:
                        pass

                    # This is a new location
                    if lf.location not in custom_forecast[forecastDay]:
                        custom_forecast[forecastDay][lf.location] = {"Conditions": []}

                        # Only add lows if user wants them
                        if 'L' in self.alerts or 'A' in self.alerts:
                            custom_forecast[forecastDay][lf.location]["AM Low"] = 999
                            custom_forecast[forecastDay][lf.location]["PM Low"] = 999
                            if fH < 12:
                                custom_forecast[forecastDay][lf.location]["AM Low"] = fjs[daytime]["Low"]
                            else:
                                custom_forecast[forecastDay][lf.location]["PM Low"] = fjs[daytime]["Low"]

                            # Only add highs  if user wants them
                        if 'H' in self.alerts or 'A' in self.alerts:
                            custom_forecast[forecastDay][lf.location]["High"] = fjs[daytime]["High"]

                    # this is an existing location
                    else:
                        # Only compare lows if they'll be there
                        if 'L' in self.alerts or 'A' in self.alerts:
                            if fH < 12 and fjs[daytime]["Low"] < custom_forecast[forecastDay][lf.location]["AM Low"]:
                                custom_forecast[forecastDay][lf.location]["AM Low"] = fjs[daytime]["Low"]
                            elif fH > 12 and fjs[daytime]["Low"] < custom_forecast[forecastDay][lf.location]["PM Low"]:
                                custom_forecast[forecastDay][lf.location]["PM Low"] = fjs[daytime]["Low"]

                        #Only compare highs if they'll be there
                        if 'H' in self.alerts or 'A' in self.alerts:
                            if fjs[daytime]["High"] > custom_forecast[forecastDay][lf.location]["High"]:
                                custom_forecast[forecastDay][lf.location]["High"] = fjs[daytime]["High"]

                    # Check for freezing temps
                    if ('F' in self.alerts or 'A' in self.alerts) and fjs[daytime]["Low"] < 33:
                        alerts_d["F"] = True

                        # If there are no lows in the report, look for a "Freezing" value
                        # If the freezing value does not exist or is higher than the current low, insert the time and temp
                        if ("AM Low" not in custom_forecast[forecastDay][lf.location] or
                            "PM Low" not in custom_forecast[forecastDay][lf.location]) \
                            and ("Freezing" not in custom_forecast[forecastDay][lf.location] or
                                 fjs[daytime]["Low"] < custom_forecast[forecastDay][lf.location]["Freezing"][1]):
                            custom_forecast[forecastDay][lf.location]["Freezing"] = (forecastTime,fjs[daytime]["Low"])

                    # Check for extreme weather
                    if fjs[daytime]["CondCode"] in possibleConditions.AllExtreme:
                        alerts_d["E"] = True
                        condadd = True

                    # Check for rain, snow, full forecast prefs
                    if ('R' in self.alerts or 'A' in self.alerts) and fjs[daytime]["CondCode"] in possibleConditions.AllRain:
                        alerts_d["R"] = True
                        condadd = True
                    elif ('S' in self.alerts or 'A' in self.alerts) and fjs[daytime]["CondCode"] in possibleConditions.Snow:
                        alerts_d["S"] = True
                        condadd = True
                    elif 'A' in self.alerts:
                        condadd = True
                    else:
                        pass

                    condsI = len(custom_forecast[forecastDay][lf.location]["Conditions"]) - 1
                    # avoid an index out of range error
                    if condsI < 0:
                        last_condition = None
                    else:
                        last_condition = custom_forecast[forecastDay][lf.location]["Conditions"][condsI][1]

                    # we're not going to add duplicate condition descriptions
                    if condadd == True and fjs[daytime]["Conditions"] != last_condition:
                        custom_forecast[forecastDay][lf.location]["Conditions"].append((forecastTime,fjs[daytime]["Conditions"]))

        # Some extra cleanup so that it doesn't have to be cleaned when composing the email
        clean_custom_forecast = {}
        for day in custom_forecast:
            day_d = {}
            for l in custom_forecast[day]:
                # Remove blank forecasts

                if (len(custom_forecast[day][l]) == 1 and len(custom_forecast[day][l]["Conditions"]) == 0) or len(custom_forecast[day][l]) < 1:
                    continue
                # Remove empty conditions lists
                if len(custom_forecast[day][l]["Conditions"]) == 0:
                    custom_forecast[day][l].pop("Conditions", None)

                if "AM Low" in custom_forecast[day][l] and custom_forecast[day][l]["AM Low"] == 999:
                    custom_forecast[day][l].pop("AM Low", None)
                if "PM Low" in custom_forecast[day][l] and custom_forecast[day][l]["PM Low"] == 999:
                    custom_forecast[day][l].pop("PM Low", None)

                if len(custom_forecast[day][l]) > 0:
                    day_d[l] = custom_forecast[day][l]
                else:
                    continue

            # Remove blank forecasts
            if len(day_d) > 0:
                clean_custom_forecast[day] = day_d
            else:
                continue

        alerts_t = []
        for a in alerts_d:
            if alerts_d[a] == True:
                alerts_t.append(a)

        # I should put a check to make sure there is something to send before running the compose function
        self.last_updated = datetime.datetime.now().strftime("%Y-%m-%d")
        self.save()
        if len(clean_custom_forecast) > 0:
            self.ComposeEmail(clean_custom_forecast,alerts_t)
        else:
            return


    def ComposeEmail(self,forecast,alerts_t):
        email_subj = "Upcoming Forecast"
        if 'E' in alerts_t:
            email_subj = "EXTREME WEATHER ALERT"
        for a in alerts_t:
            if a == 'S':
                email_subj = email_subj + " - SNOW"
            elif a == 'R':
                email_subj = email_subj + " - RAIN"
            elif a == 'F':
                email_subj = email_subj + " - FREEZING TEMPS"
            else:
                continue

        email_body = ""
        email_footer = "\r\n\r\nIf it looks like data is missing, it's because we removed the blank parts of your forecast.\r\n\r\nYou are receiving this email because you signed up for a custom forecast from Mo's Custom Forecasts and www.mohertz.com.\r\nReply to this email with 'UNSUBSCRIBE' to unsubscribe. (May take a few days to take effect.)"
        for day in forecast:
            email_body = email_body + day + "\r\n"
            for l in forecast[day]:
                email_body = email_body + "==" + l + "==\r\n"
                if "AM Low" in forecast[day][l]:
                    email_body = email_body + "  AM Low: " + str(forecast[day][l]["AM Low"]) + "\r\n"
                if "PM Low" in forecast[day][l]:
                    email_body = email_body + "  PM Low: " + str(forecast[day][l]["PM Low"]) + "\r\n"
                if "High" in forecast[day][l]:
                    email_body = email_body + "  High: " + str(forecast[day][l]["High"]) + "\r\n"
                if "Freezing" in forecast[day][l]:
                    email_body = email_body + "  Freezing Temps: " + str(forecast[day][l]["Freezing"][0]) + " - " + str(forecast[day][l]["Freezing"][1]) + "\r\n"
                if "Conditions" in forecast[day][l]:
                    email_body = email_body + "  Conditions:\r\n"
                    for c in range(len(forecast[day][l]["Conditions"])):
                        email_body = email_body + "  - " + str(forecast[day][l]["Conditions"][c][0]) + ": " + forecast[day][l]["Conditions"][c][1] + "\r\n"
            email_body = email_body + "\r\n"

        email_body = email_body + email_footer
        email = ForecastEmail.objects.create(profile=self, recipient=self.userid, subj=email_subj, body=email_body, status='PENDING')
        email.save()
        email.SendEmail()


class ForecastData(models.Model):
    location = models.CharField(primary_key=True, max_length=15)
    forecast_raw = models.TextField(blank=True)
    forecast_clean = models.TextField(blank=True)
    last_updated = models.CharField(max_length=25, blank=True)

    def CheckCurrent(self):
        if self.last_updated < datetime.datetime.now().strftime("%Y-%m-%d"):
            self.GetForecast()
        else:
            pass   # If the forecast is current, we don't need to do anything.

    def GetForecast(self):
        if len(self.location) == 5:
            url_loc = "zip=" + self.location
        else:
            url_loc = "id=" + self.location
        url = settings.OWM_SERVICE_URL + url_loc + settings.OWM_URL_END
        uh = urllib.request.urlopen(url)
        data = uh.read().decode()

        try:
            js = json.loads(data)
        except:
            js = None

        if js is not None:
            self.forecast_raw = str(data)

        self.save()
        self.CleanForecast()

    def CleanForecast(self):
        forecast = json.loads(self.forecast_raw)
        new_clean = {}
        for item in forecast["list"]:
            forecast_daytime = item["dt"]
            projLow = item["main"]["temp_min"]
            projHigh = item["main"]["temp_max"]
            projCondCode = item["weather"][0]["id"]
            projCondDesc = item["weather"][0]["description"]
            new_clean[forecast_daytime] = {"Low": projLow, "High": projHigh,"CondCode": projCondCode, "Conditions": projCondDesc}
        self.forecast_clean = json.dumps(new_clean)
        self.last_updated = datetime.datetime.now().strftime("%Y-%m-%d")
        self.save()


class ForecastEmail(models.Model):
    profile = models.ForeignKey(ForecastProfile, on_delete=models.SET_NULL, null=True)
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subj = models.CharField(max_length=125)
    body = models.TextField()
    dt_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)

    def SendEmail(self):
        rec_obj = self.recipient
        EMAIL_TO = str(rec_obj.email)
        msg = MIMEText(self.body)
        msg["Subject"] = self.subj
        msg["From"] = settings.DEFAULT_FROM_EMAIL
        msg["To"] = EMAIL_TO
        debuglevel = True
        try:
            mail = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            mail.set_debuglevel(debuglevel)
            mail.starttls()
            mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            mail.sendmail(settings.DEFAULT_FROM_EMAIL, EMAIL_TO, msg.as_string())
            mail.quit()
            self.status = "sent "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except smtplib.SMTPException as err:
            self.status = err
        self.save()
