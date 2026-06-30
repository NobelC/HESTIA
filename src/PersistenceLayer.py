import sqlite3
from pathlib import Path

class PersistenceLayer:
    def __init__(self, db_path="hestia_demo.db", schema_path=None):
        self.db_path = str(db_path)
        self.schema_path = schema_path
        self.init_db()

    def conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        schema = """
        CREATE TABLE IF NOT EXISTS user_profile (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            profile_type TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS skill_state (
            id_skill_state INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            skill_id TEXT NOT NULL,
            p_l_operativo REAL DEFAULT 0.0,
            p_l_teorico REAL DEFAULT 0.0,
            p_t REAL DEFAULT 0.0,
            p_g REAL DEFAULT 0.0,
            p_s REAL DEFAULT 0.0,
            avg_time_ms REAL DEFAULT 0.0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS method_state (
            id_method_state INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            method_id TEXT NOT NULL,
            q_value REAL DEFAULT 0.0,
            times_used INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS response_log (
            id_response INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            exercise_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            method_id TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            response_time_ms INTEGER NOT NULL,
            p_l_after REAL DEFAULT 0.0,
            selected_method TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS srs_queue (
            id_srs INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            skill_id TEXT NOT NULL,
            due_date TEXT NOT NULL,
            interval_days INTEGER DEFAULT 1,
            last_reviewed TEXT
        );

        CREATE TABLE IF NOT EXISTS motivation (
            id_motivation INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            stars INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.conectar() as conn:
            conn.executescript(schema)
            conn.commit()

    def crear_usuario(self, name, profile_type):
        with self.conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO user_profile (name, profile_type) VALUES (?, ?)",
                (name, profile_type)
            )
            conn.commit()
            return cur.lastrowid

    def load_user(self, id_user):
        with self.conectar() as conn:
            row = conn.execute(
                "SELECT id_user, name, profile_type, created_at FROM user_profile WHERE id_user = ?",
                (id_user,)
            ).fetchone()
            return dict(row) if row else None

    def save_skill_state(self, id_user, skill_id, p_l_operativo, p_l_teorico, p_t, p_g, p_s, avg_time_ms):
        with self.conectar() as conn:
            conn.execute("""
                INSERT INTO skill_state
                (id_user, skill_id, p_l_operativo, p_l_teorico, p_t, p_g, p_s, avg_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_user, skill_id, p_l_operativo, p_l_teorico, p_t, p_g, p_s, avg_time_ms))
            conn.commit()

    def load_skill_state(self, id_user, skill_id):
        with self.conectar() as conn:
            row = conn.execute("""
                SELECT * FROM skill_state
                WHERE id_user = ? AND skill_id = ?
                ORDER BY id_skill_state DESC
                LIMIT 1
            """, (id_user, skill_id)).fetchone()
            return dict(row) if row else None

    def load_all_latest_skill_states(self, id_user):
        with self.conectar() as conn:
            rows = conn.execute("""
                SELECT s1.* FROM skill_state s1
                INNER JOIN (
                    SELECT skill_id, MAX(id_skill_state) AS max_id
                    FROM skill_state
                    WHERE id_user = ?
                    GROUP BY skill_id
                ) s2 ON s1.skill_id = s2.skill_id AND s1.id_skill_state = s2.max_id
            """, (id_user,)).fetchall()
            return {row["skill_id"]: dict(row) for row in rows}

    def save_method_state(self, id_user, method_id, q_value, times_used):
        with self.conectar() as conn:
            conn.execute("""
                INSERT INTO method_state (id_user, method_id, q_value, times_used)
                VALUES (?, ?, ?, ?)
            """, (id_user, method_id, q_value, times_used))
            conn.commit()

    def load_method_state(self, id_user, method_id):
        with self.conectar() as conn:
            row = conn.execute("""
                SELECT * FROM method_state
                WHERE id_user = ? AND method_id = ?
                ORDER BY id_method_state DESC
                LIMIT 1
            """, (id_user, method_id)).fetchone()
            return dict(row) if row else None

    def load_all_latest_method_states(self, id_user):
        with self.conectar() as conn:
            rows = conn.execute("""
                SELECT m1.* FROM method_state m1
                INNER JOIN (
                    SELECT method_id, MAX(id_method_state) AS max_id
                    FROM method_state
                    WHERE id_user = ?
                    GROUP BY method_id
                ) m2 ON m1.method_id = m2.method_id AND m1.id_method_state = m2.max_id
            """, (id_user,)).fetchall()
            return {row["method_id"]: dict(row) for row in rows}

    def log_response(self, id_user, exercise_id, skill_id, method_id, is_correct, response_time_ms, p_l_after=0.0, selected_method=None):
        with self.conectar() as conn:
            conn.execute("""
                INSERT INTO response_log
                (id_user, exercise_id, skill_id, method_id, is_correct, response_time_ms, p_l_after, selected_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_user, exercise_id, skill_id, method_id, is_correct, response_time_ms, p_l_after, selected_method or method_id))
            conn.commit()

    def get_summary(self, id_user):
        with self.conectar() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(is_correct) AS correct,
                    AVG(response_time_ms) AS avg_time,
                    AVG(p_l_after) AS avg_mastery
                FROM response_log
                WHERE id_user = ?
            """, (id_user,)).fetchone()
            total = row["total"] or 0
            correct = row["correct"] or 0
            return {
                "total": total,
                "correct": correct,
                "accuracy": (correct / total) if total else 0.0,
                "avg_time": row["avg_time"] or 0.0,
                "avg_mastery": row["avg_mastery"] or 0.0,
            }

    def export_response_log(self, id_user):
        with self.conectar() as conn:
            rows = conn.execute("""
                SELECT exercise_id, skill_id, method_id, is_correct, response_time_ms, p_l_after, selected_method, created_at
                FROM response_log
                WHERE id_user = ?
                ORDER BY id_response ASC
            """, (id_user,)).fetchall()
            return [dict(row) for row in rows]
