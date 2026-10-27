import os
from pathlib import Path

# Paths
APP_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = APP_DIR.parent
ROOT_DIR = AI_SERVICE_DIR.parent

MODELS_DIR = APP_DIR / "models"
YOLO_MODEL_PATH = str(MODELS_DIR / "yolov8n.pt")
PLATE_MODEL_PATH = str(MODELS_DIR / "license_plate_detector.pt")
STORAGE_UPLOADS_DIR = str(ROOT_DIR / "storage" / "uploads")
STORAGE_EVIDENCE_DIR = str(ROOT_DIR / "storage" / "evidence")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(STORAGE_UPLOADS_DIR, exist_ok=True)
os.makedirs(STORAGE_EVIDENCE_DIR, exist_ok=True)

# Detection & Tracking Config
DETECTION_CONFIDENCE = float(os.getenv("DETECTION_CONFIDENCE", "0.40"))
PLATE_DETECTION_CONFIDENCE = float(os.getenv("PLATE_DETECTION_CONFIDENCE", "0.25"))
IOU_THRESHOLD = 0.45
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
TWO_WHEELER_CLASSES = [1, 3]    # bicycle, motorcycle
PERSON_CLASS_ID = 0
CELL_PHONE_CLASS_ID = 67
TRAFFIC_LIGHT_CLASS_ID = 9

CLASS_NAMES = {
    0: "Person",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
    9: "Traffic Light",
    67: "Cell Phone"
}

# Statutory Violation Rules Geometry
STOP_LINE = [(100, 480), (1180, 480)]
STOP_LINE_TOLERANCE_PX = 25
SPEED_LINE_1 = [(100, 320), (1180, 320)]
SPEED_LINE_2 = [(100, 520), (1180, 520)]
SPEED_DISTANCE_METERS = 12.0
SPEED_LIMIT_KMH = float(os.getenv("SPEED_LIMIT_KMH", "50.0"))
VIOLATION_COOLDOWN_SECONDS = 15.0

# Statutory Indian Motor Vehicles Act Fines
FINES = {
    "Red Light Jump": 1000,
    "Over-Speeding": 2000,
    "No Helmet": 1000,
    "Triple Riding": 1000,
    "Mobile Phone Usage": 1500,
    "Wrong-Lane / Wrong-Way Driving": 1500,
    "Expired Insurance": 2000,
    "Expired PUC": 1000
}
