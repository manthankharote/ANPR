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
* **Detection Engine**: YOLOv8 nano (`yolov8n.pt`) tracking 8 COCO classes (cars, bikes, trucks, buses, persons, traffic lights, phones).
* **Centroid Tracker**: Euclidean distance matching with spatial-temporal trajectory history (`deque(maxlen=45)`).
* **Violation Engine**:
  1. *Red Light Jump*: Stop line boundary check ($Y=480$) during active RED signal phase.
  2. *Over-Speeding*: Dual virtual timing gates (Line 1: $Y=320$, Line 2: $Y=520$) calibrated to 12.0 real-world meters ($v = \frac{d}{\Delta t} \times 3.6$ km/h).
  3. *Triple Riding*: Overlapping bounding box spatial intersections between 2-wheelers and persons.
  4. *No Helmet*: Rider head-region crop with Canny edge variation analysis.
  5. *Wrong-Lane Driving*: Vector trajectory displacement checks opposite to designated roadway flow.
* **ANPR & Forensic Pipeline**: Bilateral filtering, CLAHE adaptive histogram equalization, Indian state prefix regex disambiguation, and watermarked composite evidence generation with picture-in-picture plate insets.
* **Asynchronous Jobs**: Background threads (`threading.Thread`) processing batch video files with granular progress reporting.
