@echo off
REM Script para iniciar o Sistema de Controle de Férias

echo.
echo ========================================
echo   Sistema de Controle de Ferias
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: Python nao foi encontrado!
    echo Por favor, instale Python 3.8+
    pause
    exit /b 1
)

REM Verifica se requirements.txt existe
if not exist requirements.txt (
    echo Erro: requirements.txt nao foi encontrado!
    pause
    exit /b 1
)

REM Instala dependências
echo Instalando dependencias...
pip install -r requirements.txt

REM Inicia a aplicação
echo.
echo Iniciando aplicacao...
echo Acesse: http://localhost:5000
echo.
python app.py
