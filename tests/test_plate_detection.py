import os
import sys
import cv2
import numpy as np

# Ensure ai-service is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-service')))

from app.services import anpr_service

def test_plate_detection_and_syntax():
    print("=== TEST 2: Plate Localization & Syntax Disambiguation ===")
    
    # 1. Syntax Disambiguation Tests
    test_cases = [
        ("MHI2DE1433", "MH12DE1433"),
        ("DL01AB5555", "DL01AB5555"),
        ("KA03MJ4321", "KA03MJ4321"),
        ("AP10AR0658", "AP10AR0658"),
        ("TS09EG6531", "TS09EG6531"),
        ("22BH1234AA", "22BH1234AA"), # Bharat Series
        ("IN DAP10AR0658", "AP10AR0658"), # HSRP Prefix stripping
    ]
    
    for raw, expected in test_cases:
        cleaned = anpr_service.clean_ocr_text(raw)
        corrected = anpr_service.correct_indian_plate_syntax(cleaned)
        print(f"  > Raw: '{raw}' -> Cleaned: '{cleaned}' -> Corrected: '{corrected}'")
        assert corrected == expected, f"Expected {expected}, got {corrected}"
    print("[OK] Indian plate syntax disambiguation passed all assertions.")

    # 2. Localizer on Synthetic Plate Crop
    test_crop = np.ones((120, 300, 3), dtype=np.uint8) * 40
    # Draw white rectangular plate on dark bumper
    cv2.rectangle(test_crop, (40, 35), (260, 85), (245, 245, 245), -1)
    cv2.putText(test_crop, "MH12DE1433", (55, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    local_box, plate_img, conf = anpr_service.localize_plate(test_crop)
    print(f"[OK] Localizer Output: box={local_box}, conf={conf:.2f}, crop shape={plate_img.shape if plate_img is not None else None}")
    assert plate_img is not None, "Localizer failed to detect plate region"

    # 3. OCR on Localized Crop
    text, ocr_conf, syntax_valid, raw_text = anpr_service.recognize_plate_from_crop(plate_img)
    print(f"[OK] OCR Result on test crop: '{text}' (conf={ocr_conf:.2f}, valid={syntax_valid})")
    assert "MH12" in text or "1433" in text, f"OCR failed to capture plate characters: {text}"

    print("\n[SUCCESS] Plate localization and syntax tests passed successfully!")

if __name__ == "__main__":
    test_plate_detection_and_syntax()
