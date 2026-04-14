#include "PersistenceLayer.hpp"
#include <ctime>

namespace hestia::persistence {

std::unique_ptr<PersistenceLayer> PersistenceLayer::create(const std::string& db_path) {
    sqlite3* db;
    if (sqlite3_open_v2(db_path.c_str(), &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nullptr) != SQLITE_OK)
        return nullptr;

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
    sqlite3_close(m_db);
}

void PersistenceLayer::resetAllStatements() noexcept {
    sqlite3_clear_bindings(m_upsert_bkt); sqlite3_reset(m_upsert_bkt);
    sqlite3_clear_bindings(m_upsert_mab); sqlite3_reset(m_upsert_mab);
    sqlite3_clear_bindings(m_insert_log); sqlite3_reset(m_insert_log);
    sqlite3_clear_bindings(m_select_bkt); sqlite3_reset(m_select_bkt);
    sqlite3_clear_bindings(m_select_mab); sqlite3_reset(m_select_mab);
}

PersistenceResult PersistenceLayer::checkSchemaVersion() noexcept {
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(m_db, "PRAGMA user_version;", -1, &stmt, nullptr);
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        int ver = sqlite3_column_int(stmt, 0);
        sqlite3_finalize(stmt);
        if (ver != CURRENT_VERSION) return {StorageError::SCHEMA_MISMATCH, "DB version mismatch"};
        return {StorageError::OK, ""};
    }
    sqlite3_finalize(stmt);
    return {StorageError::READ_FAILURE, "Could not read PRAGMA user_version"};
}

PersistenceResult PersistenceLayer::prepareStatements() noexcept {
    // UPSERT Completo para consistencia pedagógica
    const char* q_bkt = 
        "INSERT INTO skill_state VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(student_id, skill_id) DO UPDATE SET "
        "p_learn_operative=excluded.p_learn_operative, p_learn_theorical=excluded.p_learn_theorical, "
        "p_transition=excluded.p_transition, p_slip=excluded.p_slip, p_guess=excluded.p_guess, "
        "p_forget=excluded.p_forget, avg_response_time=excluded.avg_response_time, "
        "last_practice_time=excluded.last_practice_time;";
        
    const char* q_mab = "INSERT INTO method_state VALUES (?,?,?,?,?) ON CONFLICT(student_id, skill_id, method_id) DO UPDATE SET attempts=excluded.attempts, successes=excluded.successes;";
    const char* q_log = "INSERT INTO response_log (student_id, skill_id, method_id, timestamp, is_correct, response_ms) VALUES (?,?,?,?,?,?);";
    const char* q_sbkt = "SELECT * FROM skill_state WHERE student_id = ? AND skill_id = ?;";
    const char* q_smab = "SELECT method_id, attempts, successes FROM method_state WHERE student_id = ? AND skill_id = ?;";

    if (sqlite3_prepare_v2(m_db, q_bkt, -1, &m_upsert_bkt, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail BKT"};
    if (sqlite3_prepare_v2(m_db, q_mab, -1, &m_upsert_mab, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail MAB"};
    if (sqlite3_prepare_v2(m_db, q_log, -1, &m_insert_log, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail Log"};
    if (sqlite3_prepare_v2(m_db, q_sbkt, -1, &m_select_bkt, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail SelBKT"};
    if (sqlite3_prepare_v2(m_db, q_smab, -1, &m_select_mab, nullptr) != SQLITE_OK) return {StorageError::CONNECTION_ERROR, "Stmt Fail SelMAB"};

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
        
        // Saneamiento estricto en el trust boundary
        s.validationProbabilityRanges(); 
        s.is_initialized = true;
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

    if (sqlite3_step(m_upsert_bkt) != SQLITE_DONE || sqlite3_step(m_upsert_mab) != SQLITE_DONE || sqlite3_step(m_insert_log) != SQLITE_DONE) {
        sqlite3_exec(m_db, "ROLLBACK;", nullptr, nullptr, nullptr);
        resetAllStatements(); // Limpieza estricta tras fallo
        return {StorageError::WRITE_FAILURE, "Transaction failed. Rolled back."};
    }

    sqlite3_exec(m_db, "COMMIT;", nullptr, nullptr, nullptr);
    resetAllStatements(); // Limpieza para la siguiente interacción
    return {StorageError::OK, ""};
}

PersistenceResult PersistenceLayer::purgeOldLogs(int months) noexcept {
    char* err_msg = nullptr;
    std::string sql = "DELETE FROM response_log WHERE timestamp < strftime('%s', 'now', '-" + std::to_string(months) + " months');";
    
    if (sqlite3_exec(m_db, sql.c_str(), nullptr, nullptr, &err_msg) != SQLITE_OK) {
        std::string error_str = err_msg ? err_msg : "Unknown error";
        sqlite3_free(err_msg); // Cierra la fuga de memoria
        return {StorageError::WRITE_FAILURE, error_str};
    }
    
    return {StorageError::OK, ""};
}

} // namespace hestia::persistence
