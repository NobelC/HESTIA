#!/bin/bash

# HESTIA Build Script
# Usage: ./scripts/build.sh [clean]

set -e

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"

if [ "$1" == "clean" ]; then
    echo "Cleaning build directory..."
    rm -rf "${BUILD_DIR}"
fi

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "Configuring with CMake..."
cmake .. -DBUILD_TESTS=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

echo "Building..."
cmake --build . --parallel $(nproc)

echo "Build complete!"
echo "Binaries available in ${BUILD_DIR}/backend"
