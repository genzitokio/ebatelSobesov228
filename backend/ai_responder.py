import requests
import asyncio
import logging
from typing import List, Dict, Optional
from collections import deque
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIResponder:
    def __init__(self):
        # Настраиваем ProxyAPI через requests
        self.api_url = f"{config.PROXY_API_BASE_URL}/chat/completions"
        self.headers = {
            'Authorization': f'Bearer {config.PROXYAPI_KEY}',
            'Content-Type': 'application/json'
        }
        logger.info(f"Используем ProxyAPI: {config.PROXY_API_BASE_URL}")
            
        self.conversation_history = deque(maxlen=10)  # Последние 10 сообщений
        self.current_profile = "general"
        
    def set_profile(self, profile_name: str):
        """Устанавливает профиль интервью"""
        if profile_name in config.INTERVIEW_PROFILES:
            self.current_profile = profile_name
            logger.info(f"Профиль изменен на: {profile_name}")
        else:
            logger.warning(f"Неизвестный профиль: {profile_name}")
    
    def add_to_history(self, role: str, content: str):
        """Добавляет сообщение в историю диалога"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def clear_history(self):
        """Очищает историю диалога"""
        self.conversation_history.clear()
        logger.info("История диалога очищена")
    
    def _prepare_messages(self, question: str) -> List[Dict[str, str]]:
        """Подготавливает сообщения для OpenAI API"""
        profile = config.INTERVIEW_PROFILES[self.current_profile]
        
        messages = [
            {"role": "system", "content": profile["system_prompt"]}
        ]
        
        # Добавляем историю диалога
        messages.extend(list(self.conversation_history))
        
        # Добавляем текущий вопрос
        messages.append({"role": "user", "content": question})
        
        return messages
    
    async def get_response(self, question: str) -> Optional[str]:
        """Получает ответ от ProxyAPI"""
        try:
            messages = self._prepare_messages(question)
            profile = config.INTERVIEW_PROFILES[self.current_profile]
            
            logger.info(f"Отправляем запрос в ProxyAPI: {question[:100]}...")
            
            # Подготавливаем данные для запроса
            data = {
                'model': config.OPENAI_MODEL,
                'messages': messages,
                'max_tokens': profile["max_tokens"],
                'temperature': config.OPENAI_TEMPERATURE
            }
            
            # Используем async запрос
            response = await asyncio.to_thread(
                requests.post,
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()
                
                # Добавляем в историю
                self.add_to_history("user", question)
                self.add_to_history("assistant", answer)
                
                logger.info(f"Получен ответ: {answer[:100]}...")
                return answer
            else:
                logger.error(f"Ошибка ProxyAPI: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от ProxyAPI: {e}")
            return None
    
    def get_quick_response(self, question: str) -> str:
        """Синхронный метод для быстрого ответа"""
        try:
            messages = self._prepare_messages(question)
            profile = config.INTERVIEW_PROFILES[self.current_profile]
            
            # Подготавливаем данные для запроса
            data = {
                'model': config.OPENAI_MODEL,
                'messages': messages,
                'max_tokens': profile["max_tokens"],
                'temperature': config.OPENAI_TEMPERATURE
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()
                
                # Добавляем в историю
                self.add_to_history("user", question)
                self.add_to_history("assistant", answer)
                
                return answer
            else:
                logger.error(f"Ошибка ProxyAPI: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при генерации ответа."
            
        except Exception as e:
            logger.error(f"Ошибка при получении быстрого ответа: {e}")
            return "Извините, произошла ошибка при генерации ответа."
    
    def get_conversation_summary(self) -> str:
        """Возвращает краткое резюме текущего диалога"""
        if not self.conversation_history:
            return "Диалог еще не начался"
        
        questions = [msg["content"] for msg in self.conversation_history if msg["role"] == "user"]
        return f"Обсуждено вопросов: {len(questions)}" 