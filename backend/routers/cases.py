from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json
import uuid
from database import get_db
from models import Case, Customer, RiskScore
from schemas import CaseCreate, CaseUpdate

router = APIRouter()


@router.get("")
def get_cases(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Case)

    if status:
        query = query.filter(Case.status == status)
    if priority:
        query = query.filter(Case.priority == priority)
    if assigned_to:
        query = query.filter(Case.assigned_to == assigned_to)

    total = query.count()
    cases = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for case in cases:
        customer = db.query(Customer).filter_by(cif=case.cif).first()
        score = db.query(RiskScore).filter_by(cif=case.cif).order_by(RiskScore.id.desc()).first()

        result.append({
            "case_id": case.case_id,
            "cif": case.cif,
            "loan_id": case.loan_id,
            "created_date": case.created_date,
            "status": case.status,
            "assigned_to": case.assigned_to,
            "description": case.description,
            "priority": case.priority,
            "audit_log": case.audit_log,
            "customer_name": customer.customer_name if customer else "N/A",
            "risk_score": score.total_score if score else 0,
            "risk_category": score.risk_category if score else "Green"
        })

    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("")
def create_case(case_data: CaseCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter_by(cif=case_data.cif).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    case_id = f"CASE_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now().strftime("%Y-%m-%d")

    audit_log = json.dumps([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": "admin",
        "action": "Case được tạo",
        "details": case_data.description
    }], ensure_ascii=False)

    new_case = Case(
        case_id=case_id,
        cif=case_data.cif,
        loan_id=case_data.loan_id,
        created_date=now,
        status="todo",
        assigned_to=case_data.assigned_to,
        description=case_data.description,
        priority=case_data.priority,
        audit_log=audit_log
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return {"case_id": new_case.case_id, "status": "created"}


@router.put("/{case_id}")
def update_case(case_id: str, update_data: CaseUpdate, db: Session = Depends(get_db)):
    case = db.query(Case).filter_by(case_id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    old_status = case.status

    if update_data.status:
        case.status = update_data.status
    if update_data.assigned_to:
        case.assigned_to = update_data.assigned_to
    if update_data.description:
        case.description = update_data.description
    if update_data.priority:
        case.priority = update_data.priority

    # Update audit log
    try:
        log = json.loads(case.audit_log) if case.audit_log else []
    except Exception:
        log = []

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": "admin",
        "action": f"Cập nhật case",
        "details": f"Trạng thái: {old_status} → {update_data.status or old_status}"
    }
    log.append(log_entry)
    case.audit_log = json.dumps(log, ensure_ascii=False)

    db.commit()
    db.refresh(case)

    return {"case_id": case.case_id, "status": case.status, "updated": True}


@router.get("/{case_id}/audit-log")
def get_case_audit_log(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter_by(case_id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        log = json.loads(case.audit_log) if case.audit_log else []
    except Exception:
        log = []

    return {"case_id": case_id, "audit_log": log}
