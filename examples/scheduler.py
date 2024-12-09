import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from comfyone.utils.logging import setup_logger
from comfyone.scheduler.api import router, setup_log_level
from fastapi import FastAPI
import logging

app = FastAPI()
# Initialize scheduler with logger
setup_log_level(logging.DEBUG)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

