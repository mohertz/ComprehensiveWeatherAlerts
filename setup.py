import sqlite3


conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()


cur.execute("DROP TABLE IF EXISTS Users")
cur.execute("DROP TABLE IF EXISTS ForecastData")
cur.execute("""CREATE TABLE Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_to VARCHAR(125) NOT NULL UNIQUE,
                email_type VARCHAR(10),
                locations VARCHAR(25) NOT NULL,
                time VARCHAR(15),
                alerts VARCHAR(125),
                forecast_days TINY INT,
                tz VARCHAR(25))""")
cur.execute("""CREATE TABLE ForecastData (
                location INTEGER PRIMARY KEY UNIQUE,
                forecast TEXT,
                last_update VARCHAR(25))""")



conn.commit()
conn.close()