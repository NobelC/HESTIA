#include "MABEngine.hpp"
#include <cmath>
#include <limits>
#include <cassert>

namespace hestia::mab {

MABEngine::MABEngine(double exploration_c, uint64_t seed) noexcept 
    : m_exploration_constant(exploration_c) {
    m_total_attempts = 0;
    m_session_total_attempts = 0;
    if (seed == 0) {
        std::random_device rd;
        m_rng.seed(rd());
    } else {
        m_rng.seed(static_cast<std::mt19937::result_type>(seed));
    }
}

void MABEngine::loadFrom(const std::array<MethodState, METHOD_COUNT>& persisted) noexcept {
    m_method_data = persisted;
    // Recalcular el total de intentos a partir del estado cargado para que UCB sea correcto
    m_total_attempts = 0;
    for (auto& s : m_method_data) {
        m_total_attempts += s.count_attempts;
        // Initialize EWMA from historical ratio if not set
        if (s.count_attempts > 0) {
            s.ewma_success = static_cast<double>(s.successes) / s.count_attempts;
        } else {
            s.ewma_success = 0.5; // Prior
        }
    }
}

void MABEngine::resetSession() noexcept {
    m_session_data.fill(MethodState{0, 0, 0.5});
    m_session_total_attempts = 0;
}

void MABEngine::updateMethod(METHOD used_method, bool success) noexcept {
    const auto idx = static_cast<std::size_t>(used_method);
    assert(idx < m_method_data.size() && "MABEngine: Index out of bounds");

    m_method_data[idx].count_attempts++;
    m_session_data[idx].count_attempts++;
    if (success) {
        m_method_data[idx].successes++;
        m_session_data[idx].successes++;
    }
    m_total_attempts++;
    m_session_total_attempts++;

    // Update EWMA: gives more weight to recent results
    constexpr double ALPHA = MethodState::EWMA_ALPHA;
    m_method_data[idx].ewma_success = ALPHA * (success ? 1.0 : 0.0) 
                                    + (1.0 - ALPHA) * m_method_data[idx].ewma_success;
}

const MethodState& MABEngine::getMethodState(METHOD m) const noexcept {
    const auto idx = static_cast<std::size_t>(m);
    assert(idx < m_method_data.size());
    return m_method_data[idx];
}

// ─── Hybrid selection: Thompson when cold, UCB when warmed up ───

[[nodiscard]] METHOD MABEngine::selectMethod() const noexcept {
    if (m_total_attempts == 0) {
        return static_cast<METHOD>(0);
    }

    // Explore untried methods first (cold start)
    for (std::size_t i = 0; i < m_method_data.size(); ++i) {
        if (m_method_data[i].count_attempts == 0) {
            return static_cast<METHOD>(i);
        }
    }

    // Hybrid: Thompson Sampling for small samples, UCB for large
    if (m_total_attempts < THOMPSON_UCB_THRESHOLD) {
        return selectMethodThompson();
    }
    return selectMethodUCB();
}

// ─── UCB with blended Q (40% global + 60% EWMA) ───

METHOD MABEngine::selectMethodUCB() const noexcept {
    double max_upper_bound = -std::numeric_limits<double>::infinity();
    std::size_t best_idx = 0;

    for (std::size_t i = 0; i < m_method_data.size(); ++i) {
        double score = calculateUCB(m_method_data[i], m_total_attempts, m_exploration_constant);
        
        if (score > max_upper_bound) {
            max_upper_bound = score;
            best_idx = i;
        }
    }
    return static_cast<METHOD>(best_idx);
}

double MABEngine::calculateUCB(const MethodState& state, uint32_t total_n, double c_param) noexcept {
    // Blend global Q with EWMA for recency bias
    const double global_q  = static_cast<double>(state.successes) / state.count_attempts;
    const double blended_q = 0.4 * global_q + 0.6 * state.ewma_success;
    
    const double exploration = c_param * std::sqrt(std::log(static_cast<double>(total_n)) / state.count_attempts);
    
    return blended_q + exploration;
}

// ─── Thompson Sampling via Beta distribution (Gamma trick) ───

METHOD MABEngine::selectMethodThompson() const noexcept {
    std::size_t best = 0;
    double best_sample = -1.0;

    for (std::size_t i = 0; i < METHOD_COUNT; ++i) {
        // Beta(alpha, beta) via Gamma distribution
        double alpha = static_cast<double>(m_method_data[i].successes) + 1.0;
        double beta  = static_cast<double>(m_method_data[i].count_attempts 
                      - m_method_data[i].successes) + 1.0;

        std::gamma_distribution<double> gamma_a(alpha, 1.0);
        std::gamma_distribution<double> gamma_b(beta,  1.0);

        double ga = gamma_a(m_rng);
        double gb = gamma_b(m_rng);
        double sample = ga / (ga + gb); // Sample from Beta(alpha, beta)

        if (sample > best_sample) {
            best_sample = sample;
            best = i;
        }
    }
    return static_cast<METHOD>(best);
}

}
