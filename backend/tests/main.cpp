#include <iostream>
#include <cassert>

#include <catch2/catch_test_macros.hpp>

// Placeholder: Verifica que el framework y CTest están configurados correctamente
TEST_CASE("Placeholder: Entorno de tests funcional", "[init]") {
    // Esta prueba siempre pasa. Sirve para confirmar que ctest detecta el ejecutable.
    REQUIRE(2 + 2 == 4);
}
int main() {
    std::cout << "[HESTIA] Running backend tests...\n";
    
    // Sanity check básico. Aquí irán tus tests reales más adelante.
    assert(2 + 2 == 4 && "Basic math check failed");
    
    std::cout << "[HESTIA] All tests passed.\n";
    return 0;
}
