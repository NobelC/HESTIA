#pragma once
#include <string>
#include <vector>
#include <unordered_map>

namespace hestia::graph {

struct Prerequisite {
    int skill_id;
    double weight{1.0};  // 1.0 = bloqueante, 0.5 = recomendado
};

struct SkillNode {
    int id;
    std::string name;
    std::string domain;
    std::vector<Prerequisite> prerequisites;
    double estimated_difficulty{0.5}; // 0.0 fácil, 1.0 difícil
    int estimated_sessions{3};        // sesiones esperadas para dominar
};

class SkillGraph {
public:
    /// Carga el grafo desde un archivo JSON con la estructura { "skills": [...] }
    bool load(const std::string& path);

    /// Retorna los prerequisitos (solo IDs) de una skill, o vector vacío si no existe
    [[nodiscard]] std::vector<int> getPrerequisites(int skill_id) const;

    /// Retorna los prerequisitos completos (con pesos) de una skill
    [[nodiscard]] std::vector<Prerequisite> getWeightedPrerequisites(int skill_id) const;

    /// Retorna las skills desbloqueadas dado un conjunto de skills dominadas.
    /// Una skill se desbloquea si TODAS sus prereqs bloqueantes (peso >= 1.0) están en mastered_ids
    /// y la skill misma NO está en mastered_ids.
    [[nodiscard]] std::vector<int> getUnlockedSkills(const std::vector<int>& mastered_ids) const;

    /// Retorna la ruta más corta (IDs de skills) desde el estado actual (mastered_ids)
    /// hasta una skill objetivo, usando BFS.
    [[nodiscard]] std::vector<int> getLearningPath(int target_skill_id, const std::vector<int>& mastered_ids) const;

    /// Validación de integridad: retorna true si la skill existe en el grafo
    [[nodiscard]] bool exists(int skill_id) const;

    /// Cantidad total de skills en el grafo
    [[nodiscard]] size_t size() const noexcept;

private:
    std::unordered_map<int, SkillNode> m_skills;
};

} // namespace hestia::graph
