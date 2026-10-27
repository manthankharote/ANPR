"""
Main Entrypoint CLI for AI-Powered Intelligent Vehicle Identification
and Traffic Violation Detection System using ANPR.
Allows launching the Streamlit Web Dashboard or running Headless Video Surveillance.
"""

import sys
import os
import argparse
import subprocess
import cv2
import config
import database
import time
from detector import TrafficViolationDetector
from video_generator import generate_sample_traffic_video

def run_intersection_headless(display: bool = True):
    """Executes 4-way intersection surveillance and dynamic signal control."""
    from multi_camera_manager import MultiCameraManager
    print(f"\n=======================================================")
    print(f" STARTING 4-WAY ADAPTIVE TRAFFIC SIGNAL CONTROLLER")
    print(f" Directions: NORTH, EAST, SOUTH, WEST")
    print(f" Press 'Q' in the OpenCV window to exit")
    print(f"=======================================================\n")

    mgr = MultiCameraManager(enable_violation_detection=True)
    mgr.start()

    try:
        while mgr.is_running():
            grid = mgr.compose_grid_frame()
            if display:
                cv2.imshow("4-Way Adaptive Intersection Surveillance Grid (Press 'Q' to Exit)", grid)
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nIntersection surveillance interrupted by user.")
    finally:
        mgr.stop()
        if display:
            cv2.destroyAllWindows()

def run_headless(source: str, display: bool = True):
    """Executes traffic surveillance and violation detection directly in terminal / OpenCV window."""
    print(f"\n=======================================================")
    print(f" STARTING TRAFFIC VIOLATION SURVEILLANCE ENGINE")
    print(f" Source: {source}")
    print(f"=======================================================\n")

    detector = TrafficViolationDetector()
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"Error: Unable to open video source '{source}'")
        return

    frame_idx = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            annotated_frame, violations = detector.process_frame(frame)

            if violations:
                for v in violations:
                    sec_info = f" (+Rs.{v['secondary_fine']} Expired Doc Penalty)" if v['secondary_fine'] > 0 else ""
                    print(f"🚨 [Frame #{frame_idx}] VIOLATION ISSUED: {v['violation_type']} | Plate: {v['plate_number']} | Fine: Rs.{v['total_fine']}{sec_info}")

            if display:
                cv2.imshow("Traffic Sentinel Surveillance Stream (Press 'Q' to Exit)", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except KeyboardInterrupt:
        print("\nSurveillance interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Processed {frame_idx} frames. Violations logged to database: {config.DATABASE_PATH}")

def launch_dashboard():
    """Launches the Streamlit Web Application."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    print("\n=======================================================")
    print(" LAUNCHING WEB DASHBOARD & SURVEILLANCE COMMAND CENTER")
    print(f" Running: streamlit run {app_path}")
    print("=======================================================\n")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Intelligent Vehicle Identification & Traffic Violation Detection System"
    )
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit Web Command Center")
    parser.add_argument("--intersection", action="store_true", help="Run 4-Way Adaptive Intersection Surveillance (2x2 grid)")
    parser.add_argument("--source", type=str, default=None, help="Video file path, camera index (0), or RTSP URL for headless run")
    parser.add_argument("--no-display", action="store_true", help="Disable OpenCV popup window during headless run")
    parser.add_argument("--generate-video", action="store_true", help="Generate or regenerate sample_traffic.mp4")
    parser.add_argument("--reset-db", action="store_true", help="Reset all violations in database")

    args = parser.parse_args()

    if args.generate_video:
        generate_sample_traffic_video()
        return

    if args.reset_db:
        database.clear_all_violations()
        print("Violation database reset successfully.")
        return

    if args.intersection:
        run_intersection_headless(display=not args.no_display)
    elif args.source:
        # If numeric string, convert to int for webcam index
        src = int(args.source) if args.source.isdigit() else args.source
        run_headless(src, display=not args.no_display)
    else:
        # Default behavior: Launch Web Dashboard
        launch_dashboard()

if __name__ == "__main__":
    main()
