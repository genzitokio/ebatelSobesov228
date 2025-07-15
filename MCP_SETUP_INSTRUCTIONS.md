# Инструкции по настройке MCP серверов

## Установленные пакеты

✅ @modelcontextprotocol/server-filesystem - работа с файловой системой
✅ @modelcontextprotocol/server-github - работа с GitHub репозиториями
✅ @modelcontextprotocol/server-postgres - работа с PostgreSQL
✅ @modelcontextprotocol/server-puppeteer - автоматизация браузера
✅ @executeautomation/playwright-mcp-server - автоматизация браузера через Playwright
✅ mcp-framework - фреймворк для создания MCP серверов

## Конфигурационный файл

Создан файл `mcp-servers.json` с базовой конфигурацией.

## Необходимые настройки

### 1. GitHub Personal Access Token

Для работы с GitHub сервером нужно создать токен:

1. Перейдите на https://github.com/settings/tokens
2. Нажмите "Generate new token" → "Generate new token (classic)"
3. Выберите scopes:
   - `repo` - для работы с репозиториями
   - `read:org` - для чтения информации об организации
   - `read:user` - для чтения информации о пользователе
4. Скопируйте токен
5. Замените `YOUR_GITHUB_TOKEN_HERE` в файле `mcp-servers.json` на ваш токен

### 2. PostgreSQL (опционально)

Если вы используете PostgreSQL, замените строку подключения:

```json
"postgresql://username:password@localhost:5432/database"
```

### 3. Файловая система

Путь к файловой системе настроен на вашу текущую рабочую директорию:

```
C:\Users\refla\ebatelSobesov228
```

## Пакеты не найдены в npm

❌ @modelcontextprotocol/server-fetch - не найден
❌ @joshuasundance/docker-mcp - не найден
❌ @modelcontextprotocol/server-git - не найден

## Альтернативы

- Вместо fetch можете использовать mcp-framework для создания собственного HTTP сервера
- Для Docker попробуйте поискать другие пакеты или создать собственный сервер
- Для Git можете использовать встроенные команды через filesystem сервер

## Тестирование

После настройки токена вы можете протестировать конфигурацию в совместимом с MCP клиенте (например, Claude Desktop).

## Предупреждения

Некоторые пакеты помечены как deprecated, но все еще работают:

- @modelcontextprotocol/server-github
- @modelcontextprotocol/server-postgres
- @modelcontextprotocol/server-puppeteer

## Безопасность

⚠️ Никогда не коммитьте файл с токеном в git! Добавьте `mcp-servers.json` в `.gitignore`
