# backend/tests/CMakeLists.txt

# Crear el ejecutable de tests
add_executable(hestia_tests main.cpp)

# Enlazar con la librería del backend (ya definida arriba) y Catch2
# Catch2::Catch2WithMain incluye el main() por defecto, así que tu main.cpp puede estar vacío o tener lógica extra
target_link_libraries(hestia_tests 
    PRIVATE 
        hestia_backend 
        Catch2::Catch2WithMain
)

# Registrar el ejecutable como un test para CTest
include(CTest)
add_test(NAME HestiaBackendTests COMMAND hestia_tests)
