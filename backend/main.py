import asyncio
import json
import logging
import threading
import time
import os
import sys
import psutil
import keyboard
from typing import Set, Optional
import websockets
from colorama import init, Fore, Style

# Инициализация colorama для Windows
init()

# Импорт наших модулей
from config import config
from ai_responder import AIResponder
from speech_processor import SpeechProcessor, MockSpeechProcessor

logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StealthAssistant:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.ai_responder = AIResponder()
        self.speech_processor = None
        self.is_running = False
        self.server = None
        self.security_monitor = None
        self.loop = None
        
        # Пытаемся создать реальный процессор речи
        try:
            self.speech_processor = SpeechProcessor()
            logger.info(f"🎤 Используется реальный SpeechProcessor")
        except Exception as e:
            logger.warning(f"❌ Не удалось создать реальный процессор речи: {e}")
            logger.info("🎭 Используем mock процессор для тестирования")
            self.speech_processor = MockSpeechProcessor()
        
        # Проверяем тип процессора
        processor_type = type(self.speech_processor).__name__
        logger.info(f"🔧 Тип процессора: {processor_type}")
        
        # Устанавливаем callback для обработки речи
        self.speech_processor.set_text_callback(self._on_speech_recognized_sync)
        
        # Настраиваем kill-switch
        self._setup_kill_switch()
    
    def _setup_kill_switch(self):
        """Настраивает глобальный kill-switch"""
        try:
            keyboard.add_hotkey(
                config.KILL_SWITCH_HOTKEY,
                self._emergency_shutdown,
                suppress=True
            )
            logger.info(f"Kill-switch настроен: {config.KILL_SWITCH_HOTKEY}")
        except Exception as e:
            logger.error(f"Ошибка при настройке kill-switch: {e}")
    
    def _emergency_shutdown(self):
        """Экстренное выключение"""
        logger.warning("🚨 ЭКСТРЕННОЕ ВЫКЛЮЧЕНИЕ!")
        self.shutdown()
        sys.exit(0)
    
    def _on_speech_recognized_sync(self, text: str):
        """Синхронная обертка для обработки речи"""
        logger.info(f"🎯 Получен текст из SpeechProcessor: '{text}'")
        
        if self.loop and self.loop.is_running():
            # Создаем задачу в основном цикле событий
            logger.info(f"🔄 Добавляем задачу в основной event loop")
            asyncio.run_coroutine_threadsafe(
                self._on_speech_recognized(text),
                self.loop
            )
        else:
            # Если цикл не запущен, используем новый цикл
            logger.info(f"🔄 Запускаем новый event loop")
            asyncio.run(self._on_speech_recognized(text))
    
    async def _on_speech_recognized(self, text: str):
        """Обрабатывает распознанную речь"""
        logger.info(f"🎤 Распознана речь: '{text}'")
        
        # Отправляем транскрипцию всем подключенным клиентам
        message = {
            "type": "speech_transcription",
            "text": text,
            "timestamp": time.time()
        }
        logger.info(f"📤 Отправляем транскрипцию всем клиентам")
        await self._broadcast_message(message)
    
    async def _process_ai_question(self, question: str):
        """Обрабатывает вопрос для AI"""
        logger.info(f"🤖 Начинаем обработку вопроса для AI: '{question}'")
        
        # Получаем ответ от AI
        logger.info(f"📡 Отправляем запрос к AI...")
        response = await self.ai_responder.get_response(question)
        
        if response:
            logger.info(f"✅ Получен ответ от AI (длина: {len(response)} символов)")
            logger.info(f"👥 Количество подключенных клиентов: {len(self.clients)}")
            
            # Отправляем ответ всем подключенным клиентам
            message = {
                "type": "ai_response",
                "question": question,
                "answer": response,
                "timestamp": time.time()
            }
            logger.info(f"📤 Отправляем ответ AI всем клиентам")
            await self._broadcast_message(message)
        else:
            logger.warning(f"❌ AI не вернул ответ на вопрос: '{question}'")
    
    async def _broadcast_message(self, message: dict):
        """Отправляет сообщение всем подключенным клиентам"""
        if self.clients:
            message_str = json.dumps(message, ensure_ascii=False)
            logger.info(f"📻 Отправляем сообщение {len(self.clients)} клиентам: {message['type']}")
            
            # Создаем задачи для отправки всем клиентам
            tasks = []
            for client in self.clients.copy():
                tasks.append(self._send_to_client(client, message_str))
            
            # Выполняем все задачи параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Проверяем результаты
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            logger.info(f"📊 Результат отправки: {successful} успешно, {failed} ошибок")
        else:
            logger.warning(f"❌ Нет подключенных клиентов для отправки сообщения: {message['type']}")
    
    async def _send_to_client(self, client: websockets.WebSocketServerProtocol, message: str):
        """Отправляет сообщение конкретному клиенту"""
        try:
            await client.send(message)
            logger.debug(f"✅ Сообщение отправлено клиенту: {client.remote_address}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения клиенту {client.remote_address}: {e}")
            self.clients.discard(client)
    
    async def _handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Обрабатывает сообщение от клиента"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "start_listening":
                logger.info(f"🎤 Запрос на начало прослушивания, процессор: {type(self.speech_processor).__name__}")
                success = self.speech_processor.start_listening()
                logger.info(f"🎤 Результат запуска прослушивания: {'✅ Успешно' if success else '❌ Ошибка'}")
                
                # Получаем статус процессора
                status = self.speech_processor.get_status()
                logger.info(f"🔧 Статус процессора: {status}")
                
                response = {
                    "type": "listening_status",
                    "status": "started" if success else "failed"
                }
                await websocket.send(json.dumps(response))
                
            elif message_type == "stop_listening":
                logger.info(f"🔇 Запрос на остановку прослушивания, процессор: {type(self.speech_processor).__name__}")
                self.speech_processor.stop_listening()
                logger.info(f"🔇 Прослушивание остановлено")
                
                response = {
                    "type": "listening_status",
                    "status": "stopped"
                }
                await websocket.send(json.dumps(response))
                
            elif message_type == "set_profile":
                profile = data.get("profile", "general")
                self.ai_responder.set_profile(profile)
                response = {
                    "type": "profile_changed",
                    "profile": profile
                }
                await websocket.send(json.dumps(response))
                
            elif message_type == "clear_history":
                self.ai_responder.clear_history()
                response = {
                    "type": "history_cleared"
                }
                await websocket.send(json.dumps(response))
                
            elif message_type == "get_status":
                status = {
                    "type": "status",
                    "speech_processor": self.speech_processor.get_status(),
                    "recorder_info": self.speech_processor.get_recorder_info() if hasattr(self.speech_processor, 'get_recorder_info') else {},
                    "ai_responder": {
                        "profile": self.ai_responder.current_profile,
                        "history_length": len(self.ai_responder.conversation_history)
                    },
                    "clients_connected": len(self.clients)
                }
                await websocket.send(json.dumps(status))
                
            elif message_type == "optimize_performance":
                # Оптимизация производительности
                if hasattr(self.speech_processor, 'optimize_performance'):
                    result = self.speech_processor.optimize_performance()
                    response = {
                        "type": "performance_optimized",
                        "message": result.get("message", "Производительность оптимизирована"),
                        "status": result.get("status", "success")
                    }
                    await websocket.send(json.dumps(response))
                
            elif message_type == "manual_question":
                # Ручной ввод вопроса для отправки в AI
                question = data.get("question", "")
                if question:
                    await self._process_ai_question(question)
                    
            elif message_type == "simulate_speech":
                # Для тестирования с mock процессором
                text = data.get("text", "")
                if hasattr(self.speech_processor, 'simulate_speech'):
                    self.speech_processor.simulate_speech(text)
                    
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения от клиента: {e}")
    
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Обрабатывает подключение клиента"""
        logger.info(f"{Fore.GREEN}🔗 Новое подключение: {websocket.remote_address}{Style.RESET_ALL}")
        self.clients.add(websocket)
        
        try:
            # Отправляем приветственное сообщение
            welcome_message = {
                "type": "welcome",
                "message": "Подключено к Stealth AI Assistant",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(welcome_message))
            logger.info(f"{Fore.GREEN}💬 Приветственное сообщение отправлено клиенту{Style.RESET_ALL}")
            
            # Обрабатываем сообщения от клиента
            async for message in websocket:
                await self._handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"{Fore.YELLOW}🔌 Клиент отключился: {websocket.remote_address}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Ошибка при обработке клиента: {e}{Style.RESET_ALL}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"{Fore.CYAN}👥 Активных подключений: {len(self.clients)}{Style.RESET_ALL}")
    
    def _monitor_security(self):
        """Мониторинг безопасности в отдельном потоке"""
        screen_capture_processes = [
            'obs64.exe', 'obs32.exe', 'obs.exe',
            'bandicam.exe', 'fraps.exe', 'camtasia.exe',
            'screenrec.exe', 'hypercam.exe', 'snagit.exe',
            'zoom.exe', 'teams.exe', 'skype.exe'
        ]
        
        while self.is_running:
            try:
                # Проверяем запущенные процессы
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower() in [p.lower() for p in screen_capture_processes]:
                            logger.warning(f"🚨 Обнаружен процесс захвата экрана: {proc.info['name']}")
                            # Здесь можно добавить автоматическое скрытие
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                time.sleep(config.SCREEN_CAPTURE_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ошибка в мониторинге безопасности: {e}")
                time.sleep(5)
    
    def start_server(self):
        """Запускает сервер"""
        logger.info(f"{Fore.GREEN}🚀 Запуск Stealth AI Assistant{Style.RESET_ALL}")
        
        # Проверяем API ключ
        if not config.PROXYAPI_KEY:
            logger.error("PROXYAPI_KEY не установлен!")
            return
        logger.info(f"{Fore.YELLOW}🌐 Используем ProxyAPI.ru{Style.RESET_ALL}")
        
        self.is_running = True
        
        # Запускаем мониторинг безопасности
        logger.info(f"{Fore.YELLOW}🔒 Запускаем мониторинг безопасности...{Style.RESET_ALL}")
        self.security_monitor = threading.Thread(
            target=self._monitor_security,
            daemon=True
        )
        self.security_monitor.start()
        logger.info(f"{Fore.GREEN}🛡️ Мониторинг безопасности активен{Style.RESET_ALL}")
        
        # Запускаем WebSocket сервер
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            logger.info(f"{Fore.YELLOW}🌐 Создаем WebSocket сервер на {config.WEBSOCKET_HOST}:{config.WEBSOCKET_PORT}...{Style.RESET_ALL}")
            
            self.server = websockets.serve(
                self._handle_client,
                config.WEBSOCKET_HOST,
                config.WEBSOCKET_PORT
            )
            
            logger.info(f"{Fore.GREEN}✅ WebSocket сервер запущен на {config.WEBSOCKET_HOST}:{config.WEBSOCKET_PORT}{Style.RESET_ALL}")
            logger.info(f"{Fore.MAGENTA}🔥 Kill-switch: {config.KILL_SWITCH_HOTKEY}{Style.RESET_ALL}")
            logger.info(f"{Fore.CYAN}📡 Ожидаем подключений фронтенда...{Style.RESET_ALL}")
            
            self.loop.run_until_complete(self.server)
            logger.info(f"{Fore.GREEN}🚀 Сервер успешно запущен и готов к работе!{Style.RESET_ALL}")
            self.loop.run_forever()
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения")
        except Exception as e:
            logger.error(f"Ошибка сервера: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Завершает работу сервера"""
        logger.info(f"{Fore.RED}🛑 Завершение работы Stealth AI Assistant{Style.RESET_ALL}")
        
        self.is_running = False
        
        # Останавливаем прослушивание
        if self.speech_processor:
            self.speech_processor.stop_listening()
        
        # Закрываем соединения с клиентами
        if self.clients:
            for client in self.clients.copy():
                try:
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(client.close(), self.loop)
                    else:
                        asyncio.run(client.close())
                except:
                    pass
        
        logger.info("Сервер остановлен")

def main():
    """Основная функция"""
    try:
        # Проверяем, что переменная окружения установлена
        if not os.getenv("PROXYAPI_KEY"):
            print(f"{Fore.RED}❌ Установите переменную окружения PROXYAPI_KEY{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Например: set PROXYAPI_KEY=sk-yseNQGJXYUnn4YjrnwNJnwW7bsnwFg8K{Style.RESET_ALL}")
            return
        
        assistant = StealthAssistant()
        assistant.start_server()
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 