"""
Multi-Camera Stream Manager for 4-Way Adaptive Intersection Surveillance
AI-Powered Intelligent Vehicle Identification and Traffic Violation Detection System using ANPR

Manages four concurrent camera feeds (NORTH, EAST, SOUTH, WEST), runs a shared
YOLOv8 detector on each, feeds vehicle-type detections into AdaptiveSignalController,
and continues running full violation-detection + ANPR + e-Challan enforcement on every lane.

Architecture
------------
• Each direction runs as a daemon Thread → cv2.VideoCapture → YOLO → shared result dict.
• The public API exposes a lock-protected snapshot dict read by the Streamlit HUD.
• The signal controller tick() is called from a separate lightweight timer thread.
• Violation detection (detector.py) is optionally enabled per-lane.
"""

import cv2
import time
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from ultralytics import YOLO

import config
from signal_controller import AdaptiveSignalController, PHASE_GREEN, PHASE_YELLOW, PHASE_RED
from detector import TrafficViolationDetector

logger = logging.getLogger("MultiCameraManager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# Lane Worker Thread
# ---------------------------------------------------------------------------

class LaneCameraThread(threading.Thread):
    """
    Daemon thread that continuously reads frames from one camera source,
    runs YOLO inference, and updates the shared result dict.

    Detection results (vehicle types, annotated frame) are written to
    `shared_state[direction]` under `lock` protection every processed frame.
    """

    def __init__(
        self,
        direction:    str,
        source:       Any,           # int | str (path / RTSP URL)
        model:        YOLO,
        shared_state: Dict,
        lock:         threading.Lock,
        signal_ctrl:  AdaptiveSignalController,
        violation_detector: Optional[TrafficViolationDetector] = None,
        frame_skip:   int = 2,       # process every Nth frame for CPU headroom
    ):
        super().__init__(daemon=True, name=f"LaneCam-{direction}")
        self.direction           = direction
        self.source              = source
        self.model               = model
        self.shared_state        = shared_state
        self.lock                = lock
        self.signal_ctrl         = signal_ctrl
        self.violation_detector  = violation_detector
        self.frame_skip          = frame_skip

        self._stop_event         = threading.Event()
        self.frames_processed    = 0
        self.last_fps            = 0.0

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        cap = self._open_capture()
        if cap is None:
            logger.error(f"[{self.direction}] Failed to open camera source: {self.source}")
            return

        frame_idx   = 0
        t_fps_start = time.time()
        fps_counter = 0

        logger.info(f"[{self.direction}] Camera thread started → source: {self.source}")

        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                # Loop video files; reconnect live streams
                if isinstance(self.source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning(f"[{self.direction}] Stream lost — reconnecting in 2s …")
                    cap.release()
                    time.sleep(2.0)
                    cap = self._open_capture()
                    if cap is None:
                        break
                    continue

            frame_idx += 1
            fps_counter += 1

            # FPS measurement
            elapsed_fps = time.time() - t_fps_start
            if elapsed_fps >= 1.0:
                self.last_fps   = fps_counter / elapsed_fps
                fps_counter     = 0
                t_fps_start     = time.time()

            # Skip frames to reduce CPU load
            if frame_idx % self.frame_skip != 0:
                continue

            # Resize to tile resolution for efficient inference
            frame_resized = cv2.resize(frame, (config.CAMERA_TILE_WIDTH, config.CAMERA_TILE_HEIGHT))

            # --- YOLO Detection ---
            detected_types, annotated = self._detect_vehicles(frame_resized)

            # Feed into adaptive signal controller
            self.signal_ctrl.update_lane_density(self.direction, detected_types)
            self.frames_processed += 1

            # --- Optional Full Violation Detection (on full-res frame) ---
            new_violations: List[Dict] = []
            if self.violation_detector is not None:
                try:
                    _, new_violations = self.violation_detector.process_frame(frame)
                except Exception as exc:
                    logger.warning(f"[{self.direction}] Violation detector error: {exc}")

            # Overlay direction compass label on tile
            annotated = self._draw_direction_label(annotated, detected_types)

            # Write to shared state (lock-protected)
            with self.lock:
                self.shared_state[self.direction] = {
                    "frame":          annotated,
                    "vehicle_count":  len(detected_types),
                    "vehicle_types":  detected_types,
                    "density_score":  self.signal_ctrl.lanes[self.direction].density_score,
                    "green_seconds":  self.signal_ctrl.schedule.get(self.direction, config.MIN_GREEN_TIME),
                    "fps":            round(self.last_fps, 1),
                    "violations":     new_violations,
                    "timestamp":      time.time(),
                }

        cap.release()
        logger.info(f"[{self.direction}] Camera thread stopped.")

    # ------------------------------------------------------------------

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        """Opens a cv2.VideoCapture for self.source with retry logic."""
        for attempt in range(3):
            cap = cv2.VideoCapture(self.source)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.CAMERA_TILE_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_TILE_HEIGHT)
                return cap
            logger.warning(f"[{self.direction}] Open attempt {attempt+1}/3 failed for {self.source}")
            time.sleep(0.5)
        return None

    def _detect_vehicles(self, frame: np.ndarray) -> Tuple[List[str], np.ndarray]:
        """
        Runs YOLO inference on a single frame.
        Returns:
            detected_types  – list of class name strings for traffic-relevant classes
            annotated_frame – frame with bounding boxes drawn (lightweight HUD)
        """
        annotated = frame.copy()
        detected_types: List[str] = []

        try:
            results = self.model(
                frame,
                conf=config.SIGNAL_DETECTION_CONFIDENCE,
                classes=config.VEHICLE_CLASSES + [config.PERSON_CLASS_ID],
                verbose=False
            )

            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    cls_id = int(box.cls[0].item())
                    xyxy   = [int(v) for v in box.xyxy[0].tolist()]
                    conf   = float(box.conf[0].item())

                    # Map class ID → weight-table key
                    label = config.CLASS_NAMES.get(cls_id, "vehicle").lower()
                    if cls_id in config.VEHICLE_CLASSES:
                        detected_types.append(label)

                    # Lightweight box drawing
                    color = (0, 255, 0) if cls_id in config.VEHICLE_CLASSES else (200, 200, 200)
                    x1, y1, x2, y2 = xyxy
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1)
                    cv2.putText(
                        annotated, f"{label} {conf:.2f}",
                        (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 1
                    )
        except Exception as exc:
            logger.warning(f"[{self.direction}] YOLO inference error: {exc}")

        return detected_types, annotated

    def _draw_direction_label(self, frame: np.ndarray, types: List[str]) -> np.ndarray:
        """
        Overlays the direction compass label, vehicle count, and allocated green time
        in the top-left corner of the camera tile.
        """
        h, w = frame.shape[:2]
        label   = config.DIRECTION_EMOJI.get(self.direction, self.direction)
        count   = len(types)
        g_time  = self.signal_ctrl.schedule.get(self.direction, config.MIN_GREEN_TIME)
        fps_str = f"{self.last_fps:.0f} FPS"

        # Translucent banner
        banner = frame.copy()
        cv2.rectangle(banner, (0, 0), (w, 36), (10, 10, 20), -1)
        alpha  = 0.65
        frame  = cv2.addWeighted(banner, alpha, frame, 1 - alpha, 0)

        cv2.putText(frame, f"{label}  |  Vehicles: {count}  |  Green: {g_time}s  |  {fps_str}",
                    (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (240, 240, 255), 1)
        return frame


# ---------------------------------------------------------------------------
# Multi-Camera Manager (orchestrator)
# ---------------------------------------------------------------------------

class MultiCameraManager:
    """
    Orchestrates 4 LaneCameraThreads + AdaptiveSignalController + signal ticker.

    Usage
    -----
    mgr = MultiCameraManager(enable_violation_detection=True)
    mgr.start()

    # Each Streamlit rerun:
    state      = mgr.get_snapshot()           # intersection state + 4 frames
    signal_hud = mgr.signal_ctrl.get_intersection_state()

    mgr.stop()
    """

    def __init__(
        self,
        camera_sources:            Optional[Dict[str, Any]] = None,
        enable_violation_detection: bool = False,
        frame_skip:                 int  = 2,
    ):
        # Resolve camera sources (override defaults if provided)
        self.sources = camera_sources if camera_sources else dict(config.CAMERA_SOURCES)
        self.frame_skip = frame_skip

        # Shared YOLO model (thread-safe read-only after init)
        logger.info("Loading shared YOLOv8 model for multi-camera manager …")
        self.model = YOLO(config.YOLO_MODEL_NAME)
        logger.info("YOLOv8 loaded.")

        # Adaptive signal controller
        self.signal_ctrl = AdaptiveSignalController()

        # Per-direction violation detectors (optional — memory-intensive)
        self.violation_detectors: Dict[str, Optional[TrafficViolationDetector]] = {}
        if enable_violation_detection:
            for d in config.SIGNAL_DIRECTIONS:
                self.violation_detectors[d] = TrafficViolationDetector(
                    model_path=config.YOLO_MODEL_NAME
                )
        else:
            for d in config.SIGNAL_DIRECTIONS:
                self.violation_detectors[d] = None

        # Shared state dict & thread-safety lock
        self.shared_state: Dict[str, Any] = {
            d: {
                "frame":         _blank_tile(),
                "vehicle_count": 0,
                "vehicle_types": [],
                "density_score": 0.0,
                "green_seconds": config.MIN_GREEN_TIME,
                "fps":           0.0,
                "violations":    [],
                "timestamp":     time.time(),
            }
            for d in config.SIGNAL_DIRECTIONS
        }
        self.lock = threading.Lock()

        # Worker threads
        self._lane_threads: Dict[str, LaneCameraThread] = {}

        # Signal tick thread (advances phase state machine at 10 Hz)
        self._tick_thread: Optional[threading.Thread] = None
        self._stop_tick   = threading.Event()

        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Starts all lane camera threads and the signal tick thread."""
        if self._running:
            return

        for direction in config.SIGNAL_DIRECTIONS:
            source = self.sources.get(direction)
            if source is None:
                logger.info(f"[{direction}] No source configured — lane disabled.")
                continue

            thread = LaneCameraThread(
                direction          = direction,
                source             = source,
                model              = self.model,
                shared_state       = self.shared_state,
                lock               = self.lock,
                signal_ctrl        = self.signal_ctrl,
                violation_detector = self.violation_detectors.get(direction),
                frame_skip         = self.frame_skip,
            )
            thread.start()
            self._lane_threads[direction] = thread

        # Signal ticker thread at ~10 Hz
        self._stop_tick.clear()
        self._tick_thread = threading.Thread(
            target=self._signal_tick_loop,
            daemon=True,
            name="SignalTicker"
        )
        self._tick_thread.start()
        self._running = True
        logger.info("MultiCameraManager started — all lane threads running.")

    def stop(self) -> None:
        """Gracefully stops all threads."""
        self._stop_tick.set()
        for thread in self._lane_threads.values():
            thread.stop()
        for thread in self._lane_threads.values():
            thread.join(timeout=3.0)
        self._lane_threads.clear()
        self._running = False
        logger.info("MultiCameraManager stopped.")

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Returns a lock-protected copy of the latest shared state for all lanes.
        Safe to call from Streamlit's main thread.
        """
        with self.lock:
            return {d: dict(self.shared_state[d]) for d in config.SIGNAL_DIRECTIONS}

    def reconfigure_source(self, direction: str, new_source: Any) -> None:
        """Hot-swap a camera source at runtime."""
        self.sources[direction] = new_source
        config.CAMERA_SOURCES[direction] = new_source

        # Stop old thread and start a new one
        old = self._lane_threads.get(direction)
        if old:
            old.stop()
            old.join(timeout=3.0)

        if new_source is not None:
            t = LaneCameraThread(
                direction          = direction,
                source             = new_source,
                model              = self.model,
                shared_state       = self.shared_state,
                lock               = self.lock,
                signal_ctrl        = self.signal_ctrl,
                violation_detector = self.violation_detectors.get(direction),
                frame_skip         = self.frame_skip,
            )
            t.start()
            self._lane_threads[direction] = t
            logger.info(f"[{direction}] Reconfigured → new source: {new_source}")

    def compose_grid_frame(
        self,
        snapshot: Optional[Dict] = None,
        signal_state: Optional[Dict] = None,
        target_w: int = 1280,
        target_h: int = 720,
    ) -> np.ndarray:
        """
        Composes a 2×2 camera grid with an embedded signal HUD overlay.

        Layout:
          ┌──────────┬──────────┐
          │  NORTH   │  EAST    │
          ├──────────┼──────────┤
          │  WEST    │  SOUTH   │
          └──────────┴──────────┘

        Overlays the active-direction border highlight and phase timer bar.
        """
        if snapshot is None:
            snapshot = self.get_snapshot()
        if signal_state is None:
            signal_state = self.signal_ctrl.get_intersection_state()

        tile_w = target_w  // 2
        tile_h = (target_h - 60) // 2  # 60 px reserved for bottom status bar

        order  = [("NORTH", "EAST"), ("WEST", "SOUTH")]
        rows   = []

        for row_dirs in order:
            cols = []
            for d in row_dirs:
                raw_frame = snapshot[d].get("frame")
                if raw_frame is None or raw_frame.size == 0:
                    tile = _blank_tile(tile_w, tile_h)
                    tile = _draw_offline_banner(tile, d)
                else:
                    tile = cv2.resize(raw_frame, (tile_w, tile_h))

                # Highlight active-direction tile with coloured border
                border_color_hex = signal_state["direction_colors"].get(d, "#ef4444")
                border_color_bgr = _hex_to_bgr(border_color_hex)
                thickness = 4 if d == signal_state["active_direction"] else 2
                cv2.rectangle(tile, (0, 0), (tile_w - 1, tile_h - 1), border_color_bgr, thickness)

                # Phase-state label at top-right of active tile
                if d == signal_state["active_direction"]:
                    state_label = signal_state["phase_state"]
                    remaining   = signal_state["remaining_seconds"]
                    label_text  = f"{state_label}  {remaining:.0f}s"
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
                    cv2.rectangle(tile, (tile_w - tw - 14, 4), (tile_w - 4, th + 10), border_color_bgr, -1)
                    cv2.putText(tile, label_text, (tile_w - tw - 10, th + 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

                cols.append(tile)
            rows.append(np.hstack(cols))

        grid = np.vstack(rows)

        # Bottom status bar
        status_bar = np.zeros((60, target_w, 3), dtype=np.uint8)
        status_bar[:] = (12, 16, 28)
        active   = signal_state["active_direction"]
        phase    = signal_state["phase_state"]
        schedule = signal_state["schedule"]
        sched_text = "  |  ".join(
            f"{d}: {t}s" for d, t in schedule.items()
        )
        cv2.putText(status_bar,
                    f"ACTIVE: {active}  [{phase}]   Green Schedule → {sched_text}",
                    (12, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 230, 255), 1)

        return np.vstack([grid, status_bar])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _signal_tick_loop(self) -> None:
        """Calls signal_ctrl.tick() at ~10 Hz to advance the phase machine."""
        while not self._stop_tick.is_set():
            self.signal_ctrl.tick()
            time.sleep(0.10)


# ---------------------------------------------------------------------------
# Small helper utilities
# ---------------------------------------------------------------------------

def _blank_tile(w: int = config.CAMERA_TILE_WIDTH, h: int = config.CAMERA_TILE_HEIGHT) -> np.ndarray:
    tile = np.zeros((h, w, 3), dtype=np.uint8)
    tile[:] = (18, 24, 38)
    return tile


def _draw_offline_banner(tile: np.ndarray, direction: str) -> np.ndarray:
    h, w = tile.shape[:2]
    label = config.DIRECTION_EMOJI.get(direction, direction)
    cv2.putText(tile, f"{label}", (w // 2 - 60, h // 2 - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (80, 80, 110), 2)
    cv2.putText(tile, "CAMERA OFFLINE", (w // 2 - 80, h // 2 + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 60, 80), 1)
    return tile


def _hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    r, g, b   = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)
