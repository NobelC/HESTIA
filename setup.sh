#!/bin/bash
set -e

echo "==========================================="
echo "   Configurando HESTIA (Linux / macOS)     "
echo "==========================================="

echo "[1/4] Verificando dependencias del sistema..."
if ! command -v cmake &> /dev/null; then
    echo "❌ CMake no encontrado. Por favor instala CMake (ej. sudo apt install cmake)."
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado."
    exit 1
fi

echo "[2/4] Creando y activando entorno virtual de Python..."
python3 -m venv venv
source venv/bin/activate

echo "[3/4] Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Compilando motor C++ (HESTIA Core)..."
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc 2>/dev/null || echo 4)
cd ..

echo "==========================================="
echo "✅ HESTIA configurado exitosamente!"
echo ""
echo "Para arrancar la interfaz gráfica ejecuta:"
echo "  source venv/bin/activate"
echo "  python frontend/run_hestia.py"
echo ""
echo "Para arrancar el Simulation Lab ejecuta:"
echo "  source venv/bin/activate"
echo "  python -m frontend.sim_lab"
echo "==========================================="
