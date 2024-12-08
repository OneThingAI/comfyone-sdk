from fastapi import FastAPI
from comfyone.scheduler.api import router

app = FastAPI()
app.include_router(router)
