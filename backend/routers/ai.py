from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from ai_engine.pipeline import get_pipeline
from ai_engine.features import extract_features_for_customer
from models import Customer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/model-info")
def get_model_info():
    """Return AI model metadata, training status, and performance metrics."""
    pipeline = get_pipeline()
    return pipeline.get_model_info()


@router.post("/retrain")
def trigger_retrain(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger full model retraining in background."""
    pipeline = get_pipeline()

    def _retrain_task():
        try:
            metrics = pipeline.train(db)
            count = pipeline.score_all(db)
            logger.info(f"[Retrain] Complete. Metrics: {metrics}. Scored {count} customers.")
        except Exception as e:
            logger.error(f"[Retrain] Failed: {e}", exc_info=True)

    background_tasks.add_task(_retrain_task)
    return {
        "status": "Training job started in background",
        "message": "Retraining Isolation Forest + Random Forest. Results will be available in ~30 seconds."
    }


@router.post("/score-all")
def trigger_batch_scoring(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger batch scoring of all customers in background."""
    pipeline = get_pipeline()

    def _score_task():
        try:
            count = pipeline.score_all(db)
            logger.info(f"[BatchScore] Scored {count} customers.")
        except Exception as e:
            logger.error(f"[BatchScore] Failed: {e}", exc_info=True)

    background_tasks.add_task(_score_task)
    return {
        "status": "Batch scoring job started",
        "message": "Scoring all customers with current models."
    }


@router.get("/features/{cif}")
def get_customer_features(cif: str, db: Session = Depends(get_db)):
    """Return the feature vector for a specific customer (for explainability/debug)."""
    customer = db.query(Customer).filter(Customer.cif == cif).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    pipeline = get_pipeline()
    hub_feats = pipeline.hub_detector.get_hub_features(cif)
    features = extract_features_for_customer(cif, db, hub_features=hub_feats)

    if not features:
        raise HTTPException(status_code=500, detail="Could not extract features for this customer")

    return {
        "cif": cif,
        "customer_name": customer.customer_name,
        "feature_vector": features,
        "feature_descriptions": {
            "max_debt_group": "Nhóm nợ cao nhất (1-5)",
            "avg_debt_group": "Trung bình nhóm nợ (có trọng số theo dư nợ)",
            "num_loans": "Số khoản vay hiện hữu",
            "total_outstanding_bn": "Tổng dư nợ (tỷ VND)",
            "restructured_ratio": "Tỷ lệ khoản vay được cơ cấu",
            "avg_ltv": "Tỷ lệ Vay/TSĐB trung bình",
            "max_ltv": "Tỷ lệ Vay/TSĐB cao nhất",
            "cash_withdrawal_ratio": "Tỷ lệ rút tiền mặt/tổng giải ngân",
            "time_to_withdrawal_h": "Thời gian đến lần rút tiền mặt đầu tiên (giờ)",
            "round_txn_ratio": "Tỷ lệ giao dịch số chẵn (nghi vấn)",
            "txn_count": "Tổng số giao dịch",
            "txn_velocity": "Tốc độ giao dịch (txn/tháng)",
            "repayment_regularity": "Độ lệch chuẩn chu kỳ trả nợ (ngày)",
            "cic_bad_debt_bn": "Nợ xấu tại TCTD khác (tỷ VND)",
            "cic_debt_group": "Nhóm nợ tại TCTD khác",
            "num_credit_institutions": "Số tổ chức tín dụng",
            "has_overdue_history": "Lịch sử quá hạn (0/1)",
            "tax_status_risk": "Mức rủi ro MST: 0=active, 1=suspended, 2=evading, 3=closed",
            "invoice_cancel_rate": "Tỷ lệ hủy hóa đơn điện tử",
            "invoice_suspicious_rate": "Tỷ lệ hóa đơn đáng ngờ",
            "total_invoice_amount_bn": "Tổng giá trị hóa đơn (tỷ VND)",
            "si_employee_ratio": "Tỷ lệ nhân sự thực tế/khai báo BHXH",
            "si_declared_employees": "Số nhân viên khai báo BHXH",
            "logistics_count": "Số vận đơn liên quan",
            "has_trading_no_logistics": "Có vay kinh doanh nhưng không có vận đơn (0/1)",
            "vendor_hub_degree": "Số hub vendor đáng ngờ có liên kết",
            "vendor_hub_amount_bn": "Tổng tiền qua hub vendor (tỷ VND)",
            "is_corporate": "Doanh nghiệp (1) / Cá nhân (0)",
            "credit_rating_score": "Điểm xếp hạng: A=0, B=1, C=2, D=3",
            "customer_age_days": "Số ngày kể từ khi tạo hồ sơ",
        }
    }


@router.get("/score/{cif}")
def get_customer_ai_score(cif: str, db: Session = Depends(get_db)):
    """Get real-time ML-based risk score for a customer."""
    customer = db.query(Customer).filter(Customer.cif == cif).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    pipeline = get_pipeline()
    result = pipeline.score_single(cif, db)

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Could not compute ML score for this customer"
        )

    return {
        "cif": cif,
        "customer_name": customer.customer_name,
        **result
    }


@router.get("/vendor-hubs")
def get_vendor_hubs(db: Session = Depends(get_db)):
    """Get vendor hub analysis from the graph model."""
    pipeline = get_pipeline()
    if not pipeline.hub_detector.hub_vendors:
        try:
            pipeline.hub_detector.build_graph(db)
        except Exception as e:
            logger.error(f"[VendorHubs] Graph build failed: {e}")
            return {"hub_count": 0, "hubs": []}
    return {
        "hub_count": len(pipeline.hub_detector.hub_vendors),
        "hubs": pipeline.hub_detector.get_hub_summary(db)
    }


@router.get("/pipeline-status")
def get_pipeline_status():
    """Get current pipeline execution status."""
    pipeline = get_pipeline()
    info = pipeline.get_model_info()
    return {
        "pipeline_ready": info["classifier_fitted"] and info["anomaly_fitted"],
        "last_trained": info["last_trained"],
        "last_scored": info["last_scored"],
        "model_metrics": info["metrics"],
    }
