"""
Configuration Module for AI-Powered Intelligent Vehicle Identification
and Traffic Violation Detection System using ANPR.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str(BASE_DIR / "traffic_system.db")
VIOLATIONS_DIR = str(BASE_DIR / "violations")
MODELS_DIR = str(BASE_DIR / "models")
SAMPLE_VIDEO_PATH = str(BASE_DIR / "sample_traffic.mp4")

# Ensure required directories exist
os.makedirs(VIOLATIONS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Camera & Video Stream Settings
# ---------------------------------------------------------------------------
DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720
TARGET_FPS = 30
FRAME_SKIP = 1  # Process every nth frame for optimized real-time throughput

# Stream source presets
STREAM_SOURCES = {
    "Sample Traffic Video": SAMPLE_VIDEO_PATH,
    "Laptop Webcam (Index 0)": 0,
    "IP Webcam / DroidCam (HTTP/RTSP)": "http://192.168.1.100:8080/video",
    "Upload Custom Video": None
}

# ---------------------------------------------------------------------------
# Detection & Tracking Settings (YOLOv8 + ByteTrack)
# ---------------------------------------------------------------------------
YOLO_MODEL_NAME = "yolov8n.pt"  # Lightweight nano model for real-time inference
DETECTION_CONFIDENCE = 0.40
IOU_THRESHOLD = 0.45

# COCO Class IDs for Traffic Objects
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck, 9: traffic light, 67: cell phone
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

# ---------------------------------------------------------------------------
# Violation Rules Geometry & Thresholds
# Standard normalized coordinates or pixel coordinates mapped to 1280x720
# ---------------------------------------------------------------------------

# 1. Red Light Stop Line: [(x1, y1), (x2, y2)]
STOP_LINE = [(100, 480), (1180, 480)]
STOP_LINE_TOLERANCE_PX = 25  # Crossing buffer

# 2. Over-Speeding Virtual Timing Lines
# Line 1 (Entry) and Line 2 (Exit)
SPEED_LINE_1 = [(100, 320), (1180, 320)]
SPEED_LINE_2 = [(100, 520), (1180, 520)]
SPEED_DISTANCE_METERS = 12.0  # Real-world distance between Line 1 and Line 2
SPEED_LIMIT_KMH = 50.0        # Default speed limit threshold

# 3. Wrong-Way / Wrong-Lane Movement
# Allowable flow direction vector (e.g. downwards from top to bottom)
ALLOWED_LANE_DIRECTION = (0, 1)  # (dx, dy)
WRONG_WAY_ANGLE_THRESHOLD_DEG = 120.0  # Flag if vehicle moves >120° against flow

# 4. Overloading / Triple Riding
MAX_RIDER_CAPACITY_TWO_WHEELER = 2  # More than 2 riders is triple riding

# 5. Mobile Phone Usage Proximity
# Ratio of head region height relative to person bounding box
HEAD_REGION_RATIO = 0.35

# Incident deduplication cooldown in seconds (prevent duplicate fines per vehicle)
VIOLATION_COOLDOWN_SECONDS = 15.0

# ---------------------------------------------------------------------------
# Statutory Fine Schedule (Indian Motor Vehicles Act / Traffic Rules)
# Amounts in INR (₹)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# SMS & Notification Settings
# ---------------------------------------------------------------------------
# Twilio Credentials (set via environment variables or replace here)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC_mock_twilio_account_sid_12345678")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "mock_twilio_auth_token_87654321")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+15551234567")

# Fast2SMS Credentials
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")

# Fallback Simulation Mode
# If True, sends styled console log and local simulation record
SMS_SIMULATION_MODE = True
CHALLAN_PORTAL_BASE_URL = "https://echallan.parivahan.gov.in/portal/pay"

# ---------------------------------------------------------------------------
# 4-Way Adaptive Traffic Signal Control Engine
# ---------------------------------------------------------------------------

# Ordered intersection approach directions
SIGNAL_DIRECTIONS = ["NORTH", "EAST", "SOUTH", "WEST"]

# Direction-specific compass emoji for HUD labels
DIRECTION_EMOJI = {
    "NORTH": "⬆️ NORTH",
    "EAST":  "➡️ EAST",
    "SOUTH": "⬇️ SOUTH",
    "WEST":  "⬅️ WEST",
}

# Green phase time bounds (seconds)
MAX_GREEN_TIME = 30    # Hard upper cap — prevents excessive hold
MIN_GREEN_TIME = 5     # Minimum safety crossing window
YELLOW_DURATION = 3    # Fixed amber/yellow interphase (seconds)
ALL_RED_CLEARANCE = 1  # All-red safety clearance between phases (seconds)

# Adaptive allocation parameters
# Green time formula: T_i = clamp(round(T_BASE + k * D_i), T_min, T_max)
SIGNAL_T_BASE  = 3.0   # Base offset seconds added to every non-empty phase
SIGNAL_K       = 1.8   # Scaling factor seconds per weighted density unit

# Low-density shortcut: if total vehicle count <= LOW_DENSITY_THRESHOLD,
# allocate T = max(MIN_GREEN, count * LOW_DENSITY_FACTOR) seconds
LOW_DENSITY_THRESHOLD = 3          # ≤ 3 vehicles triggers the low-density formula
LOW_DENSITY_FACTOR    = 2.5        # seconds per vehicle in low-density mode

# Weighted density coefficients per vehicle type
DENSITY_WEIGHTS = {
    "car":        1.0,
    "bicycle":    0.5,
    "motorcycle": 0.5,
    "bus":        2.0,
    "truck":      2.0,
    "person":     0.0,   # Pedestrians do not contribute to vehicle density
}

# ---------------------------------------------------------------------------
# Multi-Camera Source Configuration  (4 cardinal directions)
# Supports: int (webcam index), str (file path or RTSP URL), None (disabled)
# ---------------------------------------------------------------------------
CAMERA_SOURCES = {
    "NORTH": SAMPLE_VIDEO_PATH,   # Default: sample simulation video for all lanes
    "EAST":  SAMPLE_VIDEO_PATH,
    "SOUTH": SAMPLE_VIDEO_PATH,
    "WEST":  SAMPLE_VIDEO_PATH,
}

# Display resolution for each camera tile in the 4-grid HUD (pixels)
CAMERA_TILE_WIDTH  = 640
CAMERA_TILE_HEIGHT = 360

# Detection confidence used in the adaptive signal scan (can differ from
# the single-camera violation detection confidence for speed vs. accuracy)
SIGNAL_DETECTION_CONFIDENCE = 0.30
