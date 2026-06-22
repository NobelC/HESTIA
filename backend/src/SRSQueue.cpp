#include "../include/SRSQueue.hpp"
#include <algorithm>

namespace hestia::srs {

std::chrono::hours SRSQueue::getInterval(int streak) noexcept {
    int index = std::max(0, streak);
    index = std::min(index, static_cast<int>(INTERVALS_DAYS.size()) - 1);
    return std::chrono::hours{INTERVALS_DAYS[index] * 24};
}

std::chrono::hours SRSQueue::getAdaptiveInterval(
    int streak, double pL_operative, double p_forget) noexcept 
{
    int index = std::max(0, streak);
    index = std::min(index, static_cast<int>(INTERVALS_DAYS.size()) - 1);
    double base_days = INTERVALS_DAYS[index];
    
    // Adjustment by P(L): mastered skills wait longer (0.5x to 1.5x)
    double pl_multiplier = 0.5 + pL_operative;
    
    // Adjustment by P(F): forgetful students review sooner (0.75x to 1.0x)
    // p_forget is usually [0.01, 0.99]
    double forget_multiplier = 1.0 - (p_forget * 0.5);
    
    double adjusted_days = base_days * pl_multiplier * forget_multiplier;
    return std::chrono::hours{static_cast<int>(adjusted_days * 24)};
}

void SRSQueue::schedule(int skill_id, int correct_streak) {
    auto now = std::chrono::system_clock::now();
    SRSEntry entry;
    entry.skill_id = skill_id;
    entry.correct_streak = correct_streak;
    entry.next_review = now + getInterval(correct_streak);
    m_entries[skill_id] = entry;
}

std::vector<int> SRSQueue::getDueSkills() const {
    auto now = std::chrono::system_clock::now();
    std::vector<int> due;

    for (const auto& [id, entry] : m_entries) {
        if (entry.next_review <= now) {
            due.push_back(id);
        }
    }

    return due;
}

void SRSQueue::markResult(int skill_id, bool correct,
                          double pL_operative, double p_forget) {
    auto now = std::chrono::system_clock::now();
    auto it = m_entries.find(skill_id);

    if (it == m_entries.end()) {
        SRSEntry entry;
        entry.skill_id = skill_id;
        if (correct) {
            entry.correct_streak = 1;
            entry.next_review = now + getAdaptiveInterval(1, pL_operative, p_forget);
        } else {
            entry.correct_streak = 0;
            entry.next_review = now + getAdaptiveInterval(0, pL_operative, p_forget);
        }
        m_entries[skill_id] = entry;
    } else {
        if (correct) {
            it->second.correct_streak++;
            it->second.next_review = now + getAdaptiveInterval(
                it->second.correct_streak, pL_operative, p_forget);
        } else {
            it->second.correct_streak = 0;
            it->second.next_review = now + getAdaptiveInterval(
                0, pL_operative, p_forget);
        }
    }
}

bool SRSQueue::hasEntry(int skill_id) const {
    return m_entries.contains(skill_id);
}

} // namespace hestia::srs
