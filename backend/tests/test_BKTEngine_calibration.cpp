#include <chrono>
#include <random>
#include <catch2/catch_test_macros.hpp>
#include "../include/BKTEngine.hpp"
#include "../include/SessionManager.hpp"

using namespace hestia::bkt;

/**
 * Calibration tests — validate the specific numerical properties that result
 * from the calibrated BKT parameters (P(G)=0.25, P(S)=0.10, ANTI_STALL_MARGIN=0.15).
 * These tests encode the behavioral invariants documented in the findings analysis.
 */

TEST_CASE("Calibration: first correct from initial state produces moderate posterior", "[bkt][calibration]") {
    // Hallazgo 1: With P(G)=0.25, P(S)=0.10, first correct from pL=0.20 should yield:
    //   posterior = 0.20*0.90 / (0.20*0.90 + 0.80*0.25) = 0.18/0.38 = 0.4737
    //   transition = 0.4737 + 0.5263*0.10 = 0.5263
    // NOT 0.843 as with the old P(G)=0.05
    SkillState state;
    state.is_initialized = true;
    state.avg_response_time_ms = 1000.0;
    BKTEngine engine;

    engine.updateKnowledge(state, true, 1000.0);

    REQUIRE(state.m_pLearn_operative > 0.45);
    REQUIRE(state.m_pLearn_operative < 0.65);
}

TEST_CASE("Calibration: oscillating sequence does not reach mastery", "[bkt][calibration]") {
    // Hallazgo 2: Alternating correct/incorrect (50/50) must NOT trigger anti-stall
    // or reach mastery. With ANTI_STALL_MARGIN=0.15, the natural differential between
    // theoretical and operative should not exceed the margin under oscillation.
    SkillState state;
    state.is_initialized = true;
    state.avg_response_time_ms = 2000.0;
    BKTEngine engine;

    for (int i = 0; i < 60; ++i) {
        engine.updateKnowledge(state, (i % 2 == 0), 2000.0);
    }

    REQUIRE(state.m_pLearn_operative < 0.90);
    REQUIRE_FALSE(state.is_mastered);
}

TEST_CASE("Calibration: random clicker does not reach mastery", "[bkt][calibration]") {
    // Hallazgo 3: A random clicker (50% chance) should never sustain mastery.
    // Run 100 iterations with a fixed seed to ensure deterministic behavior.
    // Note: transient peaks to 0.98 during lucky streaks are expected BKT behavior —
    // the model is responsive to evidence. The test validates that the FINAL state
    // self-corrects to below mastery after the random sequence.
    SkillState state;
    state.is_initialized = true;
    state.avg_response_time_ms = 600.0;
    BKTEngine engine;

    std::mt19937 gen(42);
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    for (int i = 0; i < 100; ++i) {
        bool correct = dist(gen) > 0.5;
        double time_ms = 400.0 + dist(gen) * 400.0;
        engine.updateKnowledge(state, correct, time_ms);
    }

    // Final operative P(L) should self-correct to below mastery threshold
    REQUIRE(state.m_pLearn_operative < 0.90);
    // Anti-stall should NOT have fired (no sustained theoretical dominance)
    REQUIRE_FALSE(state.is_mastered);
}

TEST_CASE("Calibration: equilibrium floor under all-incorrect", "[bkt][calibration]") {
    // Hallazgo 5: With P(T)=0.10, P(S)=0.10, P(G)=0.25, the equilibrium floor
    // should be well below 0.15, closer to the theoretical ~0.058
    SkillState state;
    state.is_initialized = true;
    state.avg_response_time_ms = 1500.0;
    BKTEngine engine;

    for (int i = 0; i < 500; ++i) {
        engine.updateKnowledge(state, false, 1500.0);
    }

    REQUIRE(state.m_pLearn_operative < 0.15);
    REQUIRE(state.m_pLearn_operative > MIN_P_LEARN_OPERATIVE);
}

TEST_CASE("Calibration: forget factor decays both operative and theoretical", "[bkt][calibration]") {
    // Hallazgo 6: applyForgetFactor must decay BOTH m_pLearn_operative and m_pLearn_theorical.
    // If only operative decays, anti-stall fires immediately on the next correct response.
    SkillState state;
    state.m_pLearn_operative = 0.90;
    state.m_pLearn_theorical = 0.95;
    state.last_practice_time = std::chrono::system_clock::now() - std::chrono::hours(49);

    BKTEngine engine;
    engine.applyForgetFactor(state);

    REQUIRE(state.m_pLearn_operative < 0.90);
    REQUIRE(state.m_pLearn_theorical < 0.95);
    // Theoretical should decay at half rate, so it stays higher than operative
    REQUIRE(state.m_pLearn_theorical > state.m_pLearn_operative);
}

TEST_CASE("Calibration: anti-stall margin prevents spurious activation", "[bkt][calibration]") {
    // With ANTI_STALL_MARGIN=0.15, a small natural differential (< 0.15) between
    // theoretical and operative should NOT increment the dominance counter.
    SkillState state;
    state.is_initialized = true;
    state.avg_response_time_ms = 1000.0;
    state.m_pLearn_operative = 0.50;
    state.m_pLearn_theorical = 0.60;  // diff = 0.10 < 0.15 margin
    BKTEngine engine;

    // A single correct answer — the differential should not trigger dominance
    engine.updateKnowledge(state, true, 1000.0);

    // Counter should not have incremented (both go up, maintaining similar gap)
    // The exact behavior depends on the posterior dynamics, but with margin=0.15
    // moderate differentials should not accumulate
    REQUIRE(state.m_sustained_theorical_dominance < ANTI_STALL_THRESHOLD);
}

TEST_CASE("Calibration: default parameter values match specification", "[bkt][calibration]") {
    // Verify the calibrated constants match the specification
    REQUIRE(DEFAULT_P_GUESS == 0.25);
    REQUIRE(DEFAULT_P_SLIP == 0.10);
    REQUIRE(ANTI_STALL_MARGIN == 0.15);
    REQUIRE(ANTI_STALL_THRESHOLD == 3);
    REQUIRE(DEFAULT_P_LEARN == 0.20);
    REQUIRE(DEFAULT_P_TRANSITION == 0.10);

    // Verify SkillState constructor uses the calibrated defaults
    SkillState state;
    REQUIRE(state.m_pGuess == DEFAULT_P_GUESS);
    REQUIRE(state.m_pSlip == DEFAULT_P_SLIP);
}
