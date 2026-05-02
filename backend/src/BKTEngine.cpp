#include "../include/BKTEngine.hpp"
#include <chrono>
#include <cmath>

namespace hestia::bkt {

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

    //==================================================================================================================
    //==================================================================================================================

    constexpr double calculatePosteriorTheorical(const SkillState& state, bool is_correct) noexcept {
      double pL = state.m_pLearn_theorical;
      double s = state.m_pSlip;
      double g = state.m_pGuess;

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

    [[nodiscard]] constexpr double calculatePenaltyTheorical(double time, double avg_time) noexcept {
      double t_fast = avg_time;
      double t_slow = avg_time * 2.0;
      double w_min = 0.01;

      if (time <= t_fast) return 1.0;
      if (time >= t_slow) return w_min;

      return 1.0 - ((time - t_fast) / (t_slow - t_fast)) * (1.0 - w_min); 
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

    //======================================================================================================================
    //======================================================================================================================

    void BKTEngine::updateKnowledge(SkillState& state, bool is_correct, double response_time_ms) noexcept {
      state.total_attempts++;

      if(state.isColdStart()){
        state.is_initialized = true;
        state.avg_response_time_ms = response_time_ms;
      }
      else{
        state.avg_response_time_ms = state.avg_response_time_ms + (response_time_ms - state.avg_response_time_ms) / state.total_attempts;
      }

      double pL_posterior = calculatePosterior(state, is_correct);
      double pL_new = calculateTransition(pL_posterior, state.m_pTransition);

      double pL_posterior_theorical = calculatePosteriorTheorical(state,is_correct);
      double pL_new_theorical = calculateTransitionTheorical(pL_posterior_theorical, state.m_pTransition);

      if (is_correct) {
        double omega = (state.total_attempts <= 2) ? 1.0 : calculatePenalty(response_time_ms, state.avg_response_time_ms);
        double omega_theorical = (state.total_attempts <= 2) ? 1.0 : calculatePenaltyTheorical(response_time_ms, state.avg_response_time_ms);
        state.m_pLearn_operative = state.m_pLearn_operative + (pL_new - state.m_pLearn_operative) * omega;
        state.m_pLearn_theorical = state.m_pLearn_theorical + (pL_new_theorical - state.m_pLearn_theorical) * omega_theorical;
        state.consecutive_correct++;
        state.consecutive_error = 0;
        state.consecutive_slow_error = 0;
      } 
      else {
        // Lento + Incorrecto → Alta penalización. Rápido + Incorrecto -> Baja penalización.
        double omega = (state.total_attempts <= 2) ? 1.0 : calculateErrorPenalty(response_time_ms, state.avg_response_time_ms);
        double omega_theorical = omega; // Both use same error penalty curve
        state.m_pLearn_operative = state.m_pLearn_operative + (pL_new - state.m_pLearn_operative) * omega;
        state.m_pLearn_theorical = state.m_pLearn_theorical + (pL_new_theorical - state.m_pLearn_theorical) * omega_theorical;
        state.consecutive_error++;
        state.consecutive_correct = 0;

        if (response_time_ms > state.avg_response_time_ms * 2.0) {
            state.consecutive_slow_error++;
            state.m_pGuess = std::max(0.01, state.m_pGuess * 0.8);
        } else {
            state.consecutive_slow_error = 0;
        }
      }

      // Anti-stall logic: si el P(L) teórico supera consistentemente al operativo
      if (state.m_pLearn_theorical > (state.m_pLearn_operative + ANTI_STALL_MARGIN)) {
          state.m_sustained_theorical_dominance++;
          
          if (state.m_sustained_theorical_dominance >= ANTI_STALL_THRESHOLD) {
              // Desbloqueo: el operativo atrapa al teórico para salir del estancamiento
              state.m_pLearn_operative = state.m_pLearn_theorical;
              // Bug fix #4: resetear el contador DESPUÉS del desbloqueo para que el
              // mecanismo anti-stall no se convierta en un bypass permanente.
              // Sin este reset, si m_pLearn_theorical sigue alto en el siguiente intento,
              // la condición se cumple otra vez y el operativo se sobreescribe indefinidamente.
              state.m_sustained_theorical_dominance = 0;
              state.is_mastered = true;
          }
      } else {
          state.m_sustained_theorical_dominance = 0;
      }

      state.last_practice_time = std::chrono::system_clock::now(); // wall-clock para persistencia
      state.validationProbabilityRanges();
    }

    void BKTEngine::applyForgetFactor(SkillState& state) noexcept{
      if(state.exceedsForgetThreshold()){
        // Bug fix #1: el decaimiento por inactividad debe afectar AMBAS métricas.
        // Si solo decae m_pLearn_operative, el anti-stall puede desbloquear el siguiente
        // nivel inmediatamente después de que P(F) reduzca el operativo, porque el teórico
        // sigue alto y la condición de dominancia se cumple en el primer intento siguiente.
        state.m_pLearn_operative = (state.m_pLearn_operative * (1 - state.m_pForget)) + 
          ((1 - state.m_pLearn_operative) * state.m_pTransition);
        // Teórico decae más lento que el operativo (mitad de tasa de olvido)
        double theoretical_forget = state.m_pForget * 0.5;
        state.m_pLearn_theorical = (state.m_pLearn_theorical * (1 - theoretical_forget)) +
          ((1 - state.m_pLearn_theorical) * state.m_pTransition);
      }
      state.validationProbabilityRanges();
    }     
}

