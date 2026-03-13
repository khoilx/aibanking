import json
import random
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    Branch, Customer, LoanMaster, Collateral, Transaction,
    OffBalance, AccruedInterest, CICExtract, TaxStatus, TaxInvoice,
    SocialInsurance, Logistics, RiskScore, Case, User, AuditTrail
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

random.seed(42)

BRANCHES = [
    {"branch_id": "CN001", "branch_name": "CN Sài Gòn", "branch_director": "Trần Văn Minh", "address": "123 Nguyễn Huệ, Q1, TP.HCM", "region": "Nam"},
    {"branch_id": "CN002", "branch_name": "CN Hà Nội", "branch_director": "Nguyễn Thị Lan", "address": "45 Tràng Tiền, Hoàn Kiếm, Hà Nội", "region": "Bắc"},
    {"branch_id": "CN003", "branch_name": "CN Đà Nẵng", "branch_director": "Lê Hoàng Nam", "address": "88 Hùng Vương, Q.Hải Châu, Đà Nẵng", "region": "Trung"},
    {"branch_id": "CN004", "branch_name": "CN Cần Thơ", "branch_director": "Phạm Thị Hoa", "address": "55 Hòa Bình, Ninh Kiều, Cần Thơ", "region": "Nam"},
    {"branch_id": "CN005", "branch_name": "CN Hải Phòng", "branch_director": "Võ Văn Tùng", "address": "22 Lạch Tray, Ngô Quyền, Hải Phòng", "region": "Bắc"},
    {"branch_id": "CN006", "branch_name": "CN Huế", "branch_director": "Đặng Thị Mai", "address": "17 Lê Lợi, TP Huế", "region": "Trung"},
    {"branch_id": "CN007", "branch_name": "CN Nha Trang", "branch_director": "Bùi Văn Đức", "address": "99 Trần Phú, Nha Trang, Khánh Hòa", "region": "Trung"},
    {"branch_id": "CN008", "branch_name": "CN Vũng Tàu", "branch_director": "Hoàng Thị Thu", "address": "34 Bạch Đằng, TP Vũng Tàu", "region": "Nam"},
    {"branch_id": "CN009", "branch_name": "CN Bình Dương", "branch_director": "Ngô Văn Hải", "address": "123 Đại lộ Bình Dương, TX Thuận An", "region": "Nam"},
    {"branch_id": "CN010", "branch_name": "CN Long An", "branch_director": "Trịnh Thị Ngọc", "address": "45 Hùng Vương, TP Tân An, Long An", "region": "Nam"},
]

INDIVIDUAL_NAMES = [
    "Nguyễn Văn Hưng", "Trần Thị Bình", "Lê Văn Phúc", "Phạm Thị Hồng",
    "Võ Văn Cường", "Đặng Thị Lan", "Bùi Văn Thành", "Hoàng Thị Yến",
    "Ngô Văn Dũng", "Trịnh Thị Nga", "Đinh Văn Tài", "Vũ Thị Thủy",
    "Đỗ Văn Khoa", "Lý Thị Hương", "Phan Văn Long", "Cao Thị Linh",
    "Dương Văn Phong", "Hồ Thị Quỳnh", "Mai Văn Khánh", "Tô Thị Thanh",
    "Huỳnh Văn Bảo", "Lưu Thị Kim", "Châu Văn Sơn", "Diệp Thị Nhung",
    "Quách Văn Minh", "Triệu Thị Loan", "Văn Thị Hoa", "Lâm Văn Tuấn",
    "Tăng Thị Mai", "Khổng Văn Đức"
]

CORPORATE_NAMES = [
    "Công ty TNHH Minh Phát",
    "Công ty CP Thương mại Đại Việt",
    "Công ty TNHH XNK Phú Hưng",
    "Công ty CP Sản xuất Tiến Bộ",
    "Công ty TNHH Nông nghiệp Xanh",
    "Công ty CP Vật liệu Xây dựng Đông Nam",
    "Công ty TNHH Thực phẩm An Khang",
    "Công ty CP Logistics Tân Cảng",
    "Công ty TNHH Dệt may Sài Gòn",
    "Công ty CP Hóa chất Miền Nam",
    "Công ty TNHH Điện tử Viễn thông HCM",
    "Công ty CP Bất động sản Kim Long",
    "Công ty TNHH Đầu tư Phú Quý",
    "Công ty CP Xây dựng Hoàng Gia",
    "Công ty TNHH Vận tải Đường bộ Bắc Nam",
    "Công ty CP Chế biến Thủy sản Biển Đông",
    "Công ty TNHH Phân phối Hàng tiêu dùng",
    "Công ty CP Công nghệ Thông tin Việt",
    "Công ty TNHH Sản xuất Đồ gỗ Thiên Phú",
    "Công ty CP Khoáng sản Tây Nguyên",
]

VENDOR_TAX_IDS = ["0123456789", "0987654321", "0111222333"]
VENDOR_NAMES = {
    "0123456789": "Công ty TNHH Cung ứng Vật tư Toàn Cầu",
    "0987654321": "Công ty CP Thương mại Dịch vụ Hưng Thịnh",
    "0111222333": "Công ty TNHH Nhập khẩu Nguyên liệu Bắc Nam",
}

LOAN_OFFICERS = [
    "Nguyễn Minh Tuấn", "Trần Thị Phương", "Lê Văn Hùng",
    "Phạm Thị Bích", "Võ Văn Tú", "Đặng Văn Khoa", "Bùi Thị Lan"
]

LOAN_PURPOSES = {
    "BDS": ["Mua bất động sản thương mại", "Đầu tư căn hộ cho thuê", "Xây dựng văn phòng", "Mua đất sản xuất"],
    "Nong nghiep": ["Trồng lúa xuất khẩu", "Chăn nuôi gia súc", "Nuôi tôm nước lợ", "Trồng cây ăn trái", "Mua máy nông nghiệp"],
    "Ban le": ["Bổ sung vốn lưu động kinh doanh", "Mua hàng hóa nhập khẩu", "Mở rộng cửa hàng", "Kinh doanh thương mại"],
    "SX": ["Mua nguyên liệu sản xuất", "Đầu tư dây chuyền sản xuất", "Nâng cấp nhà xưởng", "Mở rộng sản xuất"],
}


def random_date(start_days_ago, end_days_ago=0):
    days = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def format_tax_id(n):
    return f"{n:010d}"


def seed_database(db: Session):
    """Seed the database with mock data."""
    print("Seeding branches...")
    for b in BRANCHES:
        if not db.query(Branch).filter_by(branch_id=b["branch_id"]).first():
            db.add(Branch(**b))
    db.commit()

    print("Seeding users...")
    users_data = [
        {"user_id": "U001", "username": "admin", "password": "admin123", "full_name": "Quản trị viên", "role": "admin", "branch_id": None},
        {"user_id": "U002", "username": "ktv_nguyenan", "password": "pass123", "full_name": "Nguyễn An", "role": "auditor", "branch_id": "CN001"},
        {"user_id": "U003", "username": "ktv_tranthi", "password": "pass123", "full_name": "Trần Thị Bích", "role": "auditor", "branch_id": "CN002"},
        {"user_id": "U004", "username": "manager_le", "password": "pass123", "full_name": "Lê Văn Quản", "role": "manager", "branch_id": None},
        {"user_id": "U005", "username": "ktv_pham", "password": "pass123", "full_name": "Phạm Văn Kiểm", "role": "auditor", "branch_id": "CN003"},
    ]
    for u in users_data:
        if not db.query(User).filter_by(username=u["username"]).first():
            db.add(User(
                user_id=u["user_id"],
                username=u["username"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                branch_id=u["branch_id"]
            ))
    db.commit()

    print("Seeding customers...")
    customers = []
    branch_ids = [b["branch_id"] for b in BRANCHES]
    segments = ["SME", "Corporate", "Retail", "Agriculture"]
    ratings = ["A", "A", "A", "B", "B", "C", "C", "D"]

    # Specific story customers
    story_customers = [
        {
            "cif": "CIF_MINHPHAT",
            "customer_name": "Công ty TNHH Minh Phát",
            "customer_type": "Corporate",
            "tax_id": "0301234567",
            "branch_id": "CN001",
            "segment": "SME",
            "credit_rating": "D",
        },
        {
            "cif": "CIF_NGVHUNG",
            "customer_name": "Nguyễn Văn Hưng",
            "customer_type": "Individual",
            "id_number": "012345678901",
            "branch_id": "CN001",
            "segment": "Retail",
            "credit_rating": "D",
        },
    ]

    for sc in story_customers:
        sc["phone"] = f"09{random.randint(10000000, 99999999)}"
        sc["email"] = f"contact{random.randint(100,999)}@example.com"
        sc["created_date"] = random_date(1800, 1000)
        if not db.query(Customer).filter_by(cif=sc["cif"]).first():
            db.add(Customer(**sc))
        customers.append(sc)

    # Individual customers (28 more)
    for i, name in enumerate(INDIVIDUAL_NAMES):
        cif = f"CIF_IND_{i+1:03d}"
        if db.query(Customer).filter_by(cif=cif).first():
            continue
        c = Customer(
            cif=cif,
            customer_name=name,
            customer_type="Individual",
            id_number=f"{random.randint(100000000000, 999999999999)}",
            phone=f"09{random.randint(10000000, 99999999)}",
            email=f"{name.split()[0].lower()}{random.randint(10,99)}@gmail.com",
            branch_id=random.choice(branch_ids),
            segment=random.choice(["Retail", "Agriculture"]),
            created_date=random_date(1800, 365),
            credit_rating=random.choice(ratings)
        )
        db.add(c)
        customers.append({"cif": cif, "customer_name": name, "customer_type": "Individual", "tax_id": None, "branch_id": c.branch_id})

    # Corporate customers (20)
    hub_customers = CORPORATE_NAMES[:8]  # First 8 will be in vendor hub
    for i, name in enumerate(CORPORATE_NAMES):
        cif = f"CIF_CORP_{i+1:03d}"
        if db.query(Customer).filter_by(cif=cif).first():
            continue
        tax_id = format_tax_id(300000000 + i * 1000 + random.randint(1, 999))
        c = Customer(
            cif=cif,
            customer_name=name,
            customer_type="Corporate",
            tax_id=tax_id,
            phone=f"028{random.randint(10000000, 99999999)}",
            email=f"info{random.randint(100,999)}@company.vn",
            branch_id=random.choice(branch_ids),
            segment=random.choice(["SME", "Corporate"]),
            created_date=random_date(2500, 500),
            credit_rating=random.choice(ratings)
        )
        db.add(c)
        customers.append({"cif": cif, "customer_name": name, "customer_type": "Corporate", "tax_id": tax_id, "branch_id": c.branch_id})

    db.commit()

    print("Seeding tax status...")
    all_customers = db.query(Customer).all()
    corp_customers = [c for c in all_customers if c.customer_type == "Corporate"]

    # Story customer: Minh Phat has closed tax status
    minhphat = db.query(Customer).filter_by(cif="CIF_MINHPHAT").first()
    if minhphat and minhphat.tax_id:
        if not db.query(TaxStatus).filter_by(tax_id=minhphat.tax_id).first():
            db.add(TaxStatus(
                tax_id=minhphat.tax_id,
                company_name=minhphat.customer_name,
                status="closed",
                registration_date=random_date(3000, 1000)
            ))
    db.flush()  # flush so dedup checks below can see it

    bad_tax_count = 0
    for c in corp_customers:
        if not c.tax_id:
            continue
        if db.query(TaxStatus).filter_by(tax_id=c.tax_id).first():
            continue
        if bad_tax_count < 4 and c.cif not in ["CIF_MINHPHAT"]:
            status = random.choice(["evading", "suspended"])
            bad_tax_count += 1
        else:
            status = "active"
        db.add(TaxStatus(
            tax_id=c.tax_id,
            company_name=c.customer_name,
            status=status,
            registration_date=random_date(3000, 500)
        ))

    # Add vendor tax statuses
    for vtax, vname in VENDOR_NAMES.items():
        if not db.query(TaxStatus).filter_by(tax_id=vtax).first():
            db.add(TaxStatus(tax_id=vtax, company_name=vname, status="active", registration_date=random_date(3000, 1000)))

    db.commit()

    print("Seeding loans...")
    all_customers = db.query(Customer).all()
    categories = ["BDS", "Nong nghiep", "Ban le", "SX"]
    cat_weights = [0.30, 0.25, 0.25, 0.20]
    # Debt groups distribution: 70% G1, 15% G2, 8% G3, 4% G4, 3% G5
    debt_group_pool = [1]*70 + [2]*15 + [3]*8 + [4]*4 + [5]*3

    loan_count = 0
    for customer in all_customers:
        if customer.cif == "CIF_MINHPHAT":
            num_loans = 3
        elif customer.cif == "CIF_NGVHUNG":
            num_loans = 2
        else:
            num_loans = random.randint(1, 4)

        for j in range(num_loans):
            loan_id = f"LN{customer.cif}_{j+1:02d}"
            if db.query(LoanMaster).filter_by(loan_id=loan_id).first():
                continue

            cat = random.choices(categories, weights=cat_weights)[0]
            if customer.customer_type == "Corporate":
                amount = random.randint(2000, 50000) * 1_000_000  # 2B - 50B
            else:
                amount = random.randint(500, 5000) * 1_000_000  # 500M - 5B

            # Story: Minh Phat has large loan
            if customer.cif == "CIF_MINHPHAT":
                amount = random.randint(10000, 30000) * 1_000_000
                cat = "Ban le"

            # Story: Nguyen Van Hung has bad debt
            if customer.cif == "CIF_NGVHUNG":
                debt_grp = random.choice([3, 4, 5])
            else:
                debt_grp = random.choice(debt_group_pool)

            outstanding = amount * random.uniform(0.4, 0.95)
            disb_date = random_date(730, 30)
            maturity_days = random.randint(365, 1825)
            disb_dt = datetime.strptime(disb_date, "%Y-%m-%d")
            maturity_date = (disb_dt + timedelta(days=maturity_days)).strftime("%Y-%m-%d")
            interest_rate = round(random.uniform(7.5, 12.5), 2)
            status = "active"
            if debt_grp >= 4:
                status = random.choice(["active", "restructured"])

            loan = LoanMaster(
                loan_id=loan_id,
                cif=customer.cif,
                branch_id=customer.branch_id,
                loan_amount=amount,
                outstanding_balance=outstanding,
                disbursement_date=disb_date,
                maturity_date=maturity_date,
                interest_rate=interest_rate,
                loan_purpose=random.choice(LOAN_PURPOSES[cat]),
                loan_category=cat,
                debt_group=debt_grp,
                loan_officer=random.choice(LOAN_OFFICERS),
                status=status
            )
            db.add(loan)
            loan_count += 1

    db.commit()
    print(f"Created {loan_count} loans")

    print("Seeding collaterals...")
    all_loans = db.query(LoanMaster).all()
    collateral_types = ["real_estate", "vehicle", "machinery", "securities"]
    for loan in all_loans:
        num_col = random.randint(1, 2)
        for k in range(num_col):
            col_id = f"COL{loan.loan_id}_{k+1}"
            if db.query(Collateral).filter_by(collateral_id=col_id).first():
                continue

            # LTV: most 60-75%, some suspicious > 90%
            is_suspicious = random.random() < 0.12
            if is_suspicious:
                ltv = random.uniform(0.88, 0.98)
            else:
                ltv = random.uniform(0.55, 0.78)

            col_value = loan.outstanding_balance / ltv

            db.add(Collateral(
                collateral_id=col_id,
                cif=loan.cif,
                loan_id=loan.loan_id,
                collateral_type=random.choice(collateral_types),
                estimated_value=col_value,
                valuation_date=random_date(365, 30),
                address=f"Số {random.randint(1,200)} đường {random.choice(['Nguyễn Trãi', 'Lê Lợi', 'Hùng Vương'])}, TP.HCM",
                status="active"
            ))

    db.commit()

    print("Seeding transactions...")
    all_loans = db.query(LoanMaster).all()
    txn_count = 0
    for loan in all_loans:
        # Disbursement transaction
        disb_txn_id = f"TXN_D_{loan.loan_id}"
        if not db.query(Transaction).filter_by(txn_id=disb_txn_id).first():
            db.add(Transaction(
                txn_id=disb_txn_id,
                loan_id=loan.loan_id,
                cif=loan.cif,
                txn_date=loan.disbursement_date,
                txn_type="disbursement",
                amount=loan.loan_amount,
                description="Giải ngân khoản vay",
                channel=random.choice(["counter", "online"])
            ))
            txn_count += 1

        # For suspicious customers: large cash withdrawal within 48h
        if loan.cif in ["CIF_MINHPHAT", "CIF_NGVHUNG"] or random.random() < 0.08:
            disb_dt = datetime.strptime(loan.disbursement_date, "%Y-%m-%d")
            withdrawal_date = (disb_dt + timedelta(hours=24)).strftime("%Y-%m-%d")
            w_txn_id = f"TXN_W_{loan.loan_id}"
            if not db.query(Transaction).filter_by(txn_id=w_txn_id).first():
                db.add(Transaction(
                    txn_id=w_txn_id,
                    loan_id=loan.loan_id,
                    cif=loan.cif,
                    txn_date=withdrawal_date,
                    txn_type="repayment",
                    amount=loan.loan_amount * random.uniform(0.82, 0.95),
                    description="Rút tiền mặt",
                    channel="counter"
                ))
                txn_count += 1

        # Regular repayments
        num_repayments = random.randint(2, 12)
        for r in range(num_repayments):
            r_txn_id = f"TXN_R_{loan.loan_id}_{r+1}"
            if db.query(Transaction).filter_by(txn_id=r_txn_id).first():
                continue
            monthly_payment = loan.loan_amount * (loan.interest_rate / 100 / 12 + 1 / (loan.loan_amount / 1_000_000))
            monthly_payment = max(monthly_payment, loan.loan_amount * 0.01)
            disb_dt = datetime.strptime(loan.disbursement_date, "%Y-%m-%d")
            pay_date = (disb_dt + timedelta(days=30 * (r + 1))).strftime("%Y-%m-%d")

            db.add(Transaction(
                txn_id=r_txn_id,
                loan_id=loan.loan_id,
                cif=loan.cif,
                txn_date=pay_date,
                txn_type="repayment",
                amount=round(monthly_payment / 1_000_000) * 1_000_000,
                description="Trả nợ định kỳ",
                channel=random.choice(["counter", "online", "atm"])
            ))
            txn_count += 1

        # Interest payments
        int_txn_id = f"TXN_I_{loan.loan_id}"
        if not db.query(Transaction).filter_by(txn_id=int_txn_id).first():
            db.add(Transaction(
                txn_id=int_txn_id,
                loan_id=loan.loan_id,
                cif=loan.cif,
                txn_date=random_date(90, 30),
                txn_type="interest_payment",
                amount=loan.outstanding_balance * loan.interest_rate / 100 / 12,
                description="Trả lãi khoản vay",
                channel=random.choice(["counter", "online"])
            ))
            txn_count += 1

    db.commit()
    print(f"Created {txn_count} transactions")

    print("Seeding CIC extracts...")
    all_customers = db.query(Customer).all()
    bad_cic_cifs = ["CIF_NGVHUNG", "CIF_MINHPHAT"]
    # Add 13 more with bad CIC
    remaining = [c.cif for c in all_customers if c.cif not in bad_cic_cifs]
    bad_cic_cifs.extend(random.sample(remaining, min(13, len(remaining))))

    for customer in all_customers:
        cic_id = f"CIC_{customer.cif}"
        if db.query(CICExtract).filter_by(cic_id=cic_id).first():
            continue
        is_bad = customer.cif in bad_cic_cifs
        db.add(CICExtract(
            cic_id=cic_id,
            cif=customer.cif,
            report_date=random_date(90, 30),
            total_debt_other_banks=random.randint(500, 5000) * 1_000_000 if is_bad else random.randint(0, 500) * 1_000_000,
            debt_group_other_banks=random.randint(3, 5) if is_bad else random.randint(1, 2),
            bad_debt_amount=random.randint(200, 2000) * 1_000_000 if is_bad else 0,
            number_of_credit_institutions=random.randint(2, 5),
            has_overdue_history=is_bad or random.random() < 0.1
        ))

    db.commit()

    print("Seeding tax invoices...")
    corp_customers = db.query(Customer).filter_by(customer_type="Corporate").all()
    # Hub: First 8 corporate customers all buy from same 3 vendors
    hub_corp = corp_customers[:8]
    hub_cifs = [c.cif for c in hub_corp]
    # Map tax_ids for hub customers
    hub_tax_ids = [c.tax_id for c in hub_corp if c.tax_id]

    inv_count = 0
    # Vendor hub invoices
    for tax_id in hub_tax_ids:
        for vendor_tax in VENDOR_TAX_IDS:
            for m in range(random.randint(3, 8)):
                inv_id = f"INV_HUB_{tax_id}_{vendor_tax}_{m}"
                if db.query(TaxInvoice).filter_by(invoice_id=inv_id).first():
                    continue
                db.add(TaxInvoice(
                    invoice_id=inv_id,
                    seller_tax_id=vendor_tax,
                    buyer_tax_id=tax_id,
                    invoice_date=random_date(365, 30),
                    amount=random.randint(500, 5000) * 1_000_000,
                    status=random.choice(["valid", "valid", "suspicious"])
                ))
                inv_count += 1

    # Regular invoices for all corporate customers
    high_cancel_cifs = [c.cif for c in corp_customers[8:14]]  # some with high cancellation
    for customer in corp_customers:
        if not customer.tax_id:
            continue
        num_invoices = random.randint(5, 15)
        for m in range(num_invoices):
            inv_id = f"INV_{customer.cif}_{m}"
            if db.query(TaxInvoice).filter_by(invoice_id=inv_id).first():
                continue
            # High cancellation for some
            if customer.cif in high_cancel_cifs:
                status = random.choices(["valid", "cancelled"], weights=[35, 65])[0]
            else:
                status = random.choices(["valid", "cancelled", "suspicious"], weights=[75, 15, 10])[0]
            db.add(TaxInvoice(
                invoice_id=inv_id,
                seller_tax_id=format_tax_id(random.randint(100000000, 999999999)),
                buyer_tax_id=customer.tax_id,
                invoice_date=random_date(365, 30),
                amount=random.randint(100, 2000) * 1_000_000,
                status=status
            ))
            inv_count += 1

    db.commit()
    print(f"Created {inv_count} invoices")

    print("Seeding social insurance...")
    mismatch_corp = corp_customers[14:19]  # 5 companies with SI mismatch
    for customer in corp_customers:
        if not customer.tax_id:
            continue
        si_id = f"SI_{customer.tax_id}"
        if db.query(SocialInsurance).filter_by(si_id=si_id).first():
            continue
        declared = random.randint(50, 500)
        if customer in mismatch_corp:
            actual = int(declared * random.uniform(0.1, 0.4))  # Drastic mismatch
        else:
            actual = int(declared * random.uniform(0.85, 1.0))
        db.add(SocialInsurance(
            si_id=si_id,
            tax_id=customer.tax_id,
            report_period="2024-Q4",
            declared_employees=declared,
            actual_employees=actual,
            total_salary_fund=actual * random.randint(8, 25) * 1_000_000
        ))

    db.commit()

    print("Seeding logistics...")
    agri_mfg_loans = db.query(LoanMaster).filter(
        LoanMaster.loan_category.in_(["Nong nghiep", "SX"])
    ).all()
    # Some customers with no logistics despite trading loan
    no_logistics_cifs = set()
    all_cifs_with_trading = set(l.cif for l in agri_mfg_loans)
    no_logistics_sample = list(all_cifs_with_trading)[:10]
    no_logistics_cifs.update(no_logistics_sample)

    log_count = 0
    for customer in corp_customers:
        if not customer.tax_id:
            continue
        if customer.cif in no_logistics_cifs:
            continue
        num_shipments = random.randint(2, 8)
        for s in range(num_shipments):
            log_id = f"LOG_{customer.tax_id}_{s}"
            if db.query(Logistics).filter_by(logistics_id=log_id).first():
                continue
            db.add(Logistics(
                logistics_id=log_id,
                shipper_tax_id=random.choice(VENDOR_TAX_IDS + [customer.tax_id]),
                receiver_tax_id=customer.tax_id,
                shipment_date=random_date(365, 30),
                goods_description=random.choice([
                    "Nguyên liệu sản xuất", "Hàng hóa thực phẩm",
                    "Phân bón nông nghiệp", "Máy móc thiết bị",
                    "Vải may mặc", "Hóa chất công nghiệp"
                ]),
                amount=random.randint(200, 3000) * 1_000_000,
                status=random.choice(["delivered", "delivered", "pending"])
            ))
            log_count += 1

    db.commit()
    print(f"Created {log_count} logistics records")

    print("Seeding off-balance items...")
    for customer in random.sample(list(all_customers), min(20, len(all_customers))):
        ob_id = f"OB_{customer.cif}_1"
        if db.query(OffBalance).filter_by(off_balance_id=ob_id).first():
            continue
        db.add(OffBalance(
            off_balance_id=ob_id,
            cif=customer.cif,
            ob_type=random.choice(["LC", "Guarantee", "Credit Commitment"]),
            amount=random.randint(500, 10000) * 1_000_000,
            issue_date=random_date(365, 30),
            expiry_date=random_date(0, -365),
            status=random.choice(["active", "active", "expired"])
        ))
    db.commit()

    print("Computing risk scores...")
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from risk_engine import run_batch_scoring
    run_batch_scoring(db)

    print("Seeding cases for Red customers...")
    red_scores = db.query(RiskScore).filter_by(risk_category="Red").all()
    statuses = ["todo"] * 4 + ["in_progress"] * 3 + ["pending_branch"] * 2 + ["closed"] * 1
    priorities = ["high", "high", "medium", "medium", "low"]
    auditors = ["ktv_nguyenan", "ktv_tranthi", "ktv_pham"]

    for score in red_scores:
        case_id = f"CASE_{score.cif}"
        if db.query(Case).filter_by(case_id=case_id).first():
            continue

        customer = db.query(Customer).filter_by(cif=score.cif).first()
        loans = db.query(LoanMaster).filter_by(cif=score.cif).all()
        loan_id = loans[0].loan_id if loans else None

        rule_hits = json.loads(score.rule_hits) if score.rule_hits else []
        top_rule = rule_hits[0]["description"] if rule_hits else "Rủi ro tổng hợp"

        audit_log = json.dumps([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": "system",
            "action": "Case tự động tạo từ scoring engine",
            "details": f"Score: {score.total_score}, Category: {score.risk_category}"
        }], ensure_ascii=False)

        db.add(Case(
            case_id=case_id,
            cif=score.cif,
            loan_id=loan_id,
            created_date=random_date(60, 1),
            status=random.choice(statuses),
            assigned_to=random.choice(auditors),
            description=f"Khách hàng {customer.customer_name if customer else score.cif}: {top_rule}. Yêu cầu kiểm tra và xác minh.",
            priority=random.choice(priorities),
            audit_log=audit_log
        ))

    db.commit()
    print("Database seeding complete!")
