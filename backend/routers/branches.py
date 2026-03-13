from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Branch, LoanMaster, Customer, RiskScore
from schemas import BranchSummary, BranchDetail, BranchBase, PortfolioBreakdown, DebtGroupBreakdown, LoanSchema

router = APIRouter()


@router.get("", response_model=list[BranchSummary])
def get_branches(db: Session = Depends(get_db)):
    branches = db.query(Branch).all()
    result = []

    for branch in branches:
        loans = db.query(LoanMaster).filter_by(branch_id=branch.branch_id).all()
        customers = db.query(Customer).filter_by(branch_id=branch.branch_id).all()
        customer_cifs = [c.cif for c in customers]

        total_outstanding = sum(l.outstanding_balance for l in loans)
        npl_loans = [l for l in loans if l.debt_group >= 3]
        npl_outstanding = sum(l.outstanding_balance for l in npl_loans)
        npl_ratio = (npl_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0

        red_flag_count = 0
        for cif in customer_cifs:
            score = db.query(RiskScore).filter_by(cif=cif, risk_category="Red").first()
            if score:
                red_flag_count += 1

        result.append(BranchSummary(
            branch_id=branch.branch_id,
            branch_name=branch.branch_name,
            branch_director=branch.branch_director,
            address=branch.address,
            region=branch.region,
            total_outstanding=total_outstanding,
            total_customers=len(customers),
            total_loans=len(loans),
            npl_ratio=round(npl_ratio, 2),
            red_flag_count=red_flag_count
        ))

    return result


@router.get("/{branch_id}")
def get_branch_detail(branch_id: str, db: Session = Depends(get_db)):
    branch = db.query(Branch).filter_by(branch_id=branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    loans = db.query(LoanMaster).filter_by(branch_id=branch_id).all()
    total_outstanding = sum(l.outstanding_balance for l in loans)

    # Portfolio breakdown by category
    categories = {}
    for loan in loans:
        cat = loan.loan_category or "Other"
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += loan.outstanding_balance

    portfolio_breakdown = []
    for cat, amount in categories.items():
        pct = (amount / total_outstanding * 100) if total_outstanding > 0 else 0
        portfolio_breakdown.append(PortfolioBreakdown(
            category=cat,
            amount=amount,
            percentage=round(pct, 2)
        ))

    # Debt group breakdown
    debt_groups = {}
    for loan in loans:
        dg = loan.debt_group
        if dg not in debt_groups:
            debt_groups[dg] = {"amount": 0, "count": 0}
        debt_groups[dg]["amount"] += loan.outstanding_balance
        debt_groups[dg]["count"] += 1

    debt_group_breakdown = [
        DebtGroupBreakdown(group=g, amount=v["amount"], count=v["count"])
        for g, v in sorted(debt_groups.items())
    ]

    # Top risky loans (by debt group and outstanding)
    risky_loans = sorted(loans, key=lambda l: (l.debt_group, l.outstanding_balance), reverse=True)[:10]
    top_risky = [LoanSchema(
        loan_id=l.loan_id,
        cif=l.cif,
        branch_id=l.branch_id,
        loan_amount=l.loan_amount,
        outstanding_balance=l.outstanding_balance,
        disbursement_date=l.disbursement_date,
        maturity_date=l.maturity_date,
        interest_rate=l.interest_rate,
        loan_purpose=l.loan_purpose,
        loan_category=l.loan_category,
        debt_group=l.debt_group,
        loan_officer=l.loan_officer,
        status=l.status
    ) for l in risky_loans]

    # Early warnings
    warnings = []
    npl_loans = [l for l in loans if l.debt_group >= 3]
    if npl_loans:
        warnings.append(f"Có {len(npl_loans)} khoản vay nợ nhóm 3+ với tổng dư nợ {sum(l.outstanding_balance for l in npl_loans)/1e9:.1f} tỷ đồng")

    group2_loans = [l for l in loans if l.debt_group == 2]
    if group2_loans:
        warnings.append(f"Có {len(group2_loans)} khoản vay nhóm 2 cần theo dõi")

    customers = db.query(Customer).filter_by(branch_id=branch_id).all()
    red_customers = []
    for c in customers:
        score = db.query(RiskScore).filter_by(cif=c.cif, risk_category="Red").first()
        if score:
            red_customers.append(c.customer_name)

    if red_customers:
        warnings.append(f"Khách hàng rủi ro cao: {', '.join(red_customers[:3])}")

    return {
        "branch_info": {
            "branch_id": branch.branch_id,
            "branch_name": branch.branch_name,
            "branch_director": branch.branch_director,
            "address": branch.address,
            "region": branch.region
        },
        "total_outstanding": total_outstanding,
        "portfolio_breakdown": [p.dict() for p in portfolio_breakdown],
        "debt_group_breakdown": [d.dict() for d in debt_group_breakdown],
        "top_risky_loans": [l.dict() for l in top_risky],
        "early_warnings": warnings
    }
