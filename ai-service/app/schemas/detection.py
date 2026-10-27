from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Box(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class VehicleDetectionItem(BaseModel):
    track_id: int
    cls_id: int
    type: str
    box: List[int]
    confidence: float
    plate_number: Optional[str] = None

class ViolationItem(BaseModel):
    tracking_id: int
    plate_number: str
    violation_type: str
    speed_recorded: Optional[float] = None
    primary_fine: int
    total_fine: int
    evidence_path: Optional[str] = None
    timestamp: str
    details: str

class DetectionResponse(BaseModel):
    success: bool
    frame_width: int
    frame_height: int
    vehicles_detected: List[VehicleDetectionItem]
    violations_detected: List[ViolationItem]

class ANPRRequest(BaseModel):
    image_base64: Optional[str] = None
    image_path: Optional[str] = None

class ANPRResponse(BaseModel):
    success: bool
    plate_number: str
    confidence: float
    syntax_valid: bool
    state_code: Optional[str] = None

class VideoProcessRequest(BaseModel):
    job_id: str
    file_path: str
    speed_limit: float = 50.0

class VideoJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    total_frames: int
    processed_frames: int
    violations_count: int
    violations: List[Dict[str, Any]]
    error: Optional[str] = None

class SignalOverrideRequest(BaseModel):
    state: str
    autoCycle: Optional[bool] = None
    direction: Optional[str] = None
