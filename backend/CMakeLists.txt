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

# Enlazar SQLite si usas PersistenceLayer (necesario en Linux)
find_package(SQLite3 REQUIRED)
target_link_libraries(hestia_backend PRIVATE SQLite::SQLite3)

# Tests: Si BUILD_TESTS es ON, entra al directorio de tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
