import logging
import threading
import time
import queue
from typing import Optional, Callable
from collections import deque
import numpy as np

try:
    from RealtimeSTT import AudioToTextRecorder
except ImportError:
    print("RealtimeSTT не установлен. Используйте: pip install RealtimeSTT")
    AudioToTextRecorder = None

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recorder = None
        self.is_listening = False
        self.listening_thread = None
        self.text_callback: Optional[Callable[[str], None]] = None
        self.should_stop = False
        
        self._setup_recorder()
    
    def _setup_recorder(self):
        """Настраивает рекордер для распознавания речи"""
        if AudioToTextRecorder is None:
            logger.error("RealtimeSTT не доступен")
            return
        
        try:
            # Правильная инициализация RealtimeSTT
            self.recorder = AudioToTextRecorder(
                model=config.WHISPER_MODEL,
                language=config.WHISPER_LANGUAGE,
                enable_realtime_transcription=True,
                use_microphone=True,
                # Контроль размера очереди и задержек
                min_length_of_recording=config.RTT_MIN_RECORDING_LENGTH,
                min_gap_between_recordings=config.RTT_MIN_GAP_BETWEEN_RECORDINGS,
                post_speech_silence_duration=config.RTT_POST_SPEECH_SILENCE,
                # Производительность
                silero_sensitivity=config.RTT_SILERO_SENSITIVITY,
                webrtc_sensitivity=config.RTT_WEBRTC_SENSITIVITY,
                silero_use_onnx=False
            )
            
            logger.info("Рекордер настроен успешно")
            logger.info(f"Параметры RealtimeSTT:")
            logger.info(f"  - Модель: {config.WHISPER_MODEL}")
            logger.info(f"  - Язык: {config.WHISPER_LANGUAGE}")
            logger.info(f"  - Мин. длина записи: {config.RTT_MIN_RECORDING_LENGTH}с")
            logger.info(f"  - Мин. интервал: {config.RTT_MIN_GAP_BETWEEN_RECORDINGS}с")
            logger.info(f"  - Тишина после речи: {config.RTT_POST_SPEECH_SILENCE}с")
            
        except Exception as e:
            logger.error(f"Ошибка при настройке рекордера: {e}")
            # Используем mock процессор при ошибке
            logger.info("Переключаемся на mock процессор")
            self.recorder = "mock"
    
    def _text_detected_callback(self, text: str):
        """Callback для обработки распознанного текста"""
        if text and text.strip():
            logger.info(f"🗣️ Распознан текст: '{text}'")
            if self.text_callback:
                logger.info(f"📞 Вызываем callback с текстом: '{text}'")
                self.text_callback(text)
            else:
                logger.warning("❌ Callback не установлен - текст не будет обработан!")
        else:
            logger.debug(f"🤐 Пропускаем пустой текст: '{text}'")
    
    def _listening_loop(self):
        """Основной цикл прослушивания в отдельном потоке"""
        logger.info("Запущен цикл прослушивания")
        
        while not self.should_stop:
            try:
                if self.recorder and self.recorder != "mock":
                    # Правильный способ использования RealtimeSTT
                    self.recorder.text(self._text_detected_callback)
                else:
                    # Mock режим - просто ждем
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Ошибка в цикле прослушивания: {e}")
                time.sleep(1)  # Пауза перед повторной попыткой
                
        logger.info("Цикл прослушивания завершен")
    
    def set_text_callback(self, callback: Callable[[str], None]):
        """Устанавливает колбэк для обработки распознанного текста"""
        self.text_callback = callback
        logger.info("Callback для обработки текста установлен")
    
    def start_listening(self):
        """Начинает прослушивание"""
        if not self.recorder:
            logger.error("Рекордер не настроен")
            return False
        
        if self.is_listening:
            logger.warning("Прослушивание уже активно")
            return True
        
        if self.recorder == "mock":
            logger.info("Используется mock режим (без реального аудио)")
            self.is_listening = True
            return True
        
        try:
            self.should_stop = False
            self.is_listening = True
            
            # Запускаем прослушивание в отдельном потоке
            self.listening_thread = threading.Thread(
                target=self._listening_loop,
                daemon=True,
                name="SpeechListening"
            )
            self.listening_thread.start()
            
            logger.info("✅ Прослушивание начато успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при запуске прослушивания: {e}")
            self.is_listening = False
            return False
    
    def stop_listening(self):
        """Останавливает прослушивание"""
        if not self.is_listening:
            logger.info("Прослушивание уже остановлено")
            return
            
        logger.info("Останавливаем прослушивание...")
        
        self.should_stop = True
        self.is_listening = False
        
        # Ждем завершения потока
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2)
            if self.listening_thread.is_alive():
                logger.warning("Поток прослушивания не завершился в отведенное время")
        
        logger.info("🛑 Прослушивание остановлено")
    
    def is_recording_active(self) -> bool:
        """Проверяет, активно ли прослушивание"""
        return self.is_listening
    
    def get_status(self) -> dict:
        """Возвращает статус процессора речи"""
        return {
            "is_listening": self.is_listening,
            "has_recorder": self.recorder is not None and self.recorder != "mock",
            "recorder_type": "mock" if self.recorder == "mock" else "realtime_stt",
            "thread_alive": self.listening_thread.is_alive() if self.listening_thread else False
        }

    def simulate_speech(self, text: str):
        """Имитирует распознавание речи для тестирования"""
        logger.info(f"🎭 Симуляция речи: '{text}'")
        if self.text_callback:
            self.text_callback(text)
        else:
            logger.warning("Callback не установлен для симуляции")

    def get_recorder_info(self) -> dict:
        """Возвращает информацию о рекордере"""
        if self.recorder == "mock":
            return {"type": "mock", "status": "active"}
        
        if not self.recorder:
            return {"type": "none", "status": "not_initialized"}
            
        try:
            info = {
                "type": "realtime_stt",
                "status": "listening" if self.is_listening else "ready",
                "model": config.WHISPER_MODEL,
                "language": config.WHISPER_LANGUAGE
            }
            return info
        except Exception as e:
            logger.error(f"Ошибка получения информации о рекордере: {e}")
            return {"type": "realtime_stt", "status": "error", "error": str(e)}

    def optimize_performance(self):
        """Оптимизирует производительность RealtimeSTT"""
        logger.info("⚡ Выполняется оптимизация производительности...")
        
        if self.recorder == "mock":
            logger.info("Mock режим - оптимизация не требуется")
            return {"status": "success", "message": "Mock режим активен"}
        
        if not self.recorder:
            logger.error("Рекордер не инициализирован")
            return {"status": "error", "message": "Рекордер не инициализирован"}
        
        try:
            # Временно останавливаем прослушивание для перенастройки
            was_listening = self.is_listening
            if was_listening:
                self.stop_listening()
                time.sleep(1)
            
            # Пересоздаем рекордер с оптимизированными параметрами
            self._setup_recorder()
            
            # Возобновляем прослушивание если было активно
            if was_listening:
                time.sleep(1)
                self.start_listening()
            
            logger.info("✅ Оптимизация производительности завершена")
            return {"status": "success", "message": "Производительность оптимизирована"}
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации: {e}")
            return {"status": "error", "message": f"Ошибка оптимизации: {e}"}

    def shutdown(self):
        """Корректно завершает работу процессора"""
        logger.info("Завершение работы SpeechProcessor...")
        self.stop_listening()
        
        if self.recorder and self.recorder != "mock":
            try:
                # У RealtimeSTT может быть метод shutdown
                if hasattr(self.recorder, 'shutdown'):
                    self.recorder.shutdown()
            except Exception as e:
                logger.error(f"Ошибка при завершении рекордера: {e}")
        
        logger.info("SpeechProcessor завершен")

# Фейковый процессор для тестирования без аудио
class MockSpeechProcessor:
    def __init__(self):
        self.is_listening = False
        self.text_callback = None
        
    def set_text_callback(self, callback):
        self.text_callback = callback
        
    def start_listening(self):
        self.is_listening = True
        logger.info("Mock: Прослушивание начато")
        return True
        
    def stop_listening(self):
        self.is_listening = False
        logger.info("Mock: Прослушивание остановлено")
        
    def simulate_speech(self, text: str):
        """Имитирует распознавание речи"""
        if self.text_callback:
            self.text_callback(text)
            
    def get_status(self):
        return {
            "is_listening": self.is_listening,
            "is_recording": self.is_listening,
            "mock": True
        } 