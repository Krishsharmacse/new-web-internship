from app.database import SessionLocal
from app.models import Enquiry, History
from app.services.sop_matcher import match_sop_detailed
from app.logger import logger
from datetime import datetime

def process_enquiry_task(enquiry_id: int):
    db = SessionLocal()
    try:
        # Fetch the enquiry
        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
        if not enquiry:
            logger.error("Enquiry not found for background processing", extra={"enquiry_id": str(enquiry_id)})
            return

        logger.info("Processing enquiry", extra={"enquiry_id": str(enquiry_id), "channel": enquiry.channel})
        
        # Update status to processing
        enquiry.status = "processing"
        enquiry.updated_at = datetime.utcnow()
        
        # Log the event in history
        history1 = History(
            enquiry_id=enquiry_id,
            event_type="status_change",
            details={"old_status": "pending", "new_status": "processing"}
        )
        db.add(history1)
        db.commit()

        # Match SOP
        message = enquiry.message or ""
        match_result = match_sop_detailed(message)
        
        if match_result and match_result.confidence > 0.3:
            sop_name = match_result.sop_name
            response = match_result.response
            enquiry.status = "resolved"
            enquiry.sop_matched = sop_name
            enquiry.suggested_response = response
            
            logger.info("SOP matched", extra={"enquiry_id": str(enquiry_id), "sop_name": sop_name, "confidence": match_result.confidence})
            
            history2 = History(
                enquiry_id=enquiry_id,
                event_type="sop_matched",
                details={
                    "sop_name": sop_name, 
                    "suggested_response": response,
                    "confidence": round(match_result.confidence, 2),
                    "priority": match_result.priority.name,
                    "matched_keywords": match_result.matched_keywords,
                    "matched_phrase": match_result.matched_phrase
                }
            )
        else:
            enquiry.status = "escalated"
            enquiry.escalation_reason = "No SOP matched"
            
            logger.warning("Escalation triggered", extra={"enquiry_id": str(enquiry_id), "reason": "No SOP matched"})
            
            history2 = History(
                enquiry_id=enquiry_id,
                event_type="escalated",
                details={"reason": "No SOP matched"}
            )

        enquiry.updated_at = datetime.utcnow()
        db.add(history2)
        
        history3 = History(
            enquiry_id=enquiry_id,
            event_type="status_change",
            details={"old_status": "processing", "new_status": enquiry.status}
        )
        db.add(history3)
        db.commit()
        
        logger.info("Task processed successfully", extra={"enquiry_id": str(enquiry_id), "final_status": enquiry.status})
    finally:
        db.close()


def process_followup_task(enquiry_id: int, delay_minutes: int, message_template: str):
    import time
    # For prototype, we will just sleep for the delay.
    # In a real-world scenario with long delays, Celery or another task queue is better.
    logger.info("Scheduled follow-up", extra={"enquiry_id": str(enquiry_id), "delay_minutes": delay_minutes})
    
    db = SessionLocal()
    try:
        history1 = History(
            enquiry_id=enquiry_id,
            event_type="followup_scheduled",
            details={"delay_minutes": delay_minutes, "message_template": message_template}
        )
        db.add(history1)
        db.commit()
    finally:
        db.close()
        
    # Wait for the delay (sync sleep since we changed to sync router operations. 
    # Warning: Background tasks in fastAPI will block threads if time.sleep is used if not handled properly.
    # But since it's a prototype it's fine.
    time.sleep(delay_minutes * 60)
    
    logger.info("Executing follow-up", extra={"enquiry_id": str(enquiry_id)})
    
    db = SessionLocal()
    try:
        history2 = History(
            enquiry_id=enquiry_id,
            event_type="followup_executed",
            details={"message_sent": message_template or "Just checking in..."}
        )
        db.add(history2)
        db.commit()
    finally:
        db.close()
