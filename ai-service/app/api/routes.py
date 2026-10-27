import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.schemas.detection import (
    DetectionResponse,
    VehicleDetectionItem,
    ViolationItem,
    ANPRResponse,
    VideoProcessRequest,
    VideoJobStatus,
    SignalOverrideRequest,
)
from app.services.detector_service import AIModernDetector
from app.services import anpr_service
from app.services.video_worker import spawn_video_worker, JOBS_STORE

router = APIRouter()
detector_instance = AIModernDetector()

# Adaptive Signal state
signal_engine_state = {
    "state": "GREEN",
    "autoCycle": True,
    "activeDirection": "NORTH",
    "remainingSeconds": 15,
    "lanes": {
        "NORTH": {"vehicle_count": 5, "density_score": 5.0, "green_seconds": 15},
        "EAST": {"vehicle_count": 1, "density_score": 1.0, "green_seconds": 5},
        "SOUTH": {"vehicle_count": 3, "density_score": 3.0, "green_seconds": 8},
        "WEST": {"vehicle_count": 2, "density_score": 2.0, "green_seconds": 6},
    },
}

@router.get("/health")
def health_check():
    import torch
    return {
        "status": "ONLINE",
        "service": "AI Computer Vision & ANPR FastAPI Microservice",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "model_loaded": detector_instance.model is not None,
    }

@router.post("/detect/vehicles", response_model=DetectionResponse)
async def detect_vehicles(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image payload could not be decoded.")

    h, w = frame.shape[:2]
    vehicles, violations = detector_instance.process_frame(frame)

    return DetectionResponse(
        success=True,
        frame_width=w,
        frame_height=h,
        vehicles_detected=[VehicleDetectionItem(**v) for v in vehicles],
        violations_detected=[ViolationItem(**vi) for vi in violations],
    )

@router.post("/anpr/recognize", response_model=ANPRResponse)
async def recognize_plate(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid plate image payload.")

    res = anpr_service.extract_and_read_plate(image)
    plate_str = res["plate_number"]
    conf = res["confidence"]
    syntax_valid = res["syntax_valid"]
    state_prefix = plate_str[:2] if len(plate_str) >= 2 and plate_str != "UNREADABLE" else None

    return ANPRResponse(
        success=True,
        plate_number=plate_str,
        confidence=conf,
        syntax_valid=syntax_valid,
        state_code=state_prefix,
        plate_box=res.get("plate_box"),
        plate_status=res.get("plate_status", "DETECTED_READ"),
        raw_text=res.get("raw_text"),
    )

@router.post("/process/video")
def process_video_endpoint(req: VideoProcessRequest):
    job_id = req.job_id
    spawn_video_worker(job_id, req.file_path, req.speed_limit)
    return {
        "success": True,
        "message": f"Async video processing initiated for job #{job_id}",
        "job_id": job_id,
    }

@router.get("/jobs/{job_id}", response_model=VideoJobStatus)
def get_job_status(job_id: str):
    job = JOBS_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found.")
    return VideoJobStatus(**job)

@router.get("/signal/state")
def get_signal_state():
    return signal_engine_state

@router.post("/signal/override")
def override_signal_state(req: SignalOverrideRequest):
    signal_engine_state["state"] = req.state.upper()
    detector_instance.set_signal_state(req.state)
    if req.autoCycle is not None:
        signal_engine_state["autoCycle"] = req.autoCycle
    if req.direction:
        signal_engine_state["activeDirection"] = req.direction.upper()
    return {
        "success": True,
        "message": f"Intersection signal changed to {req.state}",
        "data": signal_engine_state,
    }
