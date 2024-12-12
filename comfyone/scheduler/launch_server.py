from fastapi import FastAPI
from comfyone.utils.logging import setup_logger
from comfyone.scheduler.api import router, setup_log_level
import logging

app = FastAPI()
app.include_router(router)

setup_log_level(logging.DEBUG)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)