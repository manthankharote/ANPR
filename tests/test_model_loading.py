import os
import sys
from ultralytics import YOLO

def test_models():
    print("=== TEST 1: Model Loading & Integrity ===")
    
    # 1. Vehicle Model
    veh_path = 'ai-service/app/models/yolov8n.pt'
    assert os.path.exists(veh_path), f"Vehicle model not found at {veh_path}"
    veh_model = YOLO(veh_path)
    print(f"[OK] Vehicle model loaded: {veh_path} ({os.path.getsize(veh_path):,} bytes)")
    print(f"     Task: {getattr(veh_model, 'task', 'unknown')}, Total Classes: {len(veh_model.names)}")
    assert 2 in veh_model.names and veh_model.names[2] == 'car'
    assert 3 in veh_model.names and veh_model.names[3] == 'motorcycle'
    
    # 2. Plate Model
    plate_path = 'ai-service/app/models/license_plate_detector.pt'
    assert os.path.exists(plate_path), f"Plate model not found at {plate_path}"
    plate_model = YOLO(plate_path)
    print(f"[OK] License plate model loaded: {plate_path} ({os.path.getsize(plate_path):,} bytes)")
    print(f"     Task: {getattr(plate_model, 'task', 'unknown')}, Classes: {plate_model.names}")
    
    # 3. EasyOCR
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    assert reader is not None
    print("[OK] EasyOCR initialized on CPU with English language model.")
    
    print("\n[SUCCESS] All models loaded and verified successfully!")

if __name__ == "__main__":
    test_models()
