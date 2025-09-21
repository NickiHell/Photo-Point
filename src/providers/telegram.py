"""
Telegram провайдер для отправки уведомлений через Telegram Bot API.
"""

import logging
import aiohttp
import asyncio
import os
from typing import Optional, Dict, Any

from src.base import NotificationProvider
from src.models import User, NotificationMessage, NotificationResult, NotificationType
from src.exceptions import ConfigurationError, SendError, AuthenticationError, UserNotReachableError, RateLimitError


logger = logging.getLogger(__name__)


class TelegramProvider(NotificationProvider):
    """Telegram провайдер для отправки уведомлений через Bot API."""
    
    def __init__(self, bot_token: str, timeout: int = 30):
        """
        Инициализация Telegram провайдера.
        
        Args:
            bot_token: Токен Telegram бота
            timeout: Таймаут для HTTP запросов в секундах
        """
        self.bot_token = bot_token
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    @classmethod
    def from_env(cls) -> "TelegramProvider":
        """Создать провайдера из переменных окружения."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            raise ConfigurationError("Missing TELEGRAM_BOT_TOKEN environment variable")
        
        return cls(bot_token=bot_token)
    
    async def _make_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить HTTP запрос к Telegram Bot API."""
        url = f"{self.base_url}/{method}"
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    
                    if not result.get("ok"):
                        error_code = result.get("error_code", 0)
                        description = result.get("description", "Unknown error")
                        
                        if error_code == 401:
                            raise AuthenticationError(f"Unauthorized: {description}")
                        elif error_code == 429:
                            raise RateLimitError(f"Rate limit exceeded: {description}")
                        else:
                            raise SendError(f"Telegram API error {error_code}: {description}")
                    
                    return result
                    
            except aiohttp.ClientError as e:
                raise SendError(f"HTTP request failed: {e}")
            except asyncio.TimeoutError:
                raise SendError("Request timeout")
    
    async def send(self, user: User, message: NotificationMessage) -> NotificationResult:
        """Отправить Telegram уведомление."""
        if not self.is_user_reachable(user):
            return NotificationResult(
                success=False,
                provider=NotificationType.TELEGRAM,
                message="User telegram_chat_id is not available",
                error="No telegram_chat_id provided"
            )
        
        try:
            # Подготовка сообщения
            rendered_message = message.render()
            
            # Формирование текста сообщения (в Telegram тема и содержимое объединяются)
            if rendered_message['subject']:
                text = f"*{rendered_message['subject']}*\n\n{rendered_message['content']}"
            else:
                text = rendered_message['content']
            
            # Ограничение длины сообщения (Telegram поддерживает до 4096 символов)
            if len(text) > 4096:
                text = text[:4093] + "..."
            
            # Подготовка данных для отправки
            data = {
                "chat_id": user.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown"  # Поддержка markdown форматирования
            }
            
            # Отправка сообщения
            result = await self._make_request("sendMessage", data)
            
            message_id = result["result"]["message_id"]
            logger.info(f"Telegram message sent successfully to chat {user.telegram_chat_id}, message_id: {message_id}")
            
            return NotificationResult(
                success=True,
                provider=NotificationType.TELEGRAM,
                message=f"Telegram message sent to chat {user.telegram_chat_id}",
                metadata={
                    "chat_id": user.telegram_chat_id,
                    "message_id": message_id
                }
            )
            
        except AuthenticationError as e:
            logger.error(f"Telegram authentication error: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.TELEGRAM,
                message="Authentication failed",
                error=str(e)
            )
            
        except RateLimitError as e:
            logger.error(f"Telegram rate limit error: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.TELEGRAM,
                message="Rate limit exceeded",
                error=str(e)
            )
            
        except SendError as e:
            logger.error(f"Telegram send error: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.TELEGRAM,
                message="Failed to send Telegram message",
                error=str(e)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.TELEGRAM,
                message="Unexpected error occurred",
                error=str(e)
            )
    
    def is_user_reachable(self, user: User) -> bool:
        """Проверить, можно ли отправить Telegram сообщение этому пользователю."""
        if not user.telegram_chat_id:
            return False
        
        # Базовая валидация chat_id (должен быть числом или строкой, содержащей число)
        try:
            int(user.telegram_chat_id)
            return True
        except ValueError:
            return False
    
    @property
    def provider_name(self) -> str:
        """Имя провайдера."""
        return "Telegram"
    
    async def validate_config(self) -> bool:
        """Проверить корректность конфигурации провайдера."""
        try:
            # Проверка токена через получение информации о боте
            result = await self._make_request("getMe", {})
            bot_info = result["result"]
            
            logger.info(f"Telegram bot validated: @{bot_info['username']} ({bot_info['first_name']})")
            return True
            
        except AuthenticationError:
            raise AuthenticationError("Invalid Telegram bot token")
        except Exception as e:
            raise ConfigurationError(f"Telegram configuration validation failed: {e}")
    
    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о чате (вспомогательный метод)."""
        try:
            result = await self._make_request("getChat", {"chat_id": chat_id})
            return result["result"]
        except Exception as e:
            logger.warning(f"Failed to get chat info for {chat_id}: {e}")
            return None