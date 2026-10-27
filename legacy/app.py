"""
Web Dashboard & Surveillance Command Center
AI-Powered Intelligent Vehicle Identification and Traffic Violation Detection System using ANPR
"""

import os
import cv2
import time
import tempfile
import pandas as pd
import numpy as np
import streamlit as st

import config
import database
import notifier
from detector import TrafficViolationDetector
from signal_controller import AdaptiveSignalController, PHASE_GREEN, PHASE_YELLOW, PHASE_RED
from multi_camera_manager import MultiCameraManager

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Modern Theme Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI ANPR Traffic Violation & Surveillance Command Center",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dark Glassmorphic Theme & Dynamic Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Background and containers */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }

    /* Glassmorphic Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #f8fafc;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.80rem;
        color: #64748b;
        margin-top: 6px;
    }

    /* Live Radar Pulse Indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pulse-dot {
        width: 9px;
        height: 9px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        animation: pulse-animation 1.6s infinite;
    }
    @keyframes pulse-animation {
        0% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Signal Badges */
    .signal-badge-red {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.0rem;
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid #ef4444;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
    }
    .signal-badge-green {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.0rem;
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }

    /* Violation Cards in Live Feed */
    .violation-feed-item {
        background: rgba(30, 41, 59, 0.6);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .plate-badge {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        background: #f8fafc;
        color: #0f172a;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #000;
        letter-spacing: 0.05em;
        font-size: 0.85rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 0 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Initialize Session State
# -----------------------------------------------------------------------------
if "detector" not in st.session_state:
    st.session_state.detector = TrafficViolationDetector()

if "stream_running" not in st.session_state:
    st.session_state.stream_running = False

if "signal_state" not in st.session_state:
    st.session_state.signal_state = "GREEN"

if "total_frames_processed" not in st.session_state:
    st.session_state.total_frames_processed = 0

if "mcm" not in st.session_state:
    st.session_state.mcm = None          # MultiCameraManager instance

if "mcm_running" not in st.session_state:
    st.session_state.mcm_running = False

if "mcm_violation_enabled" not in st.session_state:
    st.session_state.mcm_violation_enabled = False


# -----------------------------------------------------------------------------
# Sidebar Navigation & Live Signal Control
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom: 16px;">
            <div style="font-size: 2.2rem;">🚦</div>
            <div>
                <h2 style="margin:0; font-size:1.25rem; font-weight:800; color:#f8fafc;">TRAFFIC-SENTINEL</h2>
                <span style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.04em;">AI ANPR VIOLATION ENGINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="live-indicator"><div class="pulse-dot"></div>NEURAL ENGINE READY</div>', unsafe_allow_html=True)
    st.markdown("<hr style='margin:16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        [
            "🚦 Live Surveillance Feed",
            "🚥 4-Way Adaptive Intersection",
            "📜 e-Challan & Violation Records",
            "🔍 VAHAN National Registry",
            "📊 Analytics & Heatmap",
            "⚙️ Fine Rules & System Config"
        ],
        label_visibility="collapsed"
    )

    st.markdown("<hr style='margin:16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # Traffic Signal Override Center
    st.markdown("### 🚥 Junction Signal Controller")
    current_signal = st.session_state.detector.traffic_light_state
    if current_signal == "RED":
        st.markdown('<div class="signal-badge-red">● SIGNAL: RED LIGHT</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="signal-badge-green">● SIGNAL: GREEN LIGHT</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    sig_col1, sig_col2 = st.columns(2)
    with sig_col1:
        if st.button("🔴 Force RED", use_container_width=True):
            st.session_state.detector.set_traffic_light("RED", auto_cycle=False)
            st.rerun()
    with sig_col2:
        if st.button("🟢 Force GREEN", use_container_width=True):
            st.session_state.detector.set_traffic_light("GREEN", auto_cycle=False)
            st.rerun()

    auto_cycle_toggle = st.toggle("Autonomous Signal Timing (15s/10s)", value=st.session_state.detector.auto_traffic_light)
    if auto_cycle_toggle != st.session_state.detector.auto_traffic_light:
        st.session_state.detector.auto_traffic_light = auto_cycle_toggle

    st.markdown("<hr style='margin:16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # Quick System Status
    metrics = database.get_system_metrics()
    st.caption("SYSTEM VITALS")
    st.markdown(f"**Total Violations Logged:** `{metrics['total_violations']}`")
    st.markdown(f"**Fines Accrued:** `₹{metrics['total_fines']:,}`")
    st.markdown(f"**Registered Vehicles:** `{metrics['total_registered_vehicles']}`")


# -----------------------------------------------------------------------------
# TAB 1: LIVE SURVEILLANCE & VIOLATION RADAR
# -----------------------------------------------------------------------------
if nav_selection == "🚦 Live Surveillance Feed":
    st.title("Junction Surveillance & Automated Violation Detection")
    st.caption("Real-Time Multi-Object Tracking (YOLOv8) • ANPR • 6 Statutory Violation Rules • Automated e-Challan Issuance")

    # Top Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([3, 2, 2, 2])

    with ctrl_col1:
        stream_mode = st.selectbox(
            "Video Stream Source",
            [
                "Sample Traffic Video (Built-in Multi-Violation Simulation)",
                "Laptop / USB Webcam (Device 0)",
                "IP Camera / RTSP Stream",
                "Upload Custom Video File"
            ]
        )

    with ctrl_col2:
        speed_limit_input = st.slider("Speed Limit Threshold (km/h)", min_value=30, max_value=100, value=int(config.SPEED_LIMIT_KMH), step=5)
        st.session_state.detector.speed_limit = float(speed_limit_input)

    with ctrl_col3:
        conf_input = st.slider("Detection Confidence", min_value=0.20, max_value=0.80, value=0.40, step=0.05)

    with ctrl_col4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if not st.session_state.stream_running:
            if st.button("▶ START SURVEILLANCE", type="primary", use_container_width=True):
                st.session_state.stream_running = True
                st.rerun()
        else:
            if st.button("⏹ STOP STREAM", type="secondary", use_container_width=True):
                st.session_state.stream_running = False
                st.rerun()

    # Optional Inputs for Custom Stream
    custom_video_path = None
    if stream_mode == "Upload Custom Video File":
        uploaded_file = st.file_uploader("Upload MP4 / AVI traffic video", type=["mp4", "avi", "mov"])
        if uploaded_file:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_file.read())
            custom_video_path = tfile.name
    elif stream_mode == "IP Camera / RTSP Stream":
        custom_video_path = st.text_input("Enter RTSP / HTTP URL", value="http://192.168.1.100:8080/video")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Main Stage Layout: Video Canvas (70%) + Live Violation Feed (30%)
    col_video, col_feed = st.columns([7, 3])

    with col_video:
        video_placeholder = st.empty()
        status_bar = st.empty()

        if not st.session_state.stream_running:
            # Show preview poster or static banner
            if os.path.exists(config.SAMPLE_VIDEO_PATH):
                cap_preview = cv2.VideoCapture(config.SAMPLE_VIDEO_PATH)
                ret_p, frame_p = cap_preview.read()
                cap_preview.release()
                if ret_p:
                    ann_p, _ = st.session_state.detector.process_frame(frame_p)
                    video_placeholder.image(cv2.cvtColor(ann_p, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Camera Stream Standby. Click 'START SURVEILLANCE' to begin live detection.")
            else:
                video_placeholder.info("Click 'START SURVEILLANCE' above to launch automated traffic violation tracking.")

    with col_feed:
        st.markdown("### 🚨 Live Violation Ticker")
        feed_container = st.container(height=520)

    # -------------------------------------------------------------------------
    # Active Video Processing Loop
    # -------------------------------------------------------------------------
    if st.session_state.stream_running:
        # Determine source
        if stream_mode == "Sample Traffic Video (Built-in Multi-Violation Simulation)":
            if not os.path.exists(config.SAMPLE_VIDEO_PATH):
                from video_generator import generate_sample_traffic_video
                generate_sample_traffic_video()
            source = config.SAMPLE_VIDEO_PATH
        elif stream_mode == "Laptop / USB Webcam (Device 0)":
            source = 0
        elif custom_video_path:
            source = custom_video_path
        else:
            source = config.SAMPLE_VIDEO_PATH

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            st.error(f"Failed to open video source: {source}")
            st.session_state.stream_running = False
        else:
            frame_idx = 0
            start_time = time.time()

            while st.session_state.stream_running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    # Loop video if sample video reaches end
                    if isinstance(source, str) and os.path.exists(source):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        break

                frame_idx += 1
                st.session_state.total_frames_processed += 1

                # Process Frame through Violation Engine
                t0 = time.time()
                annotated_frame, violations = st.session_state.detector.process_frame(frame)
                dt = time.time() - t0
                fps = 1.0 / dt if dt > 0 else 30.0

                # Render frame in Streamlit
                rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(rgb_frame, use_container_width=True)

                status_bar.markdown(
                    f"**FPS:** `{fps:.1f}` | **Processing Latency:** `{dt*1000:.1f} ms` | "
                    f"**Signal:** `{st.session_state.detector.traffic_light_state}` | "
                    f"**Frame:** `#{frame_idx}`"
                )

                # Update live violation ticker feed
                with feed_container:
                    if st.session_state.detector.recent_violations:
                        for v in st.session_state.detector.recent_violations[:6]:
                            sec_note = f" (+₹{v.get('secondary_fine', 0)} Expired Doc)" if v.get('secondary_fine', 0) > 0 else ""
                            st.markdown(f"""
                                <div class="violation-feed-item">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span class="plate-badge">{v.get('plate_number', 'UNKNOWN')}</span>
                                        <span style="font-size:0.75rem; color:#94a3b8;">{v.get('timestamp', '')[11:]}</span>
                                    </div>
                                    <div style="font-weight:700; color:#ef4444; margin-top:6px; font-size:0.95rem;">
                                        ⚠️ {v.get('violation_type', 'Violation')}
                                    </div>
                                    <div style="font-size:0.82rem; color:#e2e8f0; margin-top:2px;">
                                        Fine: <b>₹{v.get('total_fine', 0):,}</b>{sec_note}
                                    </div>
                                    <div style="font-size:0.72rem; color:#94a3b8; margin-top:4px;">
                                        Challan ID: #{v.get('id', 'N/A')} • SMS: {v.get('sms_status', 'SIMULATED')}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No violations detected yet. Watching traffic...")

                # Yield control briefly for smooth UI interaction
                time.sleep(0.01)

            cap.release()


# -----------------------------------------------------------------------------
# TAB 2: E-CHALLAN & VIOLATION RECORDS MANAGEMENT
# -----------------------------------------------------------------------------
elif nav_selection == "📜 e-Challan & Violation Records":
    st.title("e-Challan Registry & Statutory Case Records")
    st.caption("Official Traffic Enforcement Log • Multi-tier Fines (Primary Violation + Expired Insurance/PUC) • Evidence Repository")

    # Metrics Strip
    metrics = database.get_system_metrics()
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Violations</div>
                <div class="metric-value">{metrics['total_violations']}</div>
                <div class="metric-sub">Recorded across all cameras</div>
            </div>
        """, unsafe_allow_html=True)

    with m_col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Penalties</div>
                <div class="metric-value">₹{metrics['total_fines']:,}</div>
                <div class="metric-sub">Statutory fines assessed</div>
            </div>
        """, unsafe_allow_html=True)

    with m_col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Pending Challans</div>
                <div class="metric-value" style="color:#ef4444;">{metrics['unpaid_challans']}</div>
                <div class="metric-sub">Awaiting settlement</div>
            </div>
        """, unsafe_allow_html=True)

    with m_col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Violations Today</div>
                <div class="metric-value" style="color:#38bdf8;">{metrics['violations_today']}</div>
                <div class="metric-sub">₹{metrics['fines_today']:,} today</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Filter & Search Toolbar
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 2, 1])

    with f_col1:
        search_plate = st.text_input("🔍 Search Vehicle Plate / Registration", placeholder="e.g. MH20AB1234, DL01AB5555")

    with f_col2:
        filter_violation = st.selectbox(
            "Violation Type",
            ["All"] + list(config.FINES.keys())
        )

    with f_col3:
        filter_status = st.selectbox(
            "Payment Status",
            ["All", "ISSUED", "PAID"]
        )

    with f_col4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Clear Filters", use_container_width=True):
            st.rerun()

    # Query Database
    records = database.get_all_violations(
        plate_filter=search_plate if search_plate else None,
        violation_filter=filter_violation,
        status_filter=filter_status,
        limit=150
    )

    if not records:
        st.info("No violation records match your current filters. Start the surveillance feed or adjust filters.")
    else:
        # Display Table Summary
        df_records = pd.DataFrame(records)
        columns_to_show = [
            "id", "timestamp", "plate_number", "owner_name", "violation_type",
            "primary_fine", "secondary_fine", "total_fine", "challan_status", "sms_status"
        ]
        df_display = df_records[[c for c in columns_to_show if c in df_records.columns]]
        df_display.columns = [
            "Challan #", "Timestamp", "Vehicle Plate", "Owner Name", "Violation",
            "Primary Fine (₹)", "Secondary Fine (₹)", "Total (₹)", "Status", "SMS Delivery"
        ]

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # Challan Detail Inspector Modal / Drawer
        st.markdown("### 🔍 Challan Evidence & Action Inspector")
        challan_options = {f"Challan #{r['id']} - {r['plate_number']} ({r['violation_type']})": r for r in records}
        selected_challan_label = st.selectbox("Select Challan to Inspect", list(challan_options.keys()))
        selected_record = challan_options[selected_challan_label]

        det_col1, det_col2 = st.columns([5, 5])

        with det_col1:
            st.markdown("#### Photographic Evidence Snapshot")
            snapshot_path = selected_record.get("snapshot_path")
            if snapshot_path and os.path.exists(snapshot_path):
                st.image(snapshot_path, use_container_width=True, caption=f"Forensic Evidence Snapshot #{selected_record['id']}")
            else:
                st.warning("Snapshot archive image not available on disk.")

        with det_col2:
            st.markdown("#### Statutory e-Challan Notice Breakdown")
            st.markdown(f"""
                - **Challan Reference Number:** `E-CH-2026-{selected_record['id']}`
                - **Timestamp:** `{selected_record['timestamp']}`
                - **Vehicle Plate Number:** <span class="plate-badge">{selected_record['plate_number']}</span>
                - **Registered Owner:** **{selected_record.get('owner_name', 'Citizen Owner')}**
                - **Vehicle Model:** `{selected_record.get('vehicle_model', 'Standard Vehicle')}`
                - **Registered RTO:** `{selected_record.get('registered_rto', 'State Transport Department')}`
                - **Owner Mobile:** `{selected_record.get('mobile_number', '+919800000000')}`
                - **Violation Category:** :red[**{selected_record['violation_type']}**]
                - **Primary Violation Fine:** `₹{selected_record['primary_fine']:,}`
                - **Secondary Fine (Expired Documents):** `₹{selected_record['secondary_fine']:,}`
                - **Total Amount Payable:** :green[**₹{selected_record['total_fine']:,}**]
                - **Payment Status:** **{selected_record['challan_status']}**
                - **SMS Status:** `{selected_record.get('sms_status', 'SIMULATED')}`
            """, unsafe_allow_html=True)

            if selected_record.get("details"):
                st.info(f"**Field Officer & Sensor Notes:** {selected_record['details']}")

            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if selected_record["challan_status"] == "ISSUED":
                    if st.button("💳 Settle / Mark as PAID", type="primary", use_container_width=True):
                        database.update_challan_status(selected_record["id"], "PAID")
                        st.success(f"Challan #{selected_record['id']} marked as PAID.")
                        st.rerun()
                else:
                    st.success("✅ Challan Settled and Paid.")

            with act_col2:
                if st.button("📲 Resend SMS Notice", use_container_width=True):
                    res = notifier.dispatch_violation_notice(selected_record)
                    st.info(f"SMS re-dispatched. Status: {res['status']}")


# -----------------------------------------------------------------------------
# TAB 3: VAHAN NATIONAL REGISTRY EXPLORER
# -----------------------------------------------------------------------------
elif nav_selection == "🔍 VAHAN National Registry":
    st.title("VAHAN National Vehicle Registry Explorer")
    st.caption("Centralized RTO Database • Real-Time Insurance & PUC Validity Check • Direct Statutory Secondary Penalty Verification")

    v_search_col1, v_search_col2 = st.columns([4, 1])
    with v_search_col1:
        query_plate = st.text_input(
            "Enter License Plate / Registration Number",
            value="MH20AB1234",
            placeholder="e.g. MH20AB1234, DL01AB5555, KA03MJ4321, MH12XY9876, GJ01BC9999"
        )
    with v_search_col2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        search_vahan = st.button("Lookup VAHAN", type="primary", use_container_width=True)

    vehicle_info = database.get_vehicle(query_plate)

    if vehicle_info:
        ins_status = vehicle_info.get("insurance_status", "VALID")
        puc_status = vehicle_info.get("puc_status", "VALID")

        ins_badge = ":green[VALID]" if ins_status == "VALID" else ":red[EXPIRED (Secondary Fine ₹2,000)]"
        puc_badge = ":green[VALID]" if puc_status == "VALID" else ":red[EXPIRED (Secondary Fine ₹1,000)]"

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        card_col1, card_col2 = st.columns([6, 4])

        with card_col1:
            st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #3b82f6;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span class="plate-badge" style="font-size:1.1rem; padding:4px 12px;">{vehicle_info['plate_number']}</span>
                        <span style="font-weight:700; color:#38bdf8;">{vehicle_info['vehicle_type']}</span>
                    </div>
                    <div style="font-size:1.4rem; font-weight:800; color:#f8fafc;">
                        {vehicle_info['owner_name']}
                    </div>
                    <div style="color:#94a3b8; font-size:0.95rem; margin-top:2px;">
                        Model: <b style="color:#e2e8f0;">{vehicle_info['vehicle_model']}</b>
                    </div>
                    <hr style="margin:14px 0; border-color: rgba(255,255,255,0.08);">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:0.88rem;">
                        <div>
                            <span style="color:#94a3b8;">Registered RTO:</span><br>
                            <b>{vehicle_info['registered_rto']}</b>
                        </div>
                        <div>
                            <span style="color:#94a3b8;">Registered Contact:</span><br>
                            <b>{vehicle_info['mobile_number']}</b>
                        </div>
                        <div>
                            <span style="color:#94a3b8;">Insurance Policy:</span><br>
                            Status: {ins_badge}<br>
                            Expiry Date: <code>{vehicle_info['insurance_expiry']}</code>
                        </div>
                        <div>
                            <span style="color:#94a3b8;">PUC Certificate:</span><br>
                            Status: {puc_badge}<br>
                            Expiry Date: <code>{vehicle_info['puc_expiry']}</code>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with card_col2:
            st.markdown("#### Cumulative Violations for this Vehicle")
            veh_violations = database.get_violations_for_vehicle(vehicle_info['plate_number'])

            if veh_violations:
                tot_unpaid = sum(v['total_fine'] for v in veh_violations if v['challan_status'] == 'ISSUED')
                st.markdown(f"**Total Infractions:** `{len(veh_violations)}` | **Unpaid Debt:** :red[**₹{tot_unpaid:,}**]")
                for v in veh_violations[:4]:
                    st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px; margin-bottom:8px; border-left:3px solid #ef4444;">
                            <b>{v['violation_type']}</b> on {v['timestamp'][:10]}<br>
                            <span style="color:#94a3b8; font-size:0.8rem;">Amount: ₹{v['total_fine']:,} • Status: {v['challan_status']}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("Clean driving record! No infractions logged for this vehicle.")

    else:
        st.warning(f"Vehicle plate '{query_plate}' is not registered in the VAHAN mock database.")
        st.info("You can register this vehicle below to test immediate VAHAN linkage.")

    st.markdown("<hr style='margin:28px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # Form to register new custom vehicle in VAHAN
    with st.expander("➕ Register New Vehicle into VAHAN Mock Registry"):
        with st.form("new_vehicle_form"):
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                new_plate = st.text_input("Plate Number", placeholder="e.g. MH14AB9999").upper()
                new_owner = st.text_input("Owner Full Name", placeholder="e.g. Rohit Patil")
                new_type = st.selectbox("Vehicle Type", ["Car", "Motorcycle", "Truck", "Bus"])
            with col_r2:
                new_model = st.text_input("Vehicle Model", placeholder="e.g. Tata Harrier Dark Edition")
                new_rto = st.text_input("Registered RTO", placeholder="e.g. MH-14 Pimpri-Chinchwad")
                new_mobile = st.text_input("Mobile Number", value="+919876543210")
            with col_r3:
                new_ins_status = st.selectbox("Insurance Status", ["VALID", "EXPIRED"])
                new_ins_expiry = st.date_input("Insurance Expiry Date")
                new_puc_status = st.selectbox("PUC Status", ["VALID", "EXPIRED"])
                new_puc_expiry = st.date_input("PUC Expiry Date")

            submitted = st.form_submit_button("Register Vehicle into VAHAN", type="primary")
            if submitted and new_plate and new_owner:
                conn = database.get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO vahan_vehicles (
                        plate_number, owner_name, vehicle_model, vehicle_type,
                        insurance_expiry, insurance_status, puc_expiry, puc_status,
                        registered_rto, mobile_number, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'));
                """, (
                    new_plate.replace(" ", "").replace("-", ""),
                    new_owner, new_model, new_type,
                    str(new_ins_expiry), new_ins_status,
                    str(new_puc_expiry), new_puc_status,
                    new_rto, new_mobile
                ))
                conn.commit()
                conn.close()
                st.success(f"Vehicle {new_plate} registered successfully in VAHAN.")


# -----------------------------------------------------------------------------
# TAB 4: ANALYTICS & STATISTICAL INSIGHTS
# -----------------------------------------------------------------------------
elif nav_selection == "📊 Analytics & Heatmap":
    st.title("Traffic Violation Analytics & Statutory Revenue Insights")
    st.caption("Statistical Breakdown • High-Risk Offense Distribution • Revenue Recovery KPIs")

    all_v = database.get_all_violations(limit=1000)

    if not all_v:
        st.info("No violation data available yet for analytics. Run the surveillance stream to accumulate real-time events.")
    else:
        df = pd.DataFrame(all_v)

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown("#### Violation Category Distribution")
            v_counts = df["violation_type"].value_counts().reset_index()
            v_counts.columns = ["Violation Type", "Occurrences"]
            st.bar_chart(v_counts.set_index("Violation Type"))

        with col_a2:
            st.markdown("#### Fines Assessed: Primary vs Secondary Expired Doc Penalties")
            tot_primary = df["primary_fine"].sum()
            tot_secondary = df["secondary_fine"].sum()
            rev_df = pd.DataFrame({
                "Fine Classification": ["Primary Traffic Fine", "Secondary (Expired Insurance/PUC)"],
                "Total Amount (₹)": [tot_primary, tot_secondary]
            })
            st.bar_chart(rev_df.set_index("Fine Classification"))

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("#### Payment Settlement Status")
            status_counts = df["challan_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Challan Count"]
            st.dataframe(status_counts, use_container_width=True, hide_index=True)

        with col_b2:
            st.markdown("#### Top Offending Vehicles (Repeat Violators)")
            top_offenders = df["plate_number"].value_counts().head(5).reset_index()
            top_offenders.columns = ["Vehicle Registration", "Total Violations"]
            st.dataframe(top_offenders, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 5: FINE RULES & SYSTEM CONFIG
# -----------------------------------------------------------------------------
elif nav_selection == "⚙️ Fine Rules & System Config":
    st.title("Statutory Fine Schedule & System Parameters")
    st.caption("Configurable Statutory Rates under Motor Vehicles Act • Gateway API Credentials • SMS Sandbox")

    cfg_col1, cfg_col2 = st.columns(2)

    with cfg_col1:
        st.markdown("#### Statutory Fine Schedule (INR ₹)")
        fine_inputs = {}
        for k, v in config.FINES.items():
            fine_inputs[k] = st.number_input(f"Fine for '{k}'", min_value=100, max_value=25000, value=v, step=100)

        if st.button("Save Statutory Fine Schedule", type="primary"):
            config.FINES.update(fine_inputs)
            st.success("Fine schedule updated successfully for active runtime.")

    with cfg_col2:
        st.markdown("#### SMS & Notification Gateway Settings")
        st.markdown("""
            Configure API keys for real SMS delivery to citizen phone numbers.
            If credentials are mock or left blank, the system automatically runs in **Simulation Mode**
            with full delivery logs and receipts.
        """)

        sim_mode = st.toggle("SMS Simulation Mode (Local Delivery Receipt)", value=config.SMS_SIMULATION_MODE)
        config.SMS_SIMULATION_MODE = sim_mode

        twilio_sid = st.text_input("Twilio Account SID", value=config.TWILIO_ACCOUNT_SID, type="password")
        twilio_token = st.text_input("Twilio Auth Token", value=config.TWILIO_AUTH_TOKEN, type="password")
        twilio_phone = st.text_input("Twilio Phone Number", value=config.TWILIO_PHONE_NUMBER)

        fast2sms_key = st.text_input("Fast2SMS API Key", value=config.FAST2SMS_API_KEY, type="password")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown("#### Test SMS Dispatcher Sandbox")
        test_mobile = st.text_input("Recipient Mobile Number", value="+919822012345")
        if st.button("Send Test e-Challan SMS Notice"):
            test_violation = {
                "id": 9999,
                "plate_number": "MH20AB1234",
                "violation_type": "Over-Speeding (78 km/h)",
                "primary_fine": 2000,
                "secondary_fine": 1000,
                "total_fine": 3000,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mobile_number": test_mobile,
                "owner_name": "Test Citizen"
            }
            res = notifier.dispatch_violation_notice(test_violation)
            st.success(f"Dispatched! Status: {res['status']}. Check console/logs for formatted delivery record.")


# =============================================================================
# TAB: 4-WAY ADAPTIVE INTERSECTION CONTROL
# =============================================================================
elif nav_selection == "🚥 4-Way Adaptive Intersection":

    st.title("4-Way Adaptive Traffic Signal Control Centre")
    st.caption(
        "Real-time per-lane density analysis • Dynamic green-time allocation • "
        "Phase sequencer (GREEN → YELLOW → ALL-RED) • ANPR enforcement on all lanes"
    )

    # ------------------------------------------------------------------
    # Control Row
    # ------------------------------------------------------------------
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([3, 2, 2, 2])

    with ctrl_col1:
        mcm_violation_toggle = st.toggle(
            "Enable Full ANPR & Violation Detection on All Lanes",
            value=st.session_state.mcm_violation_enabled,
            help="When ON, each lane runs the full TrafficViolationDetector pipeline. Heavier CPU load."
        )
        st.session_state.mcm_violation_enabled = mcm_violation_toggle

    with ctrl_col2:
        frame_skip_val = st.slider("Frame Skip (CPU Throttle)", 1, 8, 3, 1,
                                   help="Process every Nth frame per lane. Higher = faster but less responsive.")

    with ctrl_col3:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        st.info(f"T_max = **{config.MAX_GREEN_TIME}s** | T_min = **{config.MIN_GREEN_TIME}s** | "
                f"Yellow = **{config.YELLOW_DURATION}s**")

    with ctrl_col4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if not st.session_state.mcm_running:
            if st.button("▶ START INTERSECTION", type="primary", use_container_width=True):
                # Initialise or restart MCM
                if st.session_state.mcm is not None:
                    try:
                        st.session_state.mcm.stop()
                    except Exception:
                        pass
                mgr = MultiCameraManager(
                    enable_violation_detection=st.session_state.mcm_violation_enabled,
                    frame_skip=frame_skip_val,
                )
                mgr.start()
                st.session_state.mcm = mgr
                st.session_state.mcm_running = True
                st.rerun()
        else:
            if st.button("⏹ STOP INTERSECTION", type="secondary", use_container_width=True):
                if st.session_state.mcm is not None:
                    st.session_state.mcm.stop()
                st.session_state.mcm_running = False
                st.rerun()

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 4-Camera Source Configurator (collapsible)
    # ------------------------------------------------------------------
    with st.expander("📷 Configure Camera Sources for Each Direction", expanded=False):
        src_cols = st.columns(4)
        src_labels = list(config.SIGNAL_DIRECTIONS)
        src_emojis = ["⬆️ N", "➡️ E", "⬇️ S", "⬅️ W"]
        new_sources = {}

        for i, (col, direction, emoji) in enumerate(zip(src_cols, src_labels, src_emojis)):
            with col:
                st.markdown(f"**{emoji} {direction}**")
                src_type = st.selectbox(
                    "Source", ["Sample Video", "Webcam (0)", "Webcam (1)", "Custom URL/Path"],
                    key=f"src_type_{direction}"
                )
                if src_type == "Sample Video":
                    new_sources[direction] = config.SAMPLE_VIDEO_PATH
                elif src_type == "Webcam (0)":
                    new_sources[direction] = 0
                elif src_type == "Webcam (1)":
                    new_sources[direction] = 1
                else:
                    custom = st.text_input("URL / Path", key=f"src_custom_{direction}",
                                           value=config.SAMPLE_VIDEO_PATH)
                    new_sources[direction] = custom

        if st.button("Apply Camera Sources", type="primary"):
            for d, src in new_sources.items():
                config.CAMERA_SOURCES[d] = src
                if st.session_state.mcm is not None and st.session_state.mcm_running:
                    st.session_state.mcm.reconfigure_source(d, src)
            st.success("Camera sources updated.")

    # ------------------------------------------------------------------
    # Main HUD layout — Grid (left 65%) + Signal Panel (right 35%)
    # ------------------------------------------------------------------
    grid_col, panel_col = st.columns([65, 35])

    with grid_col:
        st.markdown("#### 📡 Live 4-Camera Intersection Grid")
        grid_placeholder   = st.empty()
        grid_status        = st.empty()

    with panel_col:
        st.markdown("#### 🚥 Signal Phase Controller")
        signal_info_box    = st.empty()
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        st.markdown("**Manual Phase Override**")
        override_cols = st.columns(2)
        with override_cols[0]:
            for d in ["NORTH", "SOUTH"]:
                if st.button(f"Force {config.DIRECTION_EMOJI[d]}", key=f"override_{d}", use_container_width=True):
                    if st.session_state.mcm is not None:
                        st.session_state.mcm.signal_ctrl.override_phase(d)
        with override_cols[1]:
            for d in ["EAST", "WEST"]:
                if st.button(f"Force {config.DIRECTION_EMOJI[d]}", key=f"override_{d}", use_container_width=True):
                    if st.session_state.mcm is not None:
                        st.session_state.mcm.signal_ctrl.override_phase(d)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown("**Green Time Schedule (Current)**")
        schedule_table     = st.empty()

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown("**Lane Density Scores**")
        density_bars       = st.empty()

    st.markdown("---")
    st.markdown("#### 📋 Phase History Log")
    history_table = st.empty()

    # ------------------------------------------------------------------
    # Static preview when intersection is stopped
    # ------------------------------------------------------------------
    if not st.session_state.mcm_running or st.session_state.mcm is None:
        grid_placeholder.info(
            "Click **▶ START INTERSECTION** above to launch the 4-way adaptive signal system. "
            "All four camera feeds will run concurrently in background threads."
        )

        # Show mathematical model explanation
        with st.expander("ℹ️ Adaptive Signal Allocation Model", expanded=True):
            st.markdown(r"""
**Weighted Density per Lane:**
$$D_i = w_{\text{car}} \cdot N_{\text{car}} + w_{\text{bike}} \cdot N_{\text{bike}} + w_{\text{bus}} \cdot N_{\text{bus}} + w_{\text{truck}} \cdot N_{\text{truck}}$$

| Vehicle Type | Density Weight |
|---|---|
| Car | 1.0 |
| Motorcycle / Bicycle | 0.5 |
| Bus / Truck | 2.0 |
| Person | 0.0 (pedestrian, not counted) |

**Green Time Allocation:**
$$T_i = \text{clamp}\!\left(\text{round}(T_{\text{base}} + k \cdot D_i),\; T_{\text{min}},\; T_{\text{max}}\right)$$

Where $T_{\text{base}} = 3\text{s}$, $k = 1.8\text{ s/unit}$, $T_{\text{min}} = 5\text{s}$, $T_{\text{max}} = 30\text{s}$.

**Low-Density Shortcut** (≤ 3 vehicles):
$$T_i = \max(T_{\text{min}},\; N_i \times 2.5\text{ s})$$

| Vehicles | Allocated Green Time |
|---|---|
| 0 (empty) | 0 s → system uses T_min when sequencing |
| 1 vehicle | max(5, 1×2.5) = **5 s** |
| 2 vehicles | max(5, 2×2.5) = **5 s** |
| 3 vehicles | max(5, 3×2.5) = **8 s** |
| 10 vehicles (mixed) | ≈ **21 s** |
| Heavy traffic (≥15) | Capped at **30 s** |
""")
    else:
        # ------------------------------------------------------------------
        # Active Intersection Live Loop
        # ------------------------------------------------------------------
        mgr = st.session_state.mcm

        # Single-shot render loop — Streamlit re-runs the script on every
        # interaction; we use st.rerun() at the end to drive continuous updates.
        snapshot     = mgr.get_snapshot()
        signal_state = mgr.signal_ctrl.get_intersection_state()

        # 2×2 grid frame
        grid_frame = mgr.compose_grid_frame(snapshot, signal_state, target_w=1280, target_h=720)
        grid_rgb   = cv2.cvtColor(grid_frame, cv2.COLOR_BGR2RGB)
        grid_placeholder.image(grid_rgb, use_container_width=True)

        # Grid status footer
        active   = signal_state["active_direction"]
        phase    = signal_state["phase_state"]
        rem      = signal_state["remaining_seconds"]
        cycles   = signal_state["total_cycles"]
        avg_g    = signal_state["avg_green_time"]
        grid_status.markdown(
            f"**Active Lane:** `{config.DIRECTION_EMOJI[active]}`  |  "
            f"**Phase:** `{phase}`  |  "
            f"**Remaining:** `{rem:.0f}s`  |  "
            f"**Cycles Completed:** `{cycles}`  |  "
            f"**Avg Green:** `{avg_g:.1f}s`"
        )

        # Signal info box (active direction detail)
        phase_color = {"GREEN": "#10b981", "YELLOW": "#f59e0b", "RED": "#ef4444"}.get(phase, "#94a3b8")
        signal_info_box.markdown(f"""
<div class="metric-card" style="border-left: 5px solid {phase_color};">
    <div class="metric-title">Active Direction</div>
    <div class="metric-value" style="color:{phase_color};">
        {config.DIRECTION_EMOJI[active]}
    </div>
    <div style="font-size:1.1rem; font-weight:700; color:{phase_color}; margin-top:8px;">
        ● {phase}
    </div>
    <div class="metric-sub">
        Phase Budget: {signal_state['phase_budget']}s &nbsp;|&nbsp; Remaining: {rem:.0f}s<br>
        Completed Cycles: {cycles} &nbsp;|&nbsp; Avg Green: {avg_g:.1f}s
    </div>
</div>
""", unsafe_allow_html=True)

        # Schedule table
        sched_rows = []
        for d in config.SIGNAL_DIRECTIONS:
            lane = signal_state["lanes"][d]
            is_active = (d == active)
            sched_rows.append({
                "Direction":      config.DIRECTION_EMOJI[d],
                "Vehicles":       lane["vehicle_count"],
                "Density Score":  f"{lane['density_score']:.1f}",
                "Green Time (s)": lane["green_seconds"],
                "Status":         ("▶ ACTIVE" if is_active else "⏸ WAITING"),
            })
        import pandas as pd
        df_sched = pd.DataFrame(sched_rows)
        schedule_table.dataframe(df_sched, use_container_width=True, hide_index=True)

        # Density progress bars
        density_html = ""
        for d in config.SIGNAL_DIRECTIONS:
            lane      = signal_state["lanes"][d]
            score     = lane["density_score"]
            pct       = min(100, int((score / 30.0) * 100))   # normalise to max expected density ~30
            bar_color = "#10b981" if d != active else "#f59e0b"
            density_html += f"""
<div style="margin-bottom:10px;">
    <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:3px;">
        <span style="color:#cbd5e1;">{config.DIRECTION_EMOJI[d]}</span>
        <span style="color:#94a3b8;">{lane['vehicle_count']} veh | D={score:.1f}</span>
    </div>
    <div style="background:rgba(255,255,255,0.06); border-radius:4px; height:10px; overflow:hidden;">
        <div style="width:{pct}%; background:{bar_color}; height:10px; border-radius:4px;
                    transition:width 0.5s ease;"></div>
    </div>
</div>"""
        density_bars.markdown(density_html, unsafe_allow_html=True)

        # Phase history log (latest 10)
        hist_rows = mgr.signal_ctrl.get_phase_history_df_rows()
        if hist_rows:
            df_hist = pd.DataFrame(hist_rows[-10:][::-1])
            history_table.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            history_table.info("Phase history will appear here after the first full cycle completes.")

        # Drive continuous refresh (100 ms between refreshes)
        time.sleep(0.15)
        st.rerun()
