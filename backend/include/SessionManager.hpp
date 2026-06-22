#pragma once
#include "BKTEngine.hpp"

namespace hestia::bkt {

class SessionManager {
public:
    SessionManager() = default;
    ~SessionManager() = default;

    // Registra session_start_time en el estado y resetea P(T) al valor nominal (DEFAULT_P_TRANSITION)
    void startSession(SkillState& state) const noexcept;

    // Incrementa session_count y realiza cleanup
    void endSession(SkillState& state) const noexcept;

    // Retorna true si el tiempo supera 5 minutos (300,000 ms) — anomalía lenta
    [[nodiscard]] bool isResponseTimeAnomalous(double response_time_ms) const noexcept;

    // Retorna true si la respuesta es incorrecta y extremadamente rápida (< 300ms) — anomalía impulsiva
    [[nodiscard]] bool isImpulsiveError(double response_time_ms, bool is_correct) const noexcept;

    // Helper que usa session_start_time para calcular minutos transcurridos
    [[nodiscard]] double getSessionElapsedMinutes(const SkillState& state) const noexcept;

    // Aplica el decaimiento de P(T) de forma incremental
    void applyTransitionDecay(SkillState& state, double lambda) const noexcept;

    // ─── Fatigue & pattern detection ───

    // Returns fatigue multiplier: 1.0 = fresh (0-10 min), decays to 0.3 at 30+ min
    [[nodiscard]] double getFatigueMultiplier(const SkillState& state) const noexcept;

    // Returns true if average response time < 300ms with > 5 attempts (bot/random clicking)
    [[nodiscard]] bool isClickingPattern(const SkillState& state) const noexcept;

    // Returns true if 3+ consecutive slow errors (conceptual difficulty)
    [[nodiscard]] bool isConsistentlySlowWithErrors(const SkillState& state) const noexcept;
};

} // namespace hestia::bkt
