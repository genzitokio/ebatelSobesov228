// Главный процесс Electron - простая JavaScript версия
const {
  app,
  BrowserWindow,
  globalShortcut,
  ipcMain,
  dialog,
} = require("electron");
const path = require("path");
const WebSocket = require("ws");

// Конфигурация разработки
const devConfig = {
  isDev: true,
  showDevTools: true,
  enableLogging: true,
  mockSpeechProcessor: false,
};

class StealthAssistantApp {
  constructor() {
    this.mainWindow = null;
    this.websocket = null;
    this.isVisible = false;
    this.isListening = false;
    this.connectionStatus = "disconnected";
    this.settings = {
      alwaysOnTop: true,
      transparent: true,
      position: { x: 100, y: 100 },
      size: { width: 800, height: 600 },
      profile: "general",
      autoHideDelay: 10000,
    };
    this.reconnectTimer = null;
    this.hideTimer = null;
    this.init();
  }

  init() {
    // Готовность приложения
    app.whenReady().then(() => {
      this.createWindow();
      this.setupGlobalShortcuts();
      this.connectToBackend();
      this.setupIPC();

      // Для macOS
      app.on("activate", () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          this.createWindow();
        }
      });
    });

    // Все окна закрыты
    app.on("window-all-closed", () => {
      if (process.platform !== "darwin") {
        app.quit();
      }
    });

    // Перед выходом
    app.on("before-quit", () => {
      this.cleanup();
    });
  }

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: this.settings.size.width,
      height: this.settings.size.height,
      x: this.settings.position.x,
      y: this.settings.position.y,

      // Настройки окна для разработки
      alwaysOnTop: devConfig.isDev ? false : this.settings.alwaysOnTop,
      transparent: devConfig.isDev ? false : this.settings.transparent,
      frame: devConfig.isDev ? true : false,
      skipTaskbar: devConfig.isDev ? false : true,

      // Включаем node интеграцию для доступа к require
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        backgroundThrottling: false,
      },

      // Дополнительные настройки
      show: true,
      focusable: true,
      minimizable: true,
      maximizable: true,
      resizable: true,
      minWidth: 400,
      minHeight: 300,

      // Заголовок окна
      title: devConfig.isDev
        ? "Stealth AI Assistant - DEV"
        : "System Background Process",
    });

    // Защита от захвата экрана
    this.mainWindow.setContentProtection(true);

    // Загружаем HTML
    this.mainWindow.loadFile(path.join(__dirname, "index.html"));

    // Отключаем меню
    this.mainWindow.setMenuBarVisibility(false);

    // Обработчики окна
    this.mainWindow.on("closed", () => {
      this.mainWindow = null;
    });

    // Показываем DevTools для отладки
    if (devConfig.isDev && devConfig.showDevTools) {
      this.mainWindow.webContents.openDevTools();
      this.mainWindow.show();
      this.isVisible = true;
    }

    this.log("🖥️  Stealth окно создано");
  }

  setupGlobalShortcuts() {
    const shortcuts = [
      {
        key: "Ctrl+Shift+H",
        action: () => this.toggleVisibility(),
        desc: "Показать/скрыть",
      },
      {
        key: "Ctrl+Shift+F12",
        action: () => this.emergencyHide(),
        desc: "Экстренное скрытие",
      },
      {
        key: "Ctrl+Shift+1",
        action: () => this.changeProfile("technical"),
        desc: "Техническое интервью",
      },
      {
        key: "Ctrl+Shift+2",
        action: () => this.changeProfile("hr"),
        desc: "HR интервью",
      },
      {
        key: "Ctrl+Shift+3",
        action: () => this.changeProfile("sales"),
        desc: "Продажи",
      },
      {
        key: "Ctrl+Shift+4",
        action: () => this.changeProfile("general"),
        desc: "Общие вопросы",
      },
      {
        key: "Ctrl+Shift+C",
        action: () => this.clearHistory(),
        desc: "Очистить историю",
      },
    ];

    shortcuts.forEach(({ key, action, desc }) => {
      const success = globalShortcut.register(key, action);
      if (success) {
        this.log(`⌨️  ${key} - ${desc}`);
      } else {
        this.log(`❌ Не удалось зарегистрировать: ${key}`);
      }
    });
  }

  connectToBackend() {
    const wsUrl = "ws://127.0.0.1:8765";
    this.log(`🔌 Подключение к бэкенду: ${wsUrl}`);

    try {
      this.websocket = new WebSocket(wsUrl);

      this.websocket.on("open", () => {
        this.log("🎉 Подключено к бэкенду!");
        this.connectionStatus = "connected";
        this.sendToRenderer("backend-connected", {});
        this.sendToRenderer("connection-status", { status: "connected" });

        // Сбрасываем таймер переподключения
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      });

      this.websocket.on("message", (data) => {
        try {
          const message = JSON.parse(data.toString());
          this.handleBackendMessage(message);
        } catch (error) {
          this.log(`❌ Ошибка парсинга сообщения: ${error.message}`);
        }
      });

      this.websocket.on("close", () => {
        this.log("🔌 Соединение с бэкендом потеряно");
        this.connectionStatus = "disconnected";
        this.sendToRenderer("backend-disconnected", {});
        this.sendToRenderer("connection-status", { status: "disconnected" });
        this.scheduleReconnect();
      });

      this.websocket.on("error", (error) => {
        this.log(`❌ Ошибка WebSocket: ${error.message}`);
        this.connectionStatus = "error";
        this.sendToRenderer("connection-status", { status: "error" });
        this.scheduleReconnect();
      });
    } catch (error) {
      this.log(`❌ Ошибка создания WebSocket: ${error.message}`);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.log("🔄 Попытка переподключения...");
      this.connectToBackend();
    }, 5000);
  }

  handleBackendMessage(message) {
    this.log(`📨 Сообщение от бэкенда: ${JSON.stringify(message)}`);

    switch (message.type) {
      case "welcome":
        this.log(`🎉 Подключено к бэкенду: ${message.message}`);
        break;
      case "ai_response":
        // Backend отправляет: { type: "ai_response", question: "...", answer: "...", timestamp: ... }
        this.log(
          `🤖 Получен ответ AI: вопрос="${message.question}", ответ длиной ${
            message.answer?.length || 0
          } символов`
        );
        this.sendToRenderer("ai-response", {
          question: message.question,
          answer: message.answer,
          timestamp: message.timestamp,
        });
        this.log(`📡 Отправлено в renderer: ai-response`);
        break;
      case "speech_transcription":
        // Backend отправляет: { type: "speech_transcription", text: "...", timestamp: ... }
        this.log(`🎤 Получена транскрипция: "${message.text}"`);
        this.sendToRenderer("speech-transcription", {
          text: message.text,
          timestamp: message.timestamp,
        });
        this.log(`📡 Отправлено в renderer: speech-transcription`);
        break;
      case "listening_status":
        // Backend отправляет: { type: "listening_status", status: "started" }
        this.isListening = message.status === "started";
        this.sendToRenderer("listening-status", {
          status: message.status,
        });
        break;
      case "profile_changed":
        // Backend отправляет: { type: "profile_changed", profile: "technical" }
        this.sendToRenderer("profile-changed", {
          profile: message.profile,
        });
        break;
      case "system_status":
        // Backend отправляет: { type: "status", speech_processor: {...}, ... }
        this.sendToRenderer("status-update", {
          backend: true,
          websocket: true,
          speech: message.speech_processor
            ? message.speech_processor.is_listening
            : false,
          ai: true,
        });
        break;
      case "history_cleared":
        this.log("📝 История очищена");
        this.sendToRenderer("history-cleared", {});
        break;
      case "performance_optimized":
        this.log("⚡ Производительность оптимизирована");
        this.sendToRenderer("performance-optimized", {
          message: message.message || "Производительность оптимизирована",
        });
        break;
      default:
        this.log(`❓ Неизвестное сообщение: ${message.type}`);
    }
  }

  sendToRenderer(channel, data) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send(channel, data);
    }
  }

  sendToBackend(message) {
    this.log(`📡 Отправка в backend: ${JSON.stringify(message)}`);
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
      this.log("✅ Сообщение отправлено в WebSocket");
    } else {
      this.log("❌ WebSocket не подключен");
    }
  }

  setupIPC() {
    // Обработчики IPC от renderer процесса
    ipcMain.handle("toggle-visibility", () => {
      this.log("🔄 IPC: toggle-visibility");
      this.toggleVisibility();
    });

    ipcMain.handle("emergency-hide", () => {
      this.log("🚨 IPC: emergency-hide");
      this.emergencyHide();
    });

    ipcMain.handle("clear-history", () => {
      this.log("🗑️ IPC: clear-history");
      this.clearHistory();
    });

    ipcMain.handle("change-profile", (event, profile) => {
      this.log(`🔄 IPC: change-profile to ${profile}`);
      this.changeProfile(profile);
    });

    ipcMain.handle("send-question", (event, question) => {
      this.log(`📤 IPC: send-question - "${question}"`);
      this.sendToBackend({ type: "manual_question", question: question });
    });

    ipcMain.handle("toggle-listening", () => {
      this.log(
        `🎤 IPC: toggle-listening (текущее состояние: ${this.isListening})`
      );
      // Переключаем между start и stop
      if (this.isListening) {
        this.log("🔇 Отправляем команду остановки прослушивания");
        this.sendToBackend({ type: "stop_listening" });
        // НЕ изменяем this.isListening здесь - ждем ответа от backend
      } else {
        this.log("🎤 Отправляем команду запуска прослушивания");
        this.sendToBackend({ type: "start_listening" });
        // НЕ изменяем this.isListening здесь - ждем ответа от backend
      }
    });

    ipcMain.handle("simulate-speech", (event, text) => {
      this.log(`🎭 IPC: simulate-speech - "${text}"`);
      this.sendToBackend({ type: "simulate_speech", text: text });
    });

    ipcMain.handle("optimize-performance", () => {
      this.log("⚡ IPC: optimize-performance");
      this.sendToBackend({ type: "optimize_performance" });
    });
  }

  toggleVisibility() {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  show() {
    if (this.mainWindow) {
      this.mainWindow.show();
      this.mainWindow.focus();
      this.isVisible = true;
    }
  }

  hide() {
    if (this.mainWindow) {
      this.mainWindow.hide();
      this.isVisible = false;
    }
  }

  emergencyHide() {
    this.hide();
    this.log("🚨 Экстренное скрытие выполнено");
  }

  changeProfile(profile) {
    this.settings.profile = profile;
    this.sendToBackend({ type: "set_profile", profile: profile });
    this.log(`🔄 Профиль изменен на: ${profile}`);
  }

  clearHistory() {
    this.sendToBackend({ type: "clear_history" });
    this.log("🗑️ Запрос очистки истории отправлен");
  }

  cleanup() {
    if (this.websocket) {
      this.websocket.close();
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.hideTimer) {
      clearTimeout(this.hideTimer);
    }
    globalShortcut.unregisterAll();
  }

  log(message) {
    if (devConfig.enableLogging) {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`[${timestamp}] ${message}`);
    }
  }
}

// Создаем экземпляр приложения
console.log("🚀 Stealth AI Assistant запущен (JavaScript)");
const stealthApp = new StealthAssistantApp();
