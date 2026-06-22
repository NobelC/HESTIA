#pragma once
#include <sqlite3.h>
#include <string>
#include <memory>
#include <optional>
#include <array>
#include <vector>

#include "BKTEngine.hpp"
#include "MABEngine.hpp"
#include "SRSQueue.hpp"

namespace hestia::persistence {

enum class StorageError { 
    OK, 
    CONNECTION_ERROR, 
    WRITE_FAILURE, 
    READ_FAILURE, 
    SCHEMA_MISMATCH 
};

struct [[nodiscard]] PersistenceResult {
    StorageError error;
    std::string message;
    [[nodiscard]] bool success() const noexcept { return error == StorageError::OK; }
};

struct LogEntry {
    int skill_id;
    mab::METHOD method;
    int64_t timestamp;
    bool is_correct;
    double p_learn;
};

// Analytics: real progression for dashboard
struct SkillProgress {
    int skill_id;
    double pL_start;
    double pL_current;
    double pL_delta;
    int total_sessions;
    double avg_hit_rate;
    bool is_mastered;
};

class PersistenceLayer {
public:
    static constexpr int CURRENT_VERSION = 6; // v6: session_events, plearn added, indexes, students
    static constexpr size_t METHOD_COUNT = 5;

    static std::unique_ptr<PersistenceLayer> create(const std::string& db_path);
    ~PersistenceLayer();

    PersistenceLayer(const PersistenceLayer&) = delete;
    PersistenceLayer& operator=(const PersistenceLayer&) = delete;

    [[nodiscard]] PersistenceResult saveInteraction(
        int student_id, int skill_id, const bkt::SkillState& b_st,
        mab::METHOD m, bool correct, int ms, uint32_t m_att, uint32_t m_succ) noexcept;

    [[nodiscard]] std::optional<bkt::SkillState> loadSkillState(int student_id, int skill_id) noexcept;
    
    [[nodiscard]] std::array<mab::MethodState, METHOD_COUNT> loadMethodStates(int student_id, int skill_id) noexcept;

    // Consultas Analíticas (Feature 17)
    [[nodiscard]] double getHitRate(int student_id, int skill_id) noexcept;
    [[nodiscard]] std::vector<std::pair<int64_t, double>> getPLHistory(int student_id, int skill_id) noexcept;
    [[nodiscard]] mab::METHOD getBestMethod(int student_id, int skill_id) noexcept;
    [[nodiscard]] double getAverageSessionDuration(int student_id) noexcept;
    [[nodiscard]] std::vector<LogEntry> getSessionLogs(int student_id, int64_t session_start_ts) noexcept;
    
    // Feature: Progress query
    [[nodiscard]] std::vector<SkillProgress> getStudentProgress(int student_id) noexcept;

    // Bug fix #6: persistencia del estado SRS entre sesiones
    [[nodiscard]] PersistenceResult saveSrsState(int student_id, const srs::SRSQueue& queue) noexcept;
    void loadSrsState(int student_id, srs::SRSQueue& queue) noexcept;
    
    [[nodiscard]] PersistenceResult purgeOldLogs(int months_retention) noexcept;

private:
    explicit PersistenceLayer(sqlite3* db_ptr);
    PersistenceResult prepareStatements() noexcept;
    PersistenceResult checkSchemaVersion() noexcept;
    void resetAllStatements() noexcept;

    sqlite3* m_db;
    sqlite3_stmt* m_upsert_bkt = nullptr;
    sqlite3_stmt* m_upsert_mab = nullptr;
    sqlite3_stmt* m_insert_log = nullptr;
    sqlite3_stmt* m_select_bkt = nullptr;
    sqlite3_stmt* m_select_mab = nullptr;
    // Bug fix #6: statements para persistir cola SRS
    sqlite3_stmt* m_upsert_srs = nullptr;
    sqlite3_stmt* m_select_srs = nullptr;
    
    // Events
    sqlite3_stmt* m_insert_event = nullptr;

    // Analytics statements
    sqlite3_stmt* m_select_hitrate = nullptr;
    sqlite3_stmt* m_select_pl_history = nullptr;
    sqlite3_stmt* m_select_session_durations = nullptr;
    sqlite3_stmt* m_select_session_logs = nullptr;
    sqlite3_stmt* m_select_student_progress = nullptr;
};

} // namespace hestia::persistence
