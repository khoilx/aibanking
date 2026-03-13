from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from database import get_db
from models import LoanMaster, Customer, RiskScore, Case, Branch
from schemas import DashboardKPIs, TrendDataPoint, TopRedFlag

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(db: Session = Depends(get_db)):
    loans = db.query(LoanMaster).all()

    total_outstanding = sum(l.outstanding_balance for l in loans)
    npl_loans = [l for l in loans if l.debt_group >= 3]
    group2_loans = [l for l in loans if l.debt_group == 2]
    restructured_loans = [l for l in loans if l.status == "restructured"]

    npl_outstanding = sum(l.outstanding_balance for l in npl_loans)
    group2_outstanding = sum(l.outstanding_balance for l in group2_loans)
    restructured_outstanding = sum(l.outstanding_balance for l in restructured_loans)

    npl_ratio = (npl_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0
    group2_ratio = (group2_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0
    restructured_ratio = (restructured_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0

    # LLCR: Loan Loss Coverage Ratio (simulated)
    llcr = min(95, max(50, 100 - npl_ratio * 5))

    total_customers = db.query(Customer).count()
    total_loans = len(loans)
    red_flag_count = db.query(RiskScore).filter_by(risk_category="Red").count()

    return DashboardKPIs(
        npl_ratio=round(npl_ratio, 2),
        group2_ratio=round(group2_ratio, 2),
        restructured_ratio=round(restructured_ratio, 2),
        llcr=round(llcr, 1),
        total_outstanding=total_outstanding,
        total_customers=total_customers,
        total_loans=total_loans,
        red_flag_count=red_flag_count
    )


@router.get("/trend")
def get_trend(db: Session = Depends(get_db)):
    loans = db.query(LoanMaster).all()
    result = []

    for i in range(11, -1, -1):
        month_date = datetime.now() - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")

        # Simulate monthly variation
        base_outstanding = sum(l.outstanding_balance for l in loans)
        variation = 1 - (i * 0.008) + (hash(month_str) % 100) / 10000
        monthly_outstanding = base_outstanding * variation

        base_npl = sum(l.outstanding_balance for l in loans if l.debt_group >= 3)
        npl_variation = 1 + (i * 0.005) - (hash(month_str + "npl") % 100) / 5000
        monthly_npl = base_npl * npl_variation

        base_g2 = sum(l.outstanding_balance for l in loans if l.debt_group == 2)
        g2_variation = 1 + (i * 0.003)
        monthly_g2 = base_g2 * g2_variation

        npl_ratio = (monthly_npl / monthly_outstanding * 100) if monthly_outstanding > 0 else 0
        g2_ratio = (monthly_g2 / monthly_outstanding * 100) if monthly_outstanding > 0 else 0

        result.append({
            "month": month_str,
            "npl_ratio": round(max(0.5, npl_ratio), 2),
            "group2_ratio": round(max(1.0, g2_ratio), 2),
            "total_outstanding": monthly_outstanding
        })

    return result


@router.get("/top-red-flags")
def get_top_red_flags(db: Session = Depends(get_db)):
    red_scores = db.query(RiskScore).order_by(RiskScore.total_score.desc()).limit(15).all()
    result = []

    for score in red_scores:
        customer = db.query(Customer).filter_by(cif=score.cif).first()
        if not customer:
            continue

        loans = db.query(LoanMaster).filter_by(cif=score.cif).all()
        total_outstanding = sum(l.outstanding_balance for l in loans)

        branch = db.query(Branch).filter_by(branch_id=customer.branch_id).first()
        branch_name = branch.branch_name if branch else "N/A"

        rule_hits = []
        if score.rule_hits:
            try:
                hits = json.loads(score.rule_hits)
                rule_hits = [h["description"] for h in hits[:3]]
            except Exception:
                pass

        result.append({
            "cif": score.cif,
            "customer_name": customer.customer_name,
            "risk_score": score.total_score,
            "risk_category": score.risk_category,
            "total_outstanding": total_outstanding,
            "branch_name": branch_name,
            "top_rules": rule_hits
        })

    return result
