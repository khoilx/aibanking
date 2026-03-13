"""
Audit AI - Hệ thống Kiểm toán Ngân hàng
Streamlit Application - Single file multipage app
"""

import streamlit as st
import sys
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Path setup - MUST happen before any other imports
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)

# Page config MUST be first Streamlit call
st.set_page_config(
    page_title="Audit AI - Hệ thống Kiểm toán NH",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Now import backend modules
try:
    # Set working dir so relative paths inside pipeline.py resolve correctly
    os.chdir(BACKEND_DIR)
    from database import SessionLocal, engine
    import models
    BACKEND_OK = True
except Exception as _e:
    BACKEND_OK = False
    st.error(f"Không thể import backend: {_e}")
    st.stop()

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dark theme CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
    }
    .stMarkdown, .stText, h1, h2, h3, p { color: #f1f5f9 !important; }
    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
    }
    .stButton button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
    }
    [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    .stSelectbox > div, .stTextInput > div {
        background: rgba(255,255,255,0.05) !important;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .risk-red { color: #ef4444; font-weight: bold; }
    .risk-amber { color: #f59e0b; font-weight: bold; }
    .risk-green { color: #22c55e; font-weight: bold; }
    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Plotly dark layout defaults
# ---------------------------------------------------------------------------
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#94a3b8", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def fmt_vnd(amount: float) -> str:
    """Format VND amount to human-readable string."""
    if amount is None:
        return "0"
    if amount >= 1e12:
        return f"{amount / 1e12:.1f} nghìn tỷ"
    if amount >= 1e9:
        return f"{amount / 1e9:.0f} tỷ"
    if amount >= 1e6:
        return f"{amount / 1e6:.0f} triệu"
    return f"{amount:,.0f}"


def risk_badge(category: str) -> str:
    icons = {"Red": "🔴 Đỏ", "Amber": "🟡 Vàng", "Green": "🟢 Xanh"}
    return icons.get(category, "⚪ Chưa xác định")


def risk_color(category: str) -> str:
    return {"Red": "🔴", "Amber": "🟡", "Green": "🟢"}.get(category, "⚪")


def debt_group_color(group: int) -> str:
    colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "⛔"}
    return colors.get(group, "⚪")


def severity_badge(severity: str) -> str:
    return {"high": "🔴 Cao", "medium": "🟡 Trung bình", "low": "🟢 Thấp"}.get(severity, severity)


# ---------------------------------------------------------------------------
# DB & AI initialization (cached, run once per session)
# ---------------------------------------------------------------------------

@st.cache_resource
def init_db() -> bool:
    """Create tables and seed if empty."""
    try:
        models.Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            if db.query(models.Branch).count() == 0:
                from seed_data import seed_database
                seed_database(db)
                logger.info("DB seeded successfully.")
            return True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"DB init error: {e}")
        return False


@st.cache_resource
def init_ai_pipeline():
    """Load or train AI pipeline once per process."""
    try:
        from ai_engine.pipeline import get_pipeline
        pipeline = get_pipeline()
        if not pipeline.classifier.is_fitted:
            db = SessionLocal()
            try:
                pipeline.train(db)
                pipeline.score_all(db)
            finally:
                db.close()
        return pipeline
    except Exception as e:
        logger.error(f"AI pipeline init error: {e}")
        return None


# ---------------------------------------------------------------------------
# Cached data query helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def get_dashboard_kpis(_db_key: str):
    """Compute executive dashboard KPIs."""
    db = SessionLocal()
    try:
        loans = db.query(models.LoanMaster).filter(
            models.LoanMaster.status != "closed"
        ).all()

        total_outstanding = sum(l.outstanding_balance or 0 for l in loans)
        npl_outstanding = sum(
            l.outstanding_balance or 0 for l in loans if (l.debt_group or 1) >= 3
        )
        group2_outstanding = sum(
            l.outstanding_balance or 0 for l in loans if (l.debt_group or 1) == 2
        )
        restructured_outstanding = sum(
            l.outstanding_balance or 0 for l in loans if l.status == "restructured"
        )

        npl_ratio = (npl_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0
        group2_ratio = (group2_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0
        restructured_ratio = (restructured_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0

        # LLCR: loan count with collateral coverage >= 1
        from models import Collateral
        llcr_count = 0
        for loan in loans:
            collaterals = db.query(Collateral).filter(
                Collateral.loan_id == loan.loan_id
            ).all()
            total_coll = sum(c.estimated_value or 0 for c in collaterals)
            if loan.outstanding_balance and loan.outstanding_balance > 0 and total_coll > 0:
                if total_coll / loan.outstanding_balance >= 1.0:
                    llcr_count += 1
        llcr = (llcr_count / len(loans) * 100) if loans else 0

        # Red flags
        red_scores = db.query(models.RiskScore).filter(
            models.RiskScore.risk_category == "Red"
        ).count()
        amber_scores = db.query(models.RiskScore).filter(
            models.RiskScore.risk_category == "Amber"
        ).count()

        return {
            "total_outstanding": total_outstanding,
            "npl_ratio": round(npl_ratio, 2),
            "group2_ratio": round(group2_ratio, 2),
            "restructured_ratio": round(restructured_ratio, 2),
            "llcr": round(llcr, 1),
            "red_count": red_scores,
            "amber_count": amber_scores,
            "total_loans": len(loans),
        }
    except Exception as e:
        logger.error(f"KPI query error: {e}")
        return {}
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_portfolio_by_category(_db_key: str):
    """Portfolio breakdown by loan category."""
    db = SessionLocal()
    try:
        loans = db.query(models.LoanMaster).filter(
            models.LoanMaster.status != "closed"
        ).all()
        cat_map = {}
        for loan in loans:
            cat = loan.loan_category or "Khác"
            cat_map[cat] = cat_map.get(cat, 0) + (loan.outstanding_balance or 0)
        return cat_map
    except Exception as e:
        logger.error(f"Portfolio query error: {e}")
        return {}
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_top_red_flag_customers(_db_key: str, limit: int = 15):
    """Get top customers by risk score."""
    db = SessionLocal()
    try:
        scores = (
            db.query(models.RiskScore, models.Customer)
            .join(models.Customer, models.RiskScore.cif == models.Customer.cif)
            .filter(models.RiskScore.risk_category.in_(["Red", "Amber"]))
            .order_by(models.RiskScore.total_score.desc())
            .limit(limit)
            .all()
        )
        rows = []
        for score, cust in scores:
            # Sum outstanding
            outstanding = db.query(models.LoanMaster).filter(
                models.LoanMaster.cif == cust.cif,
                models.LoanMaster.status != "closed"
            ).all()
            total_ob = sum(l.outstanding_balance or 0 for l in outstanding)
            rows.append({
                "CIF": cust.cif,
                "Tên khách hàng": cust.customer_name,
                "Chi nhánh": cust.branch_id or "",
                "Rủi ro": risk_badge(score.risk_category),
                "Điểm": score.total_score or 0,
                "Dư nợ (tỷ)": round(total_ob / 1e9, 2),
                "Cập nhật": score.last_updated or "",
            })
        return rows
    except Exception as e:
        logger.error(f"Top red flag query error: {e}")
        return []
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_all_customers_df(_db_key: str):
    """All customers with risk scores as DataFrame."""
    db = SessionLocal()
    try:
        customers = db.query(models.Customer).all()
        rows = []
        for cust in customers:
            score = (
                db.query(models.RiskScore)
                .filter(models.RiskScore.cif == cust.cif)
                .first()
            )
            # Total outstanding
            loans = db.query(models.LoanMaster).filter(
                models.LoanMaster.cif == cust.cif,
                models.LoanMaster.status != "closed",
            ).all()
            total_ob = sum(l.outstanding_balance or 0 for l in loans)
            max_dg = max((l.debt_group or 1 for l in loans), default=1)
            rows.append({
                "CIF": cust.cif,
                "Tên KH": cust.customer_name,
                "Loại": cust.customer_type or "",
                "Chi nhánh": cust.branch_id or "",
                "Phân khúc": cust.segment or "",
                "Xếp hạng TD": cust.credit_rating or "",
                "Nhóm nợ max": max_dg,
                "Dư nợ (tỷ)": round(total_ob / 1e9, 2),
                "Điểm RR": score.total_score if score else None,
                "Danh mục RR": score.risk_category if score else "Chưa xếp hạng",
            })
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"Customer DF query error: {e}")
        return pd.DataFrame()
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_branches_summary(_db_key: str):
    """Summary stats per branch."""
    db = SessionLocal()
    try:
        branches = db.query(models.Branch).all()
        rows = []
        for branch in branches:
            loans = db.query(models.LoanMaster).filter(
                models.LoanMaster.branch_id == branch.branch_id,
                models.LoanMaster.status != "closed",
            ).all()
            customers = db.query(models.Customer).filter(
                models.Customer.branch_id == branch.branch_id
            ).count()
            total_ob = sum(l.outstanding_balance or 0 for l in loans)
            npl = sum(l.outstanding_balance or 0 for l in loans if (l.debt_group or 1) >= 3)
            npl_ratio = (npl / total_ob * 100) if total_ob > 0 else 0

            red_count = (
                db.query(models.RiskScore)
                .join(models.Customer, models.RiskScore.cif == models.Customer.cif)
                .filter(
                    models.Customer.branch_id == branch.branch_id,
                    models.RiskScore.risk_category == "Red",
                )
                .count()
            )
            rows.append({
                "branch_id": branch.branch_id,
                "branch_name": branch.branch_name,
                "director": branch.branch_director or "",
                "region": branch.region or "",
                "customers": customers,
                "total_outstanding": total_ob,
                "npl_ratio": round(npl_ratio, 2),
                "red_count": red_count,
                "loan_count": len(loans),
            })
        return rows
    except Exception as e:
        logger.error(f"Branch summary error: {e}")
        return []
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_customer_detail(_db_key: str, cif: str):
    """Full customer detail dict."""
    db = SessionLocal()
    try:
        cust = db.query(models.Customer).filter(models.Customer.cif == cif).first()
        if not cust:
            return None

        loans = db.query(models.LoanMaster).filter(models.LoanMaster.cif == cif).all()
        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.cif == cif)
            .order_by(models.Transaction.txn_date.desc())
            .limit(100)
            .all()
        )
        off_balance = db.query(models.OffBalance).filter(models.OffBalance.cif == cif).all()
        risk_score = db.query(models.RiskScore).filter(models.RiskScore.cif == cif).first()
        cic = db.query(models.CICExtract).filter(models.CICExtract.cif == cif).first()
        cases = db.query(models.Case).filter(models.Case.cif == cif).all()

        # Misuse data
        tax_status = None
        invoices = []
        si_data = None
        logistics_count = 0
        if cust.tax_id:
            tax_status = db.query(models.TaxStatus).filter(
                models.TaxStatus.tax_id == cust.tax_id
            ).first()
            invoices = db.query(models.TaxInvoice).filter(
                models.TaxInvoice.buyer_tax_id == cust.tax_id
            ).all()
            si_data = db.query(models.SocialInsurance).filter(
                models.SocialInsurance.tax_id == cust.tax_id
            ).first()
            logistics_count = db.query(models.Logistics).filter(
                (models.Logistics.shipper_tax_id == cust.tax_id)
                | (models.Logistics.receiver_tax_id == cust.tax_id)
            ).count()

        # Collaterals
        collaterals = db.query(models.Collateral).filter(
            models.Collateral.cif == cif
        ).all()

        return {
            "customer": {
                "cif": cust.cif,
                "name": cust.customer_name,
                "type": cust.customer_type or "",
                "tax_id": cust.tax_id or "",
                "id_number": cust.id_number or "",
                "phone": cust.phone or "",
                "email": cust.email or "",
                "branch_id": cust.branch_id or "",
                "segment": cust.segment or "",
                "created_date": cust.created_date or "",
                "credit_rating": cust.credit_rating or "",
            },
            "loans": [
                {
                    "loan_id": l.loan_id,
                    "amount": l.loan_amount or 0,
                    "outstanding": l.outstanding_balance or 0,
                    "disbursement_date": l.disbursement_date or "",
                    "maturity_date": l.maturity_date or "",
                    "interest_rate": l.interest_rate or 0,
                    "purpose": l.loan_purpose or "",
                    "category": l.loan_category or "",
                    "debt_group": l.debt_group or 1,
                    "officer": l.loan_officer or "",
                    "status": l.status or "",
                }
                for l in loans
            ],
            "transactions": [
                {
                    "txn_id": t.txn_id,
                    "date": t.txn_date or "",
                    "type": t.txn_type or "",
                    "amount": t.amount or 0,
                    "description": t.description or "",
                    "channel": t.channel or "",
                }
                for t in transactions
            ],
            "off_balance": [
                {
                    "ob_id": ob.off_balance_id,
                    "type": ob.ob_type or "",
                    "amount": ob.amount or 0,
                    "issue_date": ob.issue_date or "",
                    "expiry_date": ob.expiry_date or "",
                    "status": ob.status or "",
                }
                for ob in off_balance
            ],
            "risk_score": {
                "total_score": risk_score.total_score if risk_score else None,
                "category": risk_score.risk_category if risk_score else None,
                "rule_hits": (
                    json.loads(risk_score.rule_hits)
                    if risk_score and risk_score.rule_hits
                    else []
                ),
                "last_updated": risk_score.last_updated if risk_score else None,
            },
            "cic": {
                "total_debt_other": cic.total_debt_other_banks if cic else 0,
                "debt_group_other": cic.debt_group_other_banks if cic else 1,
                "bad_debt": cic.bad_debt_amount if cic else 0,
                "num_institutions": cic.number_of_credit_institutions if cic else 0,
                "has_overdue": cic.has_overdue_history if cic else False,
            },
            "tax_status": {
                "tax_id": cust.tax_id or "",
                "status": tax_status.status if tax_status else None,
                "company_name": tax_status.company_name if tax_status else None,
                "registration_date": tax_status.registration_date if tax_status else None,
            },
            "invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "date": inv.invoice_date or "",
                    "amount": inv.amount or 0,
                    "status": inv.status or "",
                }
                for inv in invoices
            ],
            "social_insurance": {
                "declared": si_data.declared_employees if si_data else None,
                "actual": si_data.actual_employees if si_data else None,
                "salary_fund": si_data.total_salary_fund if si_data else None,
            },
            "logistics_count": logistics_count,
            "collaterals": [
                {
                    "collateral_id": c.collateral_id,
                    "type": c.collateral_type or "",
                    "value": c.estimated_value or 0,
                    "valuation_date": c.valuation_date or "",
                    "address": c.address or "",
                    "status": c.status or "",
                }
                for c in collaterals
            ],
            "cases": [
                {
                    "case_id": c.case_id,
                    "status": c.status or "",
                    "priority": c.priority or "",
                    "description": c.description or "",
                    "created_date": c.created_date or "",
                    "assigned_to": c.assigned_to or "",
                }
                for c in cases
            ],
        }
    except Exception as e:
        logger.error(f"Customer detail error: {e}")
        return None
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_misuse_data(_db_key: str):
    """Analytics for misuse detection."""
    db = SessionLocal()
    try:
        from risk_engine import RULES

        # All red/amber customers with rule hits
        flagged_scores = db.query(models.RiskScore).filter(
            models.RiskScore.risk_category.in_(["Red", "Amber"])
        ).all()

        rule_freq = {}
        flagged_outstanding = 0.0

        for score in flagged_scores:
            hits = []
            if score.rule_hits:
                try:
                    hits = json.loads(score.rule_hits)
                except Exception:
                    hits = []
            for hit in hits:
                rid = hit.get("rule_id", "")
                desc = hit.get("description", rid)
                key = f"{rid}: {desc[:40]}"
                rule_freq[key] = rule_freq.get(key, 0) + 1

            # Sum outstanding for flagged CIF
            loans = db.query(models.LoanMaster).filter(
                models.LoanMaster.cif == score.cif,
                models.LoanMaster.status != "closed",
            ).all()
            flagged_outstanding += sum(l.outstanding_balance or 0 for l in loans)

        # Vendor hubs
        from risk_engine import get_vendor_hub_customers
        hub_cifs, hub_vendors = get_vendor_hub_customers(db)

        hub_rows = []
        for vendor_tax, buyer_set in hub_vendors.items():
            # Get vendor name
            tax_status = db.query(models.TaxStatus).filter(
                models.TaxStatus.tax_id == vendor_tax
            ).first()
            vendor_name = tax_status.company_name if tax_status else vendor_tax

            # Connected customers
            connected_customers = []
            for buyer_tax_id in buyer_set:
                cust = db.query(models.Customer).filter(
                    models.Customer.tax_id == buyer_tax_id
                ).first()
                if cust:
                    total_inv = db.query(models.TaxInvoice).filter(
                        models.TaxInvoice.buyer_tax_id == buyer_tax_id,
                        models.TaxInvoice.seller_tax_id == vendor_tax,
                    ).all()
                    inv_total = sum(i.amount or 0 for i in total_inv)
                    connected_customers.append({
                        "cif": cust.cif,
                        "name": cust.customer_name,
                        "invoice_total": inv_total,
                    })

            hub_rows.append({
                "vendor_tax": vendor_tax,
                "vendor_name": vendor_name,
                "buyer_count": len(buyer_set),
                "connected_customers": connected_customers,
            })

        return {
            "flagged_outstanding": flagged_outstanding,
            "flagged_count": len(flagged_scores),
            "rule_freq": rule_freq,
            "hub_rows": hub_rows,
            "hub_cifs": list(hub_cifs),
        }
    except Exception as e:
        logger.error(f"Misuse data error: {e}")
        return {}
    finally:
        db.close()


@st.cache_data(ttl=300)
def get_all_cases_df(_db_key: str):
    """All cases with customer names."""
    db = SessionLocal()
    try:
        cases = db.query(models.Case, models.Customer).join(
            models.Customer, models.Case.cif == models.Customer.cif
        ).all()
        rows = []
        for case, cust in cases:
            rows.append({
                "case_id": case.case_id,
                "cif": case.cif,
                "customer_name": cust.customer_name,
                "status": case.status or "todo",
                "priority": case.priority or "medium",
                "assigned_to": case.assigned_to or "",
                "description": case.description or "",
                "created_date": case.created_date or "",
                "loan_id": case.loan_id or "",
            })
        return rows
    except Exception as e:
        logger.error(f"Cases query error: {e}")
        return []
    finally:
        db.close()


@st.cache_data(ttl=60)
def get_users_list(_db_key: str):
    """All users for login lookup."""
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        return [
            {
                "username": u.username,
                "hashed_password": u.hashed_password,
                "full_name": u.full_name or u.username,
                "role": u.role or "auditor",
                "user_id": u.user_id,
            }
            for u in users
        ]
    except Exception as e:
        logger.error(f"User list error: {e}")
        return []
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

def show_sidebar():
    with st.sidebar:
        st.markdown("## 🛡️ Audit AI")
        st.markdown("*Hệ thống Kiểm toán NH*")
        st.divider()

        pages = {
            "📊 Dashboard": "dashboard",
            "🏢 Chi nhánh": "branches",
            "👤 Khách hàng": "customers",
            "⚠️ Phân tích Sai mục đích": "misuse",
            "📋 Quản lý Case": "cases",
            "🤖 AI Engine": "ai_engine",
        }

        for label, page_key in pages.items():
            is_active = st.session_state.get("selected_page") == page_key
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.selected_page = page_key
                st.rerun()

        st.divider()
        st.markdown(f"👤 **{st.session_state.get('user_fullname', 'Admin')}**")
        st.markdown(f"*{st.session_state.get('user_role', 'admin')}*")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            for key in ["authenticated", "username", "user_role", "user_fullname"]:
                st.session_state.pop(key, None)
            st.rerun()


# ---------------------------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------------------------

def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🛡️ Audit AI")
        st.markdown("### Hệ thống Kiểm toán Ngân hàng")
        st.markdown("---")

        with st.form("login_form"):
            st.markdown("#### Đăng nhập")
            username = st.text_input("Tên đăng nhập", value="admin", key="login_username")
            password = st.text_input("Mật khẩu", type="password", value="admin123", key="login_password")
            submit = st.form_submit_button("Đăng nhập", use_container_width=True)

            if submit:
                users = get_users_list("users")
                hashed = hashlib.sha256(password.encode()).hexdigest()
                matched = next(
                    (u for u in users if u["username"] == username and u["hashed_password"] == hashed),
                    None,
                )
                if matched:
                    st.session_state.authenticated = True
                    st.session_state.username = matched["username"]
                    st.session_state.user_role = matched["role"]
                    st.session_state.user_fullname = matched["full_name"]
                    st.session_state.selected_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu.")

        st.divider()
        st.markdown("**Tài khoản demo:**")
        demo_accounts = [
            ("admin", "admin123", "Quản trị viên"),
            ("auditor1", "audit123", "Kiểm toán viên"),
            ("manager1", "manager123", "Quản lý"),
        ]
        for uname, pwd, role in demo_accounts:
            st.markdown(f"- `{uname}` / `{pwd}` — {role}")


# ---------------------------------------------------------------------------
# DASHBOARD PAGE
# ---------------------------------------------------------------------------

def show_dashboard():
    st.markdown("# 📊 Dashboard Điều hành")
    st.markdown("*Tổng quan rủi ro danh mục tín dụng*")
    st.divider()

    kpis = get_dashboard_kpis("kpis")
    if not kpis:
        st.warning("Không thể tải dữ liệu KPI.")
        return

    # KPI Metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric(
            "Tỷ lệ NPL",
            f"{kpis.get('npl_ratio', 0):.2f}%",
            delta=None,
            help="Tỷ lệ nợ xấu (nhóm 3-5) / tổng dư nợ",
        )
    with col2:
        st.metric(
            "Nhóm 2",
            f"{kpis.get('group2_ratio', 0):.2f}%",
            help="Tỷ lệ nợ cần chú ý (nhóm 2)",
        )
    with col3:
        st.metric(
            "Cơ cấu nợ",
            f"{kpis.get('restructured_ratio', 0):.2f}%",
            help="Tỷ lệ nợ được cơ cấu lại",
        )
    with col4:
        st.metric(
            "LLCR",
            f"{kpis.get('llcr', 0):.1f}%",
            help="Tỷ lệ khoản vay có TSĐB đủ bảo đảm",
        )
    with col5:
        total_ob = kpis.get("total_outstanding", 0)
        st.metric(
            "Tổng dư nợ",
            fmt_vnd(total_ob),
            help="Tổng dư nợ tín dụng đang hoạt động",
        )
    with col6:
        st.metric(
            "🔴 Cờ đỏ",
            str(kpis.get("red_count", 0)),
            delta=f"+{kpis.get('amber_count', 0)} vàng",
            delta_color="inverse",
            help="Số khách hàng rủi ro cao",
        )

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Phân bổ danh mục cho vay")
        cat_data = get_portfolio_by_category("portfolio")
        if cat_data:
            labels = list(cat_data.keys())
            values = [v / 1e9 for v in cat_data.values()]
            fig_pie = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.45,
                    textinfo="label+percent",
                    marker_colors=px.colors.qualitative.Bold,
                )
            )
            fig_pie.update_layout(
                **PLOTLY_LAYOUT,
                title="Dư nợ theo danh mục (tỷ VND)",
                height=320,
                showlegend=True,
                legend=dict(orientation="v", x=1, y=0.5),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Không có dữ liệu danh mục.")

    with col_right:
        st.markdown("#### Phân bổ nhóm nợ")
        db = SessionLocal()
        try:
            group_counts = {}
            loans = db.query(models.LoanMaster).filter(
                models.LoanMaster.status != "closed"
            ).all()
            for loan in loans:
                g = loan.debt_group or 1
                group_counts[g] = group_counts.get(g, 0) + (loan.outstanding_balance or 0)
        finally:
            db.close()

        if group_counts:
            groups = sorted(group_counts.keys())
            group_labels = [f"Nhóm {g}" for g in groups]
            group_values = [group_counts[g] / 1e9 for g in groups]
            group_colors = ["#22c55e", "#f59e0b", "#f97316", "#ef4444", "#7f1d1d"]
            fig_bar = go.Figure(
                go.Bar(
                    x=group_labels,
                    y=group_values,
                    marker_color=[group_colors[min(g - 1, 4)] for g in groups],
                    text=[f"{v:.0f}B" for v in group_values],
                    textposition="outside",
                )
            )
            fig_bar.update_layout(
                **PLOTLY_LAYOUT,
                title="Dư nợ theo nhóm (tỷ VND)",
                height=320,
                showlegend=False,
                yaxis_title="Tỷ VND",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔴 Top 15 Khách hàng rủi ro cao nhất")

    top_red = get_top_red_flag_customers("top_red")
    if top_red:
        df_red = pd.DataFrame(top_red)

        # Horizontal bar chart
        fig_hbar = go.Figure(
            go.Bar(
                x=df_red["Dư nợ (tỷ)"].values,
                y=df_red["Tên khách hàng"].values,
                orientation="h",
                marker_color=[
                    "#ef4444" if "Đỏ" in row.get("Rủi ro", "")
                    else "#f59e0b"
                    for row in top_red
                ],
                text=[f"{v:.1f}B" for v in df_red["Dư nợ (tỷ)"].values],
                textposition="inside",
            )
        )
        fig_hbar.update_layout(
            **PLOTLY_LAYOUT,
            title="Dư nợ theo khách hàng rủi ro (tỷ VND)",
            height=400,
            xaxis_title="Dư nợ (tỷ VND)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_hbar, use_container_width=True)

        # Table
        st.dataframe(
            df_red,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Điểm": st.column_config.ProgressColumn(
                    "Điểm RR", min_value=0, max_value=100, format="%d"
                ),
                "Dư nợ (tỷ)": st.column_config.NumberColumn(
                    "Dư nợ (tỷ)", format="%.2f"
                ),
            },
        )
    else:
        st.info("Không có khách hàng cờ đỏ.")


# ---------------------------------------------------------------------------
# BRANCHES PAGE
# ---------------------------------------------------------------------------

def show_branches():
    st.markdown("# 🏢 Tổng quan Chi nhánh")
    st.divider()

    branches_data = get_branches_summary("branches")
    if not branches_data:
        st.warning("Không thể tải dữ liệu chi nhánh.")
        return

    branch_names = [f"{b['branch_id']} - {b['branch_name']}" for b in branches_data]
    branch_map = {f"{b['branch_id']} - {b['branch_name']}": b for b in branches_data}

    # Summary table
    st.markdown("#### Tổng quan tất cả chi nhánh")
    summary_rows = []
    for b in branches_data:
        summary_rows.append({
            "Chi nhánh": b["branch_name"],
            "Vùng": b["region"],
            "Giám đốc": b["director"],
            "Khách hàng": b["customers"],
            "Dư nợ (tỷ)": round(b["total_outstanding"] / 1e9, 1),
            "Tỷ lệ NPL (%)": b["npl_ratio"],
            "🔴 Cờ đỏ": b["red_count"],
        })
    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(
        df_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tỷ lệ NPL (%)": st.column_config.ProgressColumn(
                "NPL %", min_value=0, max_value=20, format="%.2f%%"
            ),
        },
    )

    st.divider()

    # Branch comparison chart
    branch_names_list = [b["branch_name"] for b in branches_data]
    outstanding_list = [b["total_outstanding"] / 1e9 for b in branches_data]
    npl_list = [b["npl_ratio"] for b in branches_data]

    col_l, col_r = st.columns(2)
    with col_l:
        fig_ob = go.Figure(
            go.Bar(
                x=branch_names_list,
                y=outstanding_list,
                marker_color="#3b82f6",
                text=[f"{v:.0f}B" for v in outstanding_list],
                textposition="outside",
            )
        )
        fig_ob.update_layout(
            **PLOTLY_LAYOUT,
            title="Dư nợ theo chi nhánh (tỷ VND)",
            height=350,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_ob, use_container_width=True)

    with col_r:
        fig_npl = go.Figure(
            go.Bar(
                x=branch_names_list,
                y=npl_list,
                marker_color=["#ef4444" if n > 3 else "#f59e0b" if n > 1 else "#22c55e" for n in npl_list],
                text=[f"{n:.1f}%" for n in npl_list],
                textposition="outside",
            )
        )
        fig_npl.update_layout(
            **PLOTLY_LAYOUT,
            title="Tỷ lệ NPL theo chi nhánh (%)",
            height=350,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_npl, use_container_width=True)

    st.divider()
    st.markdown("#### Chi tiết Chi nhánh")
    selected_label = st.selectbox(
        "Chọn chi nhánh:", branch_names, key="branch_selector"
    )
    if selected_label:
        b = branch_map[selected_label]
        st.session_state.selected_branch = b["branch_id"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tổng dư nợ", fmt_vnd(b["total_outstanding"]))
        with col2:
            st.metric("Tỷ lệ NPL", f"{b['npl_ratio']:.2f}%")
        with col3:
            st.metric("Số KH", str(b["customers"]))
        with col4:
            st.metric("🔴 Cờ đỏ", str(b["red_count"]))

        # Top risky loans for this branch
        db = SessionLocal()
        try:
            loans = (
                db.query(models.LoanMaster, models.Customer)
                .join(models.Customer, models.LoanMaster.cif == models.Customer.cif)
                .filter(
                    models.LoanMaster.branch_id == b["branch_id"],
                    models.LoanMaster.status != "closed",
                    models.LoanMaster.debt_group >= 2,
                )
                .order_by(models.LoanMaster.debt_group.desc(), models.LoanMaster.outstanding_balance.desc())
                .limit(20)
                .all()
            )
            if loans:
                st.markdown(f"##### Top khoản vay rủi ro - {b['branch_name']}")
                loan_rows = []
                for loan, cust in loans:
                    loan_rows.append({
                        "Mã vay": loan.loan_id,
                        "Khách hàng": cust.customer_name,
                        "Dư nợ (tỷ)": round((loan.outstanding_balance or 0) / 1e9, 2),
                        "Nhóm nợ": f"{debt_group_color(loan.debt_group or 1)} Nhóm {loan.debt_group or 1}",
                        "Danh mục": loan.loan_category or "",
                        "Mục đích": (loan.loan_purpose or "")[:40],
                        "Trạng thái": loan.status or "",
                    })
                st.dataframe(pd.DataFrame(loan_rows), use_container_width=True, hide_index=True)
            else:
                st.info("Không có khoản vay rủi ro tại chi nhánh này.")
        finally:
            db.close()


# ---------------------------------------------------------------------------
# CUSTOMERS PAGE
# ---------------------------------------------------------------------------

def show_customers():
    st.markdown("# 👤 Khách hàng 360°")
    st.divider()

    df_all = get_all_customers_df("customers")
    if df_all.empty:
        st.warning("Không có dữ liệu khách hàng.")
        return

    # Filters
    col_f1, col_f2, col_f3, col_f4 = st.columns([3, 2, 2, 2])
    with col_f1:
        search_text = st.text_input(
            "🔍 Tìm kiếm (tên / CIF)", placeholder="Nhập tên hoặc CIF..."
        )
    with col_f2:
        branches_opt = ["Tất cả"] + sorted(df_all["Chi nhánh"].dropna().unique().tolist())
        selected_branch_filter = st.selectbox("Chi nhánh", branches_opt)
    with col_f3:
        risk_opts = ["Tất cả", "Red", "Amber", "Green", "Chưa xếp hạng"]
        selected_risk = st.selectbox("Danh mục rủi ro", risk_opts)
    with col_f4:
        type_opts = ["Tất cả"] + sorted(df_all["Loại"].dropna().unique().tolist())
        selected_type = st.selectbox("Loại KH", type_opts)

    # Apply filters
    filtered = df_all.copy()
    if search_text:
        mask = (
            filtered["CIF"].str.contains(search_text, case=False, na=False)
            | filtered["Tên KH"].str.contains(search_text, case=False, na=False)
        )
        filtered = filtered[mask]
    if selected_branch_filter != "Tất cả":
        filtered = filtered[filtered["Chi nhánh"] == selected_branch_filter]
    if selected_risk != "Tất cả":
        filtered = filtered[filtered["Danh mục RR"] == selected_risk]
    if selected_type != "Tất cả":
        filtered = filtered[filtered["Loại"] == selected_type]

    st.markdown(f"**{len(filtered)}** khách hàng")
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Điểm RR": st.column_config.ProgressColumn(
                "Điểm RR", min_value=0, max_value=100, format="%d"
            ),
            "Dư nợ (tỷ)": st.column_config.NumberColumn("Dư nợ (tỷ)", format="%.2f"),
        },
    )

    st.divider()
    st.markdown("#### Chi tiết khách hàng")

    # Select customer
    cif_options = ["-- Chọn --"] + filtered["CIF"].tolist()
    default_cif = st.session_state.get("selected_cif", "-- Chọn --")
    if default_cif not in cif_options:
        default_cif = "-- Chọn --"

    selected_cif = st.selectbox(
        "Chọn khách hàng để xem chi tiết:",
        cif_options,
        index=cif_options.index(default_cif) if default_cif in cif_options else 0,
        key="cif_selector",
    )

    if selected_cif and selected_cif != "-- Chọn --":
        st.session_state.selected_cif = selected_cif
        _show_customer_detail(selected_cif)


def _show_customer_detail(cif: str):
    """Render full customer detail tabs."""
    detail = get_customer_detail("detail", cif)
    if not detail:
        st.error(f"Không tìm thấy khách hàng CIF: {cif}")
        return

    cust = detail["customer"]
    risk = detail["risk_score"]
    loans = detail["loans"]

    # Header
    risk_cat = risk.get("category") or "Chưa xếp hạng"
    risk_score_val = risk.get("total_score")
    st.markdown(
        f"### {cust['name']} — CIF: `{cust['cif']}` &nbsp;&nbsp; {risk_badge(risk_cat)}"
    )

    tabs = st.tabs(
        ["📋 Tổng quan", "💰 Dư nợ", "📈 Giao dịch", "⚠️ Phân tích Rủi ro", "🔍 Dữ liệu Sai mục đích"]
    )

    # --- Tab 1: Overview ---
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Thông tin cơ bản**")
            info_rows = [
                ("CIF", cust["cif"]),
                ("Tên", cust["name"]),
                ("Loại", cust["type"]),
                ("Phân khúc", cust["segment"]),
                ("Chi nhánh", cust["branch_id"]),
                ("Xếp hạng TD", cust["credit_rating"]),
                ("Ngày tạo", cust["created_date"]),
            ]
            if cust["tax_id"]:
                info_rows.append(("Mã số thuế", cust["tax_id"]))
            if cust["id_number"]:
                info_rows.append(("CMND/CCCD", cust["id_number"]))
            if cust["phone"]:
                info_rows.append(("Điện thoại", cust["phone"]))
            if cust["email"]:
                info_rows.append(("Email", cust["email"]))
            for label, value in info_rows:
                st.markdown(f"- **{label}:** {value}")

        with col2:
            cic = detail["cic"]
            st.markdown("**Thông tin CIC**")
            st.markdown(f"- **Dư nợ tại TCTD khác:** {fmt_vnd(cic['total_debt_other'])}")
            st.markdown(f"- **Nhóm nợ tại TCTD khác:** Nhóm {cic['debt_group_other']}")
            st.markdown(f"- **Nợ xấu:** {fmt_vnd(cic['bad_debt'])}")
            st.markdown(f"- **Số TCTD:** {cic['num_institutions']}")
            st.markdown(f"- **Lịch sử quá hạn:** {'⚠️ Có' if cic['has_overdue'] else '✅ Không'}")

            if detail["cases"]:
                st.markdown("**Cases đang xử lý**")
                for case in detail["cases"][:5]:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        case["priority"], "⚪"
                    )
                    st.markdown(
                        f"- {priority_icon} `{case['case_id']}` — {case['status']} — {case['description'][:50]}"
                    )

    # --- Tab 2: Loans ---
    with tabs[1]:
        if loans:
            loan_df = pd.DataFrame(loans)
            loan_df["Dư nợ (tỷ)"] = loan_df["outstanding"].apply(lambda x: round(x / 1e9, 2))
            loan_df["Số tiền vay (tỷ)"] = loan_df["amount"].apply(lambda x: round(x / 1e9, 2))
            loan_df["Nhóm nợ"] = loan_df["debt_group"].apply(
                lambda g: f"{debt_group_color(g)} Nhóm {g}"
            )
            display_cols = ["loan_id", "Số tiền vay (tỷ)", "Dư nợ (tỷ)", "Nhóm nợ",
                            "category", "purpose", "disbursement_date", "maturity_date",
                            "interest_rate", "status", "officer"]
            existing = [c for c in display_cols if c in loan_df.columns]
            st.dataframe(loan_df[existing], use_container_width=True, hide_index=True)

            # Collaterals
            if detail["collaterals"]:
                st.markdown("**Tài sản đảm bảo**")
                coll_df = pd.DataFrame(detail["collaterals"])
                coll_df["Giá trị (tỷ)"] = coll_df["value"].apply(lambda x: round(x / 1e9, 2))
                st.dataframe(coll_df, use_container_width=True, hide_index=True)

            # Off-balance
            if detail["off_balance"]:
                st.markdown("**Ngoại bảng**")
                ob_df = pd.DataFrame(detail["off_balance"])
                ob_df["Giá trị (tỷ)"] = ob_df["amount"].apply(lambda x: round(x / 1e9, 2))
                st.dataframe(ob_df, use_container_width=True, hide_index=True)
        else:
            st.info("Khách hàng không có khoản vay nào.")

    # --- Tab 3: Transactions ---
    with tabs[2]:
        txns = detail["transactions"]
        if txns:
            txn_df = pd.DataFrame(txns)
            txn_df["Số tiền (triệu)"] = txn_df["amount"].apply(lambda x: round(x / 1e6, 1))
            txn_df_sorted = txn_df.sort_values("date", ascending=True)

            # Bar chart by month
            try:
                txn_df_sorted["month"] = pd.to_datetime(
                    txn_df_sorted["date"], errors="coerce"
                ).dt.to_period("M").astype(str)
                monthly = txn_df_sorted.groupby(["month", "type"])["amount"].sum().reset_index()
                fig_txn = px.bar(
                    monthly,
                    x="month",
                    y="amount",
                    color="type",
                    labels={"amount": "Số tiền (VND)", "month": "Tháng", "type": "Loại GD"},
                    title="Giao dịch theo tháng",
                    barmode="stack",
                )
                fig_txn.update_layout(**PLOTLY_LAYOUT, height=300)
                st.plotly_chart(fig_txn, use_container_width=True)
            except Exception:
                pass

            st.dataframe(
                txn_df[["date", "type", "Số tiền (triệu)", "description", "channel"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Không có giao dịch.")

    # --- Tab 4: Risk Analysis ---
    with tabs[3]:
        col_gauge, col_info = st.columns([1, 2])
        with col_gauge:
            score_val = risk_score_val or 0
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=score_val,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Điểm Rủi ro", "font": {"color": "#f1f5f9"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                        "bar": {"color": "#3b82f6"},
                        "steps": [
                            {"range": [0, 30], "color": "#064e3b"},
                            {"range": [30, 60], "color": "#78350f"},
                            {"range": [60, 100], "color": "#7f1d1d"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 3},
                            "thickness": 0.75,
                            "value": score_val,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                **PLOTLY_LAYOUT,
                height=250,
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_info:
            st.markdown(f"**Danh mục rủi ro:** {risk_badge(risk_cat)}")
            if risk.get("last_updated"):
                st.markdown(f"**Cập nhật lần cuối:** {risk['last_updated']}")

            rule_hits = risk.get("rule_hits", [])
            if rule_hits:
                st.markdown("**Các vi phạm phát hiện:**")
                for hit in rule_hits:
                    sev = hit.get("severity", "low")
                    sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
                    desc = hit.get("description", hit.get("rule_id", ""))
                    pts = hit.get("points", 0)
                    st.markdown(f"- {sev_icon} **{hit.get('rule_id', '')}**: {desc} (+{pts} điểm)")
            else:
                st.success("Không phát hiện vi phạm quy tắc nào.")

        # AI probabilities
        pipeline = init_ai_pipeline()
        if pipeline:
            try:
                ai_result = pipeline.score_single(cif, SessionLocal())
                if ai_result:
                    probs = ai_result.get("probabilities", {})
                    st.markdown("**Xác suất AI (Random Forest):**")
                    col_p1, col_p2, col_p3 = st.columns(3)
                    with col_p1:
                        st.metric("🟢 Xanh (Green)", f"{probs.get('Green', 0) * 100:.1f}%")
                    with col_p2:
                        st.metric("🟡 Vàng (Amber)", f"{probs.get('Amber', 0) * 100:.1f}%")
                    with col_p3:
                        st.metric("🔴 Đỏ (Red)", f"{probs.get('Red', 0) * 100:.1f}%")

                    anomaly = ai_result.get("anomaly_score", 0)
                    st.metric("⚠️ Điểm bất thường", f"{anomaly:.1f}/100")
            except Exception as e:
                st.warning(f"Không thể chạy AI scoring: {e}")

    # --- Tab 5: Misuse Data ---
    with tabs[4]:
        tax_status = detail["tax_status"]
        invoices = detail["invoices"]
        si = detail["social_insurance"]
        logistics_count = detail["logistics_count"]

        if not cust.get("tax_id"):
            st.info("Khách hàng cá nhân - Không có dữ liệu thuế / BHXH.")
            return

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("**Trạng thái Thuế**")
            if tax_status and tax_status.get("status"):
                status_icons = {
                    "active": "✅ Hoạt động",
                    "closed": "❌ Đã đóng",
                    "evading": "⚠️ Bỏ trốn thuế",
                    "suspended": "🔶 Tạm ngừng",
                }
                st.markdown(
                    f"- **Trạng thái:** {status_icons.get(tax_status['status'], tax_status['status'])}"
                )
                if tax_status.get("company_name"):
                    st.markdown(f"- **Tên công ty:** {tax_status['company_name']}")
                if tax_status.get("registration_date"):
                    st.markdown(f"- **Ngày đăng ký:** {tax_status['registration_date']}")
            else:
                st.info("Không có dữ liệu trạng thái thuế.")

        with col_m2:
            st.markdown("**Thông tin BHXH**")
            if si and si.get("declared") is not None:
                ratio = (
                    si["actual"] / si["declared"] if si["declared"] > 0 else 0
                )
                ratio_icon = "✅" if ratio >= 0.8 else "⚠️"
                st.markdown(f"- **Số NV khai báo:** {si['declared']}")
                st.markdown(f"- **Số NV thực tế:** {si['actual']}")
                st.markdown(f"- **Tỷ lệ:** {ratio_icon} {ratio:.0%}")
                if si.get("salary_fund"):
                    st.markdown(f"- **Quỹ lương:** {fmt_vnd(si['salary_fund'])}")
            else:
                st.info("Không có dữ liệu BHXH.")

        # Invoice analysis
        if invoices:
            st.markdown("**Phân tích Hóa đơn điện tử**")
            inv_df = pd.DataFrame(invoices)
            status_counts = inv_df["status"].value_counts()
            total_inv = len(inv_df)
            cancelled_count = status_counts.get("cancelled", 0)
            suspicious_count = status_counts.get("suspicious", 0)
            valid_count = status_counts.get("valid", 0)

            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            with col_i1:
                st.metric("Tổng HĐ", total_inv)
            with col_i2:
                st.metric("Hợp lệ", valid_count)
            with col_i3:
                st.metric("Hủy", cancelled_count)
            with col_i4:
                cancel_rate = cancelled_count / total_inv * 100 if total_inv > 0 else 0
                st.metric(
                    "Tỷ lệ hủy",
                    f"{cancel_rate:.1f}%",
                    delta=None,
                    help="Ngưỡng cảnh báo: >50%",
                )

            # Pie chart
            fig_inv = go.Figure(
                go.Pie(
                    labels=status_counts.index.tolist(),
                    values=status_counts.values.tolist(),
                    hole=0.4,
                    marker_colors=["#22c55e", "#ef4444", "#f59e0b"],
                )
            )
            fig_inv.update_layout(
                **PLOTLY_LAYOUT, title="Phân loại HĐ điện tử", height=250
            )
            st.plotly_chart(fig_inv, use_container_width=True)
        else:
            st.info("Không có dữ liệu hóa đơn điện tử.")

        # Logistics
        st.markdown(f"**Vận đơn:** {'✅ Có' if logistics_count > 0 else '⚠️ Không có'} ({logistics_count} vận đơn)")


# ---------------------------------------------------------------------------
# MISUSE ANALYTICS PAGE
# ---------------------------------------------------------------------------

def show_misuse():
    st.markdown("# ⚠️ Phân tích Sai mục đích sử dụng vốn")
    st.divider()

    misuse_data = get_misuse_data("misuse")
    if not misuse_data:
        st.warning("Không thể tải dữ liệu phân tích.")
        return

    # KPI header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Dư nợ bị cờ đỏ",
            fmt_vnd(misuse_data.get("flagged_outstanding", 0)),
        )
    with col2:
        st.metric("Số KH cờ đỏ/vàng", str(misuse_data.get("flagged_count", 0)))
    with col3:
        hub_rows = misuse_data.get("hub_rows", [])
        st.metric("Hub nhà cung cấp đáng ngờ", str(len(hub_rows)))

    st.divider()

    # Fraud pattern frequency
    rule_freq = misuse_data.get("rule_freq", {})
    if rule_freq:
        st.markdown("#### Tần suất vi phạm theo quy tắc")
        sorted_rules = sorted(rule_freq.items(), key=lambda x: x[1], reverse=True)
        rule_labels = [r[0] for r in sorted_rules]
        rule_counts = [r[1] for r in sorted_rules]

        fig_rules = go.Figure(
            go.Bar(
                x=rule_counts,
                y=rule_labels,
                orientation="h",
                marker_color="#f59e0b",
                text=[str(c) for c in rule_counts],
                textposition="inside",
            )
        )
        fig_rules.update_layout(
            **PLOTLY_LAYOUT,
            title="Số lượng vi phạm theo quy tắc",
            height=max(300, len(rule_labels) * 35),
            xaxis_title="Số KH vi phạm",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_rules, use_container_width=True)

    st.divider()

    # Vendor hub analysis
    st.markdown("#### Hub Nhà cung cấp đáng ngờ")
    if hub_rows:
        for hub in hub_rows:
            with st.expander(
                f"🏭 {hub['vendor_name']} (MST: {hub['vendor_tax']}) — {hub['buyer_count']} khách hàng"
            ):
                st.markdown(f"**Mã số thuế vendor:** `{hub['vendor_tax']}`")
                st.markdown(f"**Số KH kết nối:** {hub['buyer_count']}")
                connected = hub.get("connected_customers", [])
                if connected:
                    hub_cust_df = pd.DataFrame(connected)
                    hub_cust_df["Tổng HĐ (tỷ)"] = hub_cust_df["invoice_total"].apply(
                        lambda x: round(x / 1e9, 2)
                    )
                    st.dataframe(
                        hub_cust_df[["cif", "name", "Tổng HĐ (tỷ)"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                    # Drill-down button
                    for cust in connected[:3]:
                        if st.button(
                            f"🔍 Xem chi tiết {cust['name']}",
                            key=f"hub_cust_{cust['cif']}",
                        ):
                            st.session_state.selected_cif = cust["cif"]
                            st.session_state.selected_page = "customers"
                            st.rerun()
    else:
        st.info("Không phát hiện hub nhà cung cấp đáng ngờ.")


# ---------------------------------------------------------------------------
# CASES PAGE
# ---------------------------------------------------------------------------

def show_cases():
    st.markdown("# 📋 Quản lý Case Kiểm toán")
    st.divider()

    cases_data = get_all_cases_df("cases")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả", "todo", "in_progress", "pending_branch", "closed"],
        )
    with col_f2:
        priority_filter = st.selectbox("Ưu tiên", ["Tất cả", "high", "medium", "low"])
    with col_f3:
        assignees = ["Tất cả"] + sorted(
            list({c["assigned_to"] for c in cases_data if c["assigned_to"]})
        )
        assigned_filter = st.selectbox("Được giao", assignees)

    filtered_cases = [c for c in cases_data if (
        (status_filter == "Tất cả" or c["status"] == status_filter)
        and (priority_filter == "Tất cả" or c["priority"] == priority_filter)
        and (assigned_filter == "Tất cả" or c["assigned_to"] == assigned_filter)
    )]

    st.markdown(f"**{len(filtered_cases)}** cases")

    # Kanban-style columns
    status_labels = {
        "todo": "📝 Chờ xử lý",
        "in_progress": "🔄 Đang xử lý",
        "pending_branch": "⏳ Chờ chi nhánh",
        "closed": "✅ Đã đóng",
    }
    statuses = ["todo", "in_progress", "pending_branch", "closed"]
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    kanban_cols = {
        "todo": col_k1,
        "in_progress": col_k2,
        "pending_branch": col_k3,
        "closed": col_k4,
    }

    for status, col in kanban_cols.items():
        with col:
            status_cases = [c for c in filtered_cases if c["status"] == status]
            st.markdown(f"**{status_labels[status]}** ({len(status_cases)})")
            for case in status_cases:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    case["priority"], "⚪"
                )
                with st.expander(
                    f"{priority_icon} {case['case_id']}", expanded=False
                ):
                    st.markdown(f"**KH:** {case['customer_name']}")
                    st.markdown(f"**CIF:** `{case['cif']}`")
                    st.markdown(f"**Giao cho:** {case['assigned_to']}")
                    st.markdown(f"**Ngày tạo:** {case['created_date']}")
                    if case["description"]:
                        st.markdown(f"**Mô tả:** {case['description'][:100]}")
                    if st.button(
                        "🔍 Xem KH", key=f"case_view_{case['case_id']}"
                    ):
                        st.session_state.selected_cif = case["cif"]
                        st.session_state.selected_page = "customers"
                        st.rerun()

    st.divider()

    # Create new case
    st.markdown("#### ➕ Tạo Case mới")
    with st.form("new_case_form"):
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            new_cif = st.text_input("CIF Khách hàng *", placeholder="VD: CIF001")
            new_priority = st.selectbox("Mức độ ưu tiên", ["high", "medium", "low"])
        with col_n2:
            new_assigned = st.text_input("Giao cho", placeholder="Tên kiểm toán viên")
            new_loan_id = st.text_input("Mã khoản vay (tùy chọn)")

        new_desc = st.text_area("Mô tả *", placeholder="Mô tả chi tiết về case...")
        submit_case = st.form_submit_button("Tạo Case", use_container_width=True)

        if submit_case:
            if not new_cif or not new_desc:
                st.error("Vui lòng điền đầy đủ CIF và mô tả.")
            else:
                db = SessionLocal()
                try:
                    # Check CIF exists
                    cust_check = db.query(models.Customer).filter(
                        models.Customer.cif == new_cif
                    ).first()
                    if not cust_check:
                        st.error(f"Không tìm thấy khách hàng CIF: {new_cif}")
                    else:
                        import uuid
                        new_case = models.Case(
                            case_id=f"CASE{str(uuid.uuid4())[:8].upper()}",
                            cif=new_cif,
                            loan_id=new_loan_id if new_loan_id else None,
                            created_date=datetime.now().strftime("%Y-%m-%d"),
                            status="todo",
                            assigned_to=new_assigned,
                            description=new_desc,
                            priority=new_priority,
                            audit_log=json.dumps(
                                [{"action": "created", "timestamp": datetime.now().isoformat()}]
                            ),
                        )
                        db.add(new_case)
                        db.commit()
                        st.success(f"Đã tạo case {new_case.case_id} thành công!")
                        # Clear cache
                        get_all_cases_df.clear()
                        st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Lỗi khi tạo case: {e}")
                finally:
                    db.close()


# ---------------------------------------------------------------------------
# AI ENGINE PAGE
# ---------------------------------------------------------------------------

def show_ai_engine():
    st.markdown("# 🤖 AI Engine - Mô hình Kiểm toán")
    st.divider()

    pipeline = init_ai_pipeline()
    if not pipeline:
        st.error("Không thể tải AI pipeline.")
        return

    model_info = pipeline.get_model_info()
    metrics = model_info.get("metrics", {})

    # Status cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        clf_status = "✅ Đã huấn luyện" if model_info.get("classifier_fitted") else "❌ Chưa huấn luyện"
        st.metric("Random Forest", clf_status)
    with col2:
        anom_status = "✅ Đã huấn luyện" if model_info.get("anomaly_fitted") else "❌ Chưa huấn luyện"
        st.metric("Isolation Forest", anom_status)
    with col3:
        cv_f1 = metrics.get("cv_f1_mean", 0)
        st.metric("CV F1 (weighted)", f"{cv_f1:.4f}")
    with col4:
        n_samples = metrics.get("n_samples", 0)
        st.metric("Số mẫu huấn luyện", str(n_samples))

    st.divider()

    # Training info
    col_a, col_b = st.columns(2)
    with col_a:
        last_trained = model_info.get("last_trained") or "Chưa có"
        if last_trained != "Chưa có":
            try:
                dt = datetime.fromisoformat(last_trained)
                last_trained = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                pass
        st.markdown(f"**Huấn luyện lần cuối:** {last_trained}")

        last_scored = model_info.get("last_scored") or "Chưa có"
        if last_scored != "Chưa có":
            try:
                dt = datetime.fromisoformat(last_scored)
                last_scored = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                pass
        st.markdown(f"**Chấm điểm lần cuối:** {last_scored}")

        # Label distribution
        label_dist = metrics.get("label_distribution", {})
        if label_dist:
            st.markdown("**Phân bổ nhãn huấn luyện:**")
            for label, count in label_dist.items():
                icon = {"Green": "🟢", "Amber": "🟡", "Red": "🔴"}.get(label, "⚪")
                st.markdown(f"- {icon} {label}: {count} KH")

    with col_b:
        models_info = model_info.get("models", {})
        for model_name, model_meta in models_info.items():
            with st.expander(f"📦 {model_name}", expanded=False):
                for k, v in model_meta.items():
                    if v is not None and str(v) != "[]":
                        st.markdown(f"- **{k}:** {v}")

    st.divider()

    # Top feature importances
    top_features = model_info.get("top_features", [])
    if top_features:
        st.markdown("#### Top Feature Importances")
        feat_names = [f[0] for f in top_features]
        feat_imps = [f[1] * 100 for f in top_features]

        fig_feat = go.Figure(
            go.Bar(
                x=feat_imps,
                y=feat_names,
                orientation="h",
                marker_color="#3b82f6",
                text=[f"{v:.1f}%" for v in feat_imps],
                textposition="inside",
            )
        )
        fig_feat.update_layout(
            **PLOTLY_LAYOUT,
            title="Feature Importance (%)",
            height=400,
            xaxis_title="Importance (%)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_feat, use_container_width=True)

    st.divider()

    # Retrain button
    st.markdown("#### Cập nhật Mô hình")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        retrain_btn = st.button(
            "🔄 Huấn luyện lại Mô hình",
            use_container_width=True,
            help="Huấn luyện lại toàn bộ AI pipeline với dữ liệu hiện tại",
        )
    with col_btn2:
        rescore_btn = st.button(
            "📊 Chấm điểm lại tất cả KH",
            use_container_width=True,
            help="Tính toán lại điểm rủi ro cho tất cả khách hàng",
        )

    if retrain_btn:
        with st.status("Đang huấn luyện mô hình...", expanded=True) as status_widget:
            try:
                st.write("Bước 1: Xây dựng đồ thị Hub nhà cung cấp...")
                db = SessionLocal()
                try:
                    pipeline_result = pipeline.train(db)
                finally:
                    db.close()

                if pipeline_result:
                    st.write(f"Bước 2: Trích xuất {pipeline_result.get('n_samples', 0)} mẫu dữ liệu...")
                    st.write(f"Bước 3: Huấn luyện Isolation Forest ({pipeline_result.get('n_estimators_if', 100)} cây)...")
                    st.write(f"Bước 4: Huấn luyện Random Forest ({pipeline_result.get('n_estimators_rf', 200)} cây)...")
                    cv_f1_new = pipeline_result.get("cv_f1_mean", 0)
                    st.write(f"✅ Huấn luyện thành công! CV F1 = {cv_f1_new:.4f}")
                    status_widget.update(label="Huấn luyện hoàn tất!", state="complete")
                    init_ai_pipeline.clear()
                    st.rerun()
                else:
                    status_widget.update(label="Huấn luyện thất bại.", state="error")
                    st.error("Huấn luyện không thành công.")
            except Exception as e:
                status_widget.update(label="Lỗi!", state="error")
                st.error(f"Lỗi khi huấn luyện: {e}")

    if rescore_btn:
        with st.status("Đang chấm điểm...", expanded=True) as status_widget:
            try:
                st.write("Tính toán lại điểm rủi ro cho tất cả khách hàng...")
                db = SessionLocal()
                try:
                    count = pipeline.score_all(db)
                finally:
                    db.close()

                st.write(f"✅ Đã chấm điểm {count} khách hàng.")
                status_widget.update(label="Chấm điểm hoàn tất!", state="complete")
                # Clear all data caches
                get_all_customers_df.clear()
                get_top_red_flag_customers.clear()
                get_dashboard_kpis.clear()
                st.rerun()
            except Exception as e:
                status_widget.update(label="Lỗi!", state="error")
                st.error(f"Lỗi khi chấm điểm: {e}")

    st.divider()

    # Per-customer AI explanation
    st.markdown("#### Giải thích AI cho Khách hàng cụ thể")
    db_for_list = SessionLocal()
    try:
        all_custs = db_for_list.query(models.Customer).limit(200).all()
        cust_opts = ["-- Chọn --"] + [f"{c.cif} - {c.customer_name}" for c in all_custs]
    finally:
        db_for_list.close()

    selected_for_explain = st.selectbox(
        "Chọn khách hàng:", cust_opts, key="ai_explain_cif"
    )

    if selected_for_explain and selected_for_explain != "-- Chọn --":
        explain_cif = selected_for_explain.split(" - ")[0]
        with st.spinner("Đang tính toán..."):
            try:
                explain_db = SessionLocal()
                try:
                    ai_res = pipeline.score_single(explain_cif, explain_db)
                finally:
                    explain_db.close()

                if ai_res:
                    col_e1, col_e2, col_e3 = st.columns(3)
                    probs = ai_res.get("probabilities", {})
                    with col_e1:
                        st.metric("Điểm RR", str(ai_res.get("risk_score", 0)))
                    with col_e2:
                        st.metric("Danh mục", risk_badge(ai_res.get("risk_category", "")))
                    with col_e3:
                        st.metric("Anomaly Score", f"{ai_res.get('anomaly_score', 0):.1f}")

                    hits = ai_res.get("rule_hits", [])
                    if hits:
                        st.markdown("**Giải thích chi tiết:**")
                        for hit in hits:
                            sev = hit.get("severity", "low")
                            sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
                            desc = hit.get("description", "")
                            feat = hit.get("feature", "")
                            val = hit.get("value", 0)
                            imp = hit.get("importance_pct", 0)
                            st.markdown(
                                f"- {sev_icon} **{feat}** = {val:.2f} → _{desc}_ (importance: {imp:.1f}%)"
                            )
                else:
                    st.warning("Không thể tính toán giải thích cho KH này.")
            except Exception as e:
                st.error(f"Lỗi giải thích AI: {e}")


# ---------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    # Initialize DB and seed data
    db_ok = init_db()
    if not db_ok:
        st.error("Không thể khởi tạo database. Vui lòng kiểm tra cấu hình.")
        st.stop()

    # Check authentication
    if not st.session_state.get("authenticated", False):
        show_login()
        st.stop()

    # Authenticated - show sidebar and route pages
    show_sidebar()

    current_page = st.session_state.get("selected_page", "dashboard")

    if current_page == "dashboard":
        show_dashboard()
    elif current_page == "branches":
        show_branches()
    elif current_page == "customers":
        show_customers()
    elif current_page == "misuse":
        show_misuse()
    elif current_page == "cases":
        show_cases()
    elif current_page == "ai_engine":
        show_ai_engine()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
else:
    # When imported by streamlit as a module
    main()
