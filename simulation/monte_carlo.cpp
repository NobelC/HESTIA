#include <iostream>
#include <vector>
#include <random>
#include <algorithm>
#include <cmath>
#include <numeric>
#include "../backend/include/BKTEngine.hpp"
#include "../backend/include/MABEngine.hpp"
#include "../backend/include/SessionManager.hpp"

using namespace hestia::bkt;
using namespace hestia::mab;

struct LearnerArchetype {
    std::string name;
    double p_transition;
    double p_slip;
    double p_guess;
    double p_forget;
    int hours_between_sessions;  // Simulated gap between sessions for forget activation
    std::array<double, 5> method_success_probs; // VISUAL, AUDITORY, KINESTHETIC, PHONETIC, GLOBAL
};

// Archetypes aligned with calibrated defaults (P(G)=0.25, P(S)=0.10)
// hours_between_sessions: 24h for low-forget, 72h for moderate, 168h for severe
const std::vector<LearnerArchetype> ARCHETYPES = {
    {"Fast Learner",         0.30, 0.10, 0.25, 0.02,  24, {0.9, 0.8, 0.7, 0.6, 0.8}},
    {"Average Learner",      0.15, 0.10, 0.25, 0.05,  24, {0.6, 0.7, 0.6, 0.5, 0.6}},
    {"Slow and Consistent",  0.05, 0.10, 0.25, 0.01,  24, {0.4, 0.4, 0.8, 0.4, 0.4}},
    {"Forgetful Learner",    0.20, 0.10, 0.25, 0.40, 168, {0.5, 0.5, 0.5, 0.5, 0.5}},
    {"Struggling Learner",   0.02, 0.15, 0.25, 0.15,  72, {0.3, 0.3, 0.3, 0.4, 0.3}},
};

void run_simulation(const LearnerArchetype& arch, int num_runs = 100, int items_per_session = 20, int max_sessions = 50) {
    std::cout << "--- Simulating: " << arch.name << " (" << num_runs << " runs) ---" << std::endl;
    std::cout << "Config: P(T)=" << arch.p_transition << " P(S)=" << arch.p_slip
              << " P(G)=" << arch.p_guess << " P(F)=" << arch.p_forget
              << " hours_gap=" << arch.hours_between_sessions
              << " items/session=" << items_per_session << std::endl;
    std::cout << "Mastery Criterion: m_pLearn_theorical >= 0.90" << std::endl;
    
    std::mt19937 generator(42);
    std::uniform_real_distribution<double> distribution(0.0, 1.0);

    const double MASTERY_THRESHOLD = 0.90;
    std::vector<int> convergence_times;
    int oscillating_runs = 0;

    for (int run = 0; run < num_runs; ++run) {
        BKTEngine engine;
        MABEngine mab(1.5);
        SkillState state;
        state.m_pTransition = arch.p_transition;
        state.m_pSlip = arch.p_slip;
        state.m_pGuess = arch.p_guess;
        state.m_pForget = arch.p_forget;
        state.is_initialized = true;
        // Initialize last_practice_time to now so the first session doesn't trigger forget
        state.last_practice_time = std::chrono::system_clock::now();
        
        int convergence_session = -1;

        for (int s = 0; s < max_sessions; ++s) {
            // Between sessions (except the first): inject simulated time gap
            // This is the ONLY way to activate applyForgetFactor in a simulation
            // that runs in milliseconds of wall-clock time
            if (s > 0) {
                state.last_practice_time = std::chrono::system_clock::now()
                    - std::chrono::hours(arch.hours_between_sessions);
                engine.applyForgetFactor(state);
            }

            mab.resetSession();
            for (int i = 0; i < items_per_session; ++i) {
                METHOD method = mab.selectMethod();
                double method_prob = arch.method_success_probs[static_cast<int>(method)];
                
                bool known = (distribution(generator) < state.m_pLearn_operative);
                
                // Observable response based on method preference
                double p_correct_if_known = method_prob * (1.0 - arch.p_slip);
                double p_correct_if_unknown = (1.0 - method_prob) * arch.p_guess;
                
                bool correct = known ? (distribution(generator) < p_correct_if_known) 
                                     : (distribution(generator) < p_correct_if_unknown);

                SessionManager session;
                session.applyTransitionDecay(state, 0.5);
                engine.updateKnowledge(state, correct, 1000.0);
                mab.updateMethod(method, correct);
            }

            // Document criterion: mastery is measured on m_pLearn_theorical
            if (state.m_pLearn_theorical >= MASTERY_THRESHOLD) {
                convergence_session = s + 1;
                break;
            }
        }

        if (convergence_session != -1) {
            convergence_times.push_back(convergence_session);
        } else {
            oscillating_runs++;
        }
    }

    if (convergence_times.empty()) {
        std::cout << "Result: 0% convergence. All runs oscillated or failed to reach mastery." << std::endl;
        std::cout << std::endl;
        return;
    }

    std::sort(convergence_times.begin(), convergence_times.end());
    
    double sum = std::accumulate(convergence_times.begin(), convergence_times.end(), 0.0);
    double mean = sum / convergence_times.size();
    
    double sq_sum = std::inner_product(convergence_times.begin(), convergence_times.end(), convergence_times.begin(), 0.0);
    double stddev = std::sqrt(sq_sum / convergence_times.size() - mean * mean);
    
    int p10 = convergence_times[convergence_times.size() * 0.10];
    int p50 = convergence_times[convergence_times.size() * 0.50];
    int p90 = convergence_times[convergence_times.size() * 0.90];
    double convergence_rate = (double)convergence_times.size() / num_runs * 100.0;

    std::cout << "Convergence Rate : " << convergence_rate << "%" << std::endl;
    std::cout << "Oscillating Runs : " << oscillating_runs << std::endl;
    std::cout << "Mean Sessions    : " << mean << " ± " << stddev << std::endl;
    std::cout << "Percentiles      : P10=" << p10 << ", P50=" << p50 << ", P90=" << p90 << std::endl;

    // Document criterion validation: Slow and Consistent must reach mastery in P50 <= 8 sessions
    if (arch.name == "Slow and Consistent") {
        if (p50 > 8) {
            std::cerr << "CRITERION FAIL: Slow and Consistent P50=" << p50
                      << " exceeds document limit of 8 sessions" << std::endl;
        } else {
            std::cout << "CRITERION PASS: Slow and Consistent P50=" << p50
                      << " within 8-session limit" << std::endl;
        }
    }

    // Sanity check: Forgetful should converge slower than non-forgetful archetypes
    if (arch.name == "Forgetful Learner") {
        std::cout << "NOTE: Forgetful Learner mean=" << mean
                  << " sessions (should be > Slow and Consistent with active forget)" << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "HESTIA Monte Carlo Validation System (Calibrated Parameters)\n" << std::endl;
    std::cout << "Engine Defaults: P(G)=" << DEFAULT_P_GUESS << " P(S)=" << DEFAULT_P_SLIP
              << " P(T)=" << DEFAULT_P_TRANSITION << " ANTI_STALL_MARGIN=" << ANTI_STALL_MARGIN << std::endl;
    std::cout << "Forget Threshold: " << FORGET_THRESHOLD_HOURS.count() << " hours\n" << std::endl;

    for (const auto& arch : ARCHETYPES) {
        run_simulation(arch);
    }
    return 0;
}
