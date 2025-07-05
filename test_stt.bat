@echo off
title Тест RealtimeSTT
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                    ТЕСТ RealtimeSTT                      ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [INFO] Запуск тестирования RealtimeSTT...
echo.

:: Активируем виртуальное окружение
echo [1/2] Активация виртуального окружения...
call backend\venv\Scripts\activate.bat

:: Запускаем тест
echo [2/2] Запуск тестирования...
echo.
echo 🎙️ Подготовьтесь говорить в микрофон!
echo ⏰ Тест запустится через 3 секунды...
echo.
timeout /t 3 /nobreak > nul

python test_realtime_stt.py

echo.
echo ✅ Тестирование завершено!
pause 