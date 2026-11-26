@echo off
REM ==========================================================
REM  Executa o pseudo-SO no Windows (duplo clique neste arquivo)
REM  Sem argumentos: usa o exemplo do enunciado.
REM  Com argumentos: executar.bat processes.txt files.txt string.txt
REM ==========================================================
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON=python
where py >nul 2>nul
if %errorlevel%==0 set PYTHON=py -3

if "%~1"=="" (
    %PYTHON% dispatcher.py processes.txt files.txt string.txt
) else (
    %PYTHON% dispatcher.py %*
)
echo.
pause
