import os
import re
import cv2
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any, List
from ultralytics import YOLO

from app import config

logger = logging.getLogger("ANPRService")

# Valid Indian State and Union Territory Prefix Codes
INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BH", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "OR", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UA", "UK", "UP", "WB"
}

# Common OCR character confusions for Indian plates
CHAR_TO_DIGIT = {
    'O': '0', 'D': '0', 'Q': '0',
    'I': '1', 'L': '1', '|': '1',
    'Z': '2', 'E': '3', 'A': '4',
    'S': '5', 'G': '6', 'b': '6',
    'T': '7', 'J': '7', 'B': '8',
    'g': '9', 'q': '9'
}

DIGIT_TO_CHAR = {
    '0': 'O', '1': 'I', '2': 'Z', '3': 'E',
    '4': 'A', '5': 'S', '6': 'G', '7': 'T',
    '8': 'B', '9': 'P'
}

STATE_PREFIX_FIXES = {
    "0L": "DL", "OL": "DL", "DI": "DL", "OI": "DL", "D1": "DL", "01": "DL",
    "M8": "MH", "N8": "MH", "MN": "MH", "NH": "MH",
    "K4": "KA", "K0": "KA", "T4": "TN", "7N": "TN", "TM": "TN",
    "6J": "GJ", "CJ": "GJ", "0P": "UP", "OP": "UP", "DP": "UP",
    "N0": "OD", "0D": "OD", "P8": "PB", "R3": "RJ", "C6": "CG",
    "8R": "BR", "H8": "HR", "T5": "TS", "7S": "TS"
}

# Model and Engine Singletons
_PLATE_MODEL = None
_EASYOCR_READER = None

def get_plate_detector() -> Optional[YOLO]:
    global _PLATE_MODEL
    if _PLATE_MODEL is None:
        model_path = getattr(config, "PLATE_MODEL_PATH", "ai-service/app/models/license_plate_detector.pt")
        if os.path.exists(model_path):
            try:
                _PLATE_MODEL = YOLO(model_path)
                logger.info(f"YOLO License Plate Detector loaded successfully from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load YOLO license plate detector: {e}")
                _PLATE_MODEL = False
        else:
            logger.warning(f"Plate model file not found at {model_path}")
            _PLATE_MODEL = False
    return _PLATE_MODEL if _PLATE_MODEL else None

def get_ocr_engine():
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        try:
            import easyocr
            _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR Reader successfully initialized on CPU.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")
            _EASYOCR_READER = False
    return _EASYOCR_READER if _EASYOCR_READER else None

def clean_ocr_text(raw_text: str) -> str:
    """Strips special characters, punctuation, whitespace, and HSRP 'IND' prefix."""
    if not raw_text:
        return ""
    cleaned = re.sub(r'[^A-Za-z0-9]', '', str(raw_text)).upper()
    if cleaned.startswith("IND") and len(cleaned) >= 10:
        cleaned = cleaned[3:]
    elif cleaned.startswith("IN") and len(cleaned) >= 11:
        cleaned = cleaned[2:]
    return cleaned

def correct_indian_plate_syntax(candidate: str) -> Optional[str]:
    """
    Applies character disambiguation to match Indian registration plate formats:
    Standard: [State: 2 letters] [District: 1-2 digits] [Series: 0-3 letters] [Number: 4 digits]
    Bharat Series: [Year: 2 digits] [BH] [Series: 4 digits] [Letters: 1-2]
    """
    candidate = clean_ocr_text(candidate)
    if len(candidate) < 7 or len(candidate) > 11:
        return None

    chars = list(candidate)
    n = len(chars)

    # 1. Check if candidate is Bharat Series: YY BH #### XX (e.g. 22BH1234AA)
    # Positions 2-3 are 'BH' or OCR confusions like '8H', 'BH', '88'
    is_bh = False
    if n in (9, 10):
        mid_2 = "".join(chars[2:4])
        if mid_2 in ("BH", "8H", "B8", "8B"):
            is_bh = True
        elif chars[0].isdigit() and chars[1].isdigit() and (mid_2.endswith("H") or mid_2.startswith("B")):
            is_bh = True

    if is_bh:
        # First 2 chars: digits (Year, e.g. 22)
        for i in (0, 1):
            if chars[i] in CHAR_TO_DIGIT:
                chars[i] = CHAR_TO_DIGIT[chars[i]]
        # Chars 2, 3: 'BH'
        chars[2] = 'B'
        chars[3] = 'H'
        # Chars 4..7: 4 digits
        for i in range(4, min(8, n)):
            if chars[i] in CHAR_TO_DIGIT:
                chars[i] = CHAR_TO_DIGIT[chars[i]]
        # Remaining chars (8..n): letters
        for i in range(8, n):
            if chars[i] in DIGIT_TO_CHAR:
                chars[i] = DIGIT_TO_CHAR[chars[i]]
        corrected = "".join(chars)
        bh_pattern = r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$'
        if re.match(bh_pattern, corrected):
            return corrected

    # 2. Standard Indian Plate Format:
    # State prefix (first 2 chars must be letters)
    prefix_2 = "".join(chars[:2])
    if prefix_2 in STATE_PREFIX_FIXES:
        fixed = STATE_PREFIX_FIXES[prefix_2]
        chars[0], chars[1] = fixed[0], fixed[1]
    else:
        for i in (0, 1):
            if chars[i] in DIGIT_TO_CHAR:
                chars[i] = DIGIT_TO_CHAR[chars[i]]

    # Last 4 characters: MUST be digits
    if n >= 4:
        for i in range(n - 4, n):
            if chars[i] in CHAR_TO_DIGIT:
                chars[i] = CHAR_TO_DIGIT[chars[i]]

    # Middle characters (between State prefix and last 4 digits)
    # E.g. for length 10 (MH 12 DE 1433): chars[2,3] are digits, chars[4,5] are letters
    if n == 10:
        for i in (2, 3):
            if chars[i] in CHAR_TO_DIGIT:
                chars[i] = CHAR_TO_DIGIT[chars[i]]
        for i in (4, 5):
            if chars[i] in DIGIT_TO_CHAR:
                chars[i] = DIGIT_TO_CHAR[chars[i]]
    elif n == 9:
        # e.g. DL 01 A 1234 or DL 1 AB 1234
        if chars[2] in CHAR_TO_DIGIT:
            chars[2] = CHAR_TO_DIGIT[chars[2]]
        if chars[3].isdigit() or chars[3] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            if chars[3] in CHAR_TO_DIGIT:
                chars[3] = CHAR_TO_DIGIT[chars[3]]
            if chars[4] in DIGIT_TO_CHAR:
                chars[4] = DIGIT_TO_CHAR[chars[4]]
        else:
            if chars[3] in DIGIT_TO_CHAR:
                chars[3] = DIGIT_TO_CHAR[chars[3]]
            if chars[4] in DIGIT_TO_CHAR:
                chars[4] = DIGIT_TO_CHAR[chars[4]]
    elif n == 11:
        # e.g. MH 12 ABC 1234
        for i in (2, 3):
            if chars[i] in CHAR_TO_DIGIT:
                chars[i] = CHAR_TO_DIGIT[chars[i]]
        for i in (4, 5, 6):
            if chars[i] in DIGIT_TO_CHAR:
                chars[i] = DIGIT_TO_CHAR[chars[i]]

    corrected = "".join(chars)
    standard_pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$'
    if re.match(standard_pattern, corrected):
        if corrected[:2] in INDIAN_STATE_CODES:
            return corrected

    bh_pattern = r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$'
    if re.match(bh_pattern, corrected):
        return corrected

    return None

def preprocess_plate_for_ocr(plate_crop: np.ndarray) -> np.ndarray:
    """
    Standardized multi-stage image enhancement for OCR:
    1. Resize standardized height (100px)
    2. Grayscale conversion
    3. Bilateral Filter (edge-preserving noise reduction)
    4. CLAHE contrast enhancement
    5. Adaptive Gaussian thresholding
    """
    if plate_crop is None or plate_crop.size == 0 or plate_crop.shape[0] < 2 or plate_crop.shape[1] < 2:
        return np.zeros((100, 240), dtype=np.uint8)

    h, w = plate_crop.shape[:2]
    target_h = 100
    scale = target_h / float(max(1, h))
    target_w = max(int(w * scale), 200)

    try:
        resized = cv2.resize(plate_crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
    except Exception:
        resized = cv2.resize(plate_crop, (240, 100))

    if len(resized.shape) == 3 and resized.shape[2] == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized.copy()

    bilateral = cv2.bilateralFilter(gray, d=9, sigmaColor=15, sigmaSpace=15)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(bilateral)
    thresh = cv2.adaptiveThreshold(
        contrast_enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15, 3
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    return cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

def localize_plate_contours(vehicle_crop: np.ndarray) -> Optional[Tuple[Tuple[int, int, int, int], np.ndarray]]:
    """
    Morphological and contour-based license plate localization fallback:
    - Restricts search to bottom 60% of vehicle crop.
    - Searches for rectangular contours with aspect ratios between 2.0 and 5.8.
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None

    h, w = vehicle_crop.shape[:2]
    if h < 20 or w < 30:
        return None

    roi_y1 = int(h * 0.40)
    search_roi = vehicle_crop[roi_y1:h, :]
    roi_h, roi_w = search_roi.shape[:2]

    if roi_h < 15 or roi_w < 30:
        return None

    if len(search_roi.shape) == 3:
        gray = cv2.cvtColor(search_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = search_roi.copy()

    sobel_x = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
    abs_sobel = cv2.convertScaleAbs(sobel_x)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 5))
    morph = cv2.morphologyEx(abs_sobel, cv2.MORPH_CLOSE, kernel)
    _, thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_crop = None
    best_box = None
    best_score = -1.0

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        if ch <= 0 or cw <= 0:
            continue
        aspect_ratio = float(cw) / float(ch)
        area = cw * ch

        if 2.0 <= aspect_ratio <= 5.8:
            if 300 <= area <= (roi_w * roi_h * 0.45):
                pad_x = int(cw * 0.05)
                pad_y = int(ch * 0.05)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(roi_w, x + cw + pad_x)
                y2 = min(roi_h, y + ch + pad_y)

                if (y2 - y1) >= 8 and (x2 - x1) >= 16:
                    score = area * aspect_ratio
                    if score > best_score:
                        best_score = score
                        best_crop = search_roi[y1:y2, x1:x2].copy()
                        best_box = (x1, roi_y1 + y1, x2, roi_y1 + y2)

    if best_crop is not None and best_box is not None:
        return best_box, best_crop
    return None

def localize_plate(vehicle_crop: np.ndarray) -> Tuple[Optional[List[int]], Optional[np.ndarray], float]:
    """
    Multi-stage plate localizer:
    1. Pretrained YOLO Plate Detector
    2. Contour Sobel Gradient localization
    3. Center Bumper Crop fallback
    Returns: (box_in_crop, plate_crop, detection_conf)
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None, None, 0.0

    vh, vw = vehicle_crop.shape[:2]

    # Stage 1: Dedicated YOLO License Plate Detector
    plate_detector = get_plate_detector()
    if plate_detector is not None:
        try:
            results = plate_detector(vehicle_crop, conf=getattr(config, "PLATE_DETECTION_CONFIDENCE", 0.20), verbose=False)
            if results and len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
                best_box = None
                best_conf = 0.0
                for b in results[0].boxes:
                    c = float(b.conf[0].item())
                    if c > best_conf:
                        best_conf = c
                        best_box = [int(v) for v in b.xyxy[0].tolist()]

                if best_box is not None:
                    bx1, by1, bx2, by2 = best_box
                    # Add subtle padding
                    pad_x = max(2, int((bx2 - bx1) * 0.04))
                    pad_y = max(2, int((by2 - by1) * 0.04))
                    px1 = max(0, bx1 - pad_x)
                    py1 = max(0, by1 - pad_y)
                    px2 = min(vw, bx2 + pad_x)
                    py2 = min(vh, by2 + pad_y)

                    crop = vehicle_crop[py1:py2, px1:px2]
                    if crop.size > 0 and (py2 - py1) >= 6 and (px2 - px1) >= 12:
                        return [px1, py1, px2, py2], crop, best_conf
        except Exception as e:
            logger.warning(f"Plate model inference exception: {e}")

    # Stage 2: Contour & Morphological Localization Fallback
    contour_res = localize_plate_contours(vehicle_crop)
    if contour_res is not None:
        box, crop = contour_res
        return list(box), crop, 0.65

    # Stage 3: Bottom Bumper Region Fallback
    crop_y1 = max(0, int(vh * 0.60))
    crop_y2 = min(vh, int(vh * 0.95))
    crop_x1 = max(0, int(vw * 0.15))
    crop_x2 = min(vw, int(vw * 0.85))

    if (crop_y2 - crop_y1) >= 8 and (crop_x2 - crop_x1) >= 16:
        crop = vehicle_crop[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        return [crop_x1, crop_y1, crop_x2, crop_y2], crop, 0.40

    return None, None, 0.0

def recognize_plate_from_crop(plate_crop: np.ndarray, track_id: Optional[int] = None) -> Tuple[str, float, bool, str]:
    """
    Performs OCR on localized plate crop:
    Returns: (plate_number, confidence, syntax_valid, raw_text)
    NEVER invents or fabricates registration numbers. If unreadable, returns 'UNREADABLE'.
    """
    if plate_crop is None or plate_crop.size == 0 or plate_crop.shape[0] < 8 or plate_crop.shape[1] < 12:
        return "UNREADABLE", 0.0, False, ""

    ocr = get_ocr_engine()
    if ocr is None:
        logger.warning("No active OCR engine available.")
        return "UNREADABLE", 0.0, False, ""

    try:
        enhanced = preprocess_plate_for_ocr(plate_crop)
        results = ocr.readtext(enhanced)
        if not results:
            # Retry on raw crop if enhancement binarized too aggressively
            results = ocr.readtext(plate_crop)

        if results:
            best_raw = ""
            best_conf = 0.0
            all_lines = []

            for _, text, conf in results:
                cleaned = clean_ocr_text(text)
                all_lines.append(cleaned)
                if conf > best_conf:
                    best_conf = conf
                    best_raw = cleaned

            combined = "".join(all_lines)
            corrected_single = correct_indian_plate_syntax(best_raw)
            if corrected_single:
                return corrected_single, float(best_conf), True, best_raw

            corrected_combined = correct_indian_plate_syntax(combined)
            if corrected_combined:
                return corrected_combined, float(best_conf), True, combined

            # Return raw alphanumeric if length is sensible, but mark syntax_valid=False
            if len(best_raw) >= 4:
                return best_raw, float(best_conf), False, best_raw

    except Exception as e:
        logger.warning(f"EasyOCR extraction exception: {e}")

    return "UNREADABLE", 0.0, False, ""

def extract_and_read_plate(
    vehicle_crop: np.ndarray,
    veh_box: Optional[List[int]] = None,
    track_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Unified end-to-end ANPR method:
    Localizes plate -> Crops plate -> Preprocesses -> Runs OCR -> Syntax Disambiguation.
    Returns structured plate metadata dictionary.
    """
    local_box, plate_crop, det_conf = localize_plate(vehicle_crop)

    if plate_crop is None:
        return {
            "plate_number": "UNREADABLE",
            "confidence": 0.0,
            "syntax_valid": False,
            "plate_box": None,
            "plate_status": "NO_PLATE",
            "raw_text": "",
            "plate_crop": None,
        }

    # Global coordinates in full frame if veh_box is provided
    global_plate_box = None
    if veh_box is not None and local_box is not None:
        vx1, vy1 = veh_box[0], veh_box[1]
        global_plate_box = [
            vx1 + local_box[0],
            vy1 + local_box[1],
            vx1 + local_box[2],
            vy1 + local_box[3],
        ]

    plate_str, ocr_conf, syntax_valid, raw_ocr = recognize_plate_from_crop(plate_crop, track_id)

    if plate_str != "UNREADABLE" and len(plate_str) >= 4:
        status = "DETECTED_READ"
        final_conf = round(float((det_conf * 0.4) + (ocr_conf * 0.6)), 2)
    else:
        status = "DETECTED_UNREADABLE"
        plate_str = "UNREADABLE"
        final_conf = round(float(det_conf), 2)

    return {
        "plate_number": plate_str,
        "confidence": final_conf,
        "syntax_valid": syntax_valid,
        "plate_box": global_plate_box or local_box,
        "plate_status": status,
        "raw_text": raw_ocr,
        "plate_crop": plate_crop,
    }
