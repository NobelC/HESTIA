# backend/CMakeLists.txt

# Libreria estatica con todo el backend
add_library(hestia_backend STATIC
    src/BKTEngine.cpp
    src/MABEngine.cpp
    src/PersistenceLayer.cpp
    src/ResponseProcessor.cpp
    src/SessionManager.cpp
    src/SkillGraph.cpp
    src/SRSQueue.cpp
    src/ZoneBlender.cpp
)

# Expone los headers publicos a quien enlace con esta librería
target_include_directories(hestia_backend
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Fuerza C++20 en este target
target_compile_features(hestia_backend PUBLIC cxx_std_20)

# Requerido para enlazar con PyBind11 (shared library)
set_target_properties(hestia_backend PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Enlazar SQLite si usas PersistenceLayer (necesario en Linux)
find_package(SQLite3 REQUIRED)
target_link_libraries(hestia_backend PRIVATE SQLite3::SQLite3 nlohmann_json::nlohmann_json)

# Tests: Si BUILD_TESTS es ON, entra al directorio de tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# PyBind11 Module
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
pybind11_add_module(hestia_core src/bindings.cpp)
target_link_libraries(hestia_core PRIVATE hestia_backend)
# Ensure the module is compiled with C++20
target_compile_features(hestia_core PRIVATE cxx_std_20)

# Simulation Targets
add_executable(monte_carlo ${CMAKE_SOURCE_DIR}/simulation/monte_carlo.cpp)
target_link_libraries(monte_carlo PRIVATE hestia_backend)

add_executable(stress_bot ${CMAKE_SOURCE_DIR}/simulation/stress_bot.cpp)
target_link_libraries(stress_bot PRIVATE hestia_backend)
