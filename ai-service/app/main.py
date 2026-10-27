import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TrafficSentinelAI")

app = FastAPI(
    title="Traffic Sentinel AI & Computer Vision Microservice",
    description="High-throughput inference microservice exposing YOLOv8 object tracking, ANPR plate extraction, traffic violation rules & 4-way adaptive traffic control.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_banner():
    logger.info("=======================================================")
    logger.info(" 🚀 TRAFFIC SENTINEL FASTAPI AI SERVICE INITIALIZED")
    logger.info(" Docs available at: http://localhost:8000/docs")
    logger.info(" Health endpoint  : http://localhost:8000/health")
    logger.info("=======================================================")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
