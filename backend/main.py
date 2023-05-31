from fastapi import APIRouter, FastAPI
from .routers import stargazers

app = FastAPI()

app.include_router(stargazers.router)

@app.get("/")
async def read_root():
    return {"message": "You have reached the root of stargazers api."}