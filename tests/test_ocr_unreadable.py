import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-service')))

from app.services import anpr_service

def test_unreadable_plates_not_fabricated():
    print("=== TEST 3: Unreadable & Degradation Resistance (No Fabrication) ===")
    
    # 1. None crop
    res_none = anpr_service.extract_and_read_plate(None)
    print(f"  > None Crop: plate='{res_none['plate_number']}', status='{res_none['plate_status']}'")
    assert res_none['plate_number'] == "UNREADABLE"
    assert res_none['plate_status'] == "NO_PLATE"

    # 2. Solid Black Image
    black = np.zeros((150, 300, 3), dtype=np.uint8)
    res_black = anpr_service.extract_and_read_plate(black)
    print(f"  > Black Image: plate='{res_black['plate_number']}', status='{res_black['plate_status']}'")
    assert res_black['plate_number'] == "UNREADABLE"

    # 3. Random Gaussian Noise (No plate)
    noise = np.random.randint(0, 256, (150, 300, 3), dtype=np.uint8)
    res_noise = anpr_service.extract_and_read_plate(noise)
    print(f"  > Noise Image: plate='{res_noise['plate_number']}', status='{res_noise['plate_status']}'")
    assert res_noise['plate_number'] == "UNREADABLE"

    # 4. Very tiny degenerate crop (4x4 pixels)
    tiny = np.ones((4, 4, 3), dtype=np.uint8) * 200
    res_tiny = anpr_service.extract_and_read_plate(tiny)
    print(f"  > Tiny Crop: plate='{res_tiny['plate_number']}', status='{res_tiny['plate_status']}'")
    assert res_tiny['plate_number'] == "UNREADABLE"

    # 5. Invalid State Prefix / Non-Plate Words (Requirement 3: Never marked valid solely on length/format)
    assert anpr_service.correct_indian_plate_syntax("NONTRANSPOR") is None, "Commercial banner text must not pass syntax check"
    assert anpr_service.correct_indian_plate_syntax("OHTRAHSRORT") is None, "Garbage OCR must not pass syntax check"
    assert anpr_service.correct_indian_plate_syntax("XY12AB1234") is None, "Fictitious state code XY must not pass syntax check"
    assert anpr_service.correct_indian_plate_syntax("12345678") is None, "Pure numeric text must not pass syntax check"
    print("  > Invalid Syntax & Fictitious State Codes: All correctly rejected (None)")

    print("\n[SUCCESS] Unreadable handling verified: 0 fabricated plates returned!")

if __name__ == "__main__":
    test_unreadable_plates_not_fabricated()
