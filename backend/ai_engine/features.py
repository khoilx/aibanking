import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import (
    Customer, LoanMaster, Transaction, CICExtract, TaxStatus,
    TaxInvoice, SocialInsurance, Logistics, Collateral, RiskScore
)

FEATURE_NAMES = [
    'max_debt_group', 'avg_debt_group', 'num_loans', 'total_outstanding_bn',
    'restructured_ratio', 'avg_ltv', 'max_ltv',
    'cash_withdrawal_ratio', 'time_to_withdrawal_h', 'round_txn_ratio',
    'txn_count', 'txn_velocity', 'repayment_regularity',
    'cic_bad_debt_bn', 'cic_debt_group', 'num_credit_institutions', 'has_overdue_history',
    'tax_status_risk', 'invoice_cancel_rate', 'invoice_suspicious_rate', 'total_invoice_amount_bn',
    'si_employee_ratio', 'si_declared_employees',
    'logistics_count', 'has_trading_no_logistics',
    'vendor_hub_degree', 'vendor_hub_amount_bn',
    'is_corporate', 'credit_rating_score', 'customer_age_days'
]


def _safe_days(date_str: str) -> float:
    """Parse a date string and return days since then."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return 0


def extract_features_for_customer(cif: str, db: Session, hub_features: dict = None) -> dict:
    """Extract all features for a single customer. Returns dict keyed by FEATURE_NAMES."""
    customer = db.query(Customer).filter(Customer.cif == cif).first()
    if not customer:
        return {}

    # --- Loan features ---
    loans = db.query(LoanMaster).filter(LoanMaster.cif == cif).all()
    if loans:
        debt_groups = [l.debt_group or 1 for l in loans]
        outstanding = [l.outstanding_balance or 0 for l in loans]
        total_outstanding = sum(outstanding)

        max_debt_group = max(debt_groups)
        avg_debt_group = (
            float(np.average(debt_groups, weights=outstanding))
            if total_outstanding > 0
            else float(np.mean(debt_groups))
        )
        num_loans = len(loans)
        total_outstanding_bn = total_outstanding / 1e9
        restructured = sum(1 for l in loans if l.status == 'restructured')
        restructured_ratio = restructured / num_loans

        # LTV (Loan-To-Value)
        ltvs = []
        for loan in loans:
            collaterals = db.query(Collateral).filter(Collateral.loan_id == loan.loan_id).all()
            total_col = sum(c.estimated_value or 0 for c in collaterals)
            if total_col > 0:
                ltvs.append((loan.outstanding_balance or 0) / total_col)
        avg_ltv = float(np.mean(ltvs)) if ltvs else 0.75
        max_ltv = float(max(ltvs)) if ltvs else 0.75
    else:
        max_debt_group = 1
        avg_debt_group = 1.0
        num_loans = 0
        total_outstanding_bn = 0.0
        restructured_ratio = 0.0
        avg_ltv = 0.0
        max_ltv = 0.0

    # --- Transaction features ---
    transactions = db.query(Transaction).filter(Transaction.cif == cif).all()
    txn_count = len(transactions)

    disbursements = [t for t in transactions if t.txn_type == 'disbursement']
    cash_withdrawals = [
        t for t in transactions
        if t.txn_type == 'repayment' and 'tiền mặt' in (t.description or '')
    ]

    total_disbursed = sum(t.amount or 0 for t in disbursements)

    cash_withdrawal_ratio = 0.0
    time_to_withdrawal_h = 999.0

    if disbursements and cash_withdrawals:
        total_cash = 0
        min_time_h = 999.0
        for disb in disbursements:
            try:
                disb_dt = datetime.strptime(disb.txn_date, "%Y-%m-%d")
                for w in cash_withdrawals:
                    try:
                        w_dt = datetime.strptime(w.txn_date, "%Y-%m-%d")
                        if disb_dt <= w_dt:
                            diff_h = (w_dt - disb_dt).total_seconds() / 3600
                            if diff_h <= 120:  # within 5 days
                                total_cash += w.amount or 0
                                if diff_h < min_time_h:
                                    min_time_h = diff_h
                    except Exception:
                        pass
            except Exception:
                pass

        if total_disbursed > 0:
            cash_withdrawal_ratio = min(1.0, total_cash / total_disbursed)
        time_to_withdrawal_h = min_time_h

    # Round number transactions
    amounts = [t.amount or 0 for t in transactions if t.amount]
    round_txn_count = sum(1 for a in amounts if a >= 1_000_000 and a % 1_000_000 == 0)
    round_txn_ratio = round_txn_count / len(amounts) if amounts else 0

    # Transaction velocity
    if txn_count >= 2:
        try:
            dates = sorted([
                datetime.strptime(t.txn_date, "%Y-%m-%d")
                for t in transactions if t.txn_date
            ])
            if len(dates) >= 2:
                span_months = max(1, (dates[-1] - dates[0]).days / 30)
                txn_velocity = txn_count / span_months
            else:
                txn_velocity = float(txn_count)
        except Exception:
            txn_velocity = txn_count / 12
    else:
        txn_velocity = float(txn_count)

    # Repayment regularity (std dev of intervals — lower = more regular)
    repayments = sorted(
        [t for t in transactions if t.txn_type == 'repayment' and t.txn_date],
        key=lambda t: t.txn_date
    )
    if len(repayments) >= 3:
        try:
            r_dates = [datetime.strptime(r.txn_date, "%Y-%m-%d") for r in repayments]
            intervals = [(r_dates[i + 1] - r_dates[i]).days for i in range(len(r_dates) - 1)]
            repayment_regularity = float(np.std(intervals))
        except Exception:
            repayment_regularity = 30.0
    else:
        repayment_regularity = 30.0

    # --- CIC features ---
    cic = db.query(CICExtract).filter(CICExtract.cif == cif).first()
    if cic:
        cic_bad_debt_bn = (cic.bad_debt_amount or 0) / 1e9
        cic_debt_group = cic.debt_group_other_banks or 1
        num_credit_institutions = cic.number_of_credit_institutions or 1
        has_overdue_history = int(cic.has_overdue_history or False)
    else:
        cic_bad_debt_bn = 0.0
        cic_debt_group = 1
        num_credit_institutions = 0
        has_overdue_history = 0

    # --- Tax/Invoice features ---
    tax_status_map = {'active': 0, 'suspended': 1, 'evading': 2, 'closed': 3}
    if customer.tax_id:
        tax = db.query(TaxStatus).filter(TaxStatus.tax_id == customer.tax_id).first()
        tax_status_risk = tax_status_map.get(tax.status, -1) if tax else -1

        invoices = db.query(TaxInvoice).filter(TaxInvoice.buyer_tax_id == customer.tax_id).all()
        if invoices:
            n_cancelled = sum(1 for i in invoices if i.status == 'cancelled')
            n_suspicious = sum(1 for i in invoices if i.status == 'suspicious')
            invoice_cancel_rate = n_cancelled / len(invoices)
            invoice_suspicious_rate = n_suspicious / len(invoices)
            total_invoice_amount_bn = sum(i.amount or 0 for i in invoices) / 1e9
        else:
            invoice_cancel_rate = 0.0
            invoice_suspicious_rate = 0.0
            total_invoice_amount_bn = 0.0
    else:
        tax_status_risk = -1
        invoice_cancel_rate = 0.0
        invoice_suspicious_rate = 0.0
        total_invoice_amount_bn = 0.0

    # --- BHXH (Social Insurance) features ---
    if customer.tax_id:
        si = db.query(SocialInsurance).filter(SocialInsurance.tax_id == customer.tax_id).first()
        if si and si.declared_employees and si.declared_employees > 0:
            si_employee_ratio = min(2.0, (si.actual_employees or 0) / si.declared_employees)
            si_declared_employees = si.declared_employees
        else:
            si_employee_ratio = 1.0
            si_declared_employees = 0
    else:
        si_employee_ratio = 1.0
        si_declared_employees = 0

    # --- Logistics features ---
    if customer.tax_id:
        logistics_count = db.query(Logistics).filter(
            or_(
                Logistics.shipper_tax_id == customer.tax_id,
                Logistics.receiver_tax_id == customer.tax_id
            )
        ).count()
    else:
        logistics_count = 0

    # Has trading loan but no logistics
    trading_loans = [l for l in loans if l.loan_category in ['Nong nghiep', 'Ban le', 'SX']]
    has_trading_no_logistics = int(
        bool(trading_loans) and logistics_count == 0 and customer.tax_id is not None
    )

    # --- Vendor hub features ---
    if hub_features:
        vendor_hub_degree = hub_features.get('vendor_hub_degree', 0)
        vendor_hub_amount_bn = hub_features.get('vendor_hub_amount_bn', 0.0)
    else:
        vendor_hub_degree = 0
        vendor_hub_amount_bn = 0.0

    # --- Customer profile ---
    is_corporate = int(customer.customer_type == 'Corporate')
    rating_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    credit_rating_score = rating_map.get(customer.credit_rating or 'B', 1)
    customer_age_days = _safe_days(customer.created_date or '2020-01-01')

    return {
        'max_debt_group': max_debt_group,
        'avg_debt_group': avg_debt_group,
        'num_loans': num_loans,
        'total_outstanding_bn': total_outstanding_bn,
        'restructured_ratio': restructured_ratio,
        'avg_ltv': avg_ltv,
        'max_ltv': max_ltv,
        'cash_withdrawal_ratio': cash_withdrawal_ratio,
        'time_to_withdrawal_h': time_to_withdrawal_h,
        'round_txn_ratio': round_txn_ratio,
        'txn_count': txn_count,
        'txn_velocity': txn_velocity,
        'repayment_regularity': repayment_regularity,
        'cic_bad_debt_bn': cic_bad_debt_bn,
        'cic_debt_group': cic_debt_group,
        'num_credit_institutions': num_credit_institutions,
        'has_overdue_history': has_overdue_history,
        'tax_status_risk': tax_status_risk,
        'invoice_cancel_rate': invoice_cancel_rate,
        'invoice_suspicious_rate': invoice_suspicious_rate,
        'total_invoice_amount_bn': total_invoice_amount_bn,
        'si_employee_ratio': si_employee_ratio,
        'si_declared_employees': si_declared_employees,
        'logistics_count': logistics_count,
        'has_trading_no_logistics': has_trading_no_logistics,
        'vendor_hub_degree': vendor_hub_degree,
        'vendor_hub_amount_bn': vendor_hub_amount_bn,
        'is_corporate': is_corporate,
        'credit_rating_score': credit_rating_score,
        'customer_age_days': customer_age_days,
    }


def extract_all_features(db: Session, hub_detector=None) -> pd.DataFrame:
    """Extract features for all customers. Returns DataFrame with cif as index."""
    customers = db.query(Customer).all()
    rows = []
    for customer in customers:
        hub_feats = {}
        if hub_detector:
            hub_feats = hub_detector.get_hub_features(customer.cif)
        features = extract_features_for_customer(customer.cif, db, hub_features=hub_feats)
        if features:
            features['cif'] = customer.cif
            rows.append(features)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).set_index('cif')
    # Ensure all expected feature columns are present
    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = 0

    return df[FEATURE_NAMES]


def get_bootstrap_labels(db: Session) -> pd.Series:
    """Generate initial training labels using existing rule-based risk scores.
    Returns Series: 0=Green, 1=Amber, 2=Red, indexed by cif."""
    scores = db.query(RiskScore).all()
    label_map = {'Green': 0, 'Amber': 1, 'Red': 2}
    data = {s.cif: label_map.get(s.risk_category, 0) for s in scores}

    # If no scores exist, derive labels from debt groups
    if not data:
        customers = db.query(Customer).all()
        for c in customers:
            loans = db.query(LoanMaster).filter(LoanMaster.cif == c.cif).all()
            max_dg = max((l.debt_group or 1 for l in loans), default=1)
            if max_dg >= 3:
                data[c.cif] = 2
            elif max_dg == 2:
                data[c.cif] = 1
            else:
                data[c.cif] = 0

    return pd.Series(data)
