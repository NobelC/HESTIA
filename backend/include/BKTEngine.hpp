#pragma once
#include <chrono>
#include <cstdint>
#include <algorithm>

//

namespace hestia::bkt {

// ─── Operative channel bounds ───
constexpr double MAX_P_LEARN_OPERATIVE = 0.98;
constexpr double MIN_P_LEARN_OPERATIVE = 0.01;

// ─── Forget thresholds ───
constexpr std::chrono::hours FORGET_THRESHOLD_HOURS{48};

// ─── Transition ───
constexpr double P_TRANSITION_FLOOR = 0.05;
constexpr double P_TRANSITION_CEILING = 0.40;

// ─── Default BKT parameters (operative channel) ───
constexpr double DEFAULT_P_LEARN = 0.20;
constexpr double DEFAULT_P_TRANSITION = 0.10;
constexpr double DEFAULT_P_GUESS = 0.25;
constexpr double DEFAULT_P_SLIP = 0.10;
constexpr double DEFAULT_P_FORGET = 0.50;

// ─── Theoretical channel parameters (more optimistic, models potential) ───
constexpr double THEORICAL_P_SLIP  = 0.05;   // Less punitive slip for potential
constexpr double THEORICAL_P_GUESS = 0.30;   // More credit to learning potential

// ─── Forget consolidation tiers ───
constexpr double DEFAULT_P_FORGET_CONSOLIDATED = 0.10; // Skills with pL > 0.85
constexpr double DEFAULT_P_FORGET_LEARNING     = 0.50; // Skills in active learning
constexpr double DEFAULT_P_FORGET_FRAGILE      = 0.70; // Newly initiated skills

// ─── Regression detection ───
constexpr double REGRESSION_THRESHOLD          = 0.20; // Significant P(L) drop
constexpr double MASTERY_CONSOLIDATION_THRESHOLD = 0.95; // Solidly mastered

// ─── Anti-stall (sliding window) ───
constexpr uint32_t ANTI_STALL_THRESHOLD = 3;              // Legacy: kept for test compat
constexpr double   ANTI_STALL_MARGIN = 0.15;
constexpr double   ANTI_STALL_MIN_THEORICAL = 0.70;
constexpr uint32_t STALL_WINDOW_SIZE = 10;
constexpr double   STALL_HIT_RATE_THRESHOLD = 0.80;

// ─── Response time validation ───
constexpr double MIN_RESPONSE_TIME_MS = 100.0;            // Below = suspicious

struct SkillState {
    // Pesos del modulo BKT+
    double m_pLearn_operative;  // Factor P(L) Operativo — penalizado por omega
    double m_pLearn_theorical;  // Factor P(L) Teórico — sin penalización, modela potencial
    double m_pGuess;            // Factor P(G) - suerte
    double m_pSlip;             // Factor P(S) - descuido
    double m_pForget;           // Factor P(F) - olvido
    double m_pTransition;       // Factor P(T) - Transicion
    double avg_response_time_ms{0.0};

    // Trackeo temporal
    std::chrono::system_clock::time_point last_practice_time{};   // wall-clock: persistencia y olvido
    std::chrono::system_clock::time_point session_start_time{};   // wall-clock: compatibilidad / cleanup
    std::chrono::steady_clock::time_point session_start_time_steady{}; // Bug fix #3: monótono para decay intra-sesión
    std::chrono::steady_clock::time_point last_update_time_steady{}; // Track exact time of last decay

    uint32_t skill_id;
    uint32_t total_attempts{0};
    uint32_t session_count{0};
    uint32_t consecutive_correct{0};
    uint32_t consecutive_error{0};
    uint32_t consecutive_slow_error{0};
    uint32_t m_sustained_theorical_dominance{0};

    // Sliding window anti-stall counters
    uint32_t m_stall_window_hits{0};      // Correct count in current window
    uint32_t m_stall_window_total{0};     // Total responses in current window

    // Estado
    bool is_initialized = {false};
    bool is_mastered = {false};

    // Consultas inmutables
    [[nodiscard]] constexpr bool isColdStart() const noexcept { return !is_initialized; }
    [[nodiscard]] constexpr bool isMastered(double operative_threshold = 0.85) const noexcept {
        return is_mastered && m_pLearn_operative >= operative_threshold;
    }
    [[nodiscard]] bool exceedsForgetThreshold() const noexcept {
        if (last_practice_time.time_since_epoch().count() == 0) {
            return false;
        }
        return std::chrono::system_clock::now() - last_practice_time >= FORGET_THRESHOLD_HOURS;
    }

    void validationProbabilityRanges() noexcept {
        m_pLearn_operative =
            std::clamp(m_pLearn_operative, MIN_P_LEARN_OPERATIVE, MAX_P_LEARN_OPERATIVE);
        m_pLearn_theorical = std::clamp(m_pLearn_theorical, MIN_P_LEARN_OPERATIVE, MAX_P_LEARN_OPERATIVE);
        m_pForget = std::clamp(m_pForget, 0.01, 0.99);
        m_pGuess = std::clamp(m_pGuess, 0.01, 0.99);
        m_pSlip = std::clamp(m_pSlip, 0.01, 0.99);
        m_pTransition = std::clamp(m_pTransition, P_TRANSITION_FLOOR, 0.99);
    }

    SkillState()
        : m_pLearn_operative(DEFAULT_P_LEARN),
          m_pLearn_theorical(DEFAULT_P_LEARN),
          m_pTransition(DEFAULT_P_TRANSITION),
          m_pSlip(DEFAULT_P_SLIP),
          m_pGuess(DEFAULT_P_GUESS),
          m_pForget(DEFAULT_P_FORGET),
          is_initialized(false) {}
};

class BKTEngine {
public:
    explicit BKTEngine() noexcept = default;
    // Actualizar estado tras cada respuesta del estudiante.
    // fatigue_multiplier: 1.0 = no fatigue, <1.0 = fatigued (slows learning rate)
    void updateKnowledge(SkillState& state, bool is_correct, double response_time_ms,
                         double fatigue_multiplier = 1.0) noexcept;
    void applyForgetFactor(SkillState& state) noexcept;
};
}  // namespace hestia::bkt
