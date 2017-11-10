# program to manually input/update new user

import sqlite3
import pytz


conn = sqlite3.connect("data.sqlite3")


def newUserSetup():
    user_email = input("Email address(es):    ")
    email_type = input("Email type (SMS/Email):    ")
    locations = input("Location(s):    ")
    timeSt = input("Start time:    ")
    timeEnd = input("End time (in 24hr format):    ")
    alerts = input("Alerts:    ")
    while True:
        try:
            forecast_days = int(input("Number of days in forecast (1 to 5):    "))
            break
        except:
            print("Must be integer.")
    tz = input("Timezone:    ")
    time = timeSt + "," + timeEnd
    if not tz in pytz.all_timezones:
        tz = None

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


newUserSetup()

conn.close()