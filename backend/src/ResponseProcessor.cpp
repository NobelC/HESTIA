#include "../include/ResponseProcessor.hpp"

namespace hestia::core {

ResponseProcessor::ResponseProcessor(
    bkt::BKTEngine& bkt,
    mab::MABEngine& mab,
    bkt::SessionManager& session,
    persistence::PersistenceLayer& storage,
    zone::ZoneBlender& blender,
    graph::SkillGraph& skill_graph,
    srs::SRSQueue& srs_queue,
    double lambda)
    : m_bkt(bkt)
    , m_mab(mab)
    , m_session(session)
    , m_storage(storage)
    , m_blender(blender)
    , m_skill_graph(skill_graph)
    , m_srs_queue(srs_queue)
    , m_lambda(lambda)
{}

ResponseResult ResponseProcessor::processResponse(
    int student_id, int skill_id,
    mab::METHOD used_method,
    bool correct, double response_ms)
{
    // 0. Validar que el skill_id existe en el grafo
    if (!m_skill_graph.exists(skill_id)) {
        return {mab::METHOD::VISUAL, zone::Zone::CURRENT, 0.0, false, false};
    }

    // 1. Cargar estado desde persistencia (o usar default si no existe)
    auto loaded = m_storage.loadSkillState(student_id, skill_id);
    bkt::SkillState state = loaded.value_or(bkt::SkillState{});

    // 2. Aplicar factor de olvido si han pasado >= 48 horas sin practicar
    m_bkt.applyForgetFactor(state);

    // 3. Verificar si el tiempo de respuesta es anómalo
    bool anomalous = m_session.isResponseTimeAnomalous(response_ms);

    // 4. Solo actualizar modelos si el tiempo NO es anómalo
    if (!anomalous) {
        m_bkt.updateKnowledge(state, correct, response_ms, m_lambda);
        m_mab.updateMethod(used_method, correct);
    }

    // 5. Actualizar cola SRS con el resultado
    m_srs_queue.markResult(skill_id, correct);

    // 6. Seleccionar siguiente ejercicio (zona + método)
    auto selection = m_blender.selectExercise(skill_id, state, m_mab);

    // 7. Persistir el estado actualizado
    auto method_states = m_storage.loadMethodStates(student_id, skill_id);
    auto method_idx = static_cast<size_t>(used_method);
    [[maybe_unused]] auto save_result = m_storage.saveInteraction(
        student_id, skill_id, state, used_method, correct,
        static_cast<int>(response_ms),
        method_states[method_idx].count_attempts,
        method_states[method_idx].successes);

    // 8. Retornar resultado
    return {
        selection.method,
        selection.zone,
        state.m_pLearn_operative,
        anomalous,
        true
    };
}

void ResponseProcessor::startSession(bkt::SkillState& state) {
    m_session.startSession(state);
}

void ResponseProcessor::endSession(bkt::SkillState& state) {
    m_session.endSession(state);
}

std::vector<int> ResponseProcessor::getDueSkills() const {
    return m_srs_queue.getDueSkills();
}

std::vector<int> ResponseProcessor::getUnlockedSkills(const std::vector<int>& mastered_ids) const {
    return m_skill_graph.getUnlockedSkills(mastered_ids);
}

} // namespace hestia::core
