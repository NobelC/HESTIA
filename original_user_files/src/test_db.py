import sqlite3

conexion = sqlite3.connect("hestia.db")
cursor = conexion.cursor()

with open("database/hestia.sql", "r", encoding="utf-8") as archivo:
    script_sql = archivo.read()

cursor.executescript(script_sql)

conexion.commit()
conexion.close()

print("Base de datos HESTIA creada correctamente.")

conexion = sqlite3.connect("hestia.db")
cursor = conexion.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = cursor.fetchall()

print("Tablas creadas:")
for tabla in tablas:
    print("-", tabla[0])

conexion.close()