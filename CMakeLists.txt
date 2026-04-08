cmake_minimum_required(VERSION 3.20)
project(HESTIA VERSION 1.0.0 LANGUAGES CXX)

# C++20 obligatorio
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Genera compile_commands.json automaticamente para LSP
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Opciones
option(BUILD_TESTS "Compilar tests unitarios" ON)

# --- FetchContent para Catch2 (Automático, sin instalar nada en el sistema) ---
include(FetchContent)
if(BUILD_TESTS)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.4.0  # Versión estable reciente
    )
    FetchContent_MakeAvailable(Catch2)
endif()

enable_testing()

# Subdirectorio principal (Backend)
add_subdirectory(backend)

# Target opcional para formatear todo el código C++ con clang-format
find_program(CLANG_FORMAT clang-format)
if(CLANG_FORMAT)
    file(GLOB_RECURSE CPP_FILES "${CMAKE_SOURCE_DIR}/backend/include/*.hpp" "${CMAKE_SOURCE_DIR}/backend/src/*.cpp")
    add_custom_target(format
        COMMAND ${CLANG_FORMAT} -i -style=file ${CPP_FILES}
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Formateando código C++ con clang-format"
    )
endif()
