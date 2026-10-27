"""
Database Module for AI-Powered Intelligent Vehicle Identification
and Traffic Violation Detection System using ANPR.
Manages Mock VAHAN registry, violation records, secondary fines, and challan tracking.
"""

import sqlite3
import datetime
from typing import Optional, Dict, Any, List
import config

def get_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds mock VAHAN records if not already present."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Mock VAHAN Vehicle Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vahan_vehicles (
        plate_number TEXT PRIMARY KEY,
        owner_name TEXT NOT NULL,
        vehicle_model TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        insurance_expiry TEXT NOT NULL,
        insurance_status TEXT NOT NULL,
        puc_expiry TEXT NOT NULL,
        puc_status TEXT NOT NULL,
        registered_rto TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Table 2: Violations and Issued Challans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        tracking_id INTEGER NOT NULL,
        plate_number TEXT NOT NULL,
        violation_type TEXT NOT NULL,
        speed_recorded REAL,
        primary_fine INTEGER NOT NULL,
        secondary_fine INTEGER NOT NULL DEFAULT 0,
        total_fine INTEGER NOT NULL,
        snapshot_path TEXT NOT NULL,
        challan_status TEXT NOT NULL DEFAULT 'ISSUED',
        sms_status TEXT NOT NULL DEFAULT 'PENDING',
        details TEXT,
        FOREIGN KEY (plate_number) REFERENCES vahan_vehicles(plate_number)
    );
    """)

    conn.commit()

    # Check if VAHAN registry needs seeding
    cursor.execute("SELECT COUNT(*) AS count FROM vahan_vehicles")
    row = cursor.fetchone()
    if row["count"] == 0:
        seed_vahan_data(cursor)
        conn.commit()

    conn.close()

def seed_vahan_data(cursor: sqlite3.Cursor):
    """Seeds 12+ realistic Indian VAHAN vehicle records with varied insurance and PUC statuses."""
    now = datetime.datetime.now()
    
    # Dates relative to current time for realistic validation
    expired_date_1 = (now - datetime.timedelta(days=120)).strftime("%Y-%m-%d")
    expired_date_2 = (now - datetime.timedelta(days=45)).strftime("%Y-%m-%d")
    valid_date_1 = (now + datetime.timedelta(days=210)).strftime("%Y-%m-%d")
    valid_date_2 = (now + datetime.timedelta(days=320)).strftime("%Y-%m-%d")

    mock_vehicles = [
        # 1. Car - All Documents Valid
        ("MH20AB1234", "Rajesh Sharma", "Hyundai Creta SX", "Car",
         valid_date_1, "VALID", valid_date_1, "VALID",
         "MH-20 Sambhajinagar (Aurangabad)", "+919822012345", now.isoformat()),

        # 2. 2-Wheeler - Expired Insurance (Triggers Secondary Fine)
        ("MH12XY9876", "Pooja Deshmukh", "Honda Activa 6G", "Motorcycle",
         expired_date_1, "EXPIRED", valid_date_2, "VALID",
         "MH-12 Pune Central", "+919890123456", now.isoformat()),

        # 3. Car - Expired PUC (Triggers Secondary Fine)
        ("DL01AB5555", "Amitabh Verma", "Maruti Suzuki Swift Dzire", "Car",
         valid_date_1, "VALID", expired_date_2, "EXPIRED",
         "DL-01 Delhi North", "+919811223344", now.isoformat()),

        # 4. 2-Wheeler - Both Insurance & PUC Expired (Triggers Double Secondary Fine)
        ("KA03MJ4321", "Suresh Reddy", "Royal Enfield Classic 350", "Motorcycle",
         expired_date_2, "EXPIRED", expired_date_1, "EXPIRED",
         "KA-03 Bengaluru East (Indiranagar)", "+919945678901", now.isoformat()),

        # 5. Commercial Truck - Valid
        ("GJ01BC9999", "Harish Patel", "Tata Prima 4028.S", "Truck",
         valid_date_2, "VALID", valid_date_1, "VALID",
         "GJ-01 Ahmedabad West", "+919825099887", now.isoformat()),

        # 6. Car - Expired Insurance
        ("TN09AZ1122", "K. Swaminathan", "Honda City ZX", "Car",
         expired_date_1, "EXPIRED", valid_date_1, "VALID",
         "TN-09 Chennai South (T. Nagar)", "+919444122334", now.isoformat()),

        # 7. Bus - Valid
        ("UP32DK7788", "Mahesh Chandra", "Ashok Leyland Viking Bus", "Bus",
         valid_date_2, "VALID", valid_date_2, "VALID",
         "UP-32 Lucknow Mahanagar", "+919415055667", now.isoformat()),

        # 8. 2-Wheeler - All Valid
        ("MH14GH4321", "Nikhil Kulkarni", "Yamaha FZ-S FI", "Motorcycle",
         valid_date_1, "VALID", valid_date_2, "VALID",
         "MH-14 Pimpri-Chinchwad", "+919765432109", now.isoformat()),

        # 9. Luxury Car - Expired PUC
        ("HR26DQ0001", "Vikram Singh Hooda", "BMW 3 Series Gran Limousine", "Car",
         valid_date_2, "VALID", expired_date_1, "EXPIRED",
         "HR-26 Gurugram North", "+919910011223", now.isoformat()),

        # 10. Car - Valid
        ("WB02K8888", "Subhashish Roy", "Tata Nexon EV", "Car",
         valid_date_1, "VALID", valid_date_1, "VALID",
         "WB-02 Kolkata Central", "+919830088888", now.isoformat()),

        # 11. 2-Wheeler - Expired Insurance
        ("MP09CB6543", "Anand Sharma", "TVS Jupiter 125", "Motorcycle",
         expired_date_2, "EXPIRED", valid_date_2, "VALID",
         "MP-09 Indore Regional", "+919826065432", now.isoformat()),

        # 12. Car - All Valid
        ("KL07BN2468", "Mathew Thomas", "Volkswagen Virtus GT", "Car",
         valid_date_2, "VALID", valid_date_2, "VALID",
         "KL-07 Kochi Central", "+919447012468", now.isoformat())
    ]

    cursor.executemany("""
    INSERT INTO vahan_vehicles (
        plate_number, owner_name, vehicle_model, vehicle_type,
        insurance_expiry, insurance_status, puc_expiry, puc_status,
        registered_rto, mobile_number, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, mock_vehicles)

def get_vehicle(plate_number: str) -> Optional[Dict[str, Any]]:
    """Looks up a vehicle record from VAHAN database. Normalizes plate format."""
    normalized_plate = plate_number.replace(" ", "").replace("-", "").upper()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vahan_vehicles WHERE plate_number = ?", (normalized_plate,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def register_mock_vehicle_if_missing(plate_number: str, vehicle_type: str = "Car") -> Dict[str, Any]:
    """Auto-provisions a realistic mock VAHAN record if an unrecognized plate is detected."""
    normalized = plate_number.replace(" ", "").replace("-", "").upper()
    vehicle = get_vehicle(normalized)
    if vehicle:
        return vehicle

    now = datetime.datetime.now()
    valid_date = (now + datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    
    # State prefix extraction or default
    prefix = normalized[:2] if len(normalized) >= 2 else "MH"
    rto = f"{prefix}-01 Transport Authority"

    new_record = (
        normalized,
        f"Citizen Owner ({normalized})",
        f"Generic {vehicle_type}",
        vehicle_type,
        valid_date,
        "VALID",
        valid_date,
        "VALID",
        rto,
        "+919800000000",
        now.isoformat()
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO vahan_vehicles (
        plate_number, owner_name, vehicle_model, vehicle_type,
        insurance_expiry, insurance_status, puc_expiry, puc_status,
        registered_rto, mobile_number, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, new_record)
    conn.commit()
    conn.close()

    return get_vehicle(normalized) or {}

def record_violation(
    tracking_id: int,
    plate_number: str,
    violation_type: str,
    speed_recorded: Optional[float],
    primary_fine: int,
    snapshot_path: str,
    details: str = "",
    sms_status: str = "SIMULATED"
) -> Dict[str, Any]:
    """
    Records a traffic violation.
    Automatically checks VAHAN registry for Insurance & PUC validity.
    Attaches statutory secondary fines if Insurance or PUC is expired.
    """
    normalized_plate = plate_number.replace(" ", "").replace("-", "").upper()
    vehicle = get_vehicle(normalized_plate)
    if not vehicle:
        vehicle = register_mock_vehicle_if_missing(normalized_plate)

    # Secondary fine calculations
    secondary_fine = 0
    secondary_reasons = []

    if vehicle.get("insurance_status") == "EXPIRED":
        sec_amt = config.FINES.get("Expired Insurance", 2000)
        secondary_fine += sec_amt
        secondary_reasons.append(f"Expired Insurance (+₹{sec_amt})")

    if vehicle.get("puc_status") == "EXPIRED":
        sec_puc = config.FINES.get("Expired PUC", 1000)
        secondary_fine += sec_puc
        secondary_reasons.append(f"Expired PUC (+₹{sec_puc})")

    total_fine = primary_fine + secondary_fine

    # Append secondary fine note to details if applicable
    detailed_notes = details or ""
    if secondary_reasons:
        sec_text = " [Secondary Penalty: " + ", ".join(secondary_reasons) + "]"
        detailed_notes = (detailed_notes + sec_text).strip()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO violations (
        timestamp, tracking_id, plate_number, violation_type,
        speed_recorded, primary_fine, secondary_fine, total_fine,
        snapshot_path, challan_status, sms_status, details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ISSUED', ?, ?);
    """, (
        timestamp,
        tracking_id,
        normalized_plate,
        violation_type,
        speed_recorded,
        primary_fine,
        secondary_fine,
        total_fine,
        snapshot_path,
        sms_status,
        detailed_notes
    ))
    conn.commit()
    violation_id = cursor.lastrowid
    conn.close()

    return {
        "id": violation_id,
        "timestamp": timestamp,
        "tracking_id": tracking_id,
        "plate_number": normalized_plate,
        "violation_type": violation_type,
        "speed_recorded": speed_recorded,
        "primary_fine": primary_fine,
        "secondary_fine": secondary_fine,
        "total_fine": total_fine,
        "snapshot_path": snapshot_path,
        "owner_name": vehicle.get("owner_name", "Unknown"),
        "mobile_number": vehicle.get("mobile_number", "+919800000000"),
        "insurance_status": vehicle.get("insurance_status", "VALID"),
        "puc_status": vehicle.get("puc_status", "VALID"),
        "details": detailed_notes
    }

def get_all_violations(
    plate_filter: Optional[str] = None,
    violation_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieves violation log records with optional filtering."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT v.*, veh.owner_name, veh.vehicle_model, veh.registered_rto, veh.mobile_number,
           veh.insurance_status, veh.puc_status
    FROM violations v
    LEFT JOIN vahan_vehicles veh ON v.plate_number = veh.plate_number
    WHERE 1=1
    """
    params = []

    if plate_filter:
        clean_plate = plate_filter.replace(" ", "").replace("-", "").upper()
        query += " AND v.plate_number LIKE ?"
        params.append(f"%{clean_plate}%")

    if violation_filter and violation_filter != "All":
        query += " AND v.violation_type = ?"
        params.append(violation_filter)

    if status_filter and status_filter != "All":
        query += " AND v.challan_status = ?"
        params.append(status_filter)

    query += " ORDER BY v.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_violations_for_vehicle(plate_number: str) -> List[Dict[str, Any]]:
    """Fetches all past violations and challans linked to a vehicle plate."""
    clean_plate = plate_number.replace(" ", "").replace("-", "").upper()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM violations
    WHERE plate_number = ?
    ORDER BY id DESC
    """, (clean_plate,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_challan_status(violation_id: int, status: str = "PAID") -> bool:
    """Updates the payment or resolution status of a challan."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE violations SET challan_status = ? WHERE id = ?", (status, violation_id))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def get_system_metrics() -> Dict[str, Any]:
    """Calculates summary operational KPIs for the admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total_violations FROM violations")
    total_violations = cursor.fetchone()["total_violations"]

    cursor.execute("SELECT COALESCE(SUM(total_fine), 0) AS total_fines FROM violations")
    total_fines = cursor.fetchone()["total_fines"]

    cursor.execute("SELECT COUNT(*) AS unpaid_count FROM violations WHERE challan_status = 'ISSUED'")
    unpaid_challans = cursor.fetchone()["unpaid_count"]

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT COALESCE(SUM(total_fine), 0) AS fines_today,
           COUNT(*) AS violations_today
    FROM violations
    WHERE timestamp LIKE ?
    """, (f"{today_str}%",))
    today_row = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total_registered FROM vahan_vehicles")
    total_registered = cursor.fetchone()["total_registered"]

    conn.close()

    return {
        "total_violations": total_violations,
        "total_fines": total_fines,
        "unpaid_challans": unpaid_challans,
        "violations_today": today_row["violations_today"],
        "fines_today": today_row["fines_today"],
        "total_registered_vehicles": total_registered
    }

def clear_all_violations():
    """Helper for testing: Resets violation records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM violations")
    conn.commit()
    conn.close()

# Auto-initialize database schema on module import
init_db()
