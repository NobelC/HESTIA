#include "../include/ZoneBlender.hpp"

namespace hestia::zone {

ZoneBlender::ZoneBlender(uint64_t seed) {
    if (seed == 0) {
        std::random_device rd;
        m_rng.seed(rd());
    } else {
        m_rng.seed(seed);
    }
}

double ZoneBlender::getLowZoneProbability(double pL) noexcept {
    // Sigmoidea invertida: alta probabilidad LOW cuando pL es bajo
    // P(LOW) = 0.85 / (1 + e^(10*(pL - 0.45))) + 0.05
    double sigmoid = 1.0 / (1.0 + std::exp(10.0 * (pL - 0.45)));
    return 0.05 + 0.80 * sigmoid;  // rango [0.05, 0.85]
}

Zone ZoneBlender::selectZone(const bkt::SkillState& state) {
    double prob_low = getLowZoneProbability(state.m_pLearn_operative);
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    double roll = dist(m_rng);
    return (roll < prob_low) ? Zone::LOW : Zone::CURRENT;
}

ExerciseSelection ZoneBlender::selectExercise(
    int skill_id,
    const bkt::SkillState& state,
    const graph::SkillGraph& skill_graph,
    srs::SRSQueue* srs_queue)
{
    // Prioridad 1: SRS vencido → REVIEW obligatorio
    if (srs_queue) {
        auto due = srs_queue->getDueSkills();
        if (!due.empty()) {
            // Elegir el primero de la cola (podría ordenarse por urgencia)
            return {Zone::REVIEW, due.front()};
        }
    }
    
    // Prioridad 2: Si P(L) < 0.30, forzar LOW (prereqs)
    if (state.m_pLearn_operative < 0.30) {
        auto prereqs = skill_graph.getPrerequisites(skill_id);
        if (!prereqs.empty()) {
            std::uniform_int_distribution<size_t> dist(0, prereqs.size() - 1);
            return {Zone::LOW, prereqs[dist(m_rng)]};
        }
    }

    // Prioridad 3: selección probabilística normal
    Zone zone = selectZone(state);
    
    if (zone == Zone::LOW) {
        auto prereqs = skill_graph.getPrerequisites(skill_id);
        if (!prereqs.empty()) {
            // Pick a random prerequisite
            std::uniform_int_distribution<size_t> dist(0, prereqs.size() - 1);
            return {Zone::LOW, prereqs[dist(m_rng)]};
        }
    }
    
    return {zone, skill_id};
}

} // namespace hestia::zone
