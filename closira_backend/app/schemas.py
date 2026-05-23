from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChannelEnum(str, Enum):
    whatsapp = "whatsapp"
    email = "email"
    call = "call"
    instagram = "instagram"

class StatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    resolved = "resolved"
    escalated = "escalated"

class EnquiryCreate(BaseModel):
    channel: ChannelEnum
    customer_name: str
    message: str

class FollowUpCreate(BaseModel):
    delay_minutes: int = Field(..., gt=0)
    message_template: Optional[str] = None

class EscalateCreate(BaseModel):
    reason: str

class EnquiryResponse(BaseModel):
    id: str
    channel: ChannelEnum
    customer_name: str
    message: str
    status: StatusEnum
    created_at: datetime
    updated_at: datetime
    sop_matched: Optional[str] = None
    suggested_response: Optional[str] = None
    escalation_reason: Optional[str] = None

class HistoryItem(BaseModel):
    timestamp: datetime
    event_type: str
    details: Dict[str, Any]

class EnquiryHistoryResponse(BaseModel):
    enquiry: EnquiryResponse
    history: List[HistoryItem]

class JobResponse(BaseModel):
    job_id: str
    message: str
