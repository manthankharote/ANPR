# System Architecture & Technical Specification

## AI-Powered Intelligent Vehicle Identification & Traffic Violation Detection System Using ANPR

### 1. High-Level Architectural Model

The system follows a modern decoupled microservices architecture designed to isolate heavy computer-vision GPU/CPU operations from administrative web application state:

```
[ React 18 + Vite Frontend ] (Port 5173)
            │
            │ REST + JWT Bearer
            ▼
[ Node.js / Express Backend ] (Port 5000)
    │           │               │
    │ Mongoose  │ Storage API   │ HTTP JSON / Multipart
    ▼           ▼               ▼
[ MongoDB /   [ Storage ]    [ Python FastAPI AI Microservice ] (Port 8000)
  Fallback ]   uploads/       ├── YOLOv8 Deep Learning Detector (yolov8n.pt)
               evidence/      ├── SimpleCentroidTracker (Euclidean)
                              ├── Indian ANPR & Syntax OCR Parser
                              └── 4-Way Adaptive Signal Controller
```

---

### 2. Frontend Layer (`client/`)
* **Framework**: React 18 with Vite build tool.
* **Styling**: Tailwind CSS v4 with custom dark glassmorphic design system (`#0b0f19` base, translucent cards, neon telemetry borders).
* **Navigation**: React Router v7 with route protection via `AuthContext`.
* **Telemetry & Visualization**: Recharts for violation distributions, custom radar-pulse indicators for camera health.
* **Component Architecture**:
  * `pages/`: 7 dedicated views (Login, Dashboard, LiveMonitoring, VehicleRecords, Violations, Evidence, Settings).
  * `components/common/`: StatCard, Badge, EmptyState.
  * `components/layout/`: Sidebar, Navbar with dynamic junction signal badge, AppLayout.
  * `services/`: Axios HTTP layer with request/response JWT interceptors.

---

### 3. Backend Gateway Layer (`server/`)
* **Runtime**: Node.js v20+ with Express.js.
* **Authentication**: JWT token signing (`HS256`) with `bcryptjs` password hashing.
* **Database Resiliency**:
  * Primary: MongoDB via Mongoose ODM (`User`, `Vehicle`, `Violation`, `ProcessingJob`).
  * Fallback Engine: Unified `dataStore.js` with auto-failover to pre-seeded SQLite/In-Memory dataset when MongoDB daemon is not locally running.
* **File Uploads**: `multer` with whitelist file-extension validation (`.mp4`, `.avi`, `.mov`, `.jpg`) and strict 250MB buffer ceilings.
* **Static Asset Hosting**: Securely serves `/uploads` and `/evidence` for forensic snapshots.

---

### 4. AI & Computer Vision Microservice (`ai-service/`)
* **Framework**: Python 3.10+ with FastAPI & Uvicorn.
* **Two-Stage Deep Learning Pipeline**:
  1. *Vehicle Detector*: Ultralytics YOLOv8 nano (`yolov8n.pt`, 6.55 MB, COCO 80 classes) detecting cars, motorcycles, buses, trucks, pedestrians, and traffic lights.
  2. *License Plate Detector*: Ultralytics YOLOv8 nano (`license_plate_detector.pt`, 5.95 MB, Hugging Face `yasirfaizahmed/license-plate-object-detection`, AGPL-3.0 / CC BY 4.0) localized on vehicle bounding-box crops with full-frame fallback.
* **Optical Character Recognition (OCR) Engine**:
  * EasyOCR 1.7.2 with PyTorch CPU backend (`craft_mlt_25k.pth`, `english_g2.pth`).
  * Image Enhancement: Bilateral filter noise reduction, CLAHE adaptive histogram equalization, and adaptive thresholding.
  * Syntax Disambiguation: Indian state prefix mapping (`DL`, `MH`, `KA`, `TS`, `AP`, `TN`, `UP`, etc.), Bharat Series (`YYBH####XX`), alphanumeric positional confusion repairs (`O` <-> `0`, `I` <-> `1`, `Z` <-> `2`, `S` <-> `5`, `B` <-> `8`), and HSRP `IND` prefix stripping.
  * Zero Fabrication Policy: Blurry, dark, or illegible plates explicitly return `UNREADABLE` / `UNKNOWN`. Plate numbers are never invented.
* **Centroid Tracker**: Euclidean distance matching with spatial-temporal trajectory history (`deque(maxlen=45)`).
* **Violation Engine**:
  1. *Red Light Jump*: Stop line boundary check ($Y=480$) during active RED signal phase.
  2. *Over-Speeding*: Dual virtual timing gates (Line 1: $Y=320$, Line 2: $Y=520$) calibrated to 12.0 real-world meters ($v = \frac{d}{\Delta t} \times 3.6$ km/h).
  3. *Triple Riding*: Overlapping bounding box spatial intersections between 2-wheelers and persons.
  4. *No Helmet*: Rider head-region crop with edge variance and morphology checks.
  5. *Wrong-Lane Driving*: Vector trajectory displacement checks opposite to designated roadway flow.
* **Forensic Evidence Generator**: Generates high-resolution composite JPEG snapshots containing the full context frame, vehicle bounding box, plate bounding box, zoomed plate crop inset, and legal timestamp watermark.
* **Verification & Audit Lifecycle**:
  * `VERIFIED_ANPR`: Plate detected with valid Indian syntax and high confidence.
  * `UNVERIFIED_MANUAL_REVIEW`: Plate illegible or unverified; violation review status set to `PENDING` for mandatory officer photographic review.
* **Asynchronous Jobs**: Background threads (`threading.Thread`) processing batch video files with granular progress reporting.

