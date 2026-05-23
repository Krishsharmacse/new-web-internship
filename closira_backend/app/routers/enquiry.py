from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schemas import EnquiryCreate, EnquiryResponse, EnquiryHistoryResponse, JobResponse, FollowUpCreate, EscalateCreate
from app.database import get_db
from app.models import Enquiry, History
from app.services.background_tasks import process_enquiry_task, process_followup_task
from app.logger import logger
from datetime import datetime

router = APIRouter()

def format_enquiry(enquiry: Enquiry) -> dict:
    return {
        "id": str(enquiry.id),
        "channel": enquiry.channel,
        "customer_name": enquiry.customer_name,
        "message": enquiry.message,
        "status": enquiry.status,
        "created_at": enquiry.created_at,
        "updated_at": enquiry.updated_at,
        "sop_matched": enquiry.sop_matched,
        "suggested_response": enquiry.suggested_response,
        "escalation_reason": enquiry.escalation_reason
    }

def format_history(history: History) -> dict:
    return {
        "timestamp": history.timestamp,
        "event_type": history.event_type,
        "details": history.details
    }

@router.post("/enquiry", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_enquiry(enquiry_in: EnquiryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_enquiry = Enquiry(
        channel=enquiry_in.channel.value,
        customer_name=enquiry_in.customer_name,
        message=enquiry_in.message,
        status="pending"
    )
    db.add(new_enquiry)
    db.commit()
    db.refresh(new_enquiry)
    
    enquiry_id_str = str(new_enquiry.id)
    logger.info("Enquiry created", extra={"enquiry_id": enquiry_id_str, "channel": new_enquiry.channel})
    
    # Log creation in history
    new_history = History(
        enquiry_id=new_enquiry.id,
        event_type="enquiry_created",
        details={"channel": new_enquiry.channel, "customer_name": new_enquiry.customer_name}
    )
    db.add(new_history)
    db.commit()
    
    background_tasks.add_task(process_enquiry_task, new_enquiry.id)
    
    return JobResponse(job_id=enquiry_id_str, message="Enquiry created and processing started.")

@router.post("/enquiry/{id}/followup", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def schedule_followup(id: str, followup: FollowUpCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        enquiry_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
        
    background_tasks.add_task(process_followup_task, enquiry_id, followup.delay_minutes, followup.message_template)
    
    return JobResponse(job_id=id, message=f"Follow-up scheduled in {followup.delay_minutes} minutes.")

@router.post("/enquiry/{id}/escalate", response_model=EnquiryResponse)
def escalate_enquiry(id: str, escalate: EscalateCreate, db: Session = Depends(get_db)):
    try:
        enquiry_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
        
    enquiry.status = "escalated"
    enquiry.escalation_reason = escalate.reason
    enquiry.updated_at = datetime.utcnow()
    
    new_history = History(
        enquiry_id=enquiry_id,
        event_type="escalated_manually",
        details={"reason": escalate.reason}
    )
    db.add(new_history)
    db.commit()
    db.refresh(enquiry)
    
    logger.info("Enquiry escalated manually", extra={"enquiry_id": id, "reason": escalate.reason})
    
    return format_enquiry(enquiry)

@router.get("/enquiry/{id}/history", response_model=EnquiryHistoryResponse)
def get_enquiry_history(id: str, db: Session = Depends(get_db)):
    try:
        enquiry_id = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
        
    history_docs = db.query(History).filter(History.enquiry_id == enquiry_id).order_by(History.timestamp.asc()).all()
    
    return EnquiryHistoryResponse(
        enquiry=format_enquiry(enquiry),
        history=[format_history(doc) for doc in history_docs]
    )
