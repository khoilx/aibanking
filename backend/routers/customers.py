from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
from database import get_db
from models import (
    Customer, LoanMaster, Transaction, OffBalance, CICExtract,
    RiskScore, TaxStatus, TaxInvoice, SocialInsurance, Logistics, Branch
)
from schemas import (
    CustomerListItem, CustomerDetail, CustomerBase, LoanSchema,
    OffBalanceSchema, TransactionSchema, RiskAnalysis, RuleHit,
    MisuseData, TaxStatusSchema, InvoiceSummary, SISchema
)

router = APIRouter()


@router.get("")
def get_customers(
    search: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Customer)

    if search:
        query = query.filter(
            Customer.customer_name.contains(search) |
            Customer.cif.contains(search) |
            Customer.tax_id.contains(search)
        )

    if branch_id:
        query = query.filter(Customer.branch_id == branch_id)

    total = query.count()
    customers = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for customer in customers:
        loans = db.query(LoanMaster).filter_by(cif=customer.cif).all()
        total_outstanding = sum(l.outstanding_balance for l in loans)
        max_debt_group = max((l.debt_group for l in loans), default=1)

        score = db.query(RiskScore).filter_by(cif=customer.cif).order_by(RiskScore.id.desc()).first()
        risk_score = score.total_score if score else 0
        risk_cat = score.risk_category if score else "Green"

        if risk_category and risk_cat != risk_category:
            continue

        branch = db.query(Branch).filter_by(branch_id=customer.branch_id).first()
        branch_name = branch.branch_name if branch else "N/A"

        result.append({
            "cif": customer.cif,
            "customer_name": customer.customer_name,
            "customer_type": customer.customer_type,
            "tax_id": customer.tax_id,
            "branch_id": customer.branch_id,
            "branch_name": branch_name,
            "segment": customer.segment,
            "credit_rating": customer.credit_rating,
            "total_outstanding": total_outstanding,
            "max_debt_group": max_debt_group,
            "risk_score": risk_score,
            "risk_category": risk_cat
        })

    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.get("/{cif}")
def get_customer_detail(cif: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter_by(cif=cif).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    loans = db.query(LoanMaster).filter_by(cif=cif).all()
    off_balance = db.query(OffBalance).filter_by(cif=cif).all()
    recent_txns = db.query(Transaction).filter_by(cif=cif).order_by(Transaction.txn_date.desc()).limit(20).all()
    cic = db.query(CICExtract).filter_by(cif=cif).first()

    # Risk analysis
    score = db.query(RiskScore).filter_by(cif=cif).order_by(RiskScore.id.desc()).first()
    rule_hits = []
    total_score = 0
    risk_category = "Green"
    model_version = None
    score_date = None
    if score:
        total_score = score.total_score
        risk_category = score.risk_category
        score_date = score.score_date
        # model_version is stored in last_updated field or obtained from pipeline metadata
        try:
            from ai_engine.pipeline import get_pipeline
            pipeline = get_pipeline()
            model_version = pipeline.last_trained
        except Exception:
            model_version = score.last_updated
        if score.rule_hits:
            try:
                hits = json.loads(score.rule_hits)
                rule_hits = []
                for h in hits:
                    try:
                        rule_hits.append(RuleHit(
                            rule_id=h.get("rule_id", ""),
                            description=h.get("description", ""),
                            points=h.get("points", 0),
                            severity=h.get("severity", "low")
                        ))
                    except Exception:
                        pass
            except Exception:
                pass

    # Misuse data
    tax_status_obj = None
    invoice_summary = None
    si_mismatch = None
    logistics_count = 0

    if customer.tax_id:
        tax = db.query(TaxStatus).filter_by(tax_id=customer.tax_id).first()
        if tax:
            tax_status_obj = TaxStatusSchema(
                tax_id=tax.tax_id,
                company_name=tax.company_name,
                status=tax.status,
                registration_date=tax.registration_date
            )

        invoices = db.query(TaxInvoice).filter_by(buyer_tax_id=customer.tax_id).all()
        if invoices:
            cancelled = sum(1 for i in invoices if i.status == "cancelled")
            invoice_summary = InvoiceSummary(
                total=len(invoices),
                cancelled=cancelled,
                cancellation_rate=round(cancelled / len(invoices), 3) if invoices else 0
            )

        si = db.query(SocialInsurance).filter_by(tax_id=customer.tax_id).first()
        if si:
            si_mismatch = SISchema(
                si_id=si.si_id,
                tax_id=si.tax_id,
                report_period=si.report_period,
                declared_employees=si.declared_employees,
                actual_employees=si.actual_employees,
                total_salary_fund=si.total_salary_fund
            )

        logistics_count = db.query(Logistics).filter(
            (Logistics.shipper_tax_id == customer.tax_id) |
            (Logistics.receiver_tax_id == customer.tax_id)
        ).count()

    return {
        "customer_info": {
            "cif": customer.cif,
            "customer_name": customer.customer_name,
            "customer_type": customer.customer_type,
            "tax_id": customer.tax_id,
            "id_number": customer.id_number,
            "phone": customer.phone,
            "email": customer.email,
            "branch_id": customer.branch_id,
            "segment": customer.segment,
            "created_date": customer.created_date,
            "credit_rating": customer.credit_rating
        },
        "loans": [{
            "loan_id": l.loan_id,
            "cif": l.cif,
            "branch_id": l.branch_id,
            "loan_amount": l.loan_amount,
            "outstanding_balance": l.outstanding_balance,
            "disbursement_date": l.disbursement_date,
            "maturity_date": l.maturity_date,
            "interest_rate": l.interest_rate,
            "loan_purpose": l.loan_purpose,
            "loan_category": l.loan_category,
            "debt_group": l.debt_group,
            "loan_officer": l.loan_officer,
            "status": l.status
        } for l in loans],
        "off_balance": [{
            "off_balance_id": ob.off_balance_id,
            "cif": ob.cif,
            "ob_type": ob.ob_type,
            "amount": ob.amount,
            "issue_date": ob.issue_date,
            "expiry_date": ob.expiry_date,
            "status": ob.status
        } for ob in off_balance],
        "recent_transactions": [{
            "txn_id": t.txn_id,
            "loan_id": t.loan_id,
            "cif": t.cif,
            "txn_date": t.txn_date,
            "txn_type": t.txn_type,
            "amount": t.amount,
            "description": t.description,
            "channel": t.channel
        } for t in recent_txns],
        "risk_analysis": {
            "total_score": total_score,
            "risk_category": risk_category,
            "model_version": model_version,
            "score_date": score_date,
            "rule_hits": [h.dict() for h in rule_hits],
            "cic": {
                "total_debt_other_banks": cic.total_debt_other_banks if cic else 0,
                "debt_group_other_banks": cic.debt_group_other_banks if cic else 1,
                "bad_debt_amount": cic.bad_debt_amount if cic else 0,
                "number_of_credit_institutions": cic.number_of_credit_institutions if cic else 0,
                "has_overdue_history": cic.has_overdue_history if cic else False
            } if cic else None
        },
        "misuse_data": {
            "tax_status": tax_status_obj.dict() if tax_status_obj else None,
            "invoice_summary": invoice_summary.dict() if invoice_summary else None,
            "si_mismatch": si_mismatch.dict() if si_mismatch else None,
            "logistics_count": logistics_count
        }
    }
