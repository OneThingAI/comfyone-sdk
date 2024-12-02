import websocket
import json
import threading
import time
import logging
from typing import Optional, Callable, Dict, Any
from .. import exceptions

class OneThingAIWebSocket:
    """
    ComfyOne WebSocket客户端类
    用于处理与ComfyOne服务的实时WebSocket通信
    """
    def __init__(self, token: str, 
                 url: str = "wss://pandora-server-cf.onethingai.com/v1/ws",
                 reconnect_delay: int = 5,
                 logger: Optional[logging.Logger] = None):
        self.url = url.rstrip('/')
        self.token = token
        self.ws: Optional[websocket.WebSocketApp] = None
        
        self.running = False
        self.reconnect_delay = reconnect_delay
        self.ws_thread: Optional[threading.Thread] = None
        self.logger = logger or logging.getLogger(__name__)
        
        # Callback handlers
        self._message_handlers: Dict[str, Callable] = {}
        self._error_handler: Optional[Callable] = None
        self._connection_handler: Optional[Callable] = None

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type in self._message_handlers:
                self._message_handlers[message_type](data)
            else:
                self.logger.debug(f"Unhandled message type: {message_type}")
                self.logger.debug(f"Message content: {json.dumps(data, indent=2)}")

        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON message received: {message}")

    def on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """处理WebSocket错误"""
        if self._error_handler:
            self._error_handler(error)
        else:
            self.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """处理WebSocket连接关闭"""
        self.logger.info(f"WebSocket connection closed [{close_status_code}]: {close_msg}")
        if self.running:
            self.logger.info(f"Attempting to reconnect in {self.reconnect_delay}s...")
            time.sleep(self.reconnect_delay)
            self.connect()

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        """处理WebSocket连接建立"""
        self.logger.info("WebSocket connection established")
        
        auth_message = {
            "type": "auth",
            "token": self.token
        }
        ws.send(json.dumps(auth_message))
        self.logger.debug("Authentication message sent")
        
        if self._connection_handler:
            self._connection_handler()

    def connect(self) -> None:
        """建立WebSocket连接"""
        self.logger.debug(f"Connecting to WebSocket server: {self.url}")
        
        self.ws = websocket.WebSocketApp(
            self.url,
            header={"Authorization": f"Bearer {self.token}"},
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

    def start(self) -> None:
        """在独立线程中启动WebSocket连接"""
        self.connect()
        self.ws_thread = threading.Thread(target=self.run)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        self.logger.debug("WebSocket client thread started")

    def run(self) -> None:
        """运行WebSocket连接并处理重连"""
        self.running = True
        while self.running:
            try:
                self.ws.run_forever()
                if not self.running:
                    break
                self.logger.warning("Connection lost, attempting to reconnect...")
                time.sleep(self.reconnect_delay)
            except Exception as e:
                self.logger.error(f"Runtime error: {e}")
                if self.running:
                    self.logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                    time.sleep(self.reconnect_delay)

    def close(self) -> None:
        """关闭WebSocket连接"""
        self.logger.info("Closing WebSocket connection...")
        self.running = False
        if self.ws:
            self.ws.close()

    def send_message(self, message: Dict[str, Any]) -> None:
        """发送WebSocket消息"""
        if not self.ws:
            raise exceptions.ConnectionError("WebSocket connection not established")
        
        try:
            self.ws.send(json.dumps(message))
            self.logger.debug(f"Message sent: {message.get('type', 'unknown')}")
        except Exception as e:
            raise exceptions.ConnectionError(f"Failed to send message: {str(e)}")

    def add_message_handler(self, message_type: str, handler: Callable[[Dict], None]) -> None:
        """添加消息类型处理器"""
        self._message_handlers[message_type] = handler
        self.logger.debug(f"Added message handler for type: {message_type}")

    def remove_message_handler(self, message_type: str) -> None:
        """移除消息类型处理器"""
        self._message_handlers.pop(message_type, None)
        self.logger.debug(f"Removed message handler for type: {message_type}")

    def set_error_handler(self, handler: Callable[[Exception], None]) -> None:
        """设置错误处理器"""
        self._error_handler = handler

    def set_connection_handler(self, handler: Callable[[], None]) -> None:
        """设置连接建立处理器"""
        self._connection_handler = handler

    def is_connected(self) -> bool:
        """检查WebSocket是否已连接"""
        return self.ws is not None and self.ws.sock is not None and self.ws.sock.connected