from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class BranchBase(BaseModel):
    branch_id: str
    branch_name: str
    branch_director: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None

    class Config:
        from_attributes = True


class BranchSummary(BranchBase):
    total_outstanding: float = 0
    total_customers: int = 0
    total_loans: int = 0
    npl_ratio: float = 0
    red_flag_count: int = 0


class CustomerBase(BaseModel):
    cif: str
    customer_name: str
    customer_type: Optional[str] = None
    tax_id: Optional[str] = None
    id_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    branch_id: Optional[str] = None
    segment: Optional[str] = None
    created_date: Optional[str] = None
    credit_rating: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerListItem(CustomerBase):
    branch_name: Optional[str] = None
    total_outstanding: float = 0
    max_debt_group: int = 1
    risk_score: int = 0
    risk_category: str = "Green"


class LoanSchema(BaseModel):
    loan_id: str
    cif: str
    branch_id: Optional[str] = None
    loan_amount: float
    outstanding_balance: float
    disbursement_date: Optional[str] = None
    maturity_date: Optional[str] = None
    interest_rate: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_category: Optional[str] = None
    debt_group: int = 1
    loan_officer: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class CollateralSchema(BaseModel):
    collateral_id: str
    cif: str
    loan_id: str
    collateral_type: Optional[str] = None
    estimated_value: float = 0
    valuation_date: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionSchema(BaseModel):
    txn_id: str
    loan_id: Optional[str] = None
    cif: str
    txn_date: Optional[str] = None
    txn_type: Optional[str] = None
    amount: float = 0
    description: Optional[str] = None
    channel: Optional[str] = None

    class Config:
        from_attributes = True


class OffBalanceSchema(BaseModel):
    off_balance_id: str
    cif: str
    ob_type: Optional[str] = None
    amount: float = 0
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class CICExtractSchema(BaseModel):
    cic_id: str
    cif: str
    report_date: Optional[str] = None
    total_debt_other_banks: float = 0
    debt_group_other_banks: int = 1
    bad_debt_amount: float = 0
    number_of_credit_institutions: int = 0
    has_overdue_history: bool = False

    class Config:
        from_attributes = True


class RiskScoreSchema(BaseModel):
    id: int
    cif: str
    score_date: Optional[str] = None
    total_score: int = 0
    risk_category: str = "Green"
    rule_hits: Optional[str] = None
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True


class RuleHit(BaseModel):
    rule_id: str
    description: str
    points: int
    severity: str  # high/medium/low


class RiskAnalysis(BaseModel):
    total_score: int
    risk_category: str
    rule_hits: List[RuleHit] = []


class TaxStatusSchema(BaseModel):
    tax_id: str
    company_name: Optional[str] = None
    status: Optional[str] = None
    registration_date: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceSummary(BaseModel):
    total: int
    cancelled: int
    cancellation_rate: float


class SISchema(BaseModel):
    si_id: str
    tax_id: str
    report_period: Optional[str] = None
    declared_employees: int = 0
    actual_employees: int = 0
    total_salary_fund: float = 0

    class Config:
        from_attributes = True


class MisuseData(BaseModel):
    tax_status: Optional[TaxStatusSchema] = None
    invoice_summary: Optional[InvoiceSummary] = None
    si_mismatch: Optional[SISchema] = None
    logistics_count: int = 0


class CustomerDetail(BaseModel):
    customer_info: CustomerBase
    loans: List[LoanSchema] = []
    off_balance: List[OffBalanceSchema] = []
    recent_transactions: List[TransactionSchema] = []
    risk_analysis: RiskAnalysis
    misuse_data: MisuseData


class CaseSchema(BaseModel):
    case_id: str
    cif: str
    loan_id: Optional[str] = None
    created_date: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    audit_log: Optional[str] = None
    customer_name: Optional[str] = None
    risk_score: Optional[int] = None

    class Config:
        from_attributes = True


class CaseCreate(BaseModel):
    cif: str
    loan_id: Optional[str] = None
    description: str
    priority: str = "medium"
    assigned_to: Optional[str] = None


class CaseUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


class UserSchema(BaseModel):
    user_id: str
    username: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class LoginRequest(BaseModel):
    username: str
    password: str


class DashboardKPIs(BaseModel):
    npl_ratio: float
    group2_ratio: float
    restructured_ratio: float
    llcr: float
    total_outstanding: float
    total_customers: int
    total_loans: int
    red_flag_count: int


class TrendDataPoint(BaseModel):
    month: str
    npl_ratio: float
    group2_ratio: float
    total_outstanding: float


class TopRedFlag(BaseModel):
    cif: str
    customer_name: str
    risk_score: int
    risk_category: str
    total_outstanding: float
    branch_name: str
    top_rules: List[str] = []


class PortfolioBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float


class DebtGroupBreakdown(BaseModel):
    group: int
    amount: float
    count: int


class BranchDetail(BaseModel):
    branch_info: BranchBase
    total_outstanding: float
    portfolio_breakdown: List[PortfolioBreakdown] = []
    debt_group_breakdown: List[DebtGroupBreakdown] = []
    top_risky_loans: List[LoanSchema] = []
    early_warnings: List[str] = []


class MisusePattern(BaseModel):
    pattern: str
    count: int
    total_amount: float


class MisuseOverview(BaseModel):
    total_flagged_outstanding: float
    total_flagged_cases: int
    pattern_distribution: List[MisusePattern] = []


class VendorHub(BaseModel):
    vendor_tax_id: str
    company_name: str
    connected_customers: int
    total_amount: float
    is_suspicious: bool
    customer_list: List[dict] = []
