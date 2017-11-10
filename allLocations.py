import sqlite3


conn = sqlite3.connect("data.sqlite3")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS Locations")
cur.execute("""CREATE TABLE Locations (
                id INTEGER PRIMARY KEY NOT NULL,
                name VARCHAR(50) NOT NULL,
                lat VARCHAR(15),
                lon VARCHAR(15),
                state VARCHAR(25),
                country VARCHAR(10))""")


fhand = open("city_list.txt")
locations = fhand.readlines()
print(fhand)
for line in locations:
    print(line)
    l = line.strip()
    loc = l.split(",")
    print(loc)
    cur.execute("""INSERT OR IGNORE INTO Locations (id, name, lat, lon, country)
                    VALUES (:id,:name,:lat,:lon,:country)""",
                    {"id": loc[0], "name": loc[1], "lat": loc[2], "lon": loc[3], "country": loc[4]})
    conn.commit()


conn.close()