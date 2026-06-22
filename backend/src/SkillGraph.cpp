#include "../include/SkillGraph.hpp"
#include <nlohmann/json.hpp>
#include <fstream>
#include <unordered_set>
#include <functional>
#include <queue>
#include <algorithm>

namespace hestia::graph {

bool SkillGraph::load(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) return false;

    nlohmann::json doc;
    try {
        doc = nlohmann::json::parse(file);
    } catch (const nlohmann::json::parse_error&) {
        return false;
    }

    if (!doc.contains("skills") || !doc["skills"].is_array()) return false;

    std::unordered_map<int, SkillNode> parsed;

    for (const auto& entry : doc["skills"]) {
        if (!entry.contains("id") || !entry["id"].is_number_integer()) return false;

        SkillNode node;
        node.id   = entry["id"].get<int>();
        node.name = entry.value("name", "");
        node.domain = entry.value("domain", "");
        node.estimated_difficulty = entry.value("estimated_difficulty", 0.5);
        node.estimated_sessions = entry.value("estimated_sessions", 3);

        if (entry.contains("prerequisites") && entry["prerequisites"].is_array()) {
            for (const auto& prereq : entry["prerequisites"]) {
                if (prereq.is_number_integer()) {
                    node.prerequisites.push_back({prereq.get<int>(), 1.0});
                } else if (prereq.is_object() && prereq.contains("skill_id")) {
                    node.prerequisites.push_back({
                        prereq["skill_id"].get<int>(),
                        prereq.value("weight", 1.0)
                    });
                } else {
                    return false;
                }
            }
        }

        parsed[node.id] = std::move(node);
    }

    // Validación de integridad: todos los prerequisitos deben referenciar skills existentes
    for (const auto& [id, node] : parsed) {
        for (const auto& prereq : node.prerequisites) {
            if (!parsed.contains(prereq.skill_id)) return false;
        }
    }

    // Validación de ciclos (DFS)
    std::unordered_map<int, int> visited; // 0: unvisited, 1: visiting, 2: visited
    std::function<bool(int)> has_cycle = [&](int node_id) {
        if (visited[node_id] == 1) return true;
        if (visited[node_id] == 2) return false;

        visited[node_id] = 1;
        if (parsed.contains(node_id)) {
            for (const auto& prereq : parsed.at(node_id).prerequisites) {
                if (has_cycle(prereq.skill_id)) return true;
            }
        }
        visited[node_id] = 2;
        return false;
    };

    for (const auto& [id, node] : parsed) {
        if (visited[id] == 0 && has_cycle(id)) {
            return false;
        }
    }

    m_skills = std::move(parsed);
    return true;
}

std::vector<int> SkillGraph::getPrerequisites(int skill_id) const {
    auto it = m_skills.find(skill_id);
    if (it == m_skills.end()) return {};
    
    std::vector<int> ids;
    ids.reserve(it->second.prerequisites.size());
    for (const auto& p : it->second.prerequisites) {
        ids.push_back(p.skill_id);
    }
    return ids;
}

std::vector<Prerequisite> SkillGraph::getWeightedPrerequisites(int skill_id) const {
    auto it = m_skills.find(skill_id);
    if (it == m_skills.end()) return {};
    return it->second.prerequisites;
}

std::vector<int> SkillGraph::getUnlockedSkills(const std::vector<int>& mastered_ids) const {
    std::unordered_set<int> mastered_set(mastered_ids.begin(), mastered_ids.end());
    std::vector<int> unlocked;

    for (const auto& [id, node] : m_skills) {
        // Ya dominada → no se "desbloquea"
        if (mastered_set.contains(id)) continue;

        // Verificar que TODAS las prereqs bloqueantes estén dominadas
        bool all_met = true;
        for (const auto& prereq : node.prerequisites) {
            if (prereq.weight >= 1.0 && !mastered_set.contains(prereq.skill_id)) {
                all_met = false;
                break;
            }
        }

        if (all_met) {
            unlocked.push_back(id);
        }
    }

    return unlocked;
}

std::vector<int> SkillGraph::getLearningPath(int target_skill_id, const std::vector<int>& mastered_ids) const {
    if (!m_skills.contains(target_skill_id)) return {};
    
    std::unordered_set<int> mastered_set(mastered_ids.begin(), mastered_ids.end());
    if (mastered_set.contains(target_skill_id)) return {target_skill_id}; // Already mastered

    // Reversed graph map: adjacency list of prereq -> skills it unlocks
    std::unordered_map<int, std::vector<int>> reverse_graph;
    for (const auto& [id, node] : m_skills) {
        for (const auto& prereq : node.prerequisites) {
            if (prereq.weight >= 1.0) {
                reverse_graph[prereq.skill_id].push_back(id);
            }
        }
    }

    // BFS to find shortest path to target starting from any currently unlocked skill
    std::queue<int> q;
    std::unordered_map<int, int> parent;
    std::unordered_set<int> visited;

    // Start BFS from skills that are already unlocked
    std::vector<int> unlocked = getUnlockedSkills(mastered_ids);
    for (int start_id : unlocked) {
        q.push(start_id);
        visited.insert(start_id);
        parent[start_id] = -1; // root
        
        if (start_id == target_skill_id) {
            return {target_skill_id}; // target is immediately available
        }
    }

    bool found = false;
    while (!q.empty()) {
        int curr = q.front();
        q.pop();

        if (curr == target_skill_id) {
            found = true;
            break;
        }

        // Expand to skills unlocked by 'curr'
        if (reverse_graph.contains(curr)) {
            for (int next : reverse_graph[curr]) {
                if (!visited.contains(next) && !mastered_set.contains(next)) {
                    // Quick check if 'next' has all its other prerequisites met
                    bool can_unlock = true;
                    for (const auto& pre : m_skills.at(next).prerequisites) {
                        if (pre.weight >= 1.0 && !mastered_set.contains(pre.skill_id) && !visited.contains(pre.skill_id)) {
                             // This is a simplification: if a prereq isn't mastered or visited in this path, we can't reliably say we unlock it immediately.
                             // A true learning path might need topological sort or a more complex planner.
                             // We assume BFS visitation roughly approximates learning sequence for simple DAGs.
                             can_unlock = false;
                             break;
                        }
                    }
                    if (can_unlock) {
                        visited.insert(next);
                        parent[next] = curr;
                        q.push(next);
                    }
                }
            }
        }
    }

    if (!found) return {};

    // Backtrack to build path
    std::vector<int> path;
    int curr = target_skill_id;
    while (curr != -1) {
        path.push_back(curr);
        curr = parent[curr];
    }
    std::reverse(path.begin(), path.end());
    return path;
}

bool SkillGraph::exists(int skill_id) const {
    return m_skills.contains(skill_id);
}

size_t SkillGraph::size() const noexcept {
    return m_skills.size();
}

} // namespace hestia::graph
