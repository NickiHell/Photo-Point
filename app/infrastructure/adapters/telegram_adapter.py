"""
Telegram notification adapter.
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional

from ...domain.entities.user import User
from ...domain.value_objects.notification import RenderedMessage, NotificationType
from ...domain.value_objects.delivery import DeliveryResult, DeliveryError
from ...domain.services import NotificationProviderInterface


logger = logging.getLogger(__name__)


class TelegramNotificationAdapter(NotificationProviderInterface):
    """Telegram notification provider adapter."""
    
    def __init__(
        self,
        bot_token: str,
        timeout: int = 30,
        max_message_length: int = 4096
    ) -> None:
        self._bot_token = bot_token
        self._timeout = timeout
        self._max_message_length = max_message_length
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
    
    @property
    def name(self) -> str:
        return "TelegramNotificationAdapter"
    
    def get_channel_type(self) -> NotificationType:
        return NotificationType.TELEGRAM
    
    def can_handle_user(self, user: User) -> bool:
        """Check if user has Telegram configured."""
        return user.has_telegram() and user.is_active
    
    async def _make_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Telegram Bot API."""
        url = f"{self._base_url}/{method}"
        
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    
                    if not result.get("ok"):
                        error_code = result.get("error_code", 0)
                        description = result.get("description", "Unknown error")
                        
                        if error_code == 401:
                            raise Exception(f"Authentication error: {description}")
                        elif error_code == 429:
                            raise Exception(f"Rate limit exceeded: {description}")
                        else:
                            raise Exception(f"Telegram API error {error_code}: {description}")
                    
                    return result
                    
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP request failed: {e}")
        except asyncio.TimeoutError:
            raise Exception("Request timeout")
    
    async def send(self, user: User, message: RenderedMessage) -> DeliveryResult:
        """Send Telegram notification to user."""
        if not self.can_handle_user(user):
            error = DeliveryError(
                code="USER_NOT_REACHABLE",
                message="User does not have Telegram configured or is inactive"
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Cannot send Telegram message to user",
                error=error
            )
        
        try:
            # Format message (combine subject and content for Telegram)
            if message.subject.value:
                text = f"*{message.subject.value}*\n\n{message.content.value}"
            else:
                text = message.content.value
            
            # Limit message length
            if len(text) > self._max_message_length:
                text = text[:self._max_message_length - 3] + "..."
            
            # Prepare request data
            data = {
                "chat_id": user.telegram_chat_id.value,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            # Send message
            result = await self._make_request("sendMessage", data)
            message_id = result["result"]["message_id"]
            
            logger.info(f"Telegram message sent to chat {user.telegram_chat_id.value}, message_id: {message_id}")
            
            return DeliveryResult(
                success=True,
                provider=self.name,
                message=f"Telegram message sent to chat {user.telegram_chat_id.value}",
                metadata={
                    "chat_id": user.telegram_chat_id.value,
                    "message_id": message_id
                }
            )
            
        except Exception as e:
            error_message = str(e)
            error_code = "TELEGRAM_ERROR"
            
            # Classify error types
            if "Authentication error" in error_message:
                error_code = "AUTHENTICATION_ERROR"
            elif "Rate limit exceeded" in error_message:
                error_code = "RATE_LIMIT_ERROR"
            elif "Request timeout" in error_message:
                error_code = "TIMEOUT_ERROR"
            elif "HTTP request failed" in error_message:
                error_code = "NETWORK_ERROR"
            
            logger.error(f"Telegram message sending failed: {e}")
            error = DeliveryError(
                code=error_code,
                message=error_message,
                details={"telegram_error": str(e)}
            )
            return DeliveryResult(
                success=False,
                provider=self.name,
                message="Failed to send Telegram message",
                error=error
            )
    
    async def validate_configuration(self) -> bool:
        """Validate Telegram provider configuration."""
        try:
            # Validate bot token by getting bot information
            result = await self._make_request("getMe", {})
            bot_info = result["result"]
            
            logger.info(f"Telegram bot validated: @{bot_info['username']} ({bot_info['first_name']})")
            return True
            
        except Exception as e:
            logger.error(f"Telegram configuration validation failed: {e}")
            return False