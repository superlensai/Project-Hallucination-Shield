from fastapi import FastAPI
from src.api.routes import router as internal_router

app = FastAPI(title="HalWall Trusted Package Database API")

app.include_router(internal_router)

@app.get("/internal/health")
async def health_check():
    return {"status": "ok", "service": "halwall-api"}

@app.get("/")
async def root():
    return {"message": "Welcome to HalWall Trusted Package Database API"}
