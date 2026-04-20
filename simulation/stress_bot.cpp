#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <filesystem>
#include <fstream>
#include <sqlite3.h>
#include "../backend/include/ResponseProcessor.hpp"

using namespace hestia;

/**
 * Stress Bot for HESTIA
 * Simulates 7 real scenarios to validate system behavior under different usage patterns.
 */

// Helper para inicializar la DB con el schema antes de PersistenceLayer::create
void initialize_schema(const std::string& path) {
    sqlite3* db;
    if (sqlite3_open(path.c_str(), &db) != SQLITE_OK) return;

    const char* schema = R"(
        PRAGMA user_version = 1;
        CREATE TABLE IF NOT EXISTS skill_state (
            student_id INTEGER NOT NULL, skill_id INTEGER NOT NULL,
            p_learn_operative REAL NOT NULL, p_learn_theorical REAL NOT NULL,
            p_transition REAL NOT NULL, p_slip REAL NOT NULL,
            p_guess REAL NOT NULL, p_forget REAL NOT NULL,
            avg_response_time REAL NOT NULL, last_practice_time INTEGER NOT NULL,
            PRIMARY KEY (student_id, skill_id)
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS method_state (
            student_id INTEGER NOT NULL, skill_id INTEGER NOT NULL,
            method_id INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            successes INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (student_id, skill_id, method_id)
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS response_log (
            log_id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL, method_id INTEGER NOT NULL,
            timestamp INTEGER NOT NULL, is_correct INTEGER NOT NULL,
            response_ms INTEGER NOT NULL
        );
    )";
    sqlite3_exec(db, schema, nullptr, nullptr, nullptr);
    sqlite3_close(db);
}

void run_scenario(core::ResponseProcessor& processor, const std::string& name, int iterations, int student_id, int skill_id) {
    std::cout << "\n>>> Running Scenario: " << name << " <<<" << std::endl;
    
    std::default_random_engine gen(42);
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    
    for (int i = 0; i < iterations; ++i) {
        bool correct = true;
        double time_ms = 1500.0;
        
        if (name == "Random Clicker") {
            correct = dist(gen) > 0.5;
            time_ms = 400.0 + dist(gen) * 400.0;
        } else if (name == "Fatigue (Decreasing)") {
            double drop_prob = static_cast<double>(i) / iterations;
            correct = dist(gen) > drop_prob;
            time_ms = 1500.0 + i * 50.0;
        } else if (name == "Sudden Drop") {
            if (i > iterations / 2) correct = false;
            time_ms = 1200.0;
        } else if (name == "Oscillating") {
            correct = (i % 2 == 0);
            time_ms = 2000.0;
        } else if (name == "Speed Demon (Anomalous)") {
            correct = true;
            time_ms = 50.0; // Anomaly check usually < 300ms
        } else if (name == "Slow Processor") {
            correct = true;
            time_ms = 20000.0;
        }
        
        auto result = processor.processResponse(student_id, skill_id, mab::METHOD::VISUAL, correct, time_ms);
        
        if (i % 10 == 0 || i == iterations - 1) {
            std::cout << "Iter " << i << ": pL=" << result.current_pL 
                      << " Anomaly=" << (result.was_anomalous ? "YES" : "NO") 
                      << " Valid=" << (result.valid_skill ? "YES" : "NO") << std::endl;
        }
    }
}

int main() {
    std::cout << "Starting HESTIA Stress Bot..." << std::endl;

    const std::string db_path = "stress_bot.db";
    const std::string graph_path = "stress_graph.json";

    // 1. Setup dummy graph
    {
        std::ofstream f(graph_path);
        f << R"({
            "skills": [
                {"id": 101, "name": "Skill 101", "prerequisites": []},
                {"id": 102, "name": "Skill 102", "prerequisites": []},
                {"id": 103, "name": "Skill 103", "prerequisites": []},
                {"id": 104, "name": "Skill 104", "prerequisites": []},
                {"id": 105, "name": "Skill 105", "prerequisites": []},
                {"id": 106, "name": "Skill 106", "prerequisites": []},
                {"id": 107, "name": "Skill 107", "prerequisites": []}
            ]
        })";
    }

    if (std::filesystem::exists(db_path)) std::filesystem::remove(db_path);
    initialize_schema(db_path);
    
    auto storage = persistence::PersistenceLayer::create(db_path);
    bkt::BKTEngine bkt;
    mab::MABEngine mab;
    bkt::SessionManager session;
    zone::ZoneBlender blender;
    graph::SkillGraph skill_graph;
    skill_graph.load(graph_path);
    srs::SRSQueue srs;
    
    core::ResponseProcessor processor(bkt, mab, session, *storage, blender, skill_graph, srs);
    
    run_scenario(processor, "Perfect Performance", 20, 1, 101);
    run_scenario(processor, "Random Clicker", 50, 2, 102);
    run_scenario(processor, "Fatigue (Decreasing)", 40, 3, 103);
    run_scenario(processor, "Sudden Drop", 30, 4, 104);
    run_scenario(processor, "Oscillating", 40, 5, 105);
    run_scenario(processor, "Speed Demon (Anomalous)", 20, 6, 106);
    run_scenario(processor, "Slow Processor", 10, 7, 107);
    
    // Cleanup
    std::filesystem::remove(db_path);
    std::filesystem::remove(graph_path);

    std::cout << "\nStress tests completed successfully." << std::endl;
    return 0;
}
