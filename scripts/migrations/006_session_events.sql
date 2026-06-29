-- HESTIA Database Schema v6.0 - Migration 006
-- Feature: Tabla session_events para trazabilidad de eventos de sesión.
-- Requerida por PersistenceLayer (CURRENT_VERSION = 6).

PRAGMA user_version = 6;

CREATE TABLE IF NOT EXISTS session_events (
    event_id    INTEGER PRIMARY KEY,
    student_id  INTEGER NOT NULL,
    event_type  TEXT NOT NULL,      -- e.g. 'session_start', 'session_end', 'mastery'
    skill_id    INTEGER,            -- NULL si el evento es global a la sesión
    timestamp   INTEGER NOT NULL,   -- Unix timestamp (segundos)
    metadata    TEXT                -- JSON opcional con datos extras
);

CREATE INDEX IF NOT EXISTS idx_events_student ON session_events(student_id, timestamp);
