#include "../include/ResponseProcessor.hpp"
#include <map>
#include <algorithm>

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
        return {skill_id, mab::METHOD::VISUAL, zone::Zone::CURRENT, 0.0, false, false, false};
    }

    // 1. Cargar estado desde persistencia (o usar default si no existe)
    auto loaded = m_storage.loadSkillState(student_id, skill_id);
    bkt::SkillState state = loaded.value_or(bkt::SkillState{});

    auto mab_states = m_storage.loadMethodStates(student_id, skill_id);
    m_mab.loadFrom(mab_states);

    // 2. Aplicar factor de olvido si han pasado >= 48 horas sin practicar
    m_bkt.applyForgetFactor(state);

    // 3. Verificar si el tiempo de respuesta es anómalo
    bool anomalous = m_session.isResponseTimeAnomalous(response_ms);

    // 4. Solo actualizar modelos si el tiempo NO es anómalo
    if (!anomalous) {
        m_session.applyTransitionDecay(state, m_lambda);
        m_bkt.updateKnowledge(state, correct, response_ms);
        m_mab.updateMethod(used_method, correct);
    }

    // 5. Actualizar cola SRS con el resultado
    m_srs_queue.markResult(skill_id, correct);

    // 6. Persistir el estado actualizado (antes de recargar el MAB para la siguiente skill)
    const auto& ms = m_mab.getMethodState(used_method);
    [[maybe_unused]] auto save_result = m_storage.saveInteraction(
        student_id, skill_id, state, used_method, correct,
        static_cast<int>(response_ms),
        ms.count_attempts,
        ms.successes);

    // 7. Seleccionar siguiente ejercicio (zona y skill_id)
    auto selection = m_blender.selectExercise(skill_id, state, m_skill_graph, &m_srs_queue);

    // 8. Cargar el MAB para la *nueva* skill y elegir método
    auto next_mab_states = m_storage.loadMethodStates(student_id, selection.skill_id);
    m_mab.loadFrom(next_mab_states);
    mab::METHOD next_method = m_mab.selectMethod();

    // 9. Retornar resultado
    return {
        selection.skill_id,
        next_method,
        selection.zone,
        state.m_pLearn_operative,
        anomalous,
        true,
        state.is_mastered
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

SessionReport ResponseProcessor::generateSessionReport(int student_id, int64_t session_start_ts) const {
    SessionReport report;
    report.total_attempts = 0;
    report.hit_rate = 0.0;
    report.most_used_method = mab::METHOD::VISUAL;
    report.total_session_time_minutes = 0.0;

    auto logs = m_storage.getSessionLogs(student_id, session_start_ts);
    if (logs.empty()) return report;

    report.total_attempts = logs.size();
    
    int successes = 0;
    std::map<int, std::pair<double, double>> pl_map; // skill_id -> {start_pl, end_pl}
    std::map<mab::METHOD, int> method_counts;
    
    for (const auto& log : logs) {
        if (log.is_correct) successes++;
        
        if (std::find(report.practiced_skills.begin(), report.practiced_skills.end(), log.skill_id) == report.practiced_skills.end()) {
            report.practiced_skills.push_back(log.skill_id);
            pl_map[log.skill_id] = {log.p_learn, log.p_learn};
        } else {
            pl_map[log.skill_id].second = log.p_learn;
        }
        
        method_counts[log.method]++;
    }
    
    report.hit_rate = static_cast<double>(successes) / report.total_attempts;
    
    int max_count = -1;
    for (const auto& [method, count] : method_counts) {
        if (count > max_count) {
            max_count = count;
            report.most_used_method = method;
        }
    }
    
    for (const auto& [skill_id, pls] : pl_map) {
        report.pl_evolution.emplace_back(skill_id, pls.second - pls.first);
    }
    
    int64_t session_end_ts = logs.back().timestamp;
    report.total_session_time_minutes = (session_end_ts - session_start_ts) / 60.0;
    
    return report;
}

}
