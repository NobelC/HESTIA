#include "PersistenceLayer.hpp"
#include <ctime>
#include <cmath>

namespace hestia::persistence {

std::unique_ptr<PersistenceLayer> PersistenceLayer::create(const std::string& db_path) {
    sqlite3* db;
    if (sqlite3_open_v2(db_path.c_str(), &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nullptr) != SQLITE_OK)
        return nullptr;

    // ─── WAL pragmas for robustness and analytics ───
    sqlite3_exec(db, "PRAGMA journal_mode=WAL;", nullptr, nullptr, nullptr);
    sqlite3_exec(db, "PRAGMA synchronous=NORMAL;", nullptr, nullptr, nullptr);
    sqlite3_exec(db, "PRAGMA cache_size=-64000;", nullptr, nullptr, nullptr); // 64MB cache
    sqlite3_exec(db, "PRAGMA temp_store=MEMORY;", nullptr, nullptr, nullptr);
    sqlite3_exec(db, "PRAGMA mmap_size=268435456;", nullptr, nullptr, nullptr); // 256MB mmap

    auto instance = std::unique_ptr<PersistenceLayer>(new PersistenceLayer(db));
    if (!instance->checkSchemaVersion().success() || !instance->prepareStatements().success())
        return nullptr;

    return instance;
}

PersistenceLayer::PersistenceLayer(sqlite3* db_ptr) : m_db(db_ptr) {}

PersistenceLayer::~PersistenceLayer() {
    sqlite3_finalize(m_upsert_bkt);
    sqlite3_finalize(m_upsert_mab);
    sqlite3_finalize(m_insert_log);
    sqlite3_finalize(m_select_bkt);
    sqlite3_finalize(m_select_mab);
    sqlite3_finalize(m_upsert_srs);
    sqlite3_finalize(m_select_srs);
    sqlite3_finalize(m_insert_event);
    sqlite3_finalize(m_select_hitrate);
    sqlite3_finalize(m_select_pl_history);
    sqlite3_finalize(m_select_session_durations);
    sqlite3_finalize(m_select_session_logs);
    sqlite3_finalize(m_select_student_progress);
    sqlite3_close(m_db);
}

void PersistenceLayer::resetAllStatements() noexcept {
    sqlite3_clear_bindings(m_upsert_bkt); sqlite3_reset(m_upsert_bkt);
    sqlite3_clear_bindings(m_upsert_mab); sqlite3_reset(m_upsert_mab);
    sqlite3_clear_bindings(m_insert_log); sqlite3_reset(m_insert_log);
    sqlite3_clear_bindings(m_select_bkt); sqlite3_reset(m_select_bkt);
    sqlite3_clear_bindings(m_select_mab); sqlite3_reset(m_select_mab);
    if (m_upsert_srs) { sqlite3_clear_bindings(m_upsert_srs); sqlite3_reset(m_upsert_srs); }
    if (m_select_srs) { sqlite3_clear_bindings(m_select_srs); sqlite3_reset(m_select_srs); }
    if (m_insert_event) { sqlite3_clear_bindings(m_insert_event); sqlite3_reset(m_insert_event); }
    if (m_select_hitrate) { sqlite3_clear_bindings(m_select_hitrate); sqlite3_reset(m_select_hitrate); }
    if (m_select_pl_history) { sqlite3_clear_bindings(m_select_pl_history); sqlite3_reset(m_select_pl_history); }
    if (m_select_session_durations) { sqlite3_clear_bindings(m_select_session_durations); sqlite3_reset(m_select_session_durations); }
    if (m_select_session_logs) { sqlite3_clear_bindings(m_select_session_logs); sqlite3_reset(m_select_session_logs); }
    if (m_select_student_progress) { sqlite3_clear_bindings(m_select_student_progress); sqlite3_reset(m_select_student_progress); }
}

PersistenceResult PersistenceLayer::checkSchemaVersion() noexcept {
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(m_db, "PRAGMA user_version;", -1, &stmt, nullptr);
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        int ver = sqlite3_column_int(stmt, 0);
        sqlite3_finalize(stmt);
        // Accept any previous versions; we handle gracefully if unmigrated
        if (ver < 1 || ver > CURRENT_VERSION)
            return {StorageError::SCHEMA_MISMATCH, "DB version mismatch"};
        return {StorageError::OK, ""};
    }
    sqlite3_finalize(stmt);
    return {StorageError::READ_FAILURE, "Could not read PRAGMA user_version"};
}

PersistenceResult PersistenceLayer::prepareStatements() noexcept {
    const char* q_bkt = 
        "INSERT INTO skill_state VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(student_id, skill_id) DO UPDATE SET "
        "p_learn_operative=excluded.p_learn_operative, p_learn_theorical=excluded.p_learn_theorical, "
        "p_transition=excluded.p_transition, p_slip=excluded.p_slip, p_guess=excluded.p_guess, "
        "p_forget=excluded.p_forget, avg_response_time=excluded.avg_response_time, "
        "last_practice_time=excluded.last_practice_time;";
        
    const char* q_mab = "INSERT INTO method_state VALUES (?,?,?,?,?) ON CONFLICT(student_id, skill_id, method_id) DO UPDATE SET attempts=excluded.attempts, successes=excluded.successes;";
    const char* q_log = "INSERT INTO response_log (student_id, skill_id, method_id, timestamp, is_correct, response_ms, p_learn) VALUES (?,?,?,?,?,?,?);";
    const char* q_sbkt = "SELECT * FROM skill_state WHERE student_id = ? AND skill_id = ?;";
    const char* q_smab = "SELECT method_id, attempts, successes FROM method_state WHERE student_id = ? AND skill_id = ?;";

    if (sqlite3_prepare_v2(m_db, q_bkt,  -1, &m_upsert_bkt, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail BKT"};
    if (sqlite3_prepare_v2(m_db, q_mab,  -1, &m_upsert_mab, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail MAB"};
    if (sqlite3_prepare_v2(m_db, q_log,  -1, &m_insert_log, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail Log"};
    if (sqlite3_prepare_v2(m_db, q_sbkt, -1, &m_select_bkt, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail SelBKT"};
    if (sqlite3_prepare_v2(m_db, q_smab, -1, &m_select_mab, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail SelMAB"};

    const char* q_usrs =
        "INSERT INTO srs_state (student_id, skill_id, correct_streak, next_review) VALUES (?,?,?,?) "
        "ON CONFLICT(student_id, skill_id) DO UPDATE SET "
        "correct_streak=excluded.correct_streak, next_review=excluded.next_review;";
    const char* q_ssrs = "SELECT skill_id, correct_streak, next_review FROM srs_state WHERE student_id = ?;";
    sqlite3_prepare_v2(m_db, q_usrs, -1, &m_upsert_srs, nullptr); // fallo silencioso si tabla ausente
    sqlite3_prepare_v2(m_db, q_ssrs, -1, &m_select_srs, nullptr);

    // Schema v6
    const char* q_evt = "INSERT INTO session_events (student_id, event_type, skill_id, timestamp, metadata) VALUES (?,?,?,?,?);";
    sqlite3_prepare_v2(m_db, q_evt, -1, &m_insert_event, nullptr); // silent fail if unmigrated

    const char* q_hr = "SELECT AVG(is_correct) FROM response_log WHERE student_id = ? AND skill_id = ?;";
    const char* q_pl = "SELECT timestamp, p_learn FROM response_log WHERE student_id = ? AND skill_id = ? ORDER BY timestamp ASC;";
    const char* q_sd = "SELECT timestamp FROM response_log WHERE student_id = ? ORDER BY timestamp ASC;";
    const char* q_sl = "SELECT skill_id, method_id, timestamp, is_correct, p_learn FROM response_log WHERE student_id = ? AND timestamp >= ? ORDER BY timestamp ASC;";
    
    // Progress query groups log data and joins with current state
    const char* q_prog = R"(
        SELECT 
            s.skill_id,
            (SELECT p_learn FROM response_log WHERE student_id = s.student_id AND skill_id = s.skill_id ORDER BY timestamp ASC LIMIT 1) as pL_start,
            s.p_learn_operative as pL_current,
            (SELECT COUNT(DISTINCT timestamp / 86400) FROM response_log WHERE student_id = s.student_id AND skill_id = s.skill_id) as total_sessions,
            (SELECT AVG(is_correct) FROM response_log WHERE student_id = s.student_id AND skill_id = s.skill_id) as avg_hit_rate
        FROM skill_state s
        WHERE s.student_id = ?
    )";

    sqlite3_prepare_v2(m_db, q_hr, -1, &m_select_hitrate, nullptr);
    sqlite3_prepare_v2(m_db, q_pl, -1, &m_select_pl_history, nullptr);
    sqlite3_prepare_v2(m_db, q_sd, -1, &m_select_session_durations, nullptr);
    sqlite3_prepare_v2(m_db, q_sl, -1, &m_select_session_logs, nullptr);
    sqlite3_prepare_v2(m_db, q_prog, -1, &m_select_student_progress, nullptr);

    return {StorageError::OK, ""};
}

std::optional<bkt::SkillState> PersistenceLayer::loadSkillState(int student_id, int skill_id) noexcept {
    sqlite3_bind_int(m_select_bkt, 1, student_id);
    sqlite3_bind_int(m_select_bkt, 2, skill_id);

    std::optional<bkt::SkillState> state;
    if (sqlite3_step(m_select_bkt) == SQLITE_ROW) {
        bkt::SkillState s;
        s.m_pLearn_operative = sqlite3_column_double(m_select_bkt, 2);
        s.m_pLearn_theorical = sqlite3_column_double(m_select_bkt, 3);
        s.m_pTransition = sqlite3_column_double(m_select_bkt, 4);
        s.m_pSlip = sqlite3_column_double(m_select_bkt, 5);
        s.m_pGuess = sqlite3_column_double(m_select_bkt, 6);
        s.m_pForget = sqlite3_column_double(m_select_bkt, 7);
        s.avg_response_time_ms = sqlite3_column_double(m_select_bkt, 8);
        s.last_practice_time = std::chrono::system_clock::from_time_t(sqlite3_column_int64(m_select_bkt, 9));
        
        s.validationProbabilityRanges(); 
        
        if (std::isnan(s.avg_response_time_ms) || s.avg_response_time_ms < 0) {
            s.avg_response_time_ms = 0.0;
        }

        s.is_initialized = true;
        if (s.total_attempts == 0) {
            s.total_attempts = 1;
        }
        
        // Restore mastery flag based on current P(L)
        if (s.m_pLearn_operative >= bkt::MASTERY_CONSOLIDATION_THRESHOLD ||
            (s.m_pLearn_operative >= 0.85 && s.m_pLearn_operative == s.m_pLearn_theorical)) {
            s.is_mastered = true;
        }
        
        state = s;
    }
    
    sqlite3_clear_bindings(m_select_bkt);
    sqlite3_reset(m_select_bkt);
    return state;
}

std::array<mab::MethodState, PersistenceLayer::METHOD_COUNT> PersistenceLayer::loadMethodStates(int sid, int skid) noexcept {
    std::array<mab::MethodState, METHOD_COUNT> states{}; 
    
    sqlite3_bind_int(m_select_mab, 1, sid);
    sqlite3_bind_int(m_select_mab, 2, skid);

    while (sqlite3_step(m_select_mab) == SQLITE_ROW) {
        int mid = sqlite3_column_int(m_select_mab, 0);
        if (mid >= 0 && mid < static_cast<int>(METHOD_COUNT)) {
            states[mid].count_attempts = sqlite3_column_int(m_select_mab, 1);
            states[mid].successes = sqlite3_column_int(m_select_mab, 2);
        }
    }
    
    sqlite3_clear_bindings(m_select_mab);
    sqlite3_reset(m_select_mab);
    return states;
}

PersistenceResult PersistenceLayer::saveInteraction(int sid, int skid, const bkt::SkillState& b, mab::METHOD m, bool corr, int ms, uint32_t att, uint32_t succ) noexcept {
    sqlite3_exec(m_db, "BEGIN TRANSACTION;", nullptr, nullptr, nullptr);
    
    sqlite3_bind_int(m_upsert_bkt, 1, sid); sqlite3_bind_int(m_upsert_bkt, 2, skid);
    sqlite3_bind_double(m_upsert_bkt, 3, b.m_pLearn_operative); sqlite3_bind_double(m_upsert_bkt, 4, b.m_pLearn_theorical);
    sqlite3_bind_double(m_upsert_bkt, 5, b.m_pTransition); sqlite3_bind_double(m_upsert_bkt, 6, b.m_pSlip);
    sqlite3_bind_double(m_upsert_bkt, 7, b.m_pGuess); sqlite3_bind_double(m_upsert_bkt, 8, b.m_pForget);
    sqlite3_bind_double(m_upsert_bkt, 9, b.avg_response_time_ms);
    sqlite3_bind_int64(m_upsert_bkt, 10, std::chrono::system_clock::to_time_t(b.last_practice_time));

    sqlite3_bind_int(m_upsert_mab, 1, sid); sqlite3_bind_int(m_upsert_mab, 2, skid);
    sqlite3_bind_int(m_upsert_mab, 3, static_cast<int>(m));
    sqlite3_bind_int(m_upsert_mab, 4, att); sqlite3_bind_int(m_upsert_mab, 5, succ);

    sqlite3_bind_int(m_insert_log, 1, sid); sqlite3_bind_int(m_insert_log, 2, skid);
    sqlite3_bind_int(m_insert_log, 3, static_cast<int>(m));
    sqlite3_bind_int64(m_insert_log, 4, std::time(nullptr));
    sqlite3_bind_int(m_insert_log, 5, corr ? 1 : 0); sqlite3_bind_int(m_insert_log, 6, ms);
    sqlite3_bind_double(m_insert_log, 7, b.m_pLearn_operative);

    if (sqlite3_step(m_upsert_bkt) != SQLITE_DONE || sqlite3_step(m_upsert_mab) != SQLITE_DONE || sqlite3_step(m_insert_log) != SQLITE_DONE) {
        sqlite3_exec(m_db, "ROLLBACK;", nullptr, nullptr, nullptr);
        resetAllStatements();
        return {StorageError::WRITE_FAILURE, "Transaction failed. Rolled back."};
    }

    sqlite3_exec(m_db, "COMMIT;", nullptr, nullptr, nullptr);
    resetAllStatements();
    return {StorageError::OK, ""};
}

PersistenceResult PersistenceLayer::purgeOldLogs(int months) noexcept {
    sqlite3_stmt* stmt = nullptr;
    const char* sql = "DELETE FROM response_log WHERE timestamp < strftime('%s', 'now', '-' || CAST(? AS TEXT) || ' months');";
    
    if (sqlite3_prepare_v2(m_db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        return {StorageError::WRITE_FAILURE, sqlite3_errmsg(m_db)};
    }
    
    sqlite3_bind_int(stmt, 1, months);
    
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::string error_str = sqlite3_errmsg(m_db);
        sqlite3_finalize(stmt);
        return {StorageError::WRITE_FAILURE, error_str};
    }
    
    sqlite3_finalize(stmt);
    return {StorageError::OK, ""};
}

PersistenceResult PersistenceLayer::saveSrsState(int student_id, const srs::SRSQueue& queue) noexcept {
    if (!m_upsert_srs) {
        return {StorageError::CONNECTION_ERROR, "SRS statement not prepared (table missing?)"};
    }

    const auto& entries = queue.getEntries();
    if (entries.empty()) return {StorageError::OK, ""};

    sqlite3_exec(m_db, "BEGIN TRANSACTION;", nullptr, nullptr, nullptr);

    for (const auto& [skill_id, entry] : entries) {
        int64_t ts = std::chrono::system_clock::to_time_t(entry.next_review);
        sqlite3_bind_int(m_upsert_srs,  1, student_id);
        sqlite3_bind_int(m_upsert_srs,  2, skill_id);
        sqlite3_bind_int(m_upsert_srs,  3, entry.correct_streak);
        sqlite3_bind_int64(m_upsert_srs, 4, ts);

        if (sqlite3_step(m_upsert_srs) != SQLITE_DONE) {
            sqlite3_exec(m_db, "ROLLBACK;", nullptr, nullptr, nullptr);
            sqlite3_clear_bindings(m_upsert_srs);
            sqlite3_reset(m_upsert_srs);
            return {StorageError::WRITE_FAILURE, "SRS upsert failed. Rolled back."};
        }
        sqlite3_clear_bindings(m_upsert_srs);
        sqlite3_reset(m_upsert_srs);
    }

    sqlite3_exec(m_db, "COMMIT;", nullptr, nullptr, nullptr);
    return {StorageError::OK, ""};
}

void PersistenceLayer::loadSrsState(int student_id, srs::SRSQueue& queue) noexcept {
    if (!m_select_srs) return;

    sqlite3_bind_int(m_select_srs, 1, student_id);

    while (sqlite3_step(m_select_srs) == SQLITE_ROW) {
        srs::SRSEntry entry;
        entry.skill_id      = sqlite3_column_int(m_select_srs,   0);
        entry.correct_streak = sqlite3_column_int(m_select_srs,  1);
        int64_t ts          = sqlite3_column_int64(m_select_srs,  2);
        entry.next_review   = std::chrono::system_clock::from_time_t(static_cast<std::time_t>(ts));
        queue.scheduleEntry(entry);
    }

    sqlite3_clear_bindings(m_select_srs);
    sqlite3_reset(m_select_srs);
}

double PersistenceLayer::getHitRate(int student_id, int skill_id) noexcept {
    if (!m_select_hitrate) return 0.0;
    sqlite3_bind_int(m_select_hitrate, 1, student_id);
    sqlite3_bind_int(m_select_hitrate, 2, skill_id);
    
    double rate = 0.0;
    if (sqlite3_step(m_select_hitrate) == SQLITE_ROW) {
        if (sqlite3_column_type(m_select_hitrate, 0) != SQLITE_NULL) {
            rate = sqlite3_column_double(m_select_hitrate, 0);
        }
    }
    sqlite3_clear_bindings(m_select_hitrate);
    sqlite3_reset(m_select_hitrate);
    return rate;
}

std::vector<std::pair<int64_t, double>> PersistenceLayer::getPLHistory(int student_id, int skill_id) noexcept {
    std::vector<std::pair<int64_t, double>> history;
    if (!m_select_pl_history) return history;
    
    sqlite3_bind_int(m_select_pl_history, 1, student_id);
    sqlite3_bind_int(m_select_pl_history, 2, skill_id);
    
    while (sqlite3_step(m_select_pl_history) == SQLITE_ROW) {
        int64_t ts = sqlite3_column_int64(m_select_pl_history, 0);
        double pl = sqlite3_column_double(m_select_pl_history, 1);
        history.emplace_back(ts, pl);
    }
    sqlite3_clear_bindings(m_select_pl_history);
    sqlite3_reset(m_select_pl_history);
    return history;
}

mab::METHOD PersistenceLayer::getBestMethod(int student_id, int skill_id) noexcept {
    auto states = loadMethodStates(student_id, skill_id);
    mab::METHOD best = mab::METHOD::VISUAL;
    double best_rate = -1.0;
    
    for (size_t i = 0; i < states.size(); ++i) {
        if (states[i].count_attempts > 0) {
            double rate = static_cast<double>(states[i].successes) / states[i].count_attempts;
            if (rate > best_rate) {
                best_rate = rate;
                best = static_cast<mab::METHOD>(i);
            }
        }
    }
    return best;
}

double PersistenceLayer::getAverageSessionDuration(int student_id) noexcept {
    if (!m_select_session_durations) return 0.0;
    
    sqlite3_bind_int(m_select_session_durations, 1, student_id);
    
    std::vector<int64_t> timestamps;
    while (sqlite3_step(m_select_session_durations) == SQLITE_ROW) {
        timestamps.push_back(sqlite3_column_int64(m_select_session_durations, 0));
    }
    sqlite3_clear_bindings(m_select_session_durations);
    sqlite3_reset(m_select_session_durations);
    
    if (timestamps.empty()) return 0.0;
    
    int num_sessions = 0;
    int64_t total_duration = 0;
    int64_t current_session_start = timestamps[0];
    int64_t current_session_end = timestamps[0];
    
    const int64_t SESSION_THRESHOLD = 30 * 60;
    
    for (size_t i = 1; i < timestamps.size(); ++i) {
        if (timestamps[i] - current_session_end > SESSION_THRESHOLD) {
            total_duration += (current_session_end - current_session_start);
            num_sessions++;
            current_session_start = timestamps[i];
        }
        current_session_end = timestamps[i];
    }
    total_duration += (current_session_end - current_session_start);
    num_sessions++;
    
    return static_cast<double>(total_duration) / num_sessions / 60.0;
}

std::vector<LogEntry> PersistenceLayer::getSessionLogs(int student_id, int64_t session_start_ts) noexcept {
    std::vector<LogEntry> logs;
    if (!m_select_session_logs) return logs;
    
    sqlite3_bind_int(m_select_session_logs, 1, student_id);
    sqlite3_bind_int64(m_select_session_logs, 2, session_start_ts);
    
    while (sqlite3_step(m_select_session_logs) == SQLITE_ROW) {
        LogEntry entry;
        entry.skill_id = sqlite3_column_int(m_select_session_logs, 0);
        entry.method = static_cast<mab::METHOD>(sqlite3_column_int(m_select_session_logs, 1));
        entry.timestamp = sqlite3_column_int64(m_select_session_logs, 2);
        entry.is_correct = sqlite3_column_int(m_select_session_logs, 3) != 0;
        entry.p_learn = sqlite3_column_double(m_select_session_logs, 4);
        logs.push_back(entry);
    }
    sqlite3_clear_bindings(m_select_session_logs);
    sqlite3_reset(m_select_session_logs);
    return logs;
}

std::vector<SkillProgress> PersistenceLayer::getStudentProgress(int student_id) noexcept {
    std::vector<SkillProgress> progress;
    if (!m_select_student_progress) return progress;
    
    sqlite3_bind_int(m_select_student_progress, 1, student_id);
    
    while (sqlite3_step(m_select_student_progress) == SQLITE_ROW) {
        SkillProgress sp;
        sp.skill_id = sqlite3_column_int(m_select_student_progress, 0);
        sp.pL_start = sqlite3_column_double(m_select_student_progress, 1);
        sp.pL_current = sqlite3_column_double(m_select_student_progress, 2);
        sp.pL_delta = sp.pL_current - sp.pL_start;
        sp.total_sessions = sqlite3_column_int(m_select_student_progress, 3);
        sp.avg_hit_rate = sqlite3_column_double(m_select_student_progress, 4);
        
        // Mark as mastered if current pL is at least the consolidation threshold
        sp.is_mastered = (sp.pL_current >= bkt::MASTERY_CONSOLIDATION_THRESHOLD);
        
        progress.push_back(sp);
    }
    sqlite3_clear_bindings(m_select_student_progress);
    sqlite3_reset(m_select_student_progress);
    return progress;
}

} // namespace hestia::persistence
