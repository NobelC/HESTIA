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
    // Tabla de selección de zona según P(L) operativo:
    // P(L) < 0.60         → 80% zona baja
    // 0.60 ≤ P(L) < 0.90  → 20% zona baja
    // P(L) ≥ 0.90         → 10% zona baja
    if (pL < 0.60) return 0.80;
    if (pL < 0.90) return 0.20;
    return 0.10; // P(L) >= 0.90
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
    if (srs_queue) {
        auto due = srs_queue->getDueSkills();
        if (!due.empty()) {
            return {Zone::LOW, due.front()}; // Use LOW zone for review (or REVIEW if defined)
        }
    }
    
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
