#include <iostream>
#include <random>
#include "../backend/include/BKTEngine.hpp"

using namespace hestia::bkt;

int main() {
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
        std::cout << "i=" << i 
                  << " correct=" << correct
                  << " op=" << state.m_pLearn_operative
                  << " th=" << state.m_pLearn_theorical
                  << " diff=" << (state.m_pLearn_theorical - state.m_pLearn_operative)
                  << " dom=" << state.m_sustained_theorical_dominance
                  << " mastered=" << state.is_mastered
                  << std::endl;
    }
    return 0;
}
