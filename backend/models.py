from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime


class Branch(Base):
    __tablename__ = "branches"

    branch_id = Column(String, primary_key=True)
    branch_name = Column(String, nullable=False)
    branch_director = Column(String)
    address = Column(String)
    region = Column(String)

    customers = relationship("Customer", back_populates="branch")
    loans = relationship("LoanMaster", back_populates="branch")


class Customer(Base):
    __tablename__ = "customers"

    cif = Column(String, primary_key=True)
    customer_name = Column(String, nullable=False)
    customer_type = Column(String)  # Individual/Corporate
    tax_id = Column(String, nullable=True)
    id_number = Column(String, nullable=True)
    phone = Column(String)
    email = Column(String)
    branch_id = Column(String, ForeignKey("branches.branch_id"))
    segment = Column(String)  # SME, Corporate, Retail, Agriculture
    created_date = Column(String)
    credit_rating = Column(String)  # A/B/C/D

    branch = relationship("Branch", back_populates="customers")
    loans = relationship("LoanMaster", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")
    off_balance = relationship("OffBalance", back_populates="customer")
    cic_extract = relationship("CICExtract", back_populates="customer")
    risk_scores = relationship("RiskScore", back_populates="customer")
    cases = relationship("Case", back_populates="customer")
    collaterals = relationship("Collateral", back_populates="customer")
    accrued_interests = relationship("AccruedInterest", back_populates="customer")


class LoanMaster(Base):
    __tablename__ = "loans"

    loan_id = Column(String, primary_key=True)
    cif = Column(String, ForeignKey("customers.cif"))
    branch_id = Column(String, ForeignKey("branches.branch_id"))
    loan_amount = Column(Float)
    outstanding_balance = Column(Float)
    disbursement_date = Column(String)
    maturity_date = Column(String)
    interest_rate = Column(Float)
    loan_purpose = Column(String)
    loan_category = Column(String)  # BDS/Nong nghiep/Ban le/SX
    debt_group = Column(Integer)  # 1-5
    loan_officer = Column(String)
    status = Column(String)  # active/closed/restructured

    customer = relationship("Customer", back_populates="loans")
    branch = relationship("Branch", back_populates="loans")
    transactions = relationship("Transaction", back_populates="loan")
    collaterals = relationship("Collateral", back_populates="loan")
    accrued_interests = relationship("AccruedInterest", back_populates="loan")
    cases = relationship("Case", back_populates="loan")


class Collateral(Base):
    __tablename__ = "collaterals"

    collateral_id = Column(String, primary_key=True)
    cif = Column(String, ForeignKey("customers.cif"))
    loan_id = Column(String, ForeignKey("loans.loan_id"))
    collateral_type = Column(String)  # real_estate/vehicle/machinery/securities
    estimated_value = Column(Float)
    valuation_date = Column(String)
    address = Column(String)
    status = Column(String)  # active/released

    customer = relationship("Customer", back_populates="collaterals")
    loan = relationship("LoanMaster", back_populates="collaterals")


class Transaction(Base):
    __tablename__ = "transactions"

    txn_id = Column(String, primary_key=True)
    loan_id = Column(String, ForeignKey("loans.loan_id"))
    cif = Column(String, ForeignKey("customers.cif"))
    txn_date = Column(String)
    txn_type = Column(String)  # disbursement/repayment/interest_payment
    amount = Column(Float)
    description = Column(String)
    channel = Column(String)  # counter/online/atm

    loan = relationship("LoanMaster", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")


class OffBalance(Base):
    __tablename__ = "off_balance"

    off_balance_id = Column(String, primary_key=True)
    cif = Column(String, ForeignKey("customers.cif"))
    ob_type = Column(String)  # LC/Guarantee/Credit Commitment
    amount = Column(Float)
    issue_date = Column(String)
    expiry_date = Column(String)
    status = Column(String)  # active/expired/cancelled

    customer = relationship("Customer", back_populates="off_balance")


class AccruedInterest(Base):
    __tablename__ = "accrued_interest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String, ForeignKey("loans.loan_id"))
    cif = Column(String, ForeignKey("customers.cif"))
    accrual_date = Column(String)
    amount = Column(Float)
    is_received = Column(Boolean, default=True)

    loan = relationship("LoanMaster", back_populates="accrued_interests")
    customer = relationship("Customer", back_populates="accrued_interests")


class CICExtract(Base):
    __tablename__ = "cic_extracts"

    cic_id = Column(String, primary_key=True)
    cif = Column(String, ForeignKey("customers.cif"))
    report_date = Column(String)
    total_debt_other_banks = Column(Float)
    debt_group_other_banks = Column(Integer)
    bad_debt_amount = Column(Float)
    number_of_credit_institutions = Column(Integer)
    has_overdue_history = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="cic_extract")


class TaxStatus(Base):
    __tablename__ = "tax_status"

    tax_id = Column(String, primary_key=True)
    company_name = Column(String)
    status = Column(String)  # active/closed/evading/suspended
    registration_date = Column(String)


class TaxInvoice(Base):
    __tablename__ = "tax_invoices"

    invoice_id = Column(String, primary_key=True)
    seller_tax_id = Column(String)
    buyer_tax_id = Column(String)
    invoice_date = Column(String)
    amount = Column(Float)
    status = Column(String)  # valid/cancelled/suspicious


class SocialInsurance(Base):
    __tablename__ = "social_insurance"

    si_id = Column(String, primary_key=True)
    tax_id = Column(String)
    report_period = Column(String)
    declared_employees = Column(Integer)
    actual_employees = Column(Integer)
    total_salary_fund = Column(Float)


class Logistics(Base):
    __tablename__ = "logistics"

    logistics_id = Column(String, primary_key=True)
    shipper_tax_id = Column(String)
    receiver_tax_id = Column(String)
    shipment_date = Column(String)
    goods_description = Column(String)
    amount = Column(Float)
    status = Column(String)  # delivered/pending/cancelled


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cif = Column(String, ForeignKey("customers.cif"))
    score_date = Column(String)
    total_score = Column(Integer)
    risk_category = Column(String)  # Green/Amber/Red
    rule_hits = Column(Text)  # JSON string
    last_updated = Column(String)

    customer = relationship("Customer", back_populates="risk_scores")


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True)
    cif = Column(String, ForeignKey("customers.cif"))
    loan_id = Column(String, ForeignKey("loans.loan_id"), nullable=True)
    created_date = Column(String)
    status = Column(String)  # todo/in_progress/pending_branch/closed
    assigned_to = Column(String)
    description = Column(String)
    priority = Column(String)  # high/medium/low
    audit_log = Column(Text)  # JSON string

    customer = relationship("Customer", back_populates="cases")
    loan = relationship("LoanMaster", back_populates="cases")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)  # auditor/manager/admin
    branch_id = Column(String, nullable=True)


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    timestamp = Column(String)
    details = Column(Text)
