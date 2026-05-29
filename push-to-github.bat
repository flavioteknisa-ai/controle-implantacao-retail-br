@echo off
REM Script para fazer push do código para GitHub

setlocal enabledelayedexpansion

echo.
echo ====================================
echo  DEPLOY: Push para GitHub
echo ====================================
echo.

REM Verificar se está em um repositório git
if not exist .git (
    echo ❌ Este diretório NÃO é um repositório Git
    echo.
    echo Inicializando repositório...
    git init
    git remote add origin %1
    if errorlevel 1 (
        echo.
        echo ❌ ERRO: Você precisa fornecer a URL do repositório
        echo Uso: push-to-github.bat https://github.com/seu-usuario/seu-repo.git
        pause
        exit /b 1
    )
)

REM Adicionar todos os arquivos
echo 📝 Adicionando arquivos...
git add .

REM Criar commit
set /p MESSAGE="📋 Mensagem do commit (padrão: Update): "
if "!MESSAGE!"=="" set MESSAGE=Update

echo 💾 Criando commit: !MESSAGE!
git commit -m "!MESSAGE!"

REM Push
echo 🚀 Fazendo push...
git push -u origin main

if errorlevel 0 (
    echo.
    echo ✅ SUCESSO! Código enviado para GitHub
    echo.
    echo Próximos passos:
    echo 1. Vá para Vercel e faça deploy automático
    echo 2. Ou execute: python migrate_to_supabase.py
    echo.
) else (
    echo.
    echo ❌ ERRO no push!
    echo.
)

pause
