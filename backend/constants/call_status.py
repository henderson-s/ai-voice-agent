"""
Call status constants and mappings.
"""

from typing import Dict

# Webhook event to call status mapping
WEBHOOK_STATUS_MAPPING: Dict[str, str] = {
    "call_started": "in_progress",
    "call_ended": "completed",
    "call_analyzed": "completed",
    "call_failed": "failed"
}

# Call status enum values
class CallStatus:
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
