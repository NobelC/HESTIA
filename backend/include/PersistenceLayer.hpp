#pragma once
#include <sqlite3.h>
#include <string>
#include <memory>
#include <optional>
#include <array>

#include "BKTEngine.hpp"
#include "MABEngine.hpp"

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

class PersistenceLayer {
public:
    static constexpr int CURRENT_VERSION = 1;
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
};

} // namespace hestia::persistence
