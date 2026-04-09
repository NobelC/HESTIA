#pragma once
#include <chrono>
#include <cstdint>
#include <algorithm>
#include <string>

namespace hestia::bkt {

  constexpr double MAX_P_LEARN_OPERATIVE = 0.90;
  constexpr double MIN_P_LEARN_OPERATIVE = 0.01;
  constexpr std::chrono::hours FORGET_THRESHOLD_HOURS{48};
  constexpr double P_TRANSITION_FLOOR = 0.05;
  

  struct SkillState{
    //Identificador de la prueba
    std::string skill_id;
    
    //Pesos del modulo BKT+ 
    double m_pLearnOperative; //Factor P(L) Operativo capado a <= 0.90
    double m_pLearnTheorical; //Factor P(L) para evitar el anti-stall
    double m_pGuess; //Factor P(G) - suerte
    double m_pSlip; //Factor P(S) - descuido
    double m_pForget; //Factor P(F) - olvido
    double m_pTransition; //Factor P(T) - Transicion
    
    //Trackeo temporal
    std::chrono::system_clock::time_point last_practice_time{};
    std::chrono::system_clock::time_point session_start_time{};
    
    //Metricas de rendimiento
    uint32_t total_attempts{0};
    uint32_t session_count{0};
    uint32_t consecutive_correct{0};
    uint32_t consecutive_error{0};
    uint32_t sustained_theorical_dominance{0};
    double avg_response_time_ms{0.0};

    //Estado
    bool is_initialized{false};
    
    //Consultas inmutables 
    [[nodiscard]] constexpr bool isColdStart() const noexcept{return !is_initialized;}
    [[nodiscard]] constexpr bool exceedsForgetThreshold() const noexcept{
      if(last_practice_time.time_since_epoch().count() == 0) {return false;}
      return std::chrono::system_clock::now() - last_practice_time >= FORGET_THRESHOLD_HOURS;
    }

    void validationRangesData() noexcept{
      m_pLearnOperative = std::clamp(m_pLearnOperative, MIN_P_LEARN_OPERATIVE, MAX_P_LEARN_OPERATIVE);
      m_pLearnTheorical = std::clamp(m_pLearnTheorical, MIN_P_LEARN_OPERATIVE, 1.0 );
      m_pForget = std::clamp(m_pForget, 0.01, 0.99);
      m_pGuess = std::clamp(m_pGuess, 0.01 , 0.99);
      m_pSlip = std::clamp(m_pGuess, 0.01, 0.99);
      m_pTransition = std::clamp(m_pTransition, P_TRANSITION_FLOOR, 0.99);
    }
  };

  class BKTEngine{
    public:
      explicit BKTEngine() noexcept = default;
      //Actular estado tras cada respuesta del estudiante
      void UpdateKnowledge(SkillState& state, bool is_correct, double response_time_ms) noexcept;
      [[nodiscard]] double currenPTtransition(const SkillState& state) const noexcept;
      void applyForgetFactor(SkillState& state) noexcept;
    private:
      [[nodiscard]] double computeRespondePenalty(double& response_time_ms, bool& is_correct) const noexcept;
  };
}
