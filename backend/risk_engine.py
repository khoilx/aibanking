import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    Customer, LoanMaster, Transaction, CICExtract, TaxStatus,
    TaxInvoice, SocialInsurance, Logistics, Collateral, RiskScore
)


RULES = {
    "R01": {"desc": "Nợ nhóm {group} - Nguy cơ mất vốn", "points": 30, "severity": "high"},
    "R02": {"desc": "Nợ xấu tại TCTD khác", "points": 20, "severity": "high"},
    "R03": {"desc": "Rút tiền mặt ngay sau giải ngân", "points": 25, "severity": "high"},
    "R04": {"desc": "MST bị đóng/bỏ trốn", "points": 35, "severity": "high"},
    "R05": {"desc": "Tỷ lệ hủy HĐ điện tử > 50%", "points": 25, "severity": "medium"},
    "R06": {"desc": "Bất thường nhân sự BHXH", "points": 20, "severity": "medium"},
    "R07": {"desc": "Hub nhà cung cấp đáng ngờ", "points": 30, "severity": "high"},
    "R08": {"desc": "Tỷ lệ vay/TSĐB vượt ngưỡng", "points": 20, "severity": "medium"},
    "R09": {"desc": "Lịch sử quá hạn tại TCTD", "points": 15, "severity": "low"},
    "R10": {"desc": "Không có vận đơn phù hợp mục đích vay", "points": 15, "severity": "low"},
}


def get_vendor_hub_customers(db: Session):
    """Find customers connected to same vendors (vendor hub pattern)."""
    invoices = db.query(TaxInvoice).filter(TaxInvoice.status != "cancelled").all()

    vendor_customers = {}
    for inv in invoices:
        if inv.seller_tax_id and inv.buyer_tax_id:
            if inv.seller_tax_id not in vendor_customers:
                vendor_customers[inv.seller_tax_id] = set()
            vendor_customers[inv.seller_tax_id].add(inv.buyer_tax_id)

    hub_vendors = {v: customers for v, customers in vendor_customers.items() if len(customers) >= 3}

    hub_cifs = set()
    for vendor, customers in hub_vendors.items():
        for tax_id in customers:
            customer = db.query(Customer).filter(Customer.tax_id == tax_id).first()
            if customer:
                hub_cifs.add(customer.cif)

    return hub_cifs, hub_vendors


def detect_cash_withdrawal_pattern(cif: str, db: Session) -> bool:
    """Check if customer withdrew > 80% of disbursement within 48h."""
    loans = db.query(LoanMaster).filter(LoanMaster.cif == cif).all()

    for loan in loans:
        disbursements = db.query(Transaction).filter(
            Transaction.loan_id == loan.loan_id,
            Transaction.txn_type == "disbursement"
        ).all()

        for disb in disbursements:
            try:
                disb_date = datetime.strptime(disb.txn_date, "%Y-%m-%d")
                cutoff = disb_date + timedelta(hours=48)

                withdrawals = db.query(Transaction).filter(
                    Transaction.cif == cif,
                    Transaction.txn_type == "repayment",
                    Transaction.description.contains("tiền mặt")
                ).all()

                total_withdrawn = 0
                for w in withdrawals:
                    try:
                        w_date = datetime.strptime(w.txn_date, "%Y-%m-%d")
                        if disb_date <= w_date <= cutoff:
                            total_withdrawn += w.amount
                    except Exception:
                        continue

                if disb.amount > 0 and total_withdrawn / disb.amount > 0.8:
                    return True
            except Exception:
                continue

    return False


def check_si_mismatch(tax_id: str, db: Session) -> bool:
    """Check if actual employees << declared employees."""
    si = db.query(SocialInsurance).filter(SocialInsurance.tax_id == tax_id).first()
    if si and si.declared_employees > 0:
        ratio = si.actual_employees / si.declared_employees
        return ratio < 0.5
    return False


def compute_risk_score(cif: str, db: Session) -> RiskScore:
    """Compute risk score for a customer."""
    customer = db.query(Customer).filter(Customer.cif == cif).first()
    if not customer:
        return None

    total_score = 0
    rule_hits = []

    # R01: Debt group >= 3
    loans = db.query(LoanMaster).filter(LoanMaster.cif == cif).all()
    max_debt_group = max((l.debt_group for l in loans), default=1)
    if max_debt_group >= 3:
        pts = RULES["R01"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R01",
            "description": RULES["R01"]["desc"].format(group=max_debt_group),
            "points": pts,
            "severity": RULES["R01"]["severity"]
        })

    # R02: CIC bad debt at other banks
    cic = db.query(CICExtract).filter(CICExtract.cif == cif).first()
    if cic and cic.bad_debt_amount > 0:
        pts = RULES["R02"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R02",
            "description": RULES["R02"]["desc"],
            "points": pts,
            "severity": RULES["R02"]["severity"]
        })

    # R03: Cash withdrawal > 80% within 48h of disbursement
    if detect_cash_withdrawal_pattern(cif, db):
        pts = RULES["R03"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R03",
            "description": RULES["R03"]["desc"],
            "points": pts,
            "severity": RULES["R03"]["severity"]
        })

    # R04: Tax status closed/evading
    if customer.tax_id:
        tax = db.query(TaxStatus).filter(TaxStatus.tax_id == customer.tax_id).first()
        if tax and tax.status in ["closed", "evading"]:
            pts = RULES["R04"]["points"]
            total_score += pts
            rule_hits.append({
                "rule_id": "R04",
                "description": RULES["R04"]["desc"],
                "points": pts,
                "severity": RULES["R04"]["severity"]
            })

    # R05: Invoice cancellation rate > 50%
    if customer.tax_id:
        invoices = db.query(TaxInvoice).filter(TaxInvoice.buyer_tax_id == customer.tax_id).all()
        if len(invoices) > 0:
            cancelled = sum(1 for i in invoices if i.status == "cancelled")
            if cancelled / len(invoices) > 0.5:
                pts = RULES["R05"]["points"]
                total_score += pts
                rule_hits.append({
                    "rule_id": "R05",
                    "description": RULES["R05"]["desc"],
                    "points": pts,
                    "severity": RULES["R05"]["severity"]
                })

    # R06: SI mismatch
    if customer.tax_id and check_si_mismatch(customer.tax_id, db):
        pts = RULES["R06"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R06",
            "description": RULES["R06"]["desc"],
            "points": pts,
            "severity": RULES["R06"]["severity"]
        })

    # R07: Vendor hub pattern
    hub_cifs, _ = get_vendor_hub_customers(db)
    if cif in hub_cifs:
        pts = RULES["R07"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R07",
            "description": RULES["R07"]["desc"],
            "points": pts,
            "severity": RULES["R07"]["severity"]
        })

    # R08: LTV > 85%
    for loan in loans:
        collaterals = db.query(Collateral).filter(Collateral.loan_id == loan.loan_id).all()
        total_collateral = sum(c.estimated_value for c in collaterals)
        if total_collateral > 0 and loan.outstanding_balance / total_collateral > 0.85:
            pts = RULES["R08"]["points"]
            total_score += pts
            rule_hits.append({
                "rule_id": "R08",
                "description": RULES["R08"]["desc"],
                "points": pts,
                "severity": RULES["R08"]["severity"]
            })
            break  # Only add once

    # R09: Overdue history in CIC
    if cic and cic.has_overdue_history:
        pts = RULES["R09"]["points"]
        total_score += pts
        rule_hits.append({
            "rule_id": "R09",
            "description": RULES["R09"]["desc"],
            "points": pts,
            "severity": RULES["R09"]["severity"]
        })

    # R10: No logistics data for trading loan
    trading_loans = [l for l in loans if l.loan_category in ["Nong nghiep", "Ban le"]]
    if trading_loans and customer.tax_id:
        logistics_count = db.query(Logistics).filter(
            (Logistics.shipper_tax_id == customer.tax_id) |
            (Logistics.receiver_tax_id == customer.tax_id)
        ).count()
        if logistics_count == 0:
            pts = RULES["R10"]["points"]
            total_score += pts
            rule_hits.append({
                "rule_id": "R10",
                "description": RULES["R10"]["desc"],
                "points": pts,
                "severity": RULES["R10"]["severity"]
            })

    # Determine risk category
    if total_score >= 60:
        risk_category = "Red"
    elif total_score >= 30:
        risk_category = "Amber"
    else:
        risk_category = "Green"

    today = datetime.now().strftime("%Y-%m-%d")

    # Update or create risk score
    existing = db.query(RiskScore).filter(RiskScore.cif == cif).first()
    if existing:
        existing.total_score = total_score
        existing.risk_category = risk_category
        existing.rule_hits = json.dumps(rule_hits, ensure_ascii=False)
        existing.score_date = today
        existing.last_updated = today
        db.commit()
        return existing
    else:
        risk_score = RiskScore(
            cif=cif,
            score_date=today,
            total_score=total_score,
            risk_category=risk_category,
            rule_hits=json.dumps(rule_hits, ensure_ascii=False),
            last_updated=today
        )
        db.add(risk_score)
        db.commit()
        db.refresh(risk_score)
        return risk_score


def run_batch_scoring(db: Session):
    """Score all customers."""
    customers = db.query(Customer).all()
    results = []
    for customer in customers:
        score = compute_risk_score(customer.cif, db)
        if score:
            results.append(score)
    return results
