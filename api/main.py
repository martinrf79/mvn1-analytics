from fastapi import FastAPI
import uvicorn
import logging
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[logging.FileHandler("logs/mvn_system.log"), logging.StreamHandler()])
logger = logging.getLogger("MVN-API")

mini_app = FastAPI(title="MVN Analytics API", version="2.0.0")

@mini_app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@mini_app.get("/")
async def root():
    return {"message": "MVN Analytics API v2.0.0", "status": "operational"}

if __name__ == "__main__":
    Path("uploads").mkdir(exist_ok=True)
    uvicorn.run(mini_app, host="0.0.0.0", port=8000)
