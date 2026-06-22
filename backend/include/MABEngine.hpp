#pragma once
#include <array>
#include <cstdint>
#include <cassert>
#include <random>

namespace hestia::mab {

enum class METHOD : uint8_t { VISUAL = 0, AUDITORY = 1, KINESTHETIC = 2, PHONETIC = 3, GLOBAL = 4 };

struct MethodState {
    uint32_t count_attempts{0};
    uint32_t successes{0};
    double   ewma_success{0.5};    // Exponential weighted moving average of success
    static constexpr double EWMA_ALPHA = 0.15; // Recency weight
};

class MABEngine {
public:
    static constexpr std::size_t METHOD_COUNT = 5;
    static constexpr uint32_t THOMPSON_UCB_THRESHOLD = 50; // Thompson below, UCB above

    explicit MABEngine(double exploration_c = 1.0, uint64_t seed = 0) noexcept;

    [[nodiscard]] METHOD selectMethod() const noexcept;
    void updateMethod(METHOD used_method, bool success) noexcept;
    [[nodiscard]] const MethodState& getMethodState(METHOD m) const noexcept;
    // Bug fix #2: restaura historial persistente por (niño × habilidad × método) desde la DB.
    // Debe llamarse al inicio de sesión en lugar de resetSession().
    void loadFrom(const std::array<MethodState, METHOD_COUNT>& persisted) noexcept;
    void resetSession() noexcept;

private:
    std::array<MethodState, METHOD_COUNT> m_method_data{};
    uint32_t m_total_attempts{0};
    std::array<MethodState, METHOD_COUNT> m_session_data{};
    uint32_t m_session_total_attempts{0};
    double m_exploration_constant;
    mutable std::mt19937 m_rng;  // Mutable: Thompson Sampling needs RNG in const selectMethod

    [[nodiscard]] static double calculateUCB(const MethodState& state, 
                                            uint32_t total_n, 
                                            double c_param) noexcept;
    [[nodiscard]] METHOD selectMethodUCB() const noexcept;
    [[nodiscard]] METHOD selectMethodThompson() const noexcept;
};

} 
