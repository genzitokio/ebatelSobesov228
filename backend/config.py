import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # ProxyAPI настройки
    PROXY_API_BASE_URL: str = "https://api.proxyapi.ru/openai/v1"
    PROXYAPI_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000
    
    # WebSocket настройки
    WEBSOCKET_HOST: str = "localhost"
    WEBSOCKET_PORT: int = 8765
    
    # Аудио настройки
    SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 1024
    AUDIO_BUFFER_DURATION: int = 15  # секунд
    
    # Whisper настройки
    WHISPER_MODEL: str = "base"
    WHISPER_LANGUAGE: str = "ru"
    WHISPER_DEVICE: str = "auto"  # auto, cpu, cuda
    
    # VAD настройки
    VAD_THRESHOLD: float = 0.5
    SILENCE_DURATION: float = 1.0  # секунд тишины для остановки
    
    # RealtimeSTT оптимизация
    RTT_MIN_RECORDING_LENGTH: float = 0.5  # минимальная длина записи
    RTT_MIN_GAP_BETWEEN_RECORDINGS: float = 0.3  # минимальный интервал
    RTT_POST_SPEECH_SILENCE: float = 0.7  # время тишины после речи
    RTT_MAX_QUEUE_SIZE: int = 5  # максимальный размер очереди
    RTT_CHUNK_SIZE: int = 1024  # размер аудио чанка
    RTT_BUFFER_SIZE: int = 8192  # размер буфера
    RTT_SILERO_SENSITIVITY: float = 0.4  # чувствительность VAD
    RTT_WEBRTC_SENSITIVITY: int = 2  # чувствительность WebRTC
    
    # Безопасность
    KILL_SWITCH_HOTKEY: str = "ctrl+shift+f12"
    SCREEN_CAPTURE_CHECK_INTERVAL: int = 5  # секунд
    
    # Профили интервью
    INTERVIEW_PROFILES = {
        "technical": {
            "system_prompt": "Ты опытный технический специалист. Отвечай кратко, технически точно и по делу. Предоставляй конкретные примеры кода если нужно.",
            "max_tokens": 800
        },
        "hr": {
            "system_prompt": "Ты HR-консультант. Помогай с поведенческими вопросами, рассказывай о soft skills и корпоративной культуре.",
            "max_tokens": 600
        },
        "sales": {
            "system_prompt": "Ты эксперт по продажам. Помогай с переговорами, работой с возражениями и закрытием сделок.",
            "max_tokens": 500
        },
        "general": {
            "system_prompt": "Ты умный ассистент. Отвечай кратко, по существу и полезно.",
            "max_tokens": 600
        }
    }
    
    def __post_init__(self):
        # Загружаем API ключ из переменных окружения
        if self.PROXYAPI_KEY is None:
            self.PROXYAPI_KEY = os.getenv("PROXYAPI_KEY")
        
        if not self.PROXYAPI_KEY:
            raise ValueError("PROXYAPI_KEY не найден в переменных окружения")

# Глобальная конфигурация
config = Config() 