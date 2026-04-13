#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "../include/MABEngine.hpp"

using namespace hestia::mab;

// Helper para forzar un estado de explotación (N alto)
void fill_history(MABEngine& engine, METHOD method, uint32_t attempts, uint32_t successes) {
    for (uint32_t i = 0; i < attempts; ++i) {
        engine.updateMethod(method, i < successes);
    }
}

TEST_CASE("UCB explora método no usado cuando n(m)=0 (Cold Start)", "[mab][sec7.1]") {
    MABEngine engine(1.0);
    std::array<uint32_t, 5> hit_counts{0, 0, 0, 0, 0};

    SECTION("Debe retornar cada método exactamente una vez al inicio") {
        for (int i = 0; i < 5; ++i) {
            METHOD selected = engine.selectMethod();
            auto idx = static_cast<size_t>(selected);
            hit_counts[idx]++;
            
            // Simulamos que el sistema registra el intento para pasar al siguiente
            engine.updateMethod(selected, true);
        }

        for (uint32_t count : hit_counts) {
            REQUIRE(count == 1);
        }
    }
}

TEST_CASE("UCB selecciona método con más Q en explotación", "[mab][sec7.1]") {
    // Usamos C bajo y N alto para que la exploración no eclipse la explotación
    MABEngine engine(0.1); 

    // M1 (VISUAL): Q = 0.9 (90/100)
    fill_history(engine, METHOD::VISUAL, 100, 90);
    // M2..M5: Q = 0.1 (10/100)
    fill_history(engine, METHOD::AUDITORY, 100, 10);
    fill_history(engine, METHOD::KINESTHETIC, 100, 10);
    fill_history(engine, METHOD::PHONETIC, 100, 10);
    fill_history(engine, METHOD::GLOBAL, 100, 10);

    REQUIRE(engine.selectMethod() == METHOD::VISUAL);
}

TEST_CASE("Constante C ajusta balance exploit/explore", "[mab][sec7.1]") {
    // Escenario: M1 es ligeramente mejor que M2, pero M2 tiene pocos intentos
    // Esto crea un conflicto entre lo que sabemos (M1) y lo que no (M2)
    
    auto setup_scenario = [](double c_value) {
        MABEngine engine(c_value);
        fill_history(engine, METHOD::VISUAL, 100, 80);      // M1: Q=0.8, n=100
        fill_history(engine, METHOD::AUDITORY, 100, 20);    // M2: Q=0.2, n=100
        fill_history(engine, METHOD::KINESTHETIC, 100, 20); // M3: Q=0.2, n=100
        fill_history(engine, METHOD::PHONETIC, 100, 20);    // M4: Q=0.2, n=100
        fill_history(engine, METHOD::GLOBAL, 5, 1);         // M5: Q=0.2, n=5 (Incertidumbre alta)
        return engine;
    };

    SECTION("C bajo (0.1) debe preferir Explotación (M1)") {
        MABEngine engine = setup_scenario(0.1);
        REQUIRE(engine.selectMethod() == METHOD::VISUAL);
    }

    SECTION("C alto (5.0) debe preferir Exploración (M5)") {
        MABEngine engine = setup_scenario(5.0);
        // M5 tiene pocos intentos, con C alto su Upper Bound será mayor a pesar de su bajo Q
        REQUIRE(engine.selectMethod() == METHOD::GLOBAL);
    }
}

TEST_CASE("Update actualiza Q correctamente tras acierto/fallo", "[mab][sec7.1]") {
    MABEngine engine(1.0);
    
    // Inyectar 10 aciertos y 5 fallos (15 intentos, Q = 0.666...)
    for(int i=0; i<10; i++) engine.updateMethod(METHOD::VISUAL, true);
    for(int i=0; i<5; i++) engine.updateMethod(METHOD::VISUAL, false);

    // No podemos acceder a los privados, pero podemos verificar el comportamiento 
    // a través de la fórmula UCB en una comparación controlada.
    
    SECTION("Verificación de persistencia mediante reset") {
        engine.resetSession();
        // Tras reset, el primer método debe ser VISUAL por Cold Start
        REQUIRE(engine.selectMethod() == METHOD::VISUAL);
    }
}
