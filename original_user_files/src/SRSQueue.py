import sqlite3
from datetime import datetime, timedelta


class SRSQueue:
    def __init__(self, db_path="hestia.db"):
        self.db_path = db_path

    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        return conexion
    
    def schedule_next(self, id_user, skill_id, interval_days=1):
        conexion = self.conectar()
        cursor = conexion.cursor()

        due_date = datetime.now() + timedelta(days=interval_days)

        cursor.execute("INSERT INTO srs_queue (id_user,skill_id,due_date,interval_days,last_reviewed) VALUES (?, ?, ?, ?, ?)", (id_user,skill_id,due_date.isoformat(),interval_days,datetime.now().isoformat()))

        conexion.commit()
        conexion.close()
    
    def get_due_skills(self, id_user):
        conexion = self.conectar()
        cursor = conexion.cursor()

        hoy = datetime.now().isoformat()

        cursor.execute("SELECT skill_id, due_date, interval_days FROM srs_queue WHERE id_user = ? AND due_date <= ?", (id_user, hoy))

        skills = cursor.fetchall()

        conexion.close()

        return skills
    
    def mark_reviewed(self, id_user, skill_id, was_correct):
        if was_correct:
            nuevo_intervalo = 2
        else:
            nuevo_intervalo = 1

        self.schedule_next(id_user, skill_id, nuevo_intervalo)