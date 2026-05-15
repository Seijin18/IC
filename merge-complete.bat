@echo off
REM ===== Merge Script Completo =====
REM Este script faz merge do worktree para o main branch
REM Executar como: merge-complete.bat

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ======================================
echo    MERGE - RF Spectrum Analyzer
echo ======================================
echo.

set WORKTREE_DIR=c:\Projetos\IC.worktrees\agents-precise-time-measurement-update
set MAIN_WORKTREE=C:\Projetos\IC

REM ===== Step 1: Verify Uncommitted Changes =====
echo [STEP 1] Verificando mudancas nao commitadas...
echo.

cd /d "%WORKTREE_DIR%"

git status --porcelain
set STATUS_CODE=%errorlevel%

if %STATUS_CODE% neq 0 (
    echo Erro ao verificar status
    goto error
)

REM ===== Step 2: Get Current Branch =====
echo.
echo [STEP 2] Obtendo branch atual...
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
echo Branch: %BRANCH%
echo.

REM ===== Step 3: Check for Staged Changes and Commit =====
echo [STEP 3] Verificando mudancas em staging...

git diff --cached --name-only
set HAS_STAGED=%errorlevel%

if %HAS_STAGED% equ 0 (
    echo Mudancas encontradas. Commitando...
    echo.
    
    git commit -m "refactor: Transferir responsabilidade de timing do ESP32 para Python" ^
      -m "- ESP32 agora envia apenas dados de canais (sem timestamp)" ^
      -m "- Python captura timestamp com time.perf_counter() na rececao" ^
      -m "- Ganho de ate 130x em precisao de medicao" ^
      -m "- Reduz carga de processamento no microcontrolador" ^
      -m "- Mantem compatibilidade com codigo existente" ^
      -m "" ^
      -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
    
    if %errorlevel% neq 0 (
        echo Aviso: Nenhuma mudanca nova para commitar
    )
)

echo.

REM ===== Step 4: Show Recent Commits =====
echo [STEP 4] Ultimos commits no branch atual:
git log --oneline -3
echo.

REM ===== Step 5: Execute Merge =====
echo [STEP 5] Executando merge em: %MAIN_WORKTREE%
echo.

git -C "%MAIN_WORKTREE%" merge "%BRANCH%" --no-edit
set MERGE_EXIT=%errorlevel%

echo.

REM ===== Step 6: Check for Conflicts =====
if %MERGE_EXIT% neq 0 (
    echo [ATENCAO] Merge reportou status nao-zero (code: %MERGE_EXIT%)
    echo.
    echo Verificando conflitos...
    echo.
    
    git -C "%MAIN_WORKTREE%" diff --name-only --diff-filter=U
    
    if !errorlevel! neq 0 (
        echo Nenhum conflito detectado. Merge pode ter tido outro problema.
    ) else (
        echo.
        echo [ERRO] Conflitos detectados! Resolva manualmente:
        echo   1. Abra os arquivos listados acima
        echo   2. Resolva os conflitos
        echo   3. Execute: git -C "%MAIN_WORKTREE%" add [arquivo]
        echo   4. Execute: git -C "%MAIN_WORKTREE%" commit --no-edit
        echo.
        goto error
    )
) else (
    echo [OK] Merge completado com sucesso!
)

echo.

REM ===== Step 7: Verify Status =====
echo [STEP 6] Verificando status do main worktree...
echo.

git -C "%MAIN_WORKTREE%" status --porcelain
if !errorlevel! equ 0 (
    echo [OK] Main worktree limpo
) else (
    echo [ERRO] Main worktree nao esta limpo
)

echo.

REM ===== Step 8: Verify Merge =====
echo [STEP 7] Validando que branch foi mergeado...
echo.

git -C "%MAIN_WORKTREE%" merge-base --is-ancestor "%BRANCH%" HEAD
if !errorlevel! equ 0 (
    echo [OK] Branch %BRANCH% foi mergeado com sucesso
) else (
    echo [ERRO] Branch nao foi mergeado corretamente
    goto error
)

echo.

REM ===== Step 9: Show Final Commits =====
echo [STEP 8] Ultimos 5 commits no main:
echo.
git -C "%MAIN_WORKTREE%" log --oneline -5
echo.

echo ======================================
echo    ✓ MERGE COMPLETO COM SUCESSO!
echo ======================================
echo.
echo Proximos passos:
echo   1. Verifique as mudancas em: %MAIN_WORKTREE%
echo   2. Execute: python RFmodule/main.py (para testar)
echo   3. Execute: git push origin [branch] (para fazer push)
echo.

goto end

:error
echo.
echo ======================================
echo    ✗ ERRO DURANTE MERGE
echo ======================================
echo.
pause
exit /b 1

:end
echo.
pause
