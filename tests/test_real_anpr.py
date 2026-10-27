import cv2
import os
import sys
from ultralytics import YOLO
import easyocr

def test_real_video():
    video_path = 'storage/uploads/Infinova_CCTV_Cameras_-_Infinova_Corporation__1080p__h264__1793082102015_9588.mp4'
    if not os.path.exists(video_path):
        print(f"Video not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    veh_model = YOLO('ai-service/app/models/yolov8n.pt')
    plate_model = YOLO('ai-service/app/models/license_plate_detector.pt')
    ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    os.makedirs('tests/real_video_audit', exist_ok=True)
    test_frames = [30, 60, 90, 150, 210, 270]

    for idx in test_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            print(f"Frame {idx}: Failed to read")
            continue

        h, w = frame.shape[:2]
        # 1. Vehicle detection (car=2, motorcycle=3, bus=5, truck=7)
        veh_results = veh_model(frame, classes=[2, 3, 5, 7], conf=0.30, verbose=False)
        veh_boxes = veh_results[0].boxes
        print(f"\n--- Frame {idx} ({w}x{h}) ---")
        print(f"Vehicles detected: {len(veh_boxes)}")

        annotated = frame.copy()

        # 2. Also run plate model on the full frame to compare direct vs hierarchical detection
        direct_plates = plate_model(frame, conf=0.25, verbose=False)[0].boxes
        print(f"Direct full-frame plate detections: {len(direct_plates)}")
        for dp in direct_plates:
            d_conf = float(dp.conf[0].item())
            d_box = [int(v) for v in dp.xyxy[0].tolist()]
            print(f"  > Direct Plate Box: {d_box}, conf={d_conf:.2f}")
            cv2.rectangle(annotated, (d_box[0], d_box[1]), (d_box[2], d_box[3]), (255, 0, 255), 2)
            d_crop = frame[max(0, d_box[1]):min(h, d_box[3]), max(0, d_box[0]):min(w, d_box[2])]
            if d_crop.size > 0:
                d_ocr = ocr_reader.readtext(d_crop)
                d_text = ' '.join([t[1] for t in d_ocr]) if d_ocr else "UNREADABLE"
                print(f"    Direct OCR text: '{d_text}'")

        for i, vb in enumerate(veh_boxes):
            v_cls = veh_model.names[int(vb.cls[0].item())]
            v_conf = float(vb.conf[0].item())
            vx1, vy1, vx2, vy2 = [int(x) for x in vb.xyxy[0].tolist()]
            cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (0, 255, 0), 2)
            cv2.putText(annotated, f"{v_cls} {v_conf:.2f}", (vx1, max(20, vy1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Hierarchical plate detection within vehicle crop
            veh_crop = frame[max(0, vy1):min(h, vy2), max(0, vx1):min(w, vx2)]
            if veh_crop.size > 0:
                plate_results = plate_model(veh_crop, conf=0.20, verbose=False)
                p_boxes = plate_results[0].boxes
                if len(p_boxes) > 0:
                    for pb in p_boxes:
                        p_conf = float(pb.conf[0].item())
                        px1, py1, px2, py2 = [int(x) for x in pb.xyxy[0].tolist()]
                        g_px1 = vx1 + px1
                        g_py1 = vy1 + py1
                        g_px2 = vx1 + px2
                        g_py2 = vy1 + py2
                        cv2.rectangle(annotated, (g_px1, g_py1), (g_px2, g_py2), (0, 0, 255), 2)

                        plate_crop = veh_crop[max(0, py1):min(veh_crop.shape[0], py2), max(0, px1):min(veh_crop.shape[1], px2)]
                        ocr_res = ocr_reader.readtext(plate_crop)
                        ocr_text = ' '.join([t[1] for t in ocr_res]) if ocr_res else "UNREADABLE"
                        print(f"  [Vehicle #{i+1} {v_cls}] Hierarchical Plate: bbox=[{g_px1},{g_py1},{g_px2},{g_py2}], conf={p_conf:.2f}, OCR: '{ocr_text}'")

        cv2.imwrite(f"tests/real_video_audit/frame_{idx}.jpg", annotated)

    cap.release()
    print("\n[Audit Complete] Output frames written to tests/real_video_audit/")

if __name__ == "__main__":
    test_real_video()
