CREATE TABLE IF NOT EXISTS user_profileuser_profile (
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
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES user_profile(id_user)
);

CREATE TABLE IF NOT EXISTS method_state (
    id_method_state INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    method_id TEXT NOT NULL,
    q_value REAL DEFAULT 0.0,
    times_used INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES user_profile(id_user)
);

CREATE TABLE IF NOT EXISTS response_log (
    id_response INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    exercise_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    method_id TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES user_profile(id_user)
);

CREATE TABLE IF NOT EXISTS srs_queue (
    id_srs INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    due_date TEXT NOT NULL,
    interval_days INTEGER DEFAULT 1,
    last_reviewed TEXT,
    FOREIGN KEY (id_user) REFERENCES user_profile(id_user)
);

CREATE TABLE IF NOT EXISTS motivation (
    id_motivation INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    stars INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES user_profile(id_user)
);