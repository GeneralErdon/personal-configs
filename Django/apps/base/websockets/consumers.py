import json
from typing import Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels_redis.core import RedisChannelLayer
from channels.db import database_sync_to_async
from apps.notifications.utils import NotificationUtils

class BaseAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    channel_layer: RedisChannelLayer
    TYPE_ERROR = "error"
    
    async def _send_error(self, message:str):
        await self.send(text_data=json.dumps(
            {
                "type": self.TYPE_ERROR,
                "message": message
            }
        ))
    
    
    async def receive(self, text_data=None, bytes_data=None):
        serialized_data:dict[str, Any] = json.loads(text_data)
        message_type = serialized_data.get("type", None)
        if not message_type:
            await self._send_error("Message type is required")
            return
        if not hasattr(self, message_type):
            await self._send_error(f"Message type {message_type} is not valid")
            return
        
        return serialized_data