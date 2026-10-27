"""
Safe SQLite to MongoDB / JSON Migration Utility
AI-Powered Intelligent Vehicle Identification & Traffic Violation Detection System (ANPR)

Safely reads the original preserved SQLite database ('traffic_system.db')
without altering original tables or model weights, and optionally migrates
all 1,012 historical violations and 14 VAHAN vehicles into MongoDB or a JSON archive.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQLITE_DB_PATH = BASE_DIR / "legacy" / "traffic_system.db"
OUTPUT_SEED_PATH = BASE_DIR / "server" / "src" / "config" / "full_migrated_history.json"

def sanitize_snapshot_path(raw_path: str) -> str:
    """Strips arbitrary local filesystem roots and normalizes to web URL path."""
    if not raw_path:
        return ""
    clean = raw_path.replace("\\", "/")
    if clean.startswith("/evidence/") or clean.startswith("/uploads/"):
        return clean
    filename = clean.split("/")[-1]
    return f"/evidence/{filename}" if filename else ""

def read_sqlite_data():
    if not SQLITE_DB_PATH.exists():
        print(f"[Error] SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)

    print(f"[1/3] Reading preserved SQLite database: {SQLITE_DB_PATH}")
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Read VAHAN Vehicles
    cursor.execute("SELECT * FROM vahan_vehicles")
    vehicle_rows = [dict(row) for row in cursor.fetchall()]
    print(f"      Found {len(vehicle_rows)} VAHAN vehicle registration records.")

    # Read Violations
    cursor.execute("SELECT * FROM violations ORDER BY id ASC")
    violation_rows = []
    for row in cursor.fetchall():
        d = dict(row)
        d["snapshot_path"] = sanitize_snapshot_path(d.get("snapshot_path", ""))
        d["review_status"] = "CONFIRMED" if d.get("challan_status") == "PAID" else "PENDING"
        violation_rows.append(d)
    print(f"      Found {len(violation_rows)} statutory violation records.")

    conn.close()
    return vehicle_rows, violation_rows

def export_json(vehicles, violations, target_file):
    print(f"[2/3] Exporting sanitized records to {target_file}...")
    target_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "source": "traffic_system.db (Preserved SQLite)",
            "migrated_at": str(Path(__file__).stat().st_mtime),
            "vehicle_count": len(vehicles),
            "violation_count": len(violations),
        },
        "vehicles": vehicles,
        "violations": violations,
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"      Successfully saved {len(violations)} violations to {target_file.name}!")

def migrate_to_mongo(vehicles, violations, mongo_uri):
    print(f"[3/3] Connecting to MongoDB at {mongo_uri}...")
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        db = client.get_database("traffic_sentinel")
        
        # Upsert Vehicles
        veh_col = db.get_collection("vehicles")
        for v in vehicles:
            veh_col.update_one({"plate_number": v["plate_number"]}, {"$set": v}, upsert=True)
        print(f"      Upserted {len(vehicles)} vehicles into MongoDB.")

        # Upsert Violations
        viol_col = db.get_collection("violations")
        for v in violations:
            v_id = v.get("id")
            viol_col.update_one({"violation_id": v_id}, {"$set": {**v, "violation_id": v_id}}, upsert=True)
        print(f"      Upserted {len(violations)} violations into MongoDB.")
        print("[SUCCESS] MongoDB migration completed successfully!")
    except Exception as e:
        print(f"[Warning] MongoDB insertion skipped or unavailable: {e}")

def main():
    parser = argparse.ArgumentParser(description="Safely migrate SQLite traffic records to JSON or MongoDB.")
    parser.add_argument("--mongo-uri", type=str, default=None, help="Optional MongoDB connection string")
    parser.add_argument("--export-json", action="store_true", default=True, help="Export sanitized records to JSON")
    args = parser.parse_args()

    vehicles, violations = read_sqlite_data()

    if args.export_json:
        export_json(vehicles, violations, OUTPUT_SEED_PATH)

    if args.mongo_uri:
        migrate_to_mongo(vehicles, violations, args.mongo_uri)

if __name__ == "__main__":
    main()
