@echo off
title Compilando SistemaIdentidad...
echo ================================================
echo   Compilador - Sistema de Identidad Digital
echo ================================================
echo.

REM Verificar que Python este instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Descargalo desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo [2/3] Compilando la aplicacion...
python -m PyInstaller main.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Fallo la compilacion.
    pause
    exit /b 1
)

echo [3/3] Listo!
echo.
echo La aplicacion se genero en: dist\SistemaIdentidad\
echo Ejecuta:  dist\SistemaIdentidad\SistemaIdentidad.exe
echo.
echo Para distribuir la app, comparte TODA la carpeta dist\SistemaIdentidad\
echo (no solo el .exe, necesita todos los archivos de esa carpeta)
echo.
pause
