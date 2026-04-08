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

# Expone los headers publicos
target_include_directories(hestia_backend
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Fuerza C++20 en este target
target_compile_features(hestia_backend PUBLIC cxx_std_20)

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
