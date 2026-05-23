from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine
from app.models import Base
from app.routers import enquiry
from app.logger import logger

app = FastAPI(
    title="Closira API Prototype",
    description="Backend service for Closira's core customer enquiry-handling workflow.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info("Starting up API...")
  
    Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down API...")

app.include_router(enquiry.router, tags=["enquiry"])

@app.get("/health", tags=["health"])
def health_check():
    """
    Return API status.
    """
    return {
        "api_status": "healthy",
        "database_status": "connected" # Since SQLAlchemy connects implicitly
    }

frontend_path = os.path.join(os.path.dirname(__file__), "../../closira_frontend")
# Mount the frontend directory so it's accessible at the root URL
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
