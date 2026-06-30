@echo off
setlocal enabledelayedexpansion

echo ===========================================
echo    Configurando HESTIA (Windows)     
echo ===========================================

echo [1/4] Verificando dependencias del sistema...
where cmake >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] CMake no encontrado. Por favor instala CMake y agregalo al PATH.
    exit /b 1
)
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python no encontrado. Por favor instala Python 3 y agregalo al PATH.
    exit /b 1
)

echo [2/4] Creando y activando entorno virtual de Python...
python -m venv venv
call venv\Scripts\activate.bat

echo [3/4] Instalando dependencias de Python...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Compilando motor C++ (HESTIA Core)...
if not exist "build" mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j %NUMBER_OF_PROCESSORS%
cd ..

echo ===========================================
echo HESTIA configurado exitosamente!
echo.
echo Para arrancar la interfaz grafica ejecuta:
echo   call venv\Scripts\activate.bat
echo   python frontend\run_hestia.py
echo.
echo Para arrancar el Simulation Lab ejecuta:
echo   call venv\Scripts\activate.bat
echo   python -m frontend.sim_lab
echo ===========================================
