@echo off
title Stealth AI Assistant
color 0A

echo.
echo  ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
echo  ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
echo  ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
echo  ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
echo  ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
echo  ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
echo.
echo                    AI ASSISTANT FOR INTERVIEWS
echo.

:: Устанавливаем API ключ
set PROXYAPI_KEY=sk-yseNQGJXYUnn4YjrnwNJnwW7bsnwFg8K

:: Переходим в корень проекта
cd /d "%~dp0"

echo [INFO] Запуск системы...
echo.

:: Запуск Python бэкенда в фоновом режиме
echo [1/2] Запуск Python бэкенда...
start "Stealth Backend" /min cmd /c "set PROXYAPI_KEY=%PROXYAPI_KEY% && backend\venv\Scripts\activate.bat && python backend\main.py"

:: Ждем 3 секунды для запуска бэкенда
timeout /t 3 /nobreak > nul

:: Компилируем TypeScript если нужно
echo [2/2] Подготовка фронтенда...
cd frontend
if not exist "dist\main.js" (
    echo Компилируем TypeScript...
    npm run compile > nul 2>&1
)

:: Запуск Electron фронтенда
echo Запуск Electron...
npm start

:: При закрытии фронтенда убиваем все связанные процессы
echo.
echo [INFO] Завершение работы...
taskkill /f /im python.exe > nul 2>&1
taskkill /f /im electron.exe > nul 2>&1

echo [INFO] Система остановлена
pause 