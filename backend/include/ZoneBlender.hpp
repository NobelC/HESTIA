#pragma once
#include "BKTEngine.hpp"
#include "SkillGraph.hpp"
#include "SRSQueue.hpp"
#include <random>
#include <cstdint>

namespace hestia::zone {

enum class Zone : uint8_t { LOW = 0, CURRENT = 1 };

struct ExerciseSelection {
    Zone zone;
    int skill_id;
};

class ZoneBlender {
public:
    /// Constructor. seed=0 usa std::random_device para producción;
    /// cualquier otro seed permite reproducibilidad en tests.
    explicit ZoneBlender(uint64_t seed = 0);

    /// Selecciona la zona basándose en P(L) operativo del estado
    [[nodiscard]] Zone selectZone(const bkt::SkillState& state);

    [[nodiscard]] ExerciseSelection selectExercise(
        int skill_id,
        const bkt::SkillState& state,
        const graph::SkillGraph& skill_graph,
        srs::SRSQueue* srs_queue = nullptr);

private:
    std::mt19937_64 m_rng;

    /// Retorna la probabilidad de elegir zona baja según P(L)
    [[nodiscard]] static double getLowZoneProbability(double pL) noexcept;
};

} // namespace hestia::zone
