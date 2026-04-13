#pragma once
#include <array>
#include <cstdint>
#include <cassert>

namespace hestia::mab {

enum class METHOD : uint8_t { VISUAL = 0, AUDITORY = 1, KINESTHETIC = 2, PHONETIC = 3, GLOBAL = 4 };

struct MethodState {
    uint32_t count_attempts{0};
    uint32_t successes{0};
};

class MABEngine {
public:
    explicit MABEngine(double exploration_c = 1.0) noexcept;

    [[nodiscard]] METHOD selectMethod() const noexcept;
    void updateMethod(METHOD used_method, bool success) noexcept;
    void resetSession() noexcept;

private:
    static constexpr std::size_t METHOD_COUNT = 5;
    
    std::array<MethodState, METHOD_COUNT> m_method_data{};
    uint32_t m_total_attempts{0};
    double m_exploration_constant;


    [[nodiscard]] static double calculateUCB(const MethodState& state, 
                                            uint32_t total_n, 
                                            double c_param) noexcept;
};

} 
