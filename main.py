import sqlite3
import logging
import datetime
from classes import reports
from classes import email

logging.basicConfig(filename="weatherlogs.log",format="%(asctime)s | %(filename)s , %(lineno)d| %(levelname)s: %(message)s",level=logging.DEBUG)
conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()

today = datetime.datetime.now().strftime("%Y-%m-%d")
moreusers = True
moreemails = True

def getUsers():
    global moreusers, today
    cur.execute("SELECT id FROM Users WHERE last_update IS NOT :t LIMIT 20",{"t": today})
    users = cur.fetchall()
    if users is None or len(users) < 1:
        logging.info("No more users to update.")
        moreusers = False
    else:
        for u in users:
            x = reports.Person(u[0])
            for l in x.locations:
                y = reports.Forecast(l)
                y.checkForecastLocal()
                y.readForecast()
                x.updateForecast(y)
            x.composeEmail()



def getEmails():
    global moreemails
    cur.execute("SELECT id FROM EmailArchive WHERE status = 'pending' LIMIT 20")
    emails = cur.fetchall()
    if emails is None or len(emails) < 1:
        logging.info("No more emails to send.")
        moreemails = False
    else:
        for e in emails:
            x = email.Email(e[0])
            x.send()


while moreusers == True or moreemails == True:
    getUsers()
    getEmails()

conn.close()