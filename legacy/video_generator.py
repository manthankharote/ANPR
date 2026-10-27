"""
Synthetic Traffic Simulation Video Generator for AI-Powered Intelligent Vehicle Identification
and Traffic Violation Detection System using ANPR.
Generates a realistic 1280x720 30FPS multi-lane traffic video demonstrating:
  - Normal compliant vehicle flow
  - Red Light Jump violation (vehicle crossing stop line during red signal)
  - Over-Speeding violation (high-speed car crossing timing gates)
  - Triple Riding on two-wheeler (3 riders on motorcycle)
  - No Helmet violation (unprotected motorcycle rider)
  - Wrong-Way driving (vehicle driving opposite to traffic flow)
  - Realistic Indian license plates mounted on bumpers
"""

import os
import cv2
import math
import numpy as np
import config

def draw_car(frame: np.ndarray, x: int, y: int, w: int, h: int, color: tuple, plate_text: str, heading_down: bool = True):
    """Draws a detailed top-down / isometric stylized car with windshield, roof, wheels, and license plate."""
    # Body shadow
    cv2.rectangle(frame, (x + 4, y + 4), (x + w + 6, y + h + 6), (20, 20, 20), -1)
    # Main Chassis
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (30, 30, 30), 2)

    # Roof / Cabin
    cabin_inset_x = int(w * 0.15)
    cabin_inset_y = int(h * 0.22)
    cabin_color = (max(0, color[0] - 35), max(0, color[1] - 35), max(0, color[2] - 35))
    cv2.rectangle(
        frame,
        (x + cabin_inset_x, y + cabin_inset_y),
        (x + w - cabin_inset_x, y + h - cabin_inset_y),
        cabin_color, -1
    )

    # Front and Rear Windshields
    glass_color = (210, 230, 245)
    if heading_down:
        # Front windshield (facing downwards)
        cv2.rectangle(frame, (x + cabin_inset_x + 2, y + h - cabin_inset_y - 12), (x + w - cabin_inset_x - 2, y + h - cabin_inset_y - 2), glass_color, -1)
        # Rear windshield (facing upwards)
        cv2.rectangle(frame, (x + cabin_inset_x + 2, y + cabin_inset_y + 2), (x + w - cabin_inset_x - 2, y + cabin_inset_y + 12), glass_color, -1)
        # Headlights (bottom)
        cv2.circle(frame, (x + 8, y + h - 4), 5, (200, 255, 255), -1)
        cv2.circle(frame, (x + w - 8, y + h - 4), 5, (200, 255, 255), -1)
        # Taillights (top)
        cv2.circle(frame, (x + 8, y + 4), 4, (0, 0, 220), -1)
        cv2.circle(frame, (x + w - 8, y + 4), 4, (0, 0, 220), -1)
        # Front bumper license plate
        plate_w, plate_h = int(w * 0.65), 16
        px1 = x + int((w - plate_w) / 2)
        py1 = y + h - 14
    else:
        # Heading upwards (wrong-way car)
        cv2.rectangle(frame, (x + cabin_inset_x + 2, y + cabin_inset_y + 2), (x + w - cabin_inset_x - 2, y + cabin_inset_y + 12), glass_color, -1)
        cv2.rectangle(frame, (x + cabin_inset_x + 2, y + h - cabin_inset_y - 12), (x + w - cabin_inset_x - 2, y + h - cabin_inset_y - 2), glass_color, -1)
        cv2.circle(frame, (x + 8, y + 4), 5, (200, 255, 255), -1)
        cv2.circle(frame, (x + w - 8, y + 4), 5, (200, 255, 255), -1)
        cv2.circle(frame, (x + 8, y + h - 4), 4, (0, 0, 220), -1)
        cv2.circle(frame, (x + w - 8, y + h - 4), 4, (0, 0, 220), -1)
        plate_w, plate_h = int(w * 0.65), 16
        px1 = x + int((w - plate_w) / 2)
        py1 = y - 4

    # High-contrast white license plate
    cv2.rectangle(frame, (px1, py1), (px1 + plate_w, py1 + plate_h), (255, 255, 255), -1)
    cv2.rectangle(frame, (px1, py1), (px1 + plate_w, py1 + plate_h), (0, 0, 0), 1)
    # Plate Text
    cv2.putText(frame, plate_text, (px1 + 4, py1 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 0, 0), 1)


def draw_motorcycle(frame: np.ndarray, x: int, y: int, w: int, h: int, color: tuple, plate_text: str, riders: int = 1, has_helmet: bool = True):
    """Draws a stylized motorcycle with front/back wheels, fuel tank, and 1-3 riders."""
    # Chassis / Wheels
    cv2.rectangle(frame, (x + int(w * 0.4), y), (x + int(w * 0.6), y + h), (40, 40, 40), -1)
    # Front wheel (bottom)
    cv2.circle(frame, (x + int(w * 0.5), y + h - 8), 7, (20, 20, 20), -1)
    # Rear wheel (top)
    cv2.circle(frame, (x + int(w * 0.5), y + 8), 7, (20, 20, 20), -1)
    # Handlebars
    cv2.line(frame, (x + 4, y + h - 22), (x + w - 4, y + h - 22), (180, 180, 180), 3)

    # Body fuel tank
    cv2.ellipse(frame, (x + int(w * 0.5), y + int(h * 0.5)), (int(w * 0.35), int(h * 0.25)), 0, 0, 360, color, -1)

    # Draw Riders along the seat
    spacing = int((h * 0.45) / max(1, riders))
    start_y = y + int(h * 0.32)

    for i in range(riders):
        ry = start_y + (i * spacing)
        rx = x + int(w * 0.5)

        # Torso / Shoulders
        cv2.rectangle(frame, (rx - 10, ry - 4), (rx + 10, ry + 10), (60, 90, 160) if i == 0 else (180, 70, 70), -1)

        # Head / Helmet
        is_this_rider_helmeted = has_helmet if i == 0 else (False if i == 1 else True)
        if is_this_rider_helmeted:
            # Glossy black/yellow helmet dome
            cv2.circle(frame, (rx, ry - 10), 8, (20, 20, 20), -1)
            cv2.circle(frame, (rx, ry - 10), 6, (255, 200, 0), -1)
        else:
            # Unhelmeted head: Skin tone + dark hair texture
            cv2.circle(frame, (rx, ry - 10), 7, (140, 180, 220), -1)  # Skin tone in BGR
            cv2.circle(frame, (rx, ry - 12), 6, (30, 25, 20), -1)   # Dark hair

    # Rear License Plate
    pw, ph = int(w * 0.85), 14
    px = x + int((w - pw) / 2)
    py = y - 6
    cv2.rectangle(frame, (px, py), (px + pw, py + ph), (255, 255, 255), -1)
    cv2.rectangle(frame, (px, py), (px + pw, py + ph), (0, 0, 0), 1)
    cv2.putText(frame, plate_text, (px + 2, py + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (0, 0, 0), 1)


def generate_sample_traffic_video(output_path: str = None, duration_sec: int = 16, fps: int = 30):
    """
    Renders the standardized 1280x720 synthetic traffic simulation video.
    """
    if not output_path:
        output_path = config.SAMPLE_VIDEO_PATH

    width, height = 1280, 720
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating synthetic traffic simulation video at {output_path} ({total_frames} frames)...")

    # Lane geometry: 4 lanes
    # Lane 0: x=140 to 380 (Left)
    # Lane 1: x=380 to 620 (Center-Left)
    # Lane 2: x=620 to 860 (Center-Right)
    # Lane 3: x=860 to 1100 (Right)

    for frame_idx in range(total_frames):
        t = frame_idx / float(fps)
        frame = np.full((height, width, 3), (48, 52, 54), dtype=np.uint8)  # Road asphalt

        # Curbs and Grass Shoulders
        frame[:, :120] = (34, 110, 45)      # Left grass
        frame[:, 1160:] = (34, 110, 45)     # Right grass
        cv2.line(frame, (120, 0), (120, height), (220, 220, 220), 4)  # Left road curb
        cv2.line(frame, (1160, 0), (1160, height), (220, 220, 220), 4) # Right road curb

        # Dashed lane dividers
        for lane_x in [380, 640, 900]:
            dash_offset = int((frame_idx * 4) % 40)
            for y_dash in range(-40 + dash_offset, height + 40, 40):
                cv2.line(frame, (lane_x, y_dash), (lane_x, y_dash + 20), (255, 255, 255), 2)

        # Pedestrian Zebra Crossing Stripes near Stop Line (y=480)
        for zx in range(130, 1150, 45):
            cv2.rectangle(frame, (zx, 490), (zx + 25, 520), (240, 240, 240), -1)

        # Stop Line at y=480
        cv2.line(frame, (120, 480), (1160, 480), (255, 255, 255), 4)

        # -------------------------------------------------------------------
        # Traffic Signal Simulation (Cycles from GREEN to RED at t=7.0s)
        # -------------------------------------------------------------------
        signal_is_red = (7.0 <= t <= 14.0)

        # -------------------------------------------------------------------
        # Vehicle 1: Standard Compliant Car (Lane 1, normal speed 42 km/h)
        # -------------------------------------------------------------------
        v1_speed = 3.6  # pixels per frame
        v1_y = int((frame_idx * v1_speed) % (height + 250)) - 150
        draw_car(frame, x=220, y=v1_y, w=90, h=155, color=(180, 90, 40), plate_text="MH20AB1234", heading_down=True)

        # -------------------------------------------------------------------
        # Vehicle 2: Over-Speeding Car (Lane 2, high speed ~82 km/h)
        # -------------------------------------------------------------------
        v2_speed = 8.2  # rapid movement
        v2_y = int((frame_idx * v2_speed) % (height + 300)) - 160
        draw_car(frame, x=480, y=v2_y, w=95, h=160, color=(35, 45, 205), plate_text="DL01AB5555", heading_down=True)

        # -------------------------------------------------------------------
        # Vehicle 3: Motorcycle with Triple Riding (Lane 3, 3 riders!)
        # -------------------------------------------------------------------
        v3_speed = 4.2
        v3_y = int(((frame_idx - 40) * v3_speed) % (height + 250)) - 140
        draw_motorcycle(
            frame, x=750, y=v3_y, w=50, h=120,
            color=(30, 170, 70), plate_text="KA03MJ4321",
            riders=3, has_helmet=True
        )

        # -------------------------------------------------------------------
        # Vehicle 4: Motorcycle with NO HELMET (Lane 3, 1 rider unhelmeted)
        # -------------------------------------------------------------------
        v4_speed = 3.8
        v4_y = int(((frame_idx - 160) * v4_speed) % (height + 250)) - 140
        draw_motorcycle(
            frame, x=820, y=v4_y, w=48, h=110,
            color=(170, 30, 140), plate_text="MH12XY9876",
            riders=1, has_helmet=False
        )

        # -------------------------------------------------------------------
        # Vehicle 5: Red Light Violator (Crosses Stop Line at y=480 during RED signal)
        # -------------------------------------------------------------------
        # Crosses around t=8.5s when signal is RED
        v5_speed = 4.5
        v5_y = int((frame_idx - 170) * v5_speed) - 100
        if -150 <= v5_y <= height + 100:
            draw_car(frame, x=350, y=v5_y, w=92, h=150, color=(20, 180, 210), plate_text="TN09AZ1122", heading_down=True)

        # -------------------------------------------------------------------
        # Vehicle 6: Wrong-Way Driver (Lane 4, moving UPWARDS against flow!)
        # -------------------------------------------------------------------
        if t >= 4.0:
            v6_speed = 4.0
            v6_y = height - int((frame_idx - 120) * v6_speed) + 50
            if -150 <= v6_y <= height + 150:
                draw_car(frame, x=1010, y=v6_y, w=90, h=150, color=(160, 40, 180), plate_text="GJ01BC9999", heading_down=False)

        # Gantry Traffic Light Physical Post at roadside
        tl_box_x, tl_box_y = 1205, 380
        cv2.rectangle(frame, (tl_box_x, tl_box_y), (tl_box_x + 50, tl_box_y + 110), (25, 25, 25), -1)
        cv2.rectangle(frame, (tl_box_x, tl_box_y), (tl_box_x + 50, tl_box_y + 110), (160, 160, 160), 2)
        # Red lamp
        red_color = (0, 0, 255) if signal_is_red else (0, 0, 60)
        cv2.circle(frame, (tl_box_x + 25, tl_box_y + 30), 16, red_color, -1)
        # Green lamp
        green_color = (0, 255, 0) if not signal_is_red else (0, 60, 0)
        cv2.circle(frame, (tl_box_x + 25, tl_box_y + 80), 16, green_color, -1)

        out.write(frame)

    out.release()
    print(f"Sample traffic video generated successfully: {output_path} ({os.path.getsize(output_path)} bytes)")
    return output_path

if __name__ == "__main__":
    generate_sample_traffic_video()
