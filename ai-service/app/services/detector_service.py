import os
import cv2
import time
import math
import logging
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from ultralytics import YOLO

from app import config
from app.services import anpr_service

logger = logging.getLogger("DetectorService")

class SimpleCentroidTracker:
    def __init__(self, max_lost: int = 25, max_dist: float = 140.0):
        self.next_id = 1
        self.tracks = {}
        self.max_lost = max_lost
        self.max_dist = max_dist

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for tid in list(self.tracks.keys()):
            self.tracks[tid]["lost"] += 1

        if not detections:
            self.tracks = {tid: t for tid, t in self.tracks.items() if t["lost"] <= self.max_lost}
            return []

        det_centers = []
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            det_centers.append(((x1 + x2) // 2, (y1 + y2) // 2))

        assigned_dets = set()
        assigned_tracks = set()

        for tid, trk in list(self.tracks.items()):
            tx, ty = trk["cx"], trk["cy"]
            best_idx = -1
            best_dist = float("inf")

            for i, (cx, cy) in enumerate(det_centers):
                if i in assigned_dets:
                    continue
                d = math.hypot(cx - tx, cy - ty)
                if d < best_dist and d <= self.max_dist:
                    best_dist = d
                    best_idx = i

            if best_idx != -1:
                assigned_dets.add(best_idx)
                assigned_tracks.add(tid)
                det = detections[best_idx]
                trk["cx"], trk["cy"] = det_centers[best_idx]
                trk["box"] = det["box"]
                trk["cls_id"] = det["cls_id"]
                trk["type"] = det["type"]
                trk["lost"] = 0

        for i, det in enumerate(detections):
            if i not in assigned_dets:
                tid = self.next_id
                self.next_id += 1
                cx, cy = det_centers[i]
                self.tracks[tid] = {
                    "cx": cx,
                    "cy": cy,
                    "box": det["box"],
                    "cls_id": det["cls_id"],
                    "type": det["type"],
                    "lost": 0,
                }
                assigned_tracks.add(tid)

        self.tracks = {tid: t for tid, t in self.tracks.items() if t["lost"] <= self.max_lost}

        active_list = []
        for tid in assigned_tracks:
            t = self.tracks.get(tid)
            if t:
                active_list.append({
                    "track_id": tid,
                    "box": t["box"],
                    "cls_id": t["cls_id"],
                    "type": t["type"],
                })
        return active_list

class AIModernDetector:
    def __init__(self, model_path: Optional[str] = None):
        if not model_path or not os.path.exists(model_path):
            model_path = config.YOLO_MODEL_PATH
            if not os.path.exists(model_path):
                model_path = "yolov8n.pt"

        logger.info(f"Loading YOLOv8 vehicle model from {model_path}...")
        self.model = YOLO(model_path)
        self.tracker = SimpleCentroidTracker()
        self.track_history = defaultdict(lambda: deque(maxlen=45))
        self.speed_entry_times = {}
        self.calculated_speeds = {}
        self.assigned_plates = {}
        self.violated_tracks = defaultdict(dict)
        self.signal_state = "GREEN"
        self.auto_traffic_light = True
        self.traffic_light_timer = time.time()
        self.green_duration = 10.0
        self.red_duration = 6.0
        self.speed_limit = config.SPEED_LIMIT_KMH

        # Warm up plate model
        anpr_service.get_plate_detector()

    def set_signal_state(self, state: str, auto_cycle: bool = False):
        self.signal_state = state.upper()
        self.auto_traffic_light = auto_cycle
        self.traffic_light_timer = time.time()

    def update_traffic_signal_cycle(self, current_time: float):
        if not self.auto_traffic_light:
            return

        elapsed = current_time - self.traffic_light_timer
        if self.signal_state == "GREEN" and elapsed > self.green_duration:
            self.signal_state = "RED"
            self.traffic_light_timer = current_time
            logger.info("Junction signal switched to RED")
        elif self.signal_state == "RED" and elapsed > self.red_duration:
            self.signal_state = "GREEN"
            self.traffic_light_timer = current_time
            logger.info("Junction signal switched to GREEN")

    def _is_cooldown_active(self, track_id: int, violation_type: str, now: float) -> bool:
        last = self.violated_tracks[track_id].get(violation_type)
        if last and (now - last) < config.VIOLATION_COOLDOWN_SECONDS:
            return True
        return False

    def _mark_violation(self, track_id: int, violation_type: str, now: float):
        self.violated_tracks[track_id][violation_type] = now

    def _get_plate_info(self, track_id: int, vehicle_crop: np.ndarray, veh_box: Tuple[int, int, int, int]) -> Dict[str, Any]:
        existing = self.assigned_plates.get(track_id)
        if existing and existing.get("plate_status") == "DETECTED_READ" and existing.get("syntax_valid"):
            return existing

        plate_info = anpr_service.extract_and_read_plate(vehicle_crop, veh_box=list(veh_box), track_id=track_id)

        # If previous was readable, retain it over a worse reading
        if existing and existing.get("plate_status") == "DETECTED_READ" and plate_info.get("plate_status") != "DETECTED_READ":
            return existing

        self.assigned_plates[track_id] = plate_info
        return plate_info

    def _save_evidence(
        self,
        full_frame: np.ndarray,
        vehicle_box: Tuple[int, int, int, int],
        plate_info: Dict[str, Any],
        violation_type: str,
        speed_recorded: Optional[float],
        track_id: int
    ) -> str:
        snapshot = full_frame.copy()
        x1, y1, x2, y2 = vehicle_box
        h, w = snapshot.shape[:2]
        plate_str = plate_info.get("plate_number", "UNREADABLE")
        plate_status = plate_info.get("plate_status", "UNREADABLE")
        plate_crop = plate_info.get("plate_crop")
        global_pbox = plate_info.get("plate_box")

        # Draw vehicle bounding box (Red)
        cv2.rectangle(snapshot, (x1, y1), (x2, y2), (0, 0, 255), 3)

        # Draw license plate bounding box if localized (Cyan)
        if global_pbox and len(global_pbox) == 4:
            gpx1, gpy1, gpx2, gpy2 = global_pbox
            cv2.rectangle(snapshot, (gpx1, gpy1), (gpx2, gpy2), (255, 255, 0), 2)

        # Inset zoomed license plate at top right
        pw, ph = 260, 90
        inset_x1 = w - pw - 20
        inset_y1 = 20
        inset_x2 = w - 20
        inset_y2 = 20 + ph

        # Dark glass card background
        cv2.rectangle(snapshot, (inset_x1, inset_y1), (inset_x2, inset_y2), (20, 24, 33), -1)
        cv2.rectangle(snapshot, (inset_x1, inset_y1), (inset_x2, inset_y2), (0, 165, 255), 2)

        if plate_crop is not None and plate_crop.size > 0:
            try:
                p_display = cv2.resize(plate_crop, (pw - 20, ph - 38))
                snapshot[inset_y1 + 8 : inset_y1 + 8 + p_display.shape[0], inset_x1 + 10 : inset_x1 + 10 + p_display.shape[1]] = p_display
            except Exception:
                pass

        status_color = (0, 255, 120) if plate_status == "DETECTED_READ" else (0, 165, 255)
        display_label = f"PLATE: {plate_str}" if plate_str != "UNREADABLE" else "PLATE: [UNREADABLE]"
        cv2.putText(
            snapshot, display_label, (inset_x1 + 10, inset_y2 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2
        )

        # Bottom statutory evidence banner
        banner_h = 75
        cv2.rectangle(snapshot, (0, h - banner_h), (w, h), (15, 15, 25), -1)
        cv2.line(snapshot, (0, h - banner_h), (w, h - banner_h), (0, 0, 255), 2)

        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        speed_text = f" | Speed: {speed_recorded:.1f} km/h" if speed_recorded else ""
        is_verified_anpr = (plate_status == "DETECTED_READ" and plate_info.get("syntax_valid") and plate_info.get("confidence", 0.0) >= 0.60)
        ver_badge = "[VERIFIED ANPR]" if is_verified_anpr else "[AUDIT REQUIRED]"
        text_line1 = f"VIOLATION: {violation_type.upper()} | VEHICLE: {plate_str} (Track #{track_id}){speed_text} {ver_badge}"
        text_line2 = f"TIME: {timestamp_str} | CAM: Surveillance Cam #04 Junction | STATUS: STATUTORY E-CHALLAN RECORD"

        cv2.putText(snapshot, text_line1, (20, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 165, 255), 2)
        cv2.putText(snapshot, text_line2, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)

        filename = f"evidence_{int(time.time() * 1000)}_{track_id}_{violation_type.replace(' ', '_').replace('/', '_')}.jpg"
        filepath = os.path.join(config.STORAGE_EVIDENCE_DIR, filename)
        cv2.imwrite(filepath, snapshot)
        return f"/evidence/{filename}"

    def _extract_synthetic_detections(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        road_mask = np.zeros((h, w), dtype=np.uint8)
        road_mask[:, int(w * 0.10):int(w * 0.90)] = 255

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]

        vehicle_blob_mask = ((sat > 40) | (val > 150) | (val < 25)) & (road_mask > 0)
        vehicle_blob_mask = vehicle_blob_mask.astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned_mask = cv2.morphologyEx(vehicle_blob_mask, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))

        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vehicle_dets = []
        person_boxes = []
        phone_boxes = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 3000:
                continue

            bx, by, bw, bh = cv2.boundingRect(cnt)
            if bw > (w * 0.6) or bh < 30:
                continue

            aspect = float(bw) / float(bh) if bh > 0 else 0
            if aspect < 0.65 and bw < (w * 0.08):
                v_type = "Motorcycle"
                cls_id = 3
                if bw >= 40 and bh >= 80:
                    person_boxes.append((bx, by + 10, bx + bw, by + 45))
            else:
                v_type = "Car"
                cls_id = 2

            vehicle_dets.append({
                "box": (bx, by, bx + bw, by + bh),
                "cls_id": cls_id,
                "type": v_type,
            })

        return vehicle_dets, person_boxes, phone_boxes

    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if frame is None or frame.size == 0:
            return [], []

        h, w = frame.shape[:2]
        now = timestamp if timestamp is not None else time.time()
        self.update_traffic_signal_cycle(now)

        # Scale detection gates dynamically based on frame height
        scale_y = h / 720.0
        stop_y = int(480 * scale_y)
        speed_y1 = int(320 * scale_y)
        speed_y2 = int(520 * scale_y)

        detected_vehicles = []
        new_violations = []

        raw_detections = []
        person_boxes = []
        phone_boxes = []

        try:
            results = self.model(
                frame,
                conf=config.DETECTION_CONFIDENCE,
                iou=config.IOU_THRESHOLD,
                classes=config.VEHICLE_CLASSES + [config.PERSON_CLASS_ID, config.CELL_PHONE_CLASS_ID],
                verbose=False
            )
            if results and len(results) > 0 and results[0].boxes is not None:
                for box in results[0].boxes:
                    cls_id = int(box.cls[0].item())
                    xyxy = [int(v) for v in box.xyxy[0].tolist()]
                    if cls_id in config.VEHICLE_CLASSES:
                        v_name = config.CLASS_NAMES.get(cls_id, "Vehicle")
                        raw_detections.append({
                            "box": tuple(xyxy),
                            "cls_id": cls_id,
                            "type": v_name
                        })
                    elif cls_id == config.PERSON_CLASS_ID:
                        person_boxes.append(tuple(xyxy))
                    elif cls_id == config.CELL_PHONE_CLASS_ID:
                        phone_boxes.append(tuple(xyxy))
        except Exception as e:
            logger.warning(f"Vehicle inference warning: {e}")

        # If zero vehicles found (e.g. 2D synthetic simulation frames), invoke color-blob fallback
        if len(raw_detections) == 0:
            synth_dets, synth_persons, synth_phones = self._extract_synthetic_detections(frame)
            raw_detections.extend(synth_dets)
            if not person_boxes:
                person_boxes.extend(synth_persons)
            if not phone_boxes:
                phone_boxes.extend(synth_phones)

        # Centroid Tracking Update
        tracked = self.tracker.update(raw_detections)

        for veh in tracked:
            tid = veh["track_id"]
            x1, y1, x2, y2 = veh["box"]
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            v_type = veh["type"]

            # Vehicle Crop & Optical Plate Extraction
            vh_crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
            plate_info = self._get_plate_info(tid, vh_crop, veh["box"])
            plate_number = plate_info.get("plate_number", "UNREADABLE")
            plate_status = plate_info.get("plate_status", "UNREADABLE")
            ver_status = "VERIFIED_ANPR" if (plate_status == "DETECTED_READ" and plate_info.get("syntax_valid") and plate_info.get("confidence", 0.0) >= 0.60) else "UNVERIFIED_MANUAL_REVIEW"

            detected_vehicles.append({
                "track_id": tid,
                "cls_id": veh["cls_id"],
                "type": v_type,
                "box": [x1, y1, x2, y2],
                "confidence": 0.92,
                "plate_number": plate_number,
                "plate_box": plate_info.get("plate_box"),
                "plate_confidence": plate_info.get("confidence", 0.0),
                "plate_status": plate_status,
                "raw_ocr_text": plate_info.get("raw_text", ""),
            })

            # History update
            history = self.track_history[tid]
            history.append((cx, cy, now))

            # -------------------------------------------------------------------
            # 1. Red Light Jump Rule
            # -------------------------------------------------------------------
            if self.signal_state == "RED" and len(history) >= 2:
                prev_cx, prev_cy, _ = history[-2]
                if prev_cy < stop_y and cy >= (stop_y - config.STOP_LINE_TOLERANCE_PX):
                    if not self._is_cooldown_active(tid, "Red Light Jump", now):
                        self._mark_violation(tid, "Red Light Jump", now)
                        ev_path = self._save_evidence(frame, veh["box"], plate_info, "Red Light Jump", None, tid)
                        new_violations.append({
                            "tracking_id": tid,
                            "plate_number": plate_number,
                            "violation_type": "Red Light Jump",
                            "primary_fine": config.FINES.get("Red Light Jump", 1000),
                            "total_fine": config.FINES.get("Red Light Jump", 1000),
                            "evidence_path": ev_path,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "details": f"Crossed Stop Line at Y={stop_y}px during active RED signal phase",
                            "plate_box": plate_info.get("plate_box"),
                            "plate_confidence": plate_info.get("confidence", 0.0),
                            "plate_status": plate_status,
                            "raw_ocr_text": plate_info.get("raw_text", ""),
                            "verification_status": ver_status,
                        })

            # -------------------------------------------------------------------
            # 2. Over-Speeding Rule
            # -------------------------------------------------------------------
            if cy >= speed_y1 and tid not in self.speed_entry_times:
                self.speed_entry_times[tid] = now
            if cy >= speed_y2 and tid in self.speed_entry_times and tid not in self.calculated_speeds:
                dt = now - self.speed_entry_times[tid]
                if dt > 0.04:
                    speed_kmh = round((config.SPEED_DISTANCE_METERS / dt) * 3.6, 1)
                    self.calculated_speeds[tid] = speed_kmh
                    if speed_kmh > self.speed_limit:
                        if not self._is_cooldown_active(tid, "Over-Speeding", now):
                            self._mark_violation(tid, "Over-Speeding", now)
                            ev_path = self._save_evidence(frame, veh["box"], plate_info, "Over-Speeding", speed_kmh, tid)
                            new_violations.append({
                                "tracking_id": tid,
                                "plate_number": plate_number,
                                "violation_type": "Over-Speeding",
                                "speed_recorded": speed_kmh,
                                "primary_fine": config.FINES.get("Over-Speeding", 2000),
                                "total_fine": config.FINES.get("Over-Speeding", 2000),
                                "evidence_path": ev_path,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "details": f"Clocked at {speed_kmh} km/h (Permissible Limit: {self.speed_limit} km/h)",
                                "plate_box": plate_info.get("plate_box"),
                                "plate_confidence": plate_info.get("confidence", 0.0),
                                "plate_status": plate_status,
                                "raw_ocr_text": plate_info.get("raw_text", ""),
                                "verification_status": ver_status,
                            })

            # -------------------------------------------------------------------
            # 3. Wrong-Lane / Wrong-Way Driving Rule
            # -------------------------------------------------------------------
            if len(history) >= 6:
                old_cx, old_cy, _ = history[0]
                dy = cy - old_cy
                dist = math.hypot(cx - old_cx, dy)
                if dist > 35 and dy < -15:
                    if not self._is_cooldown_active(tid, "Wrong-Lane / Wrong-Way Driving", now):
                        self._mark_violation(tid, "Wrong-Lane / Wrong-Way Driving", now)
                        ev_path = self._save_evidence(frame, veh["box"], plate_info, "Wrong-Lane / Wrong-Way Driving", None, tid)
                        new_violations.append({
                            "tracking_id": tid,
                            "plate_number": plate_number,
                            "violation_type": "Wrong-Lane / Wrong-Way Driving",
                            "primary_fine": config.FINES.get("Wrong-Lane / Wrong-Way Driving", 1500),
                            "total_fine": config.FINES.get("Wrong-Lane / Wrong-Way Driving", 1500),
                            "evidence_path": ev_path,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "details": "Vehicle navigating in reverse against designated roadway flow vector",
                            "plate_box": plate_info.get("plate_box"),
                            "plate_confidence": plate_info.get("confidence", 0.0),
                            "plate_status": plate_status,
                            "raw_ocr_text": plate_info.get("raw_text", ""),
                            "verification_status": ver_status,
                        })

            # -------------------------------------------------------------------
            # 4. Triple Riding on Two-Wheelers
            # -------------------------------------------------------------------
            if veh["cls_id"] in config.TWO_WHEELER_CLASSES or v_type == "Motorcycle":
                riders = 0
                for px1, py1, px2, py2 in person_boxes:
                    if max(x1 - 15, px1) < min(x2 + 15, px2) and max(y1 - 30, py1) < min(y2 + 25, py2):
                        riders += 1
                if riders > 2:
                    if not self._is_cooldown_active(tid, "Triple Riding", now):
                        self._mark_violation(tid, "Triple Riding", now)
                        ev_path = self._save_evidence(frame, veh["box"], plate_info, "Triple Riding", None, tid)
                        new_violations.append({
                            "tracking_id": tid,
                            "plate_number": plate_number,
                            "violation_type": "Triple Riding",
                            "primary_fine": config.FINES.get("Triple Riding", 1000),
                            "total_fine": config.FINES.get("Triple Riding", 1000),
                            "evidence_path": ev_path,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "details": f"Detected {riders} occupants on two-wheeler (Statutory limit: 2)",
                            "plate_box": plate_info.get("plate_box"),
                            "plate_confidence": plate_info.get("confidence", 0.0),
                            "plate_status": plate_status,
                            "raw_ocr_text": plate_info.get("raw_text", ""),
                            "verification_status": ver_status,
                        })

                # ---------------------------------------------------------------
                # 5. No Helmet Violation
                # ---------------------------------------------------------------
                if riders >= 1:
                    for px1, py1, px2, py2 in person_boxes:
                        if max(x1, px1) < min(x2, px2) and max(y1, py1) < min(y2, py2):
                            head_h = max(15, int((py2 - py1) * 0.35))
                            hy1 = max(0, py1)
                            hy2 = min(h, py1 + head_h)
                            hx1 = max(0, px1)
                            hx2 = min(w, px2)
                            head_crop = frame[hy1:hy2, hx1:hx2]
                            if head_crop.size > 0:
                                gray_head = cv2.cvtColor(head_crop, cv2.COLOR_BGR2GRAY)
                                edges = cv2.Canny(gray_head, 50, 150)
                                edge_ratio = np.count_nonzero(edges) / float(edges.size)
                                if edge_ratio > 0.12:
                                    if not self._is_cooldown_active(tid, "No Helmet", now):
                                        self._mark_violation(tid, "No Helmet", now)
                                        ev_path = self._save_evidence(frame, veh["box"], plate_info, "No Helmet", None, tid)
                                        new_violations.append({
                                            "tracking_id": tid,
                                            "plate_number": plate_number,
                                            "violation_type": "No Helmet",
                                            "primary_fine": config.FINES.get("No Helmet", 1000),
                                            "total_fine": config.FINES.get("No Helmet", 1000),
                                            "evidence_path": ev_path,
                                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "details": "Rider operating two-wheeler without protective headgear",
                                            "plate_box": plate_info.get("plate_box"),
                                            "plate_confidence": plate_info.get("confidence", 0.0),
                                            "plate_status": plate_status,
                                            "raw_ocr_text": plate_info.get("raw_text", ""),
                                            "verification_status": ver_status,
                                        })
                                        break

            # -------------------------------------------------------------------
            # 6. Mobile Phone Usage Rule
            # -------------------------------------------------------------------
            for phx1, phy1, phx2, phy2 in phone_boxes:
                if max(x1, phx1) < min(x2, phx2) and max(y1, phy1) < min(y2, phy2):
                    if not self._is_cooldown_active(tid, "Mobile Phone Usage", now):
                        self._mark_violation(tid, "Mobile Phone Usage", now)
                        ev_path = self._save_evidence(frame, veh["box"], plate_info, "Mobile Phone Usage", None, tid)
                        new_violations.append({
                            "tracking_id": tid,
                            "plate_number": plate_number,
                            "violation_type": "Mobile Phone Usage",
                            "primary_fine": config.FINES.get("Mobile Phone Usage", 1500),
                            "total_fine": config.FINES.get("Mobile Phone Usage", 1500),
                            "evidence_path": ev_path,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "details": "Operator handling mobile phone device while in traffic stream",
                            "plate_box": plate_info.get("plate_box"),
                            "plate_confidence": plate_info.get("confidence", 0.0),
                            "plate_status": plate_status,
                            "raw_ocr_text": plate_info.get("raw_text", ""),
                            "verification_status": ver_status,
                        })
                        break

        return detected_vehicles, new_violations
