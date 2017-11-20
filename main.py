import sqlite3
from classes import reports
from classes import email

conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()


cur.execute("SELECT id FROM Users")
for u in cur.fetchall():
    x = reports.Person(u[0])
    for l in x.locations:
        y = reports.Forecast(l)
        y.checkForecastLocal()
        y.readForecast()
        x.updateForecast(y)
    x.composeEmail()

cur.execute("SELECT id FROM EmailArchive WHERE status = 'pending'")
for e in cur.fetchall():
    x = email.Email(e[0])
    x.send()


conn.close()