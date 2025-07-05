#!/usr/bin/env python3
"""
Простой тест для проверки работы RealtimeSTT
"""
import time
import threading
from RealtimeSTT import AudioToTextRecorder

print("🎤 Тест RealtimeSTT")
print("=" * 50)

def text_detected_callback(text):
    """Callback для обработки распознанного текста"""
    print(f"🗣️ Распознано: '{text}'")

def test_realtime_stt():
    """Тест RealtimeSTT"""
    print("📝 Создание рекордера...")
    
    try:
        # Создаем рекордер с минимальными настройками
        recorder = AudioToTextRecorder(
            model="base",
            language="ru", 
            enable_realtime_transcription=True,
            use_microphone=True,
            min_length_of_recording=0.5,
            min_gap_between_recordings=0.3,
            post_speech_silence_duration=0.7
        )
        
        print("✅ Рекордер создан успешно!")
        print("🎙️ Говорите что-нибудь...")
        print("📝 Для выхода нажмите Ctrl+C")
        print("-" * 50)
        
        # Запускаем прослушивание в отдельном потоке
        def listening_loop():
            while True:
                try:
                    recorder.text(text_detected_callback)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Ошибка в цикле прослушивания: {e}")
                    time.sleep(1)
        
        listening_thread = threading.Thread(target=listening_loop, daemon=True)
        listening_thread.start()
        
        # Ожидаем ввода пользователя
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Остановка тестирования...")
            
    except Exception as e:
        print(f"❌ Ошибка при создании рекордера: {e}")
        print("💡 Возможные причины:")
        print("   - Не установлен RealtimeSTT")
        print("   - Нет доступа к микрофону")
        print("   - Проблемы с аудиодрайверами")

if __name__ == "__main__":
    test_realtime_stt() 