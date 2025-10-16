"""
Post-call analysis schemas for Retell AI.

These schemas define the structured data fields that Retell AI will extract
from call transcripts. Different schemas are used for different scenario types.
"""

from typing import List, Dict, Any


# Emergency Protocol Schema
EMERGENCY_PROTOCOL_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "boolean",
        "name": "is_emergency",
        "description": "Whether this call involves an emergency situation"
    },
    {
        "type": "enum",
        "name": "emergency_type",
        "description": "Type of emergency if applicable",
        "choices": ["accident", "breakdown", "medical", "flat_tire", "other", "none"]
    },
    {
        "type": "string",
        "name": "safety_status",
        "description": "Driver's confirmation of safety status",
        "examples": ["Driver confirmed everyone is safe", "Driver reported unsafe conditions"]
    },
    {
        "type": "enum",
        "name": "injury_status",
        "description": "Whether there are any injuries",
        "choices": ["no_injuries", "injuries_reported", "unknown"]
    },
    {
        "type": "string",
        "name": "location_emergency",
        "description": "Specific location of the emergency",
        "examples": ["I-10 near exit 42", "Mile marker 123 on I-15"]
    },
    {
        "type": "boolean",
        "name": "load_secure",
        "description": "Whether the load/cargo is secure"
    },
    {
        "type": "string",
        "name": "call_summary",
        "description": "Brief summary of the emergency call"
    }
]


# Driver Check-in Schema
DRIVER_CHECKIN_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "enum",
        "name": "call_outcome",
        "description": "The outcome or purpose of the call",
        "choices": ["in_transit_update", "arrival_confirmation", "delay_notification", "other"]
    },
    {
        "type": "enum",
        "name": "driver_status",
        "description": "Current status of the driver",
        "choices": ["driving", "arrived", "unloading", "delayed", "other"]
    },
    {
        "type": "string",
        "name": "current_location",
        "description": "Driver's current location",
        "examples": ["I-10 near Phoenix", "Exit 42 on I-15", "At delivery location"]
    },
    {
        "type": "string",
        "name": "eta",
        "description": "Estimated time of arrival",
        "examples": ["Tomorrow at 8 AM", "In 2 hours", "Around 3 PM today"]
    },
    {
        "type": "string",
        "name": "delay_reason",
        "description": "Reason for any delays if mentioned",
        "examples": ["Heavy traffic", "Weather conditions", "No delays"]
    },
    {
        "type": "string",
        "name": "unloading_status",
        "description": "Status of unloading if driver has arrived",
        "examples": ["At dock 12", "Waiting for door assignment", "N/A"]
    },
    {
        "type": "boolean",
        "name": "pod_reminder_acknowledged",
        "description": "Whether driver acknowledged the POD reminder"
    },
    {
        "type": "string",
        "name": "call_summary",
        "description": "Brief summary of the check-in call"
    }
]


def get_analysis_schema(scenario_type: str) -> List[Dict[str, Any]]:
    """
    Get the appropriate analysis schema based on scenario type.

    Args:
        scenario_type: Type of scenario ('driver_checkin' or 'emergency_protocol')

    Returns:
        List of field definitions for post-call analysis

    Example:
        >>> schema = get_analysis_schema('driver_checkin')
        >>> len(schema)
        8
    """
    if scenario_type == "emergency_protocol":
        return EMERGENCY_PROTOCOL_SCHEMA
    else:  # driver_checkin (default)
        return DRIVER_CHECKIN_SCHEMA
