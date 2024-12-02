from typing import Optional, Dict
import logging
from pathlib import Path
from .api.comfyone_client import ComfyOneClient
from .api.websocket.websocket_client import OneThingAIWebSocket
from .utils.logging import setup_logger
from .utils.debug import debug_context, DebugContext

class ComfyOne:
    """
    ComfyOne SDK主客户端
    整合API和WebSocket功能的统一接口
    """
    def __init__(self, api_key: str, 
                 instance_id: str,   
                 domain: str = "pandora-server-cf.onethingai.com",
                 max_retries: int = 3,
                 timeout: int = 5,
                 debug: bool = False,
                 log_file: Optional[Path] = None):
        
        # Set up logging
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = setup_logger(
            name="comfyone",
            level=log_level,
            log_file=log_file
        )
        
        self.domain = domain
        self.base_url = f"https://{domain}"
        self.ws_url = f"wss://{domain}/v1/ws"
        
        # Initialize components with debug context
        with debug_context(self.logger, "initialize_client") as ctx:
            ctx.context.update({
                "domain": domain,
                "max_retries": max_retries,
                "timeout": timeout
            })
            self.api = ComfyOneClient(
                api_key, 
                instance_id,
                self.base_url, 
                max_retries, 
                timeout,
                logger=self.logger
            )
            self.ws: Optional[OneThingAIWebSocket] = None

    def connect_websocket(self) -> OneThingAIWebSocket:
        """初始化并连接WebSocket"""
        with debug_context(self.logger, "connect_websocket") as ctx:
            if not self.ws:
                self.ws = OneThingAIWebSocket(
                    self.api.api_key, 
                    url=self.ws_url,
                    logger=self.logger
                )
                self.ws.start()
                ctx.context["connected"] = True
            return self.ws

    def close(self):
        """关闭所有连接"""
        with debug_context(self.logger, "close_connections") as ctx:
            if self.ws:
                self.ws.close()
                ctx.context["websocket_closed"] = True 