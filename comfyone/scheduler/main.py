from fastapi import FastAPI
from comfyone.scheduler.backend_scheduler import router

app = FastAPI()
app.include_router(router)
