#include <catch2/catch_test_macros.hpp>
#include "../include/ZoneBlender.hpp"

using namespace hestia::zone;
using namespace hestia::bkt;
using namespace hestia::graph;

TEST_CASE("ZoneBlender: Selección de zona según P(L)", "[zone]") {

    // Seed fijo para reproducibilidad
    ZoneBlender blender(42);

    SECTION("10% fáciles con P(L) >= 0.90") {
        SkillState state;
        state.m_pLearn_operative = 0.95;

        int low_count = 0;
        constexpr int N = 1000;

        // Recreamos el blender con seed fijo para cada batch
        ZoneBlender test_blender(12345);

        for (int i = 0; i < N; ++i) {
            Zone z = test_blender.selectZone(state);
            if (z == Zone::LOW) low_count++;
        }

        // Esperamos ~10% en zona baja (con margen estadístico razonable: 5%-18%)
        double ratio = static_cast<double>(low_count) / N;
        REQUIRE(ratio > 0.05);
        REQUIRE(ratio < 0.18);
    }

    SECTION("80% zona baja con P(L) < 0.60") {
        SkillState state;
        state.m_pLearn_operative = 0.45; // Antes caía en 60%, ahora en 80%

        int low_count = 0;
        constexpr int N = 1000;

        ZoneBlender test_blender(54321);

        for (int i = 0; i < N; ++i) {
            Zone z = test_blender.selectZone(state);
            if (z == Zone::LOW) low_count++;
        }

        // Esperamos ~80% (con margen: 73%-87%)
        double ratio = static_cast<double>(low_count) / N;
        REQUIRE(ratio > 0.73);
        REQUIRE(ratio < 0.87);
    }

    SECTION("20% zona baja con 0.60 <= P(L) < 0.90") {
        SkillState state;
        state.m_pLearn_operative = 0.75;

        int low_count = 0;
        constexpr int N = 1000;

        ZoneBlender test_blender(77777);

        for (int i = 0; i < N; ++i) {
            Zone z = test_blender.selectZone(state);
            if (z == Zone::LOW) low_count++;
        }

        // Esperamos ~20% (con margen: 13%-27%)
        double ratio = static_cast<double>(low_count) / N;
        REQUIRE(ratio > 0.13);
        REQUIRE(ratio < 0.27);
    }

    SECTION("Combina BKT + Graph: selectExercise retorna resultado válido") {
        SkillState state;
        state.m_pLearn_operative = 0.50;

        SkillGraph graph; // Graph vacío
        ZoneBlender test_blender(11111);

        auto selection = test_blender.selectExercise(5, state, graph);

        // Verificar que el resultado tiene valores válidos
        REQUIRE(selection.skill_id == 5);
        REQUIRE((selection.zone == Zone::LOW || selection.zone == Zone::CURRENT));
    }
}
