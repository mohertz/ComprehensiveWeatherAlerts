import sqlite3


conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()


# If you only want to replace one of these tables, remove or comment out the tables you want to keep.
cur.execute("DROP TABLE IF EXISTS Users")
cur.execute("DROP TABLE IF EXISTS ForecastData")
cur.execute("DROP TABLE IF EXISTS EmailArchive")
cur.execute("""CREATE TABLE Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_to VARCHAR(125) NOT NULL UNIQUE,
                email_type VARCHAR(10),
                locations VARCHAR(25) NOT NULL,
                time VARCHAR(15),
                alerts VARCHAR(125),
                forecast_days TINY INT,
                tz VARCHAR(25),
                last_update VARCHAR(25))""")
cur.execute("""CREATE TABLE ForecastData (
                location VARCHAR(15) PRIMARY KEY UNIQUE,
                forecast TEXT,
                last_update VARCHAR(25))""")
cur.execute("""CREATE TABLE EmailArchive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient INTEGER NOT NULL,
                subj TEXT,
                body TEXT,
                created VARCHAR(25),
                status VARCHAR(25))""")


conn.commit()
conn.close()