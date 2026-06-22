#pragma once
#include "BKTEngine.hpp"
#include "MABEngine.hpp"
#include "SessionManager.hpp"
#include "PersistenceLayer.hpp"
#include "ZoneBlender.hpp"
#include "SkillGraph.hpp"
#include "SRSQueue.hpp"

namespace hestia::core {

struct SessionReport {
    std::vector<int> practiced_skills;
    int total_attempts;
    double hit_rate;
    mab::METHOD most_used_method;
    std::vector<std::pair<int, double>> pl_evolution; // skill_id -> delta PL
    double total_session_time_minutes;
};

struct ResponseResult {
    int next_skill_id;
    mab::METHOD next_method;
    zone::Zone next_zone;
    double current_pL;
    double current_pL_theorical;
    bool was_anomalous;   // true si el tiempo fue filtrado por SessionManager
    bool valid_skill;     // false si skill_id no existe en el grafo
    bool newly_mastered;  // true si P(L) teórico dominó al operativo
};

struct ValidationResult {
    bool valid;
    std::string reason;
    double adjusted_response_ms; // tiempo corregido si fue anómalo
};

struct SessionContext {
    int student_id{-1};
    int64_t start_timestamp{0};
    std::vector<ResponseResult> history;
    double cumulative_correct{0};
    double cumulative_total{0};
    
    [[nodiscard]] double getSessionHitRate() const noexcept {
        if (cumulative_total == 0) return 0.0;
        return cumulative_correct / cumulative_total;
    }
};

class ResponseProcessor {
public:
    ResponseProcessor(
        bkt::BKTEngine& bkt,
        mab::MABEngine& mab,
        bkt::SessionManager& session,
        persistence::PersistenceLayer& storage,
        zone::ZoneBlender& blender,
        graph::SkillGraph& skill_graph,
        srs::SRSQueue& srs_queue,
        double lambda = 0.5);

    /// Procesa una respuesta del usuario. Ciclo completo:
    /// validar skill → aplicar olvido → validar tiempo → actualizar BKT →
    /// actualizar MAB → programar SRS → persistir → retornar siguiente
    [[nodiscard]] ResponseResult processResponse(
        int student_id, int skill_id,
        mab::METHOD used_method,
        bool correct, double response_ms);

    /// Gestión del ciclo de sesión (delega a SessionManager)
    void startSession(int student_id, bkt::SkillState& state);
    void endSession(bkt::SkillState& state);
    [[nodiscard]] SessionReport generateSessionReport(int student_id, int64_t session_start_ts) const;

    /// Consulta skills cuyo tiempo de repaso ya venció
    [[nodiscard]] std::vector<int> getDueSkills() const;

    /// Consulta skills desbloqueadas dado un conjunto de skills dominadas
    [[nodiscard]] std::vector<int> getUnlockedSkills(const std::vector<int>& mastered_ids) const;

private:
    bkt::BKTEngine& m_bkt;
    mab::MABEngine& m_mab;
    bkt::SessionManager& m_session;
    persistence::PersistenceLayer& m_storage;
    zone::ZoneBlender& m_blender;
    graph::SkillGraph& m_skill_graph;
    srs::SRSQueue& m_srs_queue;
    double m_lambda;

    SessionContext m_current_session;
    bool m_force_low_zone{false};

    [[nodiscard]] ValidationResult validateInput(int skill_id, double response_ms) const noexcept;
};

} // namespace hestia::core
