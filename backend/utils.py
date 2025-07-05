import logging
import requests
from typing import Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

class APITester:
    """Утилита для тестирования API подключения"""
    
    @staticmethod
    def test_proxyapi_connection() -> Dict[str, Any]:
        """Тестирует подключение к ProxyAPI"""
        try:
            headers = {
                'Authorization': f'Bearer {config.PROXYAPI_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': 'Test connection'}],
                'max_tokens': 10
            }
            
            response = requests.post(
                f"{config.PROXY_API_BASE_URL}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'ProxyAPI подключение работает',
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'message': f'Ошибка ProxyAPI: {response.status_code}',
                    'error': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка подключения к ProxyAPI: {str(e)}',
                'error': str(e)
            }
    
    @staticmethod
    def test_current_api() -> Dict[str, Any]:
        """Тестирует текущее API подключение"""
        return APITester.test_proxyapi_connection()

class ConfigManager:
    """Утилита для управления конфигурацией"""
    

    
    @staticmethod
    def get_current_config() -> Dict[str, Any]:
        """Возвращает текущую конфигурацию"""
        return {
            'proxy_api_url': config.PROXY_API_BASE_URL,
            'model': config.OPENAI_MODEL,
            'temperature': config.OPENAI_TEMPERATURE,
            'max_tokens': config.OPENAI_MAX_TOKENS,
            'has_proxyapi_key': bool(config.PROXYAPI_KEY)
        }
    
    @staticmethod
    def validate_config() -> Dict[str, Any]:
        """Проверяет корректность конфигурации"""
        issues = []
        
        if not config.PROXYAPI_KEY:
            issues.append("PROXYAPI_KEY не установлен")
        if not config.PROXY_API_BASE_URL:
            issues.append("PROXY_API_BASE_URL не установлен")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

def quick_test():
    """Быстрый тест API подключения"""
    print("🧪 Тестирование API подключения...")
    
    # Проверяем конфигурацию
    validation = ConfigManager.validate_config()
    if not validation['valid']:
        print("❌ Ошибки конфигурации:")
        for issue in validation['issues']:
            print(f"   - {issue}")
        return
    
    # Тестируем подключение
    result = APITester.test_current_api()
    if result['success']:
        print(f"✅ {result['message']}")
        if 'response_time' in result:
            print(f"⏱️ Время отклика: {result['response_time']:.2f}s")
    else:
        print(f"❌ {result['message']}")
        if 'error' in result:
            print(f"🔍 Детали: {result['error']}")

if __name__ == "__main__":
    quick_test() 