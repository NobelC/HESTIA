#include "MABEngine.hpp"
#include <cmath>
#include <limits>
#include <cassert>

namespace hestia::mab {

MABEngine::MABEngine(double exploration_c) noexcept 
    : m_exploration_constant(exploration_c) {
    resetSession();
}

void MABEngine::resetSession() noexcept {
    m_total_attempts = 0;
    for (auto& state : m_method_data) {
        state.count_attempts = 0;
        state.successes = 0;
    }
}

void MABEngine::updateMethod(METHOD used_method, bool success) noexcept {
    const auto idx = static_cast<std::size_t>(used_method);
    assert(idx < m_method_data.size() && "MABEngine: Index out of bounds");

    m_method_data[idx].count_attempts++;
    if (success) m_method_data[idx].successes++;
    m_total_attempts++;
}

[[nodiscard]] METHOD MABEngine::selectMethod() const noexcept {
    for (std::size_t i = 0; i < m_method_data.size(); ++i) {
        if (m_method_data[i].count_attempts == 0) {
            return static_cast<METHOD>(i);
        }
    }

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
    const double mu = static_cast<double>(state.successes) / state.count_attempts;
    
    const double exploration = c_param * std::sqrt(std::log(static_cast<double>(total_n)) / state.count_attempts);
    
    return mu + exploration;
}

}
