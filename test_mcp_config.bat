@echo off
echo Тестирование конфигурации MCP серверов...
echo.

echo Проверка наличия mcp-servers.json...
if exist mcp-servers.json (
    echo ✅ Конфигурационный файл найден
) else (
    echo ❌ Конфигурационный файл не найден
    echo Скопируйте mcp-servers.json.example в mcp-servers.json и настройте токены
    pause
    exit /b 1
)

echo.
echo Проверка GitHub токена...
findstr /C:"YOUR_GITHUB_TOKEN_HERE" mcp-servers.json >nul
if %errorlevel% equ 0 (
    echo ⚠️ GitHub токен не настроен
    echo Замените YOUR_GITHUB_TOKEN_HERE на ваш токен
) else (
    echo ✅ GitHub токен настроен
)

echo.
echo Проверка установленных пакетов...
npm list -g @modelcontextprotocol/server-filesystem 2>nul | findstr "@modelcontextprotocol/server-filesystem" >nul
if %errorlevel% equ 0 (
    echo ✅ Filesystem MCP установлен
) else (
    echo ❌ Filesystem MCP не установлен
)

npm list -g @modelcontextprotocol/server-github 2>nul | findstr "@modelcontextprotocol/server-github" >nul
if %errorlevel% equ 0 (
    echo ✅ GitHub MCP установлен
) else (
    echo ❌ GitHub MCP не установлен
)

npm list -g @modelcontextprotocol/server-puppeteer 2>nul | findstr "@modelcontextprotocol/server-puppeteer" >nul
if %errorlevel% equ 0 (
    echo ✅ Puppeteer MCP установлен
) else (
    echo ❌ Puppeteer MCP не установлен
)

echo.
echo Запуск MCP Inspector для тестирования...
echo Нажмите Ctrl+C для остановки
echo.
npx @modelcontextprotocol/inspector

pause 