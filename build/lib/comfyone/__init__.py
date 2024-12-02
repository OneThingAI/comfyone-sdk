from typing import Optional
from .api.comfyone_client import ComfyOneClient
from .api.websocket.websocket_client import OneThingAIWebSocket

class ComfyOne:
    """
    ComfyOne SDK主客户端
    整合API和WebSocket功能的统一接口
    """
    def __init__(self, api_key: str, 
                 base_url: str = "https://pandora-server-cf.onethingai.com",
                 max_retries: int = 3):
        self.api = ComfyOneClient(api_key, base_url, max_retries)
        self.ws: Optional[OneThingAIWebSocket] = None

    def connect_websocket(self) -> OneThingAIWebSocket:
        """初始化并连接WebSocket"""
        if not self.ws:
            self.ws = OneThingAIWebSocket(self.api.api_key)
            self.ws.start()
        return self.ws

    def close(self):
        """关闭所有连接"""
        if self.ws:
            self.ws.close() 