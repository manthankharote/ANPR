"""
4-Way Adaptive Traffic Signal Controller
AI-Powered Intelligent Vehicle Identification and Traffic Violation Detection System using ANPR

Computes optimal green-phase durations for a 4-direction signalised intersection
based on real-time per-lane vehicle density measurements using the weighted model:

    D_i  =  Σ w_type · N_type              (Weighted density score for lane i)
    T_i  =  clamp( round(T_base + k·D_i), T_min, T_max )

Low-density shortcut (≤ 3 vehicles):
    T_i  =  max( T_min,  N_i × 2.5 )

Phase sequence: GREEN → YELLOW → ALL-RED (clearance) → next direction GREEN
"""

import math
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import config

logger = logging.getLogger("SignalController")


# ---------------------------------------------------------------------------
# Phase state constants
# ---------------------------------------------------------------------------
PHASE_GREEN  = "GREEN"
PHASE_YELLOW = "YELLOW"
PHASE_RED    = "RED"


@dataclass
class PhaseRecord:
    """Immutable record of one completed signal phase (persisted for analytics)."""
    direction:     str
    green_seconds: int
    vehicle_count: int
    density_score: float
    timestamp:     float = field(default_factory=time.time)


@dataclass
class LaneSnapshot:
    """
    Current real-time state of one approach lane.
    Updated every processing cycle by MultiCameraManager.
    """
    direction:     str
    vehicle_count: int                = 0
    vehicle_types: List[str]          = field(default_factory=list)
    density_score: float              = 0.0
    green_seconds: int                = 0       # allocated green time for next phase
    frame:         Optional[object]   = None    # latest annotated numpy frame


class AdaptiveSignalController:
    """
    4-Way Dynamic Adaptive Traffic Signal Controller.

    Responsibilities
    ----------------
    1. Receives per-direction vehicle-detection lists from MultiCameraManager.
    2. Computes weighted density D_i per lane.
    3. Solves the green-time allocation T_i for each lane.
    4. Sequences phases: GREEN → YELLOW → ALL-RED → next GREEN.
    5. Exposes live state via `get_intersection_state()` for the Streamlit HUD.
    """

    def __init__(
        self,
        min_green:  int   = config.MIN_GREEN_TIME,
        max_green:  int   = config.MAX_GREEN_TIME,
        yellow_dur: int   = config.YELLOW_DURATION,
        all_red_dur: int  = config.ALL_RED_CLEARANCE,
    ):
        self.min_green   = min_green
        self.max_green   = max_green
        self.yellow_dur  = yellow_dur
        self.all_red_dur = all_red_dur

        self.directions: List[str]  = list(config.SIGNAL_DIRECTIONS)   # [N, E, S, W]

        # Current phase sequencer state
        self.phase_idx:    int   = 0          # index into self.directions
        self.phase_state:  str   = PHASE_GREEN
        self.phase_start:  float = time.time()
        self.phase_budget: int   = min_green  # seconds allocated to current green

        # Per-direction latest lane snapshot (updated externally by camera manager)
        self.lanes: Dict[str, LaneSnapshot] = {
            d: LaneSnapshot(direction=d) for d in self.directions
        }

        # Ephemeral all-directions schedule (recalculated each cycle)
        self.schedule: Dict[str, int] = {d: min_green for d in self.directions}

        # Historical log (capped at 200 records for memory safety)
        self.phase_history: deque[PhaseRecord] = deque(maxlen=200)

        # Telemetry counters
        self.total_cycles:        int   = 0
        self.total_green_seconds: float = 0.0

        logger.info(
            "AdaptiveSignalController ready — "
            f"T_min={min_green}s, T_max={max_green}s, "
            f"T_yellow={yellow_dur}s, T_all_red={all_red_dur}s"
        )

    # ------------------------------------------------------------------
    # Public API — called by MultiCameraManager on each detection update
    # ------------------------------------------------------------------

    def update_lane_density(self, direction: str, detected_types: List[str]) -> None:
        """
        Receive fresh vehicle-type list from a camera feed and recompute
        density + green-time allocation for that lane.

        Parameters
        ----------
        direction      : One of 'NORTH' | 'EAST' | 'SOUTH' | 'WEST'
        detected_types : Vehicle class names detected in this frame,
                         e.g. ['car', 'car', 'motorcycle', 'bus']
        """
        if direction not in self.lanes:
            logger.warning(f"Unknown direction '{direction}' — skipping.")
            return

        density = self._compute_weighted_density(detected_types)
        green_t = self._calculate_green_time(detected_types)

        lane = self.lanes[direction]
        lane.vehicle_count = len(detected_types)
        lane.vehicle_types = list(detected_types)
        lane.density_score = density
        lane.green_seconds = green_t

        self.schedule[direction] = green_t

    def tick(self) -> Tuple[str, str]:
        """
        Advance the signal-phase state machine by one clock tick.
        Must be called frequently (e.g. every 100 ms) by the camera-manager thread.

        Returns
        -------
        (active_direction, phase_state) — the current active direction and its phase.
        """
        now     = self.time_now()
        elapsed = now - self.phase_start
        active  = self.directions[self.phase_idx]

        if self.phase_state == PHASE_GREEN:
            if elapsed >= self.phase_budget:
                self._transition_to(PHASE_YELLOW)

        elif self.phase_state == PHASE_YELLOW:
            if elapsed >= self.yellow_dur:
                self._transition_to(PHASE_RED)

        elif self.phase_state == PHASE_RED:
            if elapsed >= self.all_red_dur:
                # Record completed phase
                lane = self.lanes[active]
                self.phase_history.append(PhaseRecord(
                    direction     = active,
                    green_seconds = self.phase_budget,
                    vehicle_count = lane.vehicle_count,
                    density_score = lane.density_score,
                ))
                self.total_cycles        += 1
                self.total_green_seconds += self.phase_budget

                # Advance to next direction and compute its green time
                self.phase_idx = (self.phase_idx + 1) % len(self.directions)
                next_dir       = self.directions[self.phase_idx]
                self.phase_budget = self.schedule.get(next_dir, self.min_green)
                if self.phase_budget == 0:
                    self.phase_budget = self.min_green   # never grant 0 s to empty lane
                self._transition_to(PHASE_GREEN)

        return active, self.phase_state

    # ------------------------------------------------------------------
    # Intersection-level state snapshot for Streamlit HUD
    # ------------------------------------------------------------------

    def get_intersection_state(self) -> Dict:
        """
        Returns a complete, HUD-ready snapshot of the intersection state.

        Schema
        ------
        {
          "active_direction": str,
          "phase_state":      str,   # GREEN | YELLOW | RED
          "elapsed_seconds":  float,
          "remaining_seconds":float,  # seconds left in current GREEN phase
          "phase_budget":     int,
          "schedule":         {direction: green_seconds},
          "lanes":            {direction: {count, density, green_t, types}},
          "history_tail":     [PhaseRecord, ...],  # last 8 phases
          "total_cycles":     int,
          "avg_green_time":   float,
          "direction_colors": {direction: color_str}  # for HUD rendering
        }
        """
        now     = self.time_now()
        elapsed = now - self.phase_start
        active  = self.directions[self.phase_idx]

        remaining = max(0.0, self.phase_budget - elapsed) if self.phase_state == PHASE_GREEN else 0.0

        lane_data = {}
        for d, lane in self.lanes.items():
            lane_data[d] = {
                "vehicle_count": lane.vehicle_count,
                "density_score": round(lane.density_score, 2),
                "green_seconds": lane.green_seconds,
                "vehicle_types": lane.vehicle_types,
            }

        # Colour tokens for each direction (used by HUD widgets)
        direction_colors = {}
        for d in self.directions:
            if d == active:
                direction_colors[d] = {
                    PHASE_GREEN:  "#10b981",
                    PHASE_YELLOW: "#f59e0b",
                    PHASE_RED:    "#ef4444",
                }.get(self.phase_state, "#6b7280")
            else:
                direction_colors[d] = "#ef4444"    # All non-active are RED

        avg_green = (
            self.total_green_seconds / self.total_cycles
            if self.total_cycles > 0 else 0.0
        )

        return {
            "active_direction":  active,
            "phase_state":       self.phase_state,
            "elapsed_seconds":   round(elapsed, 1),
            "remaining_seconds": round(remaining, 1),
            "phase_budget":      self.phase_budget,
            "schedule":          dict(self.schedule),
            "lanes":             lane_data,
            "history_tail":      list(self.phase_history)[-8:],
            "total_cycles":      self.total_cycles,
            "avg_green_time":    round(avg_green, 1),
            "direction_colors":  direction_colors,
        }

    def get_phase_history_df_rows(self) -> List[Dict]:
        """Returns phase history as a list of dicts suitable for pd.DataFrame()."""
        rows = []
        for rec in self.phase_history:
            rows.append({
                "Timestamp":      time.strftime("%H:%M:%S", time.localtime(rec.timestamp)),
                "Direction":      rec.direction,
                "Green Time (s)": rec.green_seconds,
                "Vehicles":       rec.vehicle_count,
                "Density Score":  round(rec.density_score, 2),
            })
        return rows

    # ------------------------------------------------------------------
    # Configuration setters (callable from Streamlit sidebar at runtime)
    # ------------------------------------------------------------------

    def set_camera_source(self, direction: str, source) -> None:
        """Hot-swap a camera source — picked up by MultiCameraManager."""
        config.CAMERA_SOURCES[direction] = source

    def override_phase(self, direction: str) -> None:
        """Immediately jump to a specific direction's GREEN phase (manual override)."""
        if direction not in self.directions:
            return
        self.phase_idx    = self.directions.index(direction)
        self.phase_budget = self.schedule.get(direction, self.min_green)
        self._transition_to(PHASE_GREEN)
        logger.info(f"Manual override → {direction} GREEN for {self.phase_budget}s")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_weighted_density(self, detected_types: List[str]) -> float:
        """
        D_i = Σ w_type · N_type
        Unknown type labels default to weight 1.0.
        """
        total = 0.0
        for vtype in detected_types:
            total += config.DENSITY_WEIGHTS.get(vtype.lower(), 1.0)
        return total

    def _calculate_green_time(self, detected_types: List[str]) -> int:
        """
        Implements the three-tier allocation model:
        1. Empty lane  → 0 s  (system will use min_green when sequencing)
        2. Low-density (≤ 3 vehicles) → max(T_min, count × 2.5)  capped at T_max
        3. Standard    → clamp(round(T_base + k × D), T_min, T_max)
        """
        n = len(detected_types)

        if n == 0:
            return 0

        if n <= config.LOW_DENSITY_THRESHOLD:
            allocated = max(self.min_green, math.ceil(n * config.LOW_DENSITY_FACTOR))
            return min(allocated, self.max_green)

        density  = self._compute_weighted_density(detected_types)
        raw_time = config.SIGNAL_T_BASE + config.SIGNAL_K * density
        return max(self.min_green, min(int(round(raw_time)), self.max_green))

    def _transition_to(self, new_state: str) -> None:
        self.phase_state = new_state
        self.phase_start = self.time_now()

    @staticmethod
    def time_now() -> float:
        return time.time()


# ---------------------------------------------------------------------------
# Convenience test harness — run directly to verify logic offline
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    ctrl = AdaptiveSignalController()

    # Simulate varying traffic densities per direction
    traffic_scenarios = {
        "NORTH": ["car", "car", "bus"],            # 3 vehicles, density 4.0 → T=10s
        "EAST":  ["car"] * 12 + ["truck"] * 2,     # 14 vehicles, density 16.0 → T=30s (capped)
        "SOUTH": ["motorcycle"],                    # 1 vehicle (low-density) → T=5s
        "WEST":  ["car", "car"],                    # 2 vehicles → T=5s
    }

    for direction, types in traffic_scenarios.items():
        ctrl.update_lane_density(direction, types)

    schedule = ctrl.schedule
    print("\n=== Computed Green Time Schedule ===")
    for d, t in schedule.items():
        lane = ctrl.lanes[d]
        print(f"  {d:6s}: {len(lane.vehicle_types):2d} vehicles | "
              f"Density={lane.density_score:5.1f} | Green={t:2d}s")

    print("\n=== Simulating 3 Phase Cycles ===")
    import time as _time
    _time.sleep(0.01)   # Let phase_start settle

    # Fast-clock simulation — shrink time budgets for testing
    ctrl.min_green = 1
    ctrl.max_green = 3
    ctrl.yellow_dur = 0
    ctrl.all_red_dur = 0
    for d, types in traffic_scenarios.items():
        ctrl.update_lane_density(d, types)

    for _ in range(300):
        _time.sleep(0.02)
        active, state = ctrl.tick()
        if state == PHASE_GREEN:
            print(f"  >> {active} GREEN  {ctrl.schedule.get(active)}s  "
                  f"(elapsed {ctrl.time_now() - ctrl.phase_start:.1f}s)")
        if ctrl.total_cycles >= 3:
            break

    print(f"\nCompleted {ctrl.total_cycles} full cycles. "
          f"Average green time: {ctrl.total_green_seconds / max(1, ctrl.total_cycles):.1f}s")
