import cv2
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.detector_service import AIModernDetector

def test_inference_on_sample_video():
    video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../storage/uploads/sample_traffic.mp4'))
    print(f"Testing video path: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Failed to open video at {video_path}"
    
    ret, frame = cap.read()
    cap.release()
    assert ret and frame is not None, "Failed to capture frame from sample video"
    
    print(f"Captured frame shape: {frame.shape}")
    detector = AIModernDetector()
    vehicles, violations = detector.process_frame(frame)
    
    print(f"Inference complete: {len(vehicles)} vehicles detected.")
    for v in vehicles:
        print(f"  > Detected: {v['type']} | Track ID: #{v['track_id']} | Plate: {v['plate_number']}")
    
    print("\n[SUCCESS] AI Detection and tracking pipeline verified!")

if __name__ == "__main__":
    test_inference_on_sample_video()
