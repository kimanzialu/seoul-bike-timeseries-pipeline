
from fastapi import FastAPI

from app.routes.bikes import router as bikes_router
from app.routes.mongo_bikes import router as mongo_bikes_router

app = FastAPI(
    title="Seoul Bike Sharing API",
    description="API for bike rental records and time-series queries",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Seoul Bike Sharing API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(bikes_router)
app.include_router(mongo_bikes_router)
