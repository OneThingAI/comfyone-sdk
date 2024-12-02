class ComfyOneError(Exception):
    """Base exception for ComfyOne SDK"""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}

class ValidationError(ComfyOneError):
    """Validation related errors"""
    pass

class APIError(ComfyOneError):
    """API related errors"""
    def __init__(self, code: int, message: str, context: dict = None):
        super().__init__(message, context)
        self.code = code

class AuthenticationError(APIError):
    """Authentication related errors"""
    pass

class ConnectionError(APIError):
    """Connection related errors"""
    pass 