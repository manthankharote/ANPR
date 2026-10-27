import cv2
import time
import logging
import threading
from typing import Dict, Any, List

from app.services.detector_service import AIModernDetector

logger = logging.getLogger("VideoWorker")

# In-memory background jobs registry
JOBS_STORE: Dict[str, Dict[str, Any]] = {}

def process_video_background(job_id: str, file_path: str, speed_limit: float = 50.0):
    """Processes uploaded video asynchronously in a background thread."""
    logger.info(f"[Job {job_id}] Initiating background computer-vision processing for {file_path}")

    JOBS_STORE[job_id] = {
        "job_id": job_id,
        "status": "PROCESSING",
        "progress": 0.0,
        "total_frames": 0,
        "processed_frames": 0,
        "violations_count": 0,
        "violations": [],
        "error": None,
    }

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        logger.error(f"[Job {job_id}] Failed to open video file {file_path}")
        JOBS_STORE[job_id]["status"] = "FAILED"
        JOBS_STORE[job_id]["error"] = f"Unable to decode video file: {file_path}"
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    JOBS_STORE[job_id]["total_frames"] = total_frames

    detector = AIModernDetector()
    detector.speed_limit = speed_limit

    frame_count = 0
    all_violations = []

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            # Virtual video playback time in seconds
            frame_time = frame_count / float(fps)

            # Skip frames for faster inference (process 1 out of 3)
            if frame_count % 3 == 0:
                _, frame_violations = detector.process_frame(frame, timestamp=frame_time)
                if frame_violations:
                    for v in frame_violations:
                        all_violations.append(v)
                        logger.info(f"[Job {job_id}] VIOLATION CAPTURED: {v['violation_type']} by {v['plate_number']}")

            # Update progress
            if frame_count % 15 == 0 or frame_count >= total_frames:
                prog = min(100.0, round((frame_count / float(total_frames)) * 100.0, 1))
                JOBS_STORE[job_id]["progress"] = prog
                JOBS_STORE[job_id]["processed_frames"] = frame_count
                JOBS_STORE[job_id]["violations_count"] = len(all_violations)
                JOBS_STORE[job_id]["violations"] = all_violations

    except Exception as e:
        logger.error(f"[Job {job_id}] Processing failure: {e}")
        JOBS_STORE[job_id]["status"] = "FAILED"
        JOBS_STORE[job_id]["error"] = str(e)
    finally:
        cap.release()
        if JOBS_STORE[job_id]["status"] != "FAILED":
            JOBS_STORE[job_id]["status"] = "COMPLETED"
            JOBS_STORE[job_id]["progress"] = 100.0
            JOBS_STORE[job_id]["processed_frames"] = frame_count
            JOBS_STORE[job_id]["violations_count"] = len(all_violations)
            JOBS_STORE[job_id]["violations"] = all_violations
            logger.info(f"[Job {job_id}] Completed! Processed {frame_count} frames, flagged {len(all_violations)} violations.")

def spawn_video_worker(job_id: str, file_path: str, speed_limit: float = 50.0):
    t = threading.Thread(
        target=process_video_background,
        args=(job_id, file_path, speed_limit),
        daemon=True,
    )
    t.start()
    return t
