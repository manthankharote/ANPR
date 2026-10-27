import os
import sys
import cv2
import time
import json

# Ensure ai-service is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-service')))

from app.services.detector_service import AIModernDetector

def run_real_video_evaluation():
    video_path = os.path.abspath("storage/uploads/Infinova_CCTV_Cameras_-_Infinova_Corporation__1080p__h264__1793082102015_9588.mp4")
    if not os.path.exists(video_path):
        print(f"[ERROR] Video file not found at: {video_path}")
        return

    print("=" * 70)
    print("🚦 REAL CCTV TRAFFIC VIDEO VALIDATION & ANPR AUDIT")
    print(f"Video File: {os.path.basename(video_path)}")
    print("=" * 70)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Unable to open video {video_path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video Info: {width}x{height} @ {fps:.1f} FPS, Total Frames: {total_frames}")

    detector = AIModernDetector()
    detector.speed_limit = 40.0  # Threshold for testing

    os.makedirs("tests/real_video_audit", exist_ok=True)

    frame_idx = 0
    max_frames_to_test = 150  # 10 seconds of CCTV footage
    violations_captured = []
    plates_detected = []
    vehicles_tracked = set()

    start_time = time.time()

    while cap.isOpened() and frame_idx < max_frames_to_test:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        frame_time = frame_idx / float(fps)

        # Process every 2nd frame for responsive tracking
        if frame_idx % 2 == 0:
            vehicles, viols = detector.process_frame(frame, timestamp=frame_time)

            for v in vehicles:
                tid = v.get("track_id") or v.get("tracking_id")
                vehicles_tracked.add(tid)
                if v.get("plate_number") and v["plate_number"] != "UNREADABLE":
                    plates_detected.append({
                        "frame": frame_idx,
                        "tracking_id": tid,
                        "class": v.get("type", "Vehicle"),
                        "plate": v["plate_number"],
                        "status": v.get("plate_status"),
                        "conf": v.get("plate_confidence", 0.0),
                        "raw_ocr": v.get("raw_ocr_text", ""),
                    })

            for viol in viols:
                violations_captured.append(viol)

        if frame_idx % 30 == 0:
            elapsed = time.time() - start_time
            print(f"  > Frame {frame_idx}/{max_frames_to_test} ({frame_idx/float(max_frames_to_test)*100:.1f}%) | "
                  f"Tracked Vehicles: {len(vehicles_tracked)} | Plates Read: {len(plates_detected)} | "
                  f"Violations: {len(violations_captured)} | Elapsed: {elapsed:.1f}s")

    cap.release()
    total_elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("📊 REAL CCTV VALIDATION AUDIT RESULTS")
    print("=" * 70)
    print(f"Frames Processed       : {frame_idx} (sampled at 1/2 cadence)")
    print(f"Inference Time         : {total_elapsed:.2f}s ({frame_idx / max_frames_to_test * 100:.1f}% processed)")
    print(f"Unique Tracked Vehicles: {len(vehicles_tracked)}")
    print(f"Plate Readings Logged  : {len(plates_detected)}")
    print(f"Violations Flagged     : {len(violations_captured)}")

    print("\n--- SAMPLE REAL PLATE DETECTIONS & OCR READINGS ---")
    unique_plates = {}
    for p in plates_detected:
        plate = p["plate"]
        if plate not in unique_plates or p["conf"] > unique_plates[plate]["conf"]:
            unique_plates[plate] = p

    for plate, info in unique_plates.items():
        print(f"  • Plate: {plate:12} | Vehicle: {info['class']} (ID #{info['tracking_id']}) | "
              f"Conf: {info['conf']:.2f} | Status: {info['status']} | Raw OCR: '{info['raw_ocr']}'")

    print("\n--- CAPTURED VIOLATIONS ---")
    for vi in violations_captured[:5]:
        print(f"  • #{vi['tracking_id']} {vi['violation_type']:15} | Plate: {vi['plate_number']} | "
              f"Status: {vi.get('verification_status')} | Evidence: {vi.get('evidence_path')}")

    print("\n--- GROUND TRUTH & ACCURACY DISCLAIMER (Per Requirement 11) ---")
    print("Notice: No human-annotated ground-truth label file exists for this CCTV clip.")
    print("Detections shown above reflect actual optical inference by YOLOv8n + EasyOCR.")
    print("Accuracy claims must remain unquantified until labeled benchmarks are evaluated.")
    print("=" * 70)

if __name__ == "__main__":
    run_real_video_evaluation()
