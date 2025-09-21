"""
SMS провайдер для отправки уведомлений через Twilio API.
"""

import logging
import re
import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from src.base import NotificationProvider
from src.models import User, NotificationMessage, NotificationResult, NotificationType
from src.exceptions import ConfigurationError, SendError, AuthenticationError, UserNotReachableError, RateLimitError


logger = logging.getLogger(__name__)


class SMSProvider(NotificationProvider):
    """SMS провайдер для отправки уведомлений через Twilio."""
    
    def __init__(self, account_sid: str, auth_token: str, from_phone: str):
        """
        Инициализация SMS провайдера.
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_phone: Номер телефона отправителя (в формате +1234567890)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.client = Client(account_sid, auth_token)
    
    @classmethod
    def from_env(cls) -> "SMSProvider":
        """Создать провайдера из переменных окружения."""
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([account_sid, auth_token, from_phone]):
            raise ConfigurationError("Missing required SMS configuration")
        
        return cls(account_sid=account_sid, auth_token=auth_token, from_phone=from_phone)
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Нормализовать номер телефона."""
        # Удаляем все символы кроме цифр и +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Если номер начинается не с +, добавляем + и код страны
        if not phone.startswith('+'):
            if phone.startswith('8'):
                phone = '+7' + phone[1:]  # Россия
            elif phone.startswith('7'):
                phone = '+' + phone
            else:
                phone = '+' + phone
        
        return phone
    
    async def send(self, user: User, message: NotificationMessage) -> NotificationResult:
        """Отправить SMS уведомление."""
        if not self.is_user_reachable(user):
            return NotificationResult(
                success=False,
                provider=NotificationType.SMS,
                message="User phone number is not available",
                error="No phone number provided"
            )
        
        try:
            # Подготовка сообщения
            rendered_message = message.render()
            # Для SMS используем только содержимое, тема игнорируется
            content = rendered_message['content']
            
            # SMS имеют ограничение по длине (обычно 160 символов для латиницы, 70 для кириллицы)
            if len(content) > 1600:  # Twilio может разбить длинные сообщения
                content = content[:1597] + "..."
            
            # Нормализация номера телефона
            to_phone = self._normalize_phone_number(user.phone)
            
            # Отправка SMS
            message_obj = self.client.messages.create(
                body=content,
                from_=self.from_phone,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully to {to_phone}, SID: {message_obj.sid}")
            return NotificationResult(
                success=True,
                provider=NotificationType.SMS,
                message=f"SMS sent to {to_phone}",
                metadata={
                    "recipient": to_phone,
                    "message_sid": message_obj.sid,
                    "status": message_obj.status
                }
            )
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            
            # Обработка специфичных ошибок Twilio
            if e.status == 401:
                return NotificationResult(
                    success=False,
                    provider=NotificationType.SMS,
                    message="Authentication failed",
                    error="Invalid Twilio credentials"
                )
            elif e.status == 429:
                return NotificationResult(
                    success=False,
                    provider=NotificationType.SMS,
                    message="Rate limit exceeded",
                    error="Too many SMS requests"
                )
            elif e.code == 21614:  # Invalid phone number
                return NotificationResult(
                    success=False,
                    provider=NotificationType.SMS,
                    message="Invalid phone number",
                    error=str(e)
                )
            else:
                return NotificationResult(
                    success=False,
                    provider=NotificationType.SMS,
                    message="Twilio API error",
                    error=str(e)
                )
                
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return NotificationResult(
                success=False,
                provider=NotificationType.SMS,
                message="Unexpected error occurred",
                error=str(e)
            )
    
    def is_user_reachable(self, user: User) -> bool:
        """Проверить, можно ли отправить SMS этому пользователю."""
        if not user.phone:
            return False
        
        # Базовая валидация номера телефона
        phone = re.sub(r'[^\d+]', '', user.phone)
        return len(phone) >= 10 and (phone.startswith('+') or phone.isdigit())
    
    @property
    def provider_name(self) -> str:
        """Имя провайдера."""
        return "SMS"
    
    async def validate_config(self) -> bool:
        """Проверить корректность конфигурации провайдера."""
        try:
            # Проверка аутентификации через получение информации об аккаунте
            account = self.client.api.accounts(self.account_sid).fetch()
            
            # Проверка формата номера телефона отправителя
            if not self.from_phone.startswith('+'):
                raise ConfigurationError("From phone number must start with '+'")
            
            # Проверка статуса аккаунта
            if account.status != 'active':
                raise ConfigurationError(f"Twilio account status: {account.status}")
            
            return True
            
        except TwilioRestException as e:
            if e.status == 401:
                raise AuthenticationError("Invalid Twilio credentials")
            else:
                raise ConfigurationError(f"Twilio configuration error: {e}")
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")