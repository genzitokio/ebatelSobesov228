// Простой JavaScript файл для renderer процесса
// Получаем доступ к ipcRenderer через window.require
const { ipcRenderer } = window.require("electron");

class StealthAssistantRenderer {
  constructor() {
    this.ui = {};
    this.isListening = false;
    this.currentProfile = "general";
    this.connectionStatus = "disconnected";
    this.responseHistory = [];

    // Состояние транскрипции
    this.transcriptionBuffer = "";
    this.isAutoSendEnabled = true;
    this.isProcessing = false;

    // Инициализация при загрузке DOM
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => {
        this.init();
      });
    } else {
      this.init();
    }
  }

  init() {
    console.log("🚀 Инициализация StealthAssistantRenderer...");
    this.initializeDOM();
    this.setupEventListeners();
    this.setupIPCListeners();
    this.updateUI();
  }

  initializeDOM() {
    console.log("🏗️ Инициализация DOM элементов...");

    // Получаем все элементы UI
    this.ui = {
      statusIndicator: this.getElementById("status-indicator"),
      connectionStatus: this.getElementById("connection-status"),
      currentProfile: this.getElementById("current-profile"),
      questionHistory: this.getElementById("question-history"),
      responseContainer: this.getElementById("response-container"),
      controlButtons: this.getElementById("control-buttons"),
      profileButtons: this.getElementById("profile-buttons"),
      manualInput: this.getElementById("manual-input"),
      sendButton: this.getElementById("send-button"),
      clearButton: this.getElementById("clear-button"),
      listeningToggle: this.getElementById("listening-toggle"),
      emergencyHide: this.getElementById("emergency-hide"),
      optimizeButton: this.getElementById("optimize-button"),
      simulateInput: this.getElementById("simulate-input"),
      simulateButton: this.getElementById("simulate-button"),
      // Новые элементы транскрипции
      transcriptionStatus: this.getElementById("transcription-status"),
      transcriptionText: this.getElementById("transcription-text"),
      autoSendToggle: this.getElementById("auto-send-toggle"),
      sendTranscription: this.getElementById("send-transcription"),
      clearTranscription: this.getElementById("clear-transcription"),
    };

    console.log("✅ DOM элементы инициализированы:", Object.keys(this.ui));

    // Инициализируем состояние транскрипции
    this.updateTranscriptionControlsOnly();
  }

  getElementById(id) {
    const element = document.getElementById(id);
    if (!element) {
      console.error(`❌ Элемент с ID '${id}' не найден!`);
      throw new Error(`Element with id '${id}' not found`);
    }
    console.log(`✅ Найден элемент: ${id}`);
    return element;
  }

  setupEventListeners() {
    console.log("🔧 Настройка обработчиков событий...");

    // Кнопки управления
    this.ui.listeningToggle.addEventListener("click", () => {
      console.log("🎤 Кнопка прослушивания нажата");
      this.toggleListening();
    });

    this.ui.emergencyHide.addEventListener("click", () => {
      console.log("🚨 Кнопка скрытия нажата");
      this.emergencyHide();
    });

    this.ui.optimizeButton.addEventListener("click", () => {
      console.log("⚡ Кнопка оптимизации нажата");
      this.optimizePerformance();
    });

    this.ui.clearButton.addEventListener("click", () => {
      console.log("🗑️ Кнопка очистки нажата");
      this.clearHistory();
    });

    this.ui.sendButton.addEventListener("click", () => {
      console.log("📤 Кнопка отправки нажата");
      this.sendManualQuestion();
    });

    // Симулировать речь
    this.ui.simulateButton.addEventListener("click", () => {
      console.log("🎭 Кнопка симуляции нажата");
      this.simulateSpeech();
    });

    // Обработчики транскрипции
    this.ui.autoSendToggle.addEventListener("change", () => {
      console.log(
        "🔄 Тоггл автоотправки изменен:",
        this.ui.autoSendToggle.checked
      );
      this.updateTranscriptionControls();
    });

    this.ui.sendTranscription.addEventListener("click", () => {
      console.log("🚀 Кнопка отправки транскрипции нажата");
      this.sendTranscriptionToAI();
    });

    this.ui.clearTranscription.addEventListener("click", () => {
      console.log("🗑️ Кнопка очистки транскрипции нажата");
      this.clearTranscriptionText();
    });

    // Ввод вопроса по Enter
    this.ui.manualInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.sendManualQuestion();
      }
    });

    // Симуляция речи по Enter
    this.ui.simulateInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.simulateSpeech();
      }
    });

    // Обработчик редактирования транскрипции
    this.ui.transcriptionText.addEventListener("input", () => {
      // Синхронизируем буфер с содержимым поля
      this.transcriptionBuffer = this.ui.transcriptionText.value;
      console.log(
        `✏️ Транскрипция отредактирована: "${this.transcriptionBuffer}"`
      );

      // Обновляем контролы без обновления display (чтобы не перезаписать ввод пользователя)
      this.updateTranscriptionControlsOnly();
    });

    // Кнопки профилей
    this.setupProfileButtons();

    // Горячие клавиши
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.shiftKey) {
        switch (e.key) {
          case "H":
            e.preventDefault();
            ipcRenderer.invoke("toggle-visibility");
            break;
          case "F12":
            e.preventDefault();
            this.emergencyHide();
            break;
          case "C":
            e.preventDefault();
            this.clearHistory();
            break;
        }
      }
    });
  }

  setupProfileButtons() {
    const profiles = [
      { id: "technical", name: "Техническое", color: "#3b82f6" },
      { id: "hr", name: "HR", color: "#10b981" },
      { id: "sales", name: "Продажи", color: "#f59e0b" },
      { id: "general", name: "Общие", color: "#8b5cf6" },
    ];

    profiles.forEach((profile) => {
      const button = document.createElement("button");
      button.className = "profile-button";
      button.textContent = profile.name;
      button.style.backgroundColor = profile.color;
      button.addEventListener("click", () => {
        this.changeProfile(profile.id);
      });
      this.ui.profileButtons.appendChild(button);
    });
  }

  setupIPCListeners() {
    console.log("📡 Настройка IPC слушателей...");

    // Ответы AI
    ipcRenderer.on("ai-response", (_event, data) => {
      console.log("📡 Получен ai-response:", data);
      if (data && data.question && data.answer) {
        console.log(
          `🎯 Обрабатываем AI ответ: "${
            data.question
          }" -> "${data.answer.substring(0, 100)}..."`
        );
        this.handleAIResponse(data);
      } else {
        console.warn("⚠️ Неверные данные ai-response:", data);
      }
    });

    // Статус подключения
    ipcRenderer.on("connection-status", (_event, data) => {
      this.connectionStatus = data.status;
      this.updateConnectionStatus();
    });

    // Статус прослушивания
    ipcRenderer.on("listening-status", (_event, data) => {
      console.log("📡 Получен listening-status:", data);
      if (data && data.status) {
        this.isListening = data.status === "started";
        this.updateListeningStatus();
      } else {
        console.warn("⚠️ Неверные данные listening-status:", data);
      }
    });

    // Смена профиля
    ipcRenderer.on("profile-changed", (_event, data) => {
      console.log("📡 Получен profile-changed:", data);
      if (data && data.profile) {
        this.currentProfile = data.profile;
        this.updateProfileIndicator();
      } else {
        console.warn("⚠️ Неверные данные profile-changed:", data);
      }
    });

    // Обновление системного статуса
    ipcRenderer.on("status-update", (_event, data) => {
      console.log("📡 Получен status-update:", data);
      if (data) {
        this.handleSystemStatus(data);
      } else {
        console.warn("⚠️ Неверные данные status-update:", data);
      }
    });

    // Подключение/отключение бэкенда
    ipcRenderer.on("backend-connected", () => {
      this.showNotification("Подключено к бэкенду", "success");
    });

    ipcRenderer.on("backend-disconnected", () => {
      this.showNotification("Соединение с бэкендом потеряно", "error");
    });

    // Очистка истории
    ipcRenderer.on("history-cleared", () => {
      this.responseHistory = [];
      this.updateQuestionHistory();
      this.showNotification("История очищена", "info");
    });

    // Оптимизация производительности
    ipcRenderer.on("performance-optimized", (_event, data) => {
      console.log("📡 Получен performance-optimized:", data);
      this.showNotification(
        data.message || "Производительность оптимизирована",
        "success"
      );
    });

    // Транскрипция речи
    ipcRenderer.on("speech-transcription", (_event, data) => {
      console.log("📡 Получена транскрипция:", data);
      if (data && data.text) {
        this.handleTranscriptionUpdate(data.text);
      } else {
        console.warn("⚠️ Неверные данные speech-transcription:", data);
      }
    });
  }

  handleAIResponse(data) {
    console.log("🤖 Обработка ответа AI:", data);

    const response = {
      id: Date.now().toString(),
      question: data.question,
      answer: data.answer,
      timestamp: new Date(),
      profile: this.currentProfile,
    };

    console.log(
      `📝 Добавляем в историю ответ (всего будет ${
        this.responseHistory.length + 1
      } ответов)`
    );
    this.responseHistory.unshift(response);

    console.log(`🎨 Отображаем ответ в UI`);
    this.displayResponse(response);

    console.log(`📋 Обновляем историю вопросов`);
    this.updateQuestionHistory();

    console.log(`✅ Обработка AI ответа завершена`);
  }

  displayResponse(response) {
    const responseElement = document.createElement("div");
    responseElement.className = "response-item";
    responseElement.innerHTML = `
      <div class="response-header">
        <span class="response-time">${response.timestamp.toLocaleTimeString()}</span>
        <span class="response-profile">${this.currentProfile}</span>
      </div>
      <div class="response-question">
        <strong>Вопрос:</strong> ${this.escapeHtml(response.question)}
      </div>
      <div class="response-answer">
        <strong>Ответ:</strong> ${this.formatAnswer(response.answer)}
      </div>
    `;

    this.ui.responseContainer.insertBefore(
      responseElement,
      this.ui.responseContainer.firstChild
    );

    // Ограничиваем количество отображаемых ответов
    while (this.ui.responseContainer.children.length > 5) {
      this.ui.responseContainer.removeChild(
        this.ui.responseContainer.lastChild
      );
    }
  }

  formatAnswer(answer) {
    // Простое форматирование с поддержкой списков и кода
    return answer
      .replace(/\n/g, "<br>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  updateQuestionHistory() {
    const historyHtml = this.responseHistory
      .slice(0, 10)
      .map(
        (response) => `
        <div class="history-item">
          <span class="history-time">${response.timestamp.toLocaleTimeString()}</span>
          <span class="history-question">${this.escapeHtml(
            response.question
          )}</span>
        </div>
      `
      )
      .join("");

    this.ui.questionHistory.innerHTML = historyHtml;
  }

  handleSystemStatus(status) {
    this.updateStatusIndicator(status);
  }

  updateStatusIndicator(status) {
    const allGood = status.backend && status.websocket && status.ai;
    this.ui.statusIndicator.className = `status-indicator ${
      allGood ? "connected" : "error"
    }`;
    this.ui.statusIndicator.textContent = allGood ? "●" : "⚠";
  }

  updateConnectionStatus() {
    const statusText = {
      connected: "Подключено",
      disconnected: "Отключено",
      connecting: "Подключение...",
      error: "Ошибка",
    };

    this.ui.connectionStatus.textContent = statusText[this.connectionStatus];
    this.ui.connectionStatus.className = `connection-status ${this.connectionStatus}`;
  }

  updateProfileIndicator() {
    const profileNames = {
      technical: "Техническое",
      hr: "HR",
      sales: "Продажи",
      general: "Общие",
    };

    this.ui.currentProfile.textContent = profileNames[this.currentProfile];
    this.ui.currentProfile.className = `current-profile ${this.currentProfile}`;

    // Обновляем активную кнопку профиля
    const profileButtons =
      this.ui.profileButtons.querySelectorAll(".profile-button");
    profileButtons.forEach((button, index) => {
      const profiles = ["technical", "hr", "sales", "general"];
      if (profiles[index] === this.currentProfile) {
        button.classList.add("active");
      } else {
        button.classList.remove("active");
      }
    });
  }

  updateUI() {
    this.updateConnectionStatus();
    this.updateListeningStatus();
    this.updateProfileIndicator();
    this.updateQuestionHistory();
  }

  // Методы управления
  async toggleListening() {
    console.log("🎤 Переключение прослушивания...");
    ipcRenderer.invoke("toggle-listening");
  }

  async emergencyHide() {
    console.log("🚨 Экстренное скрытие...");
    ipcRenderer.invoke("emergency-hide");
  }

  async clearHistory() {
    console.log("🗑️ Очистка истории...");
    ipcRenderer.invoke("clear-history");
  }

  async changeProfile(profile) {
    console.log(`🔄 Смена профиля на: ${profile}`);
    ipcRenderer.invoke("change-profile", profile);
  }

  async sendManualQuestion() {
    const question = this.ui.manualInput.value.trim();
    if (!question) {
      this.showNotification("Введите вопрос", "error");
      return;
    }

    console.log(`📤 Отправка вопроса: ${question}`);
    ipcRenderer.invoke("send-question", question);
    this.ui.manualInput.value = "";
  }

  async simulateSpeech() {
    const text = this.ui.simulateInput.value.trim();
    if (!text) {
      this.showNotification("Введите текст для симуляции", "error");
      return;
    }

    console.log(`🎭 Симуляция речи: ${text}`);
    ipcRenderer.invoke("simulate-speech", text);
    this.ui.simulateInput.value = "";
  }

  async optimizePerformance() {
    console.log("⚡ Оптимизируем производительность...");
    try {
      await ipcRenderer.invoke("optimize-performance");
      this.showNotification("Производительность оптимизирована", "success");
    } catch (error) {
      console.error("❌ Ошибка при оптимизации:", error);
      this.showNotification("Ошибка при оптимизации", "error");
    }
  }

  showNotification(message, type) {
    // Создаем уведомление
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Добавляем к body
    document.body.appendChild(notification);

    // Убираем через 3 секунды
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  // Методы для работы с транскрипцией
  handleTranscriptionUpdate(text) {
    console.log(`📝 Обновление транскрипции: "${text}"`);

    // Обновляем статус обработки
    this.setTranscriptionStatus("processing", "Обрабатываем речь...");

    // Проверяем состояние автоотправки НАПРЯМУЮ из checkbox
    const isAutoSendActive = this.ui.autoSendToggle.checked;
    console.log(`🔍 Проверка автоотправки: ${isAutoSendActive}`);

    if (isAutoSendActive) {
      console.log("🤖 Автоотправка включена - отправляем сразу в AI");
      // При автоотправке отправляем только текущую фразу
      this.sendTextDirectlyToAI(text);
    } else {
      console.log("⏸️ Автоотправка выключена - накапливаем текст");

      // Добавляем текст в буфер для накопления
      if (this.transcriptionBuffer) {
        this.transcriptionBuffer += " " + text;
      } else {
        this.transcriptionBuffer = text;
      }

      // Обновляем поле транскрипции
      this.updateTranscriptionDisplay();
      this.setTranscriptionStatus("ready", "Готово к отправке");
    }
  }

  setTranscriptionStatus(state, message) {
    const statusElement = this.ui.transcriptionStatus;
    statusElement.textContent = message;

    // Убираем все классы состояния
    statusElement.classList.remove("listening", "processing", "ready", "error");

    // Добавляем новый класс состояния
    if (state) {
      statusElement.classList.add(state);
    }

    console.log(`📊 Статус транскрипции: ${state} - ${message}`);
  }

  updateTranscriptionDisplay() {
    this.ui.transcriptionText.value = this.transcriptionBuffer;

    // Обновляем только контролы
    this.updateTranscriptionControlsOnly();
  }

  updateTranscriptionControls() {
    // Обновляем поле отображения и контролы
    this.updateTranscriptionDisplay();
  }

  updateTranscriptionControlsOnly() {
    // Обновляем только контролы без изменения поля
    const hasText = this.transcriptionBuffer.trim().length > 0;
    const autoSend = this.ui.autoSendToggle.checked;

    this.isAutoSendEnabled = autoSend;

    // Кнопка отправки активна только если есть текст и автоотправка выключена
    this.ui.sendTranscription.disabled = !hasText || autoSend;

    // Кнопка очистки активна только если есть текст
    this.ui.clearTranscription.disabled = !hasText;

    // Обновляем визуальные стили поля
    if (this.transcriptionBuffer) {
      this.ui.transcriptionText.classList.add("has-text");
    } else {
      this.ui.transcriptionText.classList.remove("has-text");
    }

    console.log(
      `🎛️ Обновлены контролы транскрипции: текст=${hasText}, авто=${autoSend}`
    );
  }

  async sendTextDirectlyToAI(text) {
    console.log(`🚀 Прямая отправка в AI: "${text}"`);

    // Устанавливаем статус обработки
    this.setTranscriptionStatus("processing", "Отправляем в AI...");

    try {
      // Отправляем через IPC
      await ipcRenderer.invoke("send-question", text);

      // НЕ очищаем транскрипцию при автоотправке - просто показываем статус
      this.setTranscriptionStatus("ready", "Ответ получен!");

      // Через 2 секунды возвращаем обычный статус
      setTimeout(() => {
        if (this.isListening) {
          this.setTranscriptionStatus("listening", "🎤 Слушаю...");
        } else {
          this.setTranscriptionStatus("ready", "Готов к прослушиванию");
        }
      }, 2000);
    } catch (error) {
      console.error("❌ Ошибка при отправке текста:", error);
      this.setTranscriptionStatus("error", "Ошибка отправки");
      this.showNotification("Ошибка при отправке в AI", "error");
    }
  }

  async sendTranscriptionToAI() {
    if (!this.transcriptionBuffer.trim()) {
      console.warn("⚠️ Нет текста для отправки");
      return;
    }

    console.log(
      `🚀 Отправляем накопленную транскрипцию в AI: "${this.transcriptionBuffer}"`
    );

    // Устанавливаем статус обработки
    this.setTranscriptionStatus("processing", "Отправляем в AI...");

    try {
      // Отправляем через IPC
      await ipcRenderer.invoke("send-question", this.transcriptionBuffer);

      // Очищаем транскрипцию после отправки (только в ручном режиме)
      this.clearTranscriptionText();

      this.setTranscriptionStatus("ready", "Ответ получен!");

      // Через 2 секунды возвращаем обычный статус
      setTimeout(() => {
        this.setTranscriptionStatus("ready", "Готов к прослушиванию");
      }, 2000);
    } catch (error) {
      console.error("❌ Ошибка при отправке транскрипции:", error);
      this.setTranscriptionStatus("error", "Ошибка отправки");
      this.showNotification("Ошибка при отправке в AI", "error");
    }
  }

  clearTranscriptionText() {
    console.log("🗑️ Очищаем транскрипцию");
    this.transcriptionBuffer = "";
    this.updateTranscriptionDisplay();
    this.setTranscriptionStatus("ready", "Готов к прослушиванию");
  }

  updateListeningStatus() {
    // Обновляем основную кнопку
    const button = this.ui.listeningToggle;
    const statusElement = this.ui.statusIndicator;

    if (this.isListening) {
      button.textContent = "⏸️ Остановить прослушивание";
      button.classList.add("active");
      statusElement.textContent = "Прослушивание...";
      statusElement.className = "status-listening";

      // Обновляем статус транскрипции
      this.setTranscriptionStatus("listening", "🎤 Слушаю...");
    } else {
      button.textContent = "▶️ Начать прослушивание";
      button.classList.remove("active");
      statusElement.textContent = "Готов к работе";
      statusElement.className = "status-ready";

      // Обновляем статус транскрипции
      this.setTranscriptionStatus("ready", "Готов к прослушиванию");
    }
  }
}

// Создаем экземпляр приложения
console.log("🚀 Создание экземпляра StealthAssistantRenderer...");
const app = new StealthAssistantRenderer();
