# AI-Powered Intelligent Vehicle Identification & Traffic Violation Detection System using ANPR

An end-to-end, production-grade Intelligent Transportation System (ITS) integrating Deep Learning Computer Vision, Automatic Number Plate Recognition (ANPR), Multi-Rule Traffic Violation Enforcement, National VAHAN Vehicle Registry Integration with Statutory Secondary Penalties, and Automated e-Challan SMS Dispatch.

---

## 📌 Executive Summary & Architecture Overview

Modern urban traffic management faces challenges in manual enforcement, delayed penalty collection, and lack of real-time multi-violation correlation. This system automates the complete lifecycle:
1. **Real-time Video Processing**: Supports CCTV RTSP streams, USB/webcams, sample simulations, and pre-recorded high-definition traffic feeds.
2. **Deep Learning Tracking**: Employs **YOLOv8** combined with Euclidean Centroid Tracking to maintain persistent vehicle tracks across frames.
3. **6 Statutory Traffic Violation Detectors**:
   - 🔴 **Red Light Jump**: Dynamically monitors stop-line crossings during RED signal phase.
   - ⚡ **Over-Speeding**: Calculates real-world velocity using calibrated dual virtual timing lines ($v = \frac{d}{\Delta t} \times 3.6$ km/h).
   - 👥 **Triple Riding / Overloading**: Identifies two-wheelers carrying $>2$ riders via spatial overlap analysis.
   - 🛡️ **No Helmet Violation**: Analyzes rider head region for protective gear compliance.
   - 🔄 **Wrong-Lane / Wrong-Way Driving**: Flags vehicles traversing contrary to designated roadway vector flow.
   - 📱 **Mobile Phone Usage**: Detects distracted drivers operating handheld devices while driving.
4. **ANPR & Forensic Evidence Pipeline**:
   - Morphological filtering (Sobel gradient, Bilateral filter, CLAHE) and contour localization.
   - OCR character extraction with syntax validation tailored to Indian State/UT registration formats.
   - Generates high-resolution forensic evidence snapshots with zoomed license plate insets and metadata watermarks.
5. **National VAHAN Registry & Multi-Tier Secondary Fines**:
   - Queries SQLite VAHAN vehicle database for owner records, insurance, and Pollution Under Control (PUC) certificate validity.
   - **Automated Secondary Penalty**: If a vehicle commits an offense while its Insurance is expired ($+₹2,000$) or PUC is expired ($+₹1,000$), these statutory fines are automatically compounded into the total e-Challan.
6. **Statutory SMS Dispatch & Web Command Center**:
   - Integrates Fast2SMS, Twilio, and production-grade simulated logging for instant delivery of legal notices with secure payment portal URLs.
   - Streamlit-powered dark glassmorphic command center with live surveillance radar, interactive signal controllers, e-Challan management, and compliance analytics.
7. **🚦 4-Way Adaptive Traffic Signal Control & Dynamic Signal Timing Engine**:
   - Multi-threaded orchestrator streaming 4 orthogonal camera angles simultaneously (NORTH, EAST, SOUTH, WEST).
   - Real-time lane vehicle counting & vehicle-class weighting (cars, motorcycles, buses, trucks).
   - Dynamic Green-Time allocation formula ($T_{\text{green}} = \text{clamp}(T_{\text{base}} + \alpha \cdot D, 5, 30)$ seconds).
   - Low-density queue clearing optimization: dynamically adjusts to minimal clearing windows ($5-8$ seconds) for lanes with 2–3 vehicles, eliminating wasted green time.
   - 3-Phase State Sequencer (GREEN → YELLOW $\rightarrow$ ALL-RED) synchronized with Red Light Violation Detection.
   - Multi-Camera 2×2 composite view with color-coded signal status borders and live phase timer HUD.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph MultiIntersection ["4-Way Multi-Camera Adaptive Intersection"]
        CamN["North Camera Feed"] & CamE["East Camera Feed"] & CamS["South Camera Feed"] & CamW["West Camera Feed"]
        CamN & CamE & CamS & CamW --> MCM["MultiCameraManager (Daemon Threads)"]
        MCM --> SharedYOLO["Shared YOLOv8 Vehicle Detection"]
        SharedYOLO --> DensityCalc["Per-Direction Weighted Density Calculation\n(Cars: 1.0, Bikes: 0.5, Buses: 2.5, Trucks: 3.0)"]
        DensityCalc --> SignalEngine["AdaptiveSignalController Engine\nT_green = clamp(3 + 1.8 * Density, 5s, 30s)"]
        SignalEngine --> PhaseSeq["Phase Sequencer\n(GREEN -> YELLOW 3s -> ALL-RED 2s)"]
        PhaseSeq --> SignalHUD["2x2 Composite Live HUD Overlay & Signal Sync"]
    end

    subgraph ViolationEnforcement ["Violation Detection & e-Challan Pipeline"]
        FrameExtraction["Frame Preprocessing & Normalization"] --> YOLOTracker["YOLOv8 Object Detection & Tracking\n(Cars, Bikes, Persons, Phones, Signals)"]
        PhaseSeq -.->|Active RED Lanes| RulesEngine
        
        YOLOTracker --> RulesEngine{"Violation Rules Engine"}
        RulesEngine -->|Signal is RED & crosses line| V1["Red Light Jump (₹1,000)"]
        RulesEngine -->|Speed > Threshold| V2["Over-Speeding (₹2,000)"]
        RulesEngine -->|Heading opposite to flow| V3["Wrong-Way Driving (₹1,500)"]
        RulesEngine -->|Riders > 2 on 2-Wheeler| V4["Triple Riding (₹1,000)"]
        RulesEngine -->|Unprotected head region| V5["No Helmet (₹1,000)"]
        RulesEngine -->|Phone detected in driver ROI| V6["Mobile Phone Usage (₹1,500)"]

        V1 & V2 & V3 & V4 & V5 & V6 --> ANPR["ANPR Engine (Contour Localization + OCR)"]
        ANPR --> VAHAN["VAHAN RTO Database Lookup"]
        VAHAN --> SecondaryCheck{"Insurance / PUC Status"}
        SecondaryCheck -->|Insurance Expired| SecFine1["Add ₹2,000 Penalty"]
        SecondaryCheck -->|PUC Expired| SecFine2["Add ₹1,000 Penalty"]
        SecondaryCheck -->|All Valid| TotalCalc["Compute Total Challan Amount"]
        SecFine1 & SecFine2 --> TotalCalc

        TotalCalc --> EvidenceSnap["Generate Forensic Watermarked Snapshot"]
        EvidenceSnap --> DBLog["Persist Challan in SQLite Database"]
        DBLog --> Notifier["SMS Dispatcher (Twilio / Fast2SMS / Sim)"]
        DBLog --> WebDashboard["Live Streamlit Command Center & Analytics"]
        SignalHUD --> WebDashboard
    end
```

---

## 📂 Project Repository Structure

```
├── anpr.py                # License plate localization, CLAHE enhancement, Indian syntax OCR
├── app.py                 # Streamlit Web Surveillance Command Center & e-Challan Portal
├── config.py              # Centralized configuration, geometry, signal timings & thresholds
├── database.py            # SQLite database schema, VAHAN registry seeding & challan queries
├── detector.py            # Real-time YOLOv8 + Centroid Tracking & 6 Violation rules engine
├── main.py                # Master CLI launcher (dashboard, 4-way intersection, video generator)
├── multi_camera_manager.py# Multi-threaded stream orchestrator for NORTH, EAST, SOUTH, WEST feeds
├── notifier.py            # Statutory e-Challan notification engine (Twilio, Fast2SMS, simulation)
├── requirements.txt       # Project dependencies
├── sample_traffic.mp4     # Generated 1280x720 30FPS multi-violation traffic test stream
├── signal_controller.py   # 4-Way dynamic signal allocation engine & green-phase scheduler
├── traffic_system.db      # SQLite database containing VAHAN registry & violations
├── video_generator.py     # Synthetic traffic simulation video generator
├── models/                # Directory for deep learning weight artifacts (yolov8n.pt)
└── violations/            # High-resolution timestamped forensic evidence snapshots
```

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- Webcam (optional for live camera mode)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Web Command Center Dashboard
```bash
python main.py
```
*Or directly via Streamlit:*
```bash
streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## 🎮 Command-Line Usage

The `main.py` entrypoint supports flexible execution modes:

```bash
# 1. Launch Web Dashboard (Default)
python main.py --dashboard

# 2. Run 4-Way Adaptive Intersection Surveillance (2x2 Grid View)
python main.py --intersection

# 3. Run Headless Surveillance on Sample Video (with OpenCV HUD display)
python main.py --source sample_traffic.mp4

# 4. Run Headless Surveillance on Laptop Webcam (Index 0)
python main.py --source 0

# 5. Run Headless on RTSP IP Camera stream
python main.py --source "rtsp://admin:12345@192.168.1.50:554/h264Preview_01_main"

# 6. Regenerate Synthetic Multi-Violation Simulation Video
python main.py --generate-video

# 7. Reset Violation Database to Clean State
python main.py --reset-db
```

---

## 🚦 4-Way Adaptive Traffic Signal Control Engine

The system features a multi-threaded dynamic signal control engine designed to replace rigid fixed-timer traffic lights with real-time computer vision-driven density adaptation.

### 1. Mathematical Green-Time Allocation Formula

The green phase duration $T_{\text{green}}$ for each direction $d \in \{\text{NORTH}, \text{EAST}, \text{SOUTH}, \text{WEST}\}$ is computed dynamically:

$$T_{\text{green}}(d) = \text{clamp}\left(T_{\text{base}} + \alpha \cdot D(d), \; T_{\text{min}}, \; T_{\text{max}}\right)$$

Where:
- $T_{\text{base}} = 3.0\text{ s}$ (Base clearance start-up time)
- $\alpha = 1.8\text{ s / density unit}$ (Dynamic scaling factor)
- $T_{\text{min}} = 5\text{ s}$ (Absolute minimum green duration)
- $T_{\text{max}} = 30\text{ s}$ (Statutory maximum green window cap)
- $D(d) = \sum_{v \in \text{vehicles}(d)} W(v)$ is the weighted traffic density per lane.

### 2. Vehicle Density Weighting Schedule ($W$)

Larger, slower-clearing vehicles require longer acceleration headway:

| Vehicle Class | Weight ($W$) | Rationale |
| :--- | :---: | :--- |
| **Motorcycle / Scooter** | `0.5` | High acceleration, narrow profile, clears rapidly |
| **Car / SUV / Auto** | `1.0` | Standard Passenger Car Unit (PCU) reference |
| **Bus** | `2.5` | Large turning radius, slow acceleration |
| **Truck** | `3.0` | Heavy cargo inertia, requires maximum clearance headroom |

### 3. Low-Density Lane Optimization (2–3 Vehicles)

When a lane contains only 2–3 vehicles:
- The queue requires only a short burst to clear before green time is wasted on an empty road.
- The controller switches to a minimal queue clearance formula:
  $$T_{\text{low}} = \max\left(T_{\text{min}}, \; \lceil N \times 2.5\text{ s}\rceil\right)$$
- Example: 3 vehicles allocate $\lceil 3 \times 2.5\rceil = 8\text{ s}$ green time instead of a full 30-second cycle.

### 4. 3-Phase State Machine & Safety Intervals

The controller strictly sequences phases to prevent intersection collisions:

```
[GREEN Phase (5-30s)] ──> [YELLOW Clearance (3s)] ──> [ALL-RED Clearance (2s)] ──> [Next Direction GREEN]
```

- **YELLOW Phase ($3\text{s}$)**: Allows vehicles in the dilemma zone to clear before red transition.
- **ALL-RED Clearance ($2\text{s}$)**: Inter-green interval where all 4 directions display RED, clearing lingering intersection stragglers.
- **Synchronized Red Light Enforcement**: The 3 directions currently in RED actively run automated red light jump detection, ANPR, and secondary fine compounding.

---

## 📑 Statutory Fine Schedule (Indian Motor Vehicles Act)

| Violation Category | Statutory MV Act Section | Primary Fine (₹) | Secondary Condition Penalties |
| :--- | :--- | :--- | :--- |
| **Red Light Jump** | Section 184 / 119 | ₹1,000 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **Over-Speeding** | Section 183 | ₹2,000 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **Triple Riding (2-Wheeler)** | Section 128 / 194C | ₹1,000 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **No Helmet** | Section 129 / 194D | ₹1,000 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **Wrong-Lane / Wrong-Way** | Section 177 / 184 | ₹1,500 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **Mobile Phone Usage** | Section 184(c) | ₹1,500 | $+₹2,000$ if Insurance Expired<br>$+₹1,000$ if PUC Expired |
| **Expired Vehicle Insurance** | Section 196 | ₹2,000 | Compound automatic secondary fine |
| **Expired PUC Certificate** | Section 190(2) | ₹1,000 | Compound automatic secondary fine |

---

## 🏛️ Seeded VAHAN Vehicles for Testing

The database automatically seeds realistic Indian vehicle records across various states with deliberate documentation defects to demonstrate multi-tier secondary penalties:

| Registration Plate | Registered Owner | Vehicle Model & Type | RTO Location | Insurance | PUC Status | Expected Penalty Trigger |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `MH20AB1234` | Rajesh Sharma | Hyundai Creta SX (Car) | MH-20 Sambhajinagar | VALID | VALID | Standard Primary Fine |
| `MH12XY9876` | Pooja Deshmukh | Honda Activa 6G (Motorcycle) | MH-12 Pune Central | **EXPIRED** | VALID | Primary $+ ₹2,000$ Secondary |
| `DL01AB5555` | Amitabh Verma | Maruti Swift Dzire (Car) | DL-01 Delhi North | VALID | **EXPIRED** | Primary $+ ₹1,000$ Secondary |
| `KA03MJ4321` | Suresh Reddy | Royal Enfield 350 (Motorcycle)| KA-03 Bengaluru East | **EXPIRED** | **EXPIRED** | Primary $+ ₹3,000$ Secondary |
| `TN09AZ1122` | K. Swaminathan | Honda City ZX (Car) | TN-09 Chennai South | **EXPIRED** | VALID | Primary $+ ₹2,000$ Secondary |
| `GJ01BC9999` | Harish Patel | Tata Prima 4028.S (Truck) | GJ-01 Ahmedabad West | VALID | VALID | Standard Primary Fine |

---

## 💬 Notification Dispatching (SMS & e-Challan)

The system formats legally sound SMS messages containing the violation timestamp, vehicle plate, fine breakdown, and payment link:

```
TRAFFIC POLICE NOTICE: E-Challan #2 issued for vehicle DL01AB5555.
Violation: Red Light Jump on 2026-09-30 14:07:11.
Fine Amount: INR 2000 (Includes ₹1000 expired doc penalty).
Pay online within 15 days to avoid court summons: https://echallan.parivahan.gov.in/portal/pay?challan=E-CH-2026-2&veh=DL01AB5555
```

- When credentials are provided in `config.py` or the Web UI, SMS is dispatched live via **Twilio** or **Fast2SMS**.
- If running in offline or demo mode, the system outputs formatted delivery receipts to the terminal and database without any runtime failure.

---

## 🛡️ License
Academic and Research Project under GNU General Public License / MIT License.
