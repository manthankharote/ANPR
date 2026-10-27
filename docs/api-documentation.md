# REST API & Microservice Documentation

## 1. Express Backend Gateway (Port 5000)

Base URL: `http://localhost:5000/api`

### Authentication
* `POST /auth/login`
  * Body: `{ "email": "admin@traffic-sentinel.gov", "password": "Admin@1234" }`
  * Response: `{ success: true, data: { token: string, user: object } }`
* `GET /auth/me`
  * Headers: `Authorization: Bearer <token>`
  * Response: `{ success: true, data: { user: object } }`

### Dashboard
* `GET /dashboard/stats`
  * Headers: `Authorization: Bearer <token>`
  * Response: `{ success: true, data: { totalVehicles, totalViolations, helmetViolations, redLightViolations, pendingReviews, totalFinesAssessed, categoryDistribution, recentActivity } }`

### Vehicles (VAHAN National Registry)
* `GET /vehicles?plate=&limit=100`
  * Headers: `Authorization: Bearer <token>`
  * Returns registered vehicle records with Insurance and PUC certificate validity.
* `GET /vehicles/:plate`
  * Headers: `Authorization: Bearer <token>`
  * Returns single vehicle profile with document statuses.
* `POST /vehicles`
  * Headers: `Authorization: Bearer <token>`
  * Body: `{ plate_number, owner_name, vehicle_model, vehicle_type, insurance_status, insurance_expiry, puc_status, puc_expiry, registered_rto, mobile_number }`

### Violations & Human Review
* `GET /violations?plate=&type=&status=&limit=100`
  * Headers: `Authorization: Bearer <token>`
  * Returns list of issued e-Challan records.
* `GET /violations/:id`
  * Headers: `Authorization: Bearer <token>`
  * Returns single violation detail.
* `PATCH /violations/:id/review`
  * Headers: `Authorization: Bearer <token>`
  * Body: `{ review_status?: "CONFIRMED" | "REJECTED", challan_status?: "PAID" }`
  * Human-in-the-loop audit verification.

### AI Processing & Signal Engine
* `POST /ai/process-video`
  * Headers: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
  * FormData: `video` (file), `speedLimit` (number)
  * Response: `{ success: true, jobId: string, filename: string }`
* `GET /ai/jobs/:jobId`
  * Headers: `Authorization: Bearer <token>`
  * Response: `{ success: true, data: { progress: number, status: string, violations_count: number } }`
* `GET /ai/signal/state`
  * Public endpoint returning active signal phase, remaining time, and per-lane density scores.
* `POST /ai/signal/override`
  * Headers: `Authorization: Bearer <token>`
  * Body: `{ state: "RED" | "GREEN", autoCycle: boolean }`

### Statutory Settings & SMS Sandbox
* `GET /settings`
  * Returns statutory fine schedule and notification gateway settings.
* `PUT /settings`
  * Updates fine rates and gateway credentials.
* `POST /settings/test-notice`
  * Dispatches simulated or live SMS legal notice to citizen phone number.

---

## 2. Python AI Microservice (Port 8000)

Base URL: `http://localhost:8000`
Interactive Swagger Docs: `http://localhost:8000/docs`

* `GET /health`: System vitals, PyTorch CUDA detection, YOLO model status.
* `POST /detect/vehicles`: Multipart frame upload for real-time bounding box and violation detection.
  * Response attributes per detection:
    * `plate_box`: `[x1, y1, x2, y2]` bounding coordinates of localized plate.
    * `plate_confidence`: `float` detection confidence from `license_plate_detector.pt`.
    * `plate_status`: `"DETECTED_READ" | "DETECTED_UNREADABLE" | "NO_PLATE"`.
    * `raw_ocr_text`: Pre-cleaned string output from EasyOCR.
    * `verification_status`: `"VERIFIED_ANPR" | "UNVERIFIED_MANUAL_REVIEW"`.
* `POST /anpr/recognize`: Upload crop for OCR plate reading and Indian syntax correction.
  * Response: `{ success, plate_number, confidence, syntax_valid, state_code, plate_box, plate_status, raw_text }`.
* `POST /process/video`: Spawns async background video inference thread.
* `GET /jobs/{job_id}`: Retrieves async job progress percentage and detected offenses list.
* `GET /signal/state`: Retrieves mathematical 4-way adaptive traffic signal state.
* `POST /signal/override`: Overrides signal state for emergency vehicle priority.

