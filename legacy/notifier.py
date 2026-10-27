"""
Notification Engine for AI-Powered Intelligent Vehicle Identification
and Traffic Violation Detection System using ANPR.
Integrates Twilio SMS, Fast2SMS API, and a production-grade simulated SMS logger.
"""

import os
import logging
from typing import Dict, Any, Optional
import config

logger = logging.getLogger("TrafficNotifier")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def build_challan_message(violation_data: Dict[str, Any]) -> str:
    """Builds the standardized e-Challan statutory SMS notification text."""
    plate = violation_data.get("plate_number", "UNKNOWN")
    v_type = violation_data.get("violation_type", "Traffic Violation")
    primary = violation_data.get("primary_fine", 0)
    secondary = violation_data.get("secondary_fine", 0)
    total = violation_data.get("total_fine", primary + secondary)
    timestamp = violation_data.get("timestamp", "Recent")
    challan_id = violation_data.get("id", "000")
    
    pay_url = f"{config.CHALLAN_PORTAL_BASE_URL}?challan=E-CH-2026-{challan_id}&veh={plate}"

    sec_note = f" (Includes ₹{secondary} expired doc penalty)" if secondary > 0 else ""

    message = (
        f"TRAFFIC POLICE NOTICE: E-Challan #{challan_id} issued for vehicle {plate}.\n"
        f"Violation: {v_type} on {timestamp}.\n"
        f"Fine Amount: INR {total}{sec_note}.\n"
        f"Pay online within 15 days to avoid court summons: {pay_url}"
    )
    return message

def send_twilio_sms(to_number: str, message_body: str) -> bool:
    """Dispatches SMS via Twilio API if valid credentials are provided."""
    try:
        from twilio.rest import Client
        
        # Check if dummy credentials
        if "mock" in config.TWILIO_ACCOUNT_SID or not config.TWILIO_ACCOUNT_SID.startswith("AC"):
            return False

        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=config.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        logger.info(f"Twilio SMS dispatched. SID: {message.sid}")
        return True
    except Exception as e:
        logger.warning(f"Twilio SMS delivery skipped/failed: {e}")
        return False

def send_fast2sms(to_number: str, message_body: str) -> bool:
    """Dispatches SMS via Fast2SMS Indian SMS Gateway API."""
    if not config.FAST2SMS_API_KEY:
        return False

    try:
        import requests
        # Clean mobile number to 10 digits
        clean_number = "".join(filter(str.isdigit, to_number))
        if len(clean_number) > 10:
            clean_number = clean_number[-10:]

        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": message_body,
            "language": "english",
            "flash": 0,
            "numbers": clean_number,
        }
        headers = {
            "authorization": config.FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        res_data = response.json()
        if res_data.get("return"):
            logger.info(f"Fast2SMS dispatched successfully to {clean_number}")
            return True
        else:
            logger.warning(f"Fast2SMS API response: {res_data}")
            return False
    except Exception as e:
        logger.warning(f"Fast2SMS dispatch failed: {e}")
        return False

def print_simulated_sms(to_number: str, owner_name: str, message_body: str, violation_data: Dict[str, Any]):
    """Pretty prints a realistic SMS push notification receipt to console."""
    border = "=" * 76
    sub_border = "-" * 76
    plate = violation_data.get("plate_number", "UNKNOWN")
    v_type = violation_data.get("violation_type", "Violation")
    total = violation_data.get("total_fine", 0)
    sec_fine = violation_data.get("secondary_fine", 0)

    print("\n" + border)
    print(f" [SMS NOTIFICATION DISPATCHED] Recipient: {to_number} ({owner_name})")
    print(sub_border)
    print(f" Vehicle Plate : {plate}")
    print(f" Violation     : {v_type}")
    print(f" Total Fine    : Rs. {total:,}" + (f" (Primary + Rs. {sec_fine} Secondary)" if sec_fine > 0 else ""))
    print(f" Snapshot Ref  : {violation_data.get('snapshot_path', 'N/A')}")
    print(sub_border)
    print(" [SMS Body Delivered]:")
    for line in message_body.split("\n"):
        print(f"   {line}")
    print(border + "\n")

def dispatch_violation_notice(violation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main notification dispatcher:
    1. Builds standardized legal notice text.
    2. Attempts Twilio or Fast2SMS if configured.
    3. Seamlessly falls back to simulated console delivery without breaking flow.
    """
    to_number = violation_data.get("mobile_number", "+919800000000")
    owner_name = violation_data.get("owner_name", "Vehicle Owner")
    message_body = build_challan_message(violation_data)

    sms_status = "FAILED"

    # Attempt 1: Fast2SMS if API key provided
    if send_fast2sms(to_number, message_body):
        sms_status = "SENT (Fast2SMS)"
    # Attempt 2: Twilio SMS
    elif send_twilio_sms(to_number, message_body):
        sms_status = "SENT (Twilio)"
    # Fallback: Production-grade Simulation Logger
    else:
        print_simulated_sms(to_number, owner_name, message_body, violation_data)
        sms_status = "SIMULATED"

    return {
        "status": sms_status,
        "recipient": to_number,
        "owner": owner_name,
        "message": message_body
    }
