import os
import sys
import time
import json
import cv2

# Ensure ai-service is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-service')))

from app.services import video_worker

def audit_full_real_video():
    video_path = os.path.abspath("storage/uploads/Infinova_CCTV_Cameras_-_Infinova_Corporation__1080p__h264__1793082102015_9588.mp4")
    if not os.path.exists(video_path):
        print(f"ERROR: Video not found at {video_path}")
        return

    job_id = f"AUDIT_FULL_{int(time.time())}"
    print("=" * 70)
    print("AUDIT: RUNNING COMPLETE REAL CCTV TRAFFIC VIDEO PIPELINE")
    print(f"Job ID    : {job_id}")
    print(f"Video File: {os.path.basename(video_path)}")
    print("=" * 70)

    # Launch video worker directly
    worker_thread = video_worker.spawn_video_worker(job_id, video_path, speed_limit=45.0)

    # Monitor progress to completion
    last_prog = -1
    while worker_thread.is_alive():
        job_data = video_worker.JOBS_STORE.get(job_id, {})
        status = job_data.get("status", "PENDING")
        prog = job_data.get("progress", 0.0)
        proc_f = job_data.get("processed_frames", 0)
        tot_f = job_data.get("total_frames", 0)
        viols = job_data.get("violations_count", 0)

        if prog != last_prog:
            print(f"  [Progress] Status: {status} | Progress: {prog}% | Frames: {proc_f}/{tot_f} | Violations: {viols}")
            last_prog = prog
        time.sleep(2.0)

    # Final Job Status
    worker_thread.join()
    final_job = video_worker.JOBS_STORE.get(job_id, {})

    print("\n" + "=" * 70)
    print("FINAL JOB AUDIT METRICS")
    print("=" * 70)
    print(f"Final Job Status      : {final_job.get('status')}")
    print(f"Total Video Frames    : {final_job.get('total_frames')}")
    print(f"Processed Frames      : {final_job.get('processed_frames')}")
    print(f"Errors Logged         : {final_job.get('error') or 'None (0 errors)'}")
    print(f"Violations Captured   : {final_job.get('violations_count')}")

    print("\n" + "=" * 70)
    print("CAPTURED VIOLATIONS & ANPR AUDIT TABLE")
    print("=" * 70)
    all_viols = final_job.get("violations", [])
    for idx, v in enumerate(all_viols):
        tid = v.get("tracking_id")
        v_type = v.get("violation_type")
        plate = v.get("plate_number")
        conf = v.get("plate_confidence", 0.0)
        p_status = v.get("plate_status")
        raw_ocr = v.get("raw_ocr_text", "")
        v_stat = v.get("verification_status")
        ev_file = os.path.basename(v.get("evidence_path", ""))
        print(f"#{idx+1:02d} | Track #{tid:2d} | {v_type:20s} | Plate: {plate:12s} | Conf: {conf:.2f} | Status: {p_status} | Ver: {v_stat} | Raw OCR: '{raw_ocr}' | Ev: {ev_file}")

if __name__ == "__main__":
    audit_full_real_video()
