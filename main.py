import sqlite3
from classes import reports

conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()


cur.execute("SELECT id FROM Users")
for u in cur.fetchall():
    x = reports.Person(u)
    x.populatePerson()
    for l in x.locations:
        y = reports.Forecast(l)
        y.checkForecastLocal()
        y.readForecast()
        x.updateForecast(y)
    x.dumpForecast()


conn.close()