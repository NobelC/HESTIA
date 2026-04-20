#include <catch2/catch_test_macros.hpp>
#include "../include/SkillGraph.hpp"
#include <fstream>
#include <filesystem>
#include <cstdio>

using namespace hestia::graph;

// Helper RAII para el archivo JSON temporal
struct TempJsonGuard {
    std::string path;
    TempJsonGuard(const std::string& p, const std::string& content) : path(p) {
        std::ofstream out(path);
        out << content;
    }
    ~TempJsonGuard() { std::remove(path.c_str()); }
};

TEST_CASE("SkillGraph: Carga y validacion de JSON", "[graph]") {
    SkillGraph graph;

    SECTION("Carga exitosa desde JSON valido") {
        std::string json_content = R"({
            "skills": [
                { "id": 1, "name": "A", "domain": "test", "prerequisites": [] },
                { "id": 2, "name": "B", "domain": "test", "prerequisites": [1] },
                { "id": 3, "name": "C", "domain": "test", "prerequisites": [1, 2] }
            ]
        })";
        TempJsonGuard guard("test_graph_valid.json", json_content);

        REQUIRE(graph.load("test_graph_valid.json"));
        REQUIRE(graph.size() == 3);
        REQUIRE(graph.exists(1));
        REQUIRE(graph.exists(2));
        REQUIRE(graph.exists(3));
        REQUIRE_FALSE(graph.exists(4));
    }

    SECTION("Falla con JSON malformado (sin array 'skills')") {
        std::string json_content = R"({ "not_skills": [] })";
        TempJsonGuard guard("test_graph_invalid1.json", json_content);
        REQUIRE_FALSE(graph.load("test_graph_invalid1.json"));
    }

    SECTION("Falla si un prerequisito no existe") {
        std::string json_content = R"({
            "skills": [
                { "id": 1, "name": "A", "prerequisites": [999] }
            ]
        })";
        TempJsonGuard guard("test_graph_invalid2.json", json_content);
        REQUIRE_FALSE(graph.load("test_graph_invalid2.json"));
    }

    SECTION("Archivo inexistente") {
        REQUIRE_FALSE(graph.load("non_existent_file.json"));
    }
}

TEST_CASE("SkillGraph: Consultas de prerequisitos y desbloqueos", "[graph]") {
    SkillGraph graph;
    std::string json_content = R"({
        "skills": [
            { "id": 1, "name": "A", "prerequisites": [] },
            { "id": 2, "name": "B", "prerequisites": [1] },
            { "id": 3, "name": "C", "prerequisites": [1] },
            { "id": 4, "name": "D", "prerequisites": [2, 3] }
        ]
    })";
    TempJsonGuard guard("test_graph_queries.json", json_content);
    REQUIRE(graph.load("test_graph_queries.json"));

    SECTION("getPrerequisites retorna los IDs correctos") {
        auto pre1 = graph.getPrerequisites(1);
        REQUIRE(pre1.empty());

        auto pre4 = graph.getPrerequisites(4);
        REQUIRE(pre4.size() == 2);
        // Podrían estar en cualquier orden según el json, pero aquí es [2, 3]
        REQUIRE((pre4[0] == 2 || pre4[1] == 2));
        REQUIRE((pre4[0] == 3 || pre4[1] == 3));

        auto pre_invalid = graph.getPrerequisites(99);
        REQUIRE(pre_invalid.empty());
    }

    SECTION("getUnlockedSkills sin nada dominado") {
        std::vector<int> mastered = {};
        auto unlocked = graph.getUnlockedSkills(mastered);
        REQUIRE(unlocked.size() == 1);
        REQUIRE(unlocked[0] == 1); // Solo la skill 1 no tiene prerequisitos
    }

    SECTION("getUnlockedSkills con 1 dominada") {
        std::vector<int> mastered = {1};
        auto unlocked = graph.getUnlockedSkills(mastered);
        // Si 1 está dominada, se desbloquean 2 y 3. (1 ya no cuenta como desbloqueada)
        REQUIRE(unlocked.size() == 2);
        bool has_2 = false, has_3 = false;
        for (int id : unlocked) {
            if (id == 2) has_2 = true;
            if (id == 3) has_3 = true;
        }
        REQUIRE(has_2);
        REQUIRE(has_3);
    }

    SECTION("getUnlockedSkills requiere TODAS las prereqs") {
        std::vector<int> mastered = {1, 2};
        auto unlocked = graph.getUnlockedSkills(mastered);
        // Si dominamos 1 y 2, la 3 está desbloqueada (sus prereqs: [1] están cumplidas).
        // La 4 no está desbloqueada porque requiere [2, 3] y falta la 3.
        REQUIRE(unlocked.size() == 1);
        REQUIRE(unlocked[0] == 3);
    }

    SECTION("getUnlockedSkills con todo dominado") {
        std::vector<int> mastered = {1, 2, 3};
        auto unlocked = graph.getUnlockedSkills(mastered);
        REQUIRE(unlocked.size() == 1);
        REQUIRE(unlocked[0] == 4); // La 4 está desbloqueada
    }
}
