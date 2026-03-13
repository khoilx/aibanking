from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Customer, LoanMaster, TaxStatus, TaxInvoice, SocialInsurance, Logistics, RiskScore
import json

router = APIRouter()

VENDOR_NAMES = {
    "0123456789": "Công ty TNHH Cung ứng Vật tư Toàn Cầu",
    "0987654321": "Công ty CP Thương mại Dịch vụ Hưng Thịnh",
    "0111222333": "Công ty TNHH Nhập khẩu Nguyên liệu Bắc Nam",
}


@router.get("/overview")
def get_misuse_overview(db: Session = Depends(get_db)):
    red_scores = db.query(RiskScore).filter_by(risk_category="Red").all()
    amber_scores = db.query(RiskScore).filter_by(risk_category="Amber").all()
    flagged_cifs = set(s.cif for s in red_scores + amber_scores)

    total_flagged_outstanding = 0
    for cif in flagged_cifs:
        loans = db.query(LoanMaster).filter_by(cif=cif).all()
        total_flagged_outstanding += sum(l.outstanding_balance for l in loans)

    # Pattern distribution
    patterns = {
        "Rút tiền mặt": {"count": 0, "amount": 0},
        "Hóa đơn hủy": {"count": 0, "amount": 0},
        "Vendor Hub": {"count": 0, "amount": 0},
        "Mismatch BHXH": {"count": 0, "amount": 0},
        "MST đóng/bỏ trốn": {"count": 0, "amount": 0},
    }

    for score in red_scores + amber_scores:
        if not score.rule_hits:
            continue
        try:
            hits = json.loads(score.rule_hits)
            rule_ids = [h["rule_id"] for h in hits]
            loans = db.query(LoanMaster).filter_by(cif=score.cif).all()
            cif_outstanding = sum(l.outstanding_balance for l in loans)

            if "R03" in rule_ids:
                patterns["Rút tiền mặt"]["count"] += 1
                patterns["Rút tiền mặt"]["amount"] += cif_outstanding
            if "R05" in rule_ids:
                patterns["Hóa đơn hủy"]["count"] += 1
                patterns["Hóa đơn hủy"]["amount"] += cif_outstanding
            if "R07" in rule_ids:
                patterns["Vendor Hub"]["count"] += 1
                patterns["Vendor Hub"]["amount"] += cif_outstanding
            if "R06" in rule_ids:
                patterns["Mismatch BHXH"]["count"] += 1
                patterns["Mismatch BHXH"]["amount"] += cif_outstanding
            if "R04" in rule_ids:
                patterns["MST đóng/bỏ trốn"]["count"] += 1
                patterns["MST đóng/bỏ trốn"]["amount"] += cif_outstanding
        except Exception:
            continue

    pattern_distribution = [
        {"pattern": k, "count": v["count"], "total_amount": v["amount"]}
        for k, v in patterns.items()
        if v["count"] > 0
    ]

    return {
        "total_flagged_outstanding": total_flagged_outstanding,
        "total_flagged_cases": len(flagged_cifs),
        "pattern_distribution": pattern_distribution
    }


@router.get("/vendor-hubs")
def get_vendor_hubs(db: Session = Depends(get_db)):
    """Get vendor hub analysis using the AI pipeline graph model."""
    try:
        from ai_engine.pipeline import get_pipeline
        pipeline = get_pipeline()
        # Rebuild graph if it hasn't been built yet
        if not pipeline.hub_detector.hub_vendors:
            pipeline.hub_detector.build_graph(db)
        hub_summary = pipeline.hub_detector.get_hub_summary(db)
        # Normalize field names to match existing frontend expectations
        result = []
        for h in hub_summary:
            result.append({
                "vendor_tax_id": h["vendor_tax_id"],
                "company_name": h["vendor_name"],
                "connected_customers": h["connected_customer_count"],
                "total_amount": h["total_amount_bn"] * 1e9,
                "is_suspicious": h["is_suspicious"],
                "customer_list": [
                    {
                        "cif": c["cif"],
                        "customer_name": c["name"],
                        "outstanding": c["amount_bn"] * 1e9
                    }
                    for c in h.get("connected_customers", [])
                ]
            })
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[VendorHubs] AI pipeline error, falling back: {e}")
        # Fallback to original SQL-based implementation
        invoices = db.query(TaxInvoice).all()
        vendor_data = {}
        for inv in invoices:
            if not inv.seller_tax_id or inv.status == "cancelled":
                continue
            if inv.seller_tax_id not in vendor_data:
                vendor_data[inv.seller_tax_id] = {"buyers": set(), "total_amount": 0}
            vendor_data[inv.seller_tax_id]["buyers"].add(inv.buyer_tax_id)
            vendor_data[inv.seller_tax_id]["total_amount"] += (inv.amount or 0)

        result = []
        for vendor_tax_id, data in vendor_data.items():
            if len(data["buyers"]) < 2:
                continue
            customer_list = []
            for buyer_tax_id in data["buyers"]:
                customer = db.query(Customer).filter_by(tax_id=buyer_tax_id).first()
                if customer:
                    loans = db.query(LoanMaster).filter_by(cif=customer.cif).all()
                    outstanding = sum(l.outstanding_balance for l in loans)
                    customer_list.append({
                        "cif": customer.cif,
                        "customer_name": customer.customer_name,
                        "outstanding": outstanding
                    })
            vendor_name = VENDOR_NAMES.get(vendor_tax_id, f"Công ty MST {vendor_tax_id}")
            result.append({
                "vendor_tax_id": vendor_tax_id,
                "company_name": vendor_name,
                "connected_customers": len(data["buyers"]),
                "total_amount": data["total_amount"],
                "is_suspicious": len(data["buyers"]) >= 3,
                "customer_list": customer_list
            })
        result.sort(key=lambda x: x["connected_customers"], reverse=True)
        return result


@router.get("/{cif}")
def get_customer_misuse(cif: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter_by(cif=cif).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    result = {
        "cif": cif,
        "customer_name": customer.customer_name,
        "tax_status": None,
        "invoices": [],
        "invoice_summary": None,
        "social_insurance": None,
        "logistics": [],
        "logistics_count": 0,
        "vendor_connections": []
    }

    if customer.tax_id:
        tax = db.query(TaxStatus).filter_by(tax_id=customer.tax_id).first()
        if tax:
            result["tax_status"] = {
                "tax_id": tax.tax_id,
                "company_name": tax.company_name,
                "status": tax.status,
                "registration_date": tax.registration_date
            }

        invoices = db.query(TaxInvoice).filter_by(buyer_tax_id=customer.tax_id).all()
        result["invoices"] = [{
            "invoice_id": inv.invoice_id,
            "seller_tax_id": inv.seller_tax_id,
            "invoice_date": inv.invoice_date,
            "amount": inv.amount,
            "status": inv.status
        } for inv in invoices]

        if invoices:
            cancelled = sum(1 for i in invoices if i.status == "cancelled")
            result["invoice_summary"] = {
                "total": len(invoices),
                "cancelled": cancelled,
                "valid": len(invoices) - cancelled,
                "cancellation_rate": round(cancelled / len(invoices), 3)
            }

        si = db.query(SocialInsurance).filter_by(tax_id=customer.tax_id).first()
        if si:
            result["social_insurance"] = {
                "tax_id": si.tax_id,
                "report_period": si.report_period,
                "declared_employees": si.declared_employees,
                "actual_employees": si.actual_employees,
                "total_salary_fund": si.total_salary_fund,
                "mismatch_ratio": round(si.actual_employees / si.declared_employees, 2) if si.declared_employees > 0 else 1.0
            }

        logistics = db.query(Logistics).filter(
            (Logistics.shipper_tax_id == customer.tax_id) |
            (Logistics.receiver_tax_id == customer.tax_id)
        ).all()
        result["logistics_count"] = len(logistics)
        result["logistics"] = [{
            "logistics_id": l.logistics_id,
            "shipment_date": l.shipment_date,
            "goods_description": l.goods_description,
            "amount": l.amount,
            "status": l.status
        } for l in logistics[:20]]

        # Find vendor hub connections
        buyer_invoices = db.query(TaxInvoice).filter_by(buyer_tax_id=customer.tax_id).all()
        seller_tax_ids = set(inv.seller_tax_id for inv in buyer_invoices)
        for seller_id in seller_tax_ids:
            other_buyers = db.query(TaxInvoice.buyer_tax_id).filter_by(seller_tax_id=seller_id).distinct().all()
            other_buyers = [b[0] for b in other_buyers if b[0] != customer.tax_id]
            if len(other_buyers) >= 2:
                result["vendor_connections"].append({
                    "vendor_tax_id": seller_id,
                    "vendor_name": VENDOR_NAMES.get(seller_id, f"MST {seller_id}"),
                    "other_connected_buyers": len(other_buyers),
                    "is_hub": True
                })

    return result
