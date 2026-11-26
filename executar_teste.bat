@echo off
REM Executa o cenario de teste extra (processos de usuario, recursos e memoria)
chcp 65001 >nul
cd /d "%~dp0"
set PYTHON=python
where py >nul 2>nul
if %errorlevel%==0 set PYTHON=py -3
%PYTHON% dispatcher.py testes\processes.txt testes\files.txt testes\string.txt
echo.
pause
