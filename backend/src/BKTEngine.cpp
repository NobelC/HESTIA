#include "../include/BKTEngine.hpp"
#include <chrono>
#include <cmath>

namespace hestia::bkt {

    //==========================================================================
    // Operative channel posteriors — uses state-level P(S) and P(G)
    //==========================================================================

    constexpr double calculatePosterior(const SkillState& state, bool is_correct) noexcept {
      double pL = state.m_pLearn_operative;
      double s = state.m_pSlip;
      double g = state.m_pGuess;

      if (is_correct) {
        return (pL * (1.0 - s)) / ((pL * (1.0 - s)) + ((1.0 - pL) * g));
      } 
      else {
        return (pL * s) / ((pL * s) + ((1.0 - pL) * (1.0 - g)));
      }
    }

    [[nodiscard]] constexpr double calculateTransition(double pL_posterior, double pT) noexcept {
      return pL_posterior + (1.0 - pL_posterior) * pT;
    }

    [[nodiscard]] constexpr double calculatePenalty(double time, double avg_time) noexcept {
      double t_fast = avg_time;
      double t_slow = avg_time * 2.0;
      double w_min = 0.01;

      if (time <= t_fast) return 1.0;
      if (time >= t_slow) return w_min;

      return 1.0 - ((time - t_fast) / (t_slow - t_fast)) * (1.0 - w_min); 
    }

    //==========================================================================
    // Theoretical channel posteriors — uses SEPARATE, more optimistic params
    // This is the key fix: theoretical models "potential" without time penalty
    //==========================================================================

    constexpr double calculatePosteriorTheorical(const SkillState& state, bool is_correct) noexcept {
      double pL = state.m_pLearn_theorical;
      // Use dedicated theoretical parameters instead of state-level ones
      double s = THEORICAL_P_SLIP;
      double g = THEORICAL_P_GUESS;

      if (is_correct) {
        return (pL * (1.0 - s)) / ((pL * (1.0 - s)) + ((1.0 - pL) * g));
      } 
      else {
        return (pL * s) / ((pL * s) + ((1.0 - pL) * (1.0 - g)));
      }
    }

    [[nodiscard]] constexpr double calculateTransitionTheorical(double pL_posterior, double p_transition) noexcept {
      return pL_posterior + (1.0 - pL_posterior) * p_transition;
    }

    [[nodiscard]] constexpr double calculateErrorPenalty(double time, double avg_time) noexcept {
      // Impulsive error (fast) -> less penalty. Conceptual error (slow) -> full penalty.
      double t_fast = avg_time * 0.5;
      double t_slow = avg_time * 1.5;
      double w_min = 0.2; // Min penalty multiplier for impulsive errors

      if (time <= t_fast) return w_min;
      if (time >= t_slow) return 1.0;

      return w_min + ((time - t_fast) / (t_slow - t_fast)) * (1.0 - w_min); 
    }

    //==========================================================================
    // Core update
    //==========================================================================

    void BKTEngine::updateKnowledge(SkillState& state, bool is_correct, double response_time_ms,
                                    double fatigue_multiplier) noexcept {
      state.total_attempts++;

      if(state.isColdStart()){
        state.is_initialized = true;
        state.avg_response_time_ms = response_time_ms;
      }
      else{
        state.avg_response_time_ms = state.avg_response_time_ms + (response_time_ms - state.avg_response_time_ms) / state.total_attempts;
      }

      // ── Operative channel: posterior + transition + omega penalty ──
      double pL_posterior = calculatePosterior(state, is_correct);
      double pL_new = calculateTransition(pL_posterior, state.m_pTransition);

      // ── Theoretical channel: separate params, NO omega penalty ──
      double pL_posterior_theorical = calculatePosteriorTheorical(state, is_correct);
      double pL_new_theorical = calculateTransitionTheorical(pL_posterior_theorical, state.m_pTransition);

      double time_ratio = (state.avg_response_time_ms > 0.0) 
                         ? (response_time_ms / state.avg_response_time_ms) 
                         : 1.0;

      if (is_correct) {
        // Operative: apply omega penalty modulated by fatigue
        double omega = (state.total_attempts <= 2) ? 1.0 : calculatePenalty(response_time_ms, state.avg_response_time_ms);
        omega *= fatigue_multiplier;
        state.m_pLearn_operative = state.m_pLearn_operative + (pL_new - state.m_pLearn_operative) * omega;

        // Theoretical: direct update, no omega, no fatigue (models pure potential)
        state.m_pLearn_theorical = pL_new_theorical;

        state.consecutive_correct++;
        state.consecutive_error = 0;
        state.consecutive_slow_error = 0;

        // ── Dynamic P(T) boost: reward sustained correct streaks ──
        if (state.consecutive_correct >= 3) {
            double boost = 0.01 * static_cast<double>(state.consecutive_correct - 2);
            state.m_pTransition = std::min(P_TRANSITION_CEILING, state.m_pTransition + boost);
        }

        // ── Adaptive P(G) restoration: consistent fast correct answers ──
        if (time_ratio <= 1.0 && state.consecutive_correct >= 5) {
            state.m_pGuess = std::min(DEFAULT_P_GUESS, state.m_pGuess * 1.02);
        }
      } 
      else {
        // Operative: error penalty modulated by fatigue
        double omega = (state.total_attempts <= 2) ? 1.0 : calculateErrorPenalty(response_time_ms, state.avg_response_time_ms);
        omega *= fatigue_multiplier;
        state.m_pLearn_operative = state.m_pLearn_operative + (pL_new - state.m_pLearn_operative) * omega;

        // Theoretical: direct update (errors still reduce theoretical knowledge)
        state.m_pLearn_theorical = pL_new_theorical;

        state.consecutive_error++;
        state.consecutive_correct = 0;

        // ── Adaptive P(G): finer error classification ──
        if (time_ratio > 2.0) {
            // Deep conceptual error — strong P(G) decay
            state.m_pGuess = std::max(0.01, state.m_pGuess * 0.70);
            state.m_pSlip  = std::min(0.30, state.m_pSlip  * 1.05);
            state.consecutive_slow_error++;
        } else if (time_ratio < 0.5) {
            // Impulsive error — mild penalty
            state.m_pGuess = std::max(0.01, state.m_pGuess * 0.95);
            state.consecutive_slow_error = 0;
        } else {
            // Normal-speed error
            state.m_pGuess = std::max(0.01, state.m_pGuess * 0.80);
            if (response_time_ms > state.avg_response_time_ms * 2.0) {
                state.consecutive_slow_error++;
            } else {
                state.consecutive_slow_error = 0;
            }
        }

        // ── Dynamic P(T) decay: penalize sustained error streaks ──
        if (state.consecutive_error >= 2) {
            state.m_pTransition = std::max(P_TRANSITION_FLOOR,
                                           state.m_pTransition * 0.85);
        }
      }

      // ── Sliding window anti-stall ──
      state.m_stall_window_total++;
      if (is_correct) state.m_stall_window_hits++;

      if (state.m_stall_window_total >= STALL_WINDOW_SIZE) {
          double window_rate = static_cast<double>(state.m_stall_window_hits) / state.m_stall_window_total;
          double th_op_gap   = state.m_pLearn_theorical - state.m_pLearn_operative;

          if (window_rate >= STALL_HIT_RATE_THRESHOLD &&
              th_op_gap > ANTI_STALL_MARGIN &&
              state.m_pLearn_theorical >= ANTI_STALL_MIN_THEORICAL) {
              // Unlock: operative catches up to theoretical
              state.m_pLearn_operative = state.m_pLearn_theorical;
              state.is_mastered = true;
          }

          // Reset window regardless
          state.m_stall_window_hits  = 0;
          state.m_stall_window_total = 0;
      }

      // Legacy dominance counter (kept for backward compat with tests)
      if (state.m_pLearn_theorical > (state.m_pLearn_operative + ANTI_STALL_MARGIN) &&
          state.m_pLearn_theorical >= ANTI_STALL_MIN_THEORICAL) {
          state.m_sustained_theorical_dominance++;
      } else {
          state.m_sustained_theorical_dominance = 0;
      }

      state.last_practice_time = std::chrono::system_clock::now(); // wall-clock para persistencia
      state.validationProbabilityRanges();
    }

    //==========================================================================
    // Exponential forget with real elapsed time
    //==========================================================================

    void BKTEngine::applyForgetFactor(SkillState& state) noexcept{
      if(!state.exceedsForgetThreshold()){
        state.validationProbabilityRanges();
        return;
      }

      // Calculate actual hours elapsed
      auto hours_elapsed = std::chrono::duration_cast<std::chrono::hours>(
          std::chrono::system_clock::now() - state.last_practice_time).count();
      
      double days = static_cast<double>(hours_elapsed) / 24.0;
      double forget_rate = state.m_pForget;

      // Consolidation-aware: well-mastered skills forget much slower
      if (state.m_pLearn_operative > 0.85) {
          forget_rate *= 0.3;
      } else if (state.m_pLearn_operative > 0.60) {
          forget_rate *= 0.6;
      }

      // Exponential decay: P(L)_new = P(L) * e^(-rate * days)
      double decay = std::exp(-forget_rate * days);

      state.m_pLearn_operative  *= decay;
      // Theoretical is more resistant to forgetting (sqrt of decay)
      state.m_pLearn_theorical  *= std::sqrt(decay);

      state.validationProbabilityRanges();
    }     
}
