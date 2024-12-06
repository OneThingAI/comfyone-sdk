import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from comfyone.utils.logging import setup_logger
from comfyone.scheduler.backend_scheduler import router, setup_external_logger
from fastapi import FastAPI
import logging

# Initialize logger
logger = setup_logger(
    name="scheduler_example",
    level=logging.DEBUG,
)

app = FastAPI()
# Initialize scheduler with logger
setup_external_logger(logger)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting scheduler example server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

