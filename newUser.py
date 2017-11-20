# program to manually input/update new user

import sqlite3
import pytz


conn = sqlite3.connect("data.sqlite3")


def newUserSetup():
    user_email = None
    while user_email = None:
        user_email = input("Email address(es):    ")

    email_type = input("Email type (SMS/Email):    ")

    locations = None
    while locations is None:
        locations = input("Location(s):    ")

    timeSt = None
    timeEnd = None
    while True:
        timeSt = input("Start time:    ")
        timeEnd = input("End time (in 24hr format):    ")
        if timeSt is not None and timeEnd is not None and timeSt < timeEnd:
            break
        elif timeSt is None or timeEnd is None:
            break
        else:
            print("Start time must be before end time.")
    if timeSt is None and timeEnd is None:
        time = None
    else:
        time = timeSt + "," + timeEnd

    alerts = input("Alerts:    ")

    while True:
        try:
            forecast_days = int(input("Number of days in forecast (1 to 5):    "))
            if forecast_days > 5:
                forecast_days = 5
            elif forecast_days < 1:
                forecast_days = 1
            else:
                pass
            break
        except:
            print("Must be integer.")

    tz = None
    while tz not in pytz.all_timezones:
        tz = input("Timezone:    ")


    cur = conn.cursor()
    cur.execute("SELECT id FROM Users WHERE email_to LIKE :email",{"email": user_email})
    if cur.fetchone() is None or len(cur.fetchone()) == 0:
        cur.execute("""INSERT INTO Users (email_to, email_type, locations, time, alerts, forecast_days, tz)
                        VALUES (:email,:type,:loc,:time,:alerts,:days,:tz)""",
                    {"email": user_email,"type": email_type, "loc": locations, "time": time, "alerts": alerts,"days": forecast_days, "tz": tz})
        conn.commit()
    else:
        user_id = cur.fetchone()
        print("User already exists.")
        upd = input("Update existing record? (Y/N)    ")
        if upd.lower() == "y" or upd.lower() == "yes":
            cur.execute("""UPDATE Users SET
                            email_to = :email,
                            email_type = :type,
                            locations = :loc, 
                            time = :time, 
                            alerts = :alerts, 
                            forecast_days = :days
                            tz = :tz
                            WHERE id = :id""",
                        {"email": user_email,"type": email_type, "loc": locations, "time": time, "alerts": alerts,"days": forecast_days, "tz": tz, "id": user_id})
        else:
            pass
        conn.commit()

    cur.close()


newUserSetup()

conn.close()