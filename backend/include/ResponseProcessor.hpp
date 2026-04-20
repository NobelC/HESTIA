#pragma once
#include "BKTEngine.hpp"
#include "MABEngine.hpp"
#include "SessionManager.hpp"
#include "PersistenceLayer.hpp"
#include "ZoneBlender.hpp"
#include "SkillGraph.hpp"
#include "SRSQueue.hpp"

namespace hestia::core {

struct ResponseResult {
    mab::METHOD next_method;
    zone::Zone next_zone;
    double current_pL;
    bool was_anomalous;   // true si el tiempo fue filtrado por SessionManager
    bool valid_skill;     // false si skill_id no existe en el grafo
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
    void startSession(bkt::SkillState& state);
    void endSession(bkt::SkillState& state);

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
};

} // namespace hestia::core
