#pragma once
#include <chrono>
#include <unordered_map>
#include <vector>
#include <array>

namespace hestia::srs {

/// Intervalos base de repetición espaciada (expandido): 1d → 2d → 4d → 7d → 14d → 21d → 30d
inline constexpr std::array<int, 7> INTERVALS_DAYS = {1, 2, 4, 7, 14, 21, 30};

struct SRSEntry {
    int skill_id;
    int correct_streak{0};
    std::chrono::system_clock::time_point next_review;
};

class SRSQueue {
public:
    /// Programa (o reprograma) una skill con la racha dada
    void schedule(int skill_id, int correct_streak);

    /// Retorna los IDs de skills cuyo tiempo de revisión ya venció
    [[nodiscard]] std::vector<int> getDueSkills() const;

    /// Actualiza la racha: correcto → incrementa streak + recalcula intervalo;
    /// incorrecto → resetea streak a 0 + intervalo a 1 día.
    /// pL_operative and p_forget enable adaptive interval calculation.
    void markResult(int skill_id, bool correct,
                    double pL_operative = 0.5, double p_forget = 0.5);

    /// Verifica si una skill tiene entrada en la cola
    [[nodiscard]] bool hasEntry(int skill_id) const;

    // Bug fix #6: accesores para persistencia
    /// Retorna todas las entradas de la cola (para guardar en DB)
    [[nodiscard]] const std::unordered_map<int, SRSEntry>& getEntries() const noexcept { return m_entries; }
    /// Restaura una entrada ya construida desde la DB (sin recalcular el intervalo)
    void scheduleEntry(const SRSEntry& entry) { m_entries[entry.skill_id] = entry; }

private:
    std::unordered_map<int, SRSEntry> m_entries;

    /// Mapea la racha al intervalo correspondiente en horas (fixed)
    [[nodiscard]] static std::chrono::hours getInterval(int streak) noexcept;

    /// Adaptive interval based on streak, mastery level, and forget rate
    [[nodiscard]] static std::chrono::hours getAdaptiveInterval(
        int streak, double pL_operative, double p_forget) noexcept;
};

} // namespace hestia::srs
