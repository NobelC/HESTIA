import sqlite3
from datetime import datetime, timedelta

class SRSQueue:
    def __init__(self, db_path="hestia_demo.db"):
        self.db_path = str(db_path)

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def schedule_next(self, id_user, skill_id, interval_days=1):
        with self.conectar() as conn:
            due_date = datetime.now() + timedelta(days=interval_days)
            conn.execute("""
                INSERT INTO srs_queue (id_user, skill_id, due_date, interval_days, last_reviewed)
                VALUES (?, ?, ?, ?, ?)
            """, (id_user, skill_id, due_date.isoformat(), interval_days, datetime.now().isoformat()))
            conn.commit()

    def get_due_skills(self, id_user):
        with self.conectar() as conn:
            hoy = datetime.now().isoformat()
            rows = conn.execute("""
                SELECT skill_id, due_date, interval_days
                FROM srs_queue
                WHERE id_user = ? AND due_date <= ?
            """, (id_user, hoy)).fetchall()
            return rows

    def mark_reviewed(self, id_user, skill_id, was_correct):
        self.schedule_next(id_user, skill_id, 2 if was_correct else 1)
