from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import numpy as np
import pandas as pd

RISK_LABELS = {0: 'Green', 1: 'Amber', 2: 'Red'}
RISK_LABEL_REVERSE = {'Green': 0, 'Amber': 1, 'Red': 2}


class RiskClassifier:
    """Random Forest-based risk classifier with feature importance explanations."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42
        )
        self.is_fitted = False
        self.feature_names = None
        self.cv_scores = []
        self.feature_importances_ = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Train classifier. X=features DataFrame, y=labels (0=Green, 1=Amber, 2=Red)."""
        self.feature_names = list(X.columns)
        X_filled = X.fillna(0)

        # Cross-validation if enough samples
        if len(X) >= 10:
            try:
                cv_folds = min(5, len(X) // 3)
                if cv_folds >= 2:
                    self.cv_scores = cross_val_score(
                        self.model, X_filled, y, cv=cv_folds, scoring='f1_weighted'
                    ).tolist()
                else:
                    self.cv_scores = []
            except Exception:
                self.cv_scores = []

        self.model.fit(X_filled, y)
        self.is_fitted = True
        self.feature_importances_ = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Returns probability array [p_green, p_amber, p_red] for each row."""
        cols = [c for c in self.feature_names if c in X.columns]
        X_filled = X.reindex(columns=self.feature_names, fill_value=0).fillna(0)
        # Ensure all model classes are represented
        proba = self.model.predict_proba(X_filled)
        # The model may have fewer classes if training set lacked some — pad to 3
        n_classes = proba.shape[1]
        model_classes = list(self.model.classes_)
        if n_classes < 3:
            full_proba = np.zeros((len(proba), 3))
            for idx, cls in enumerate(model_classes):
                full_proba[:, cls] = proba[:, idx]
            return full_proba
        return proba

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Returns predicted class (0/1/2) for each row."""
        return np.argmax(self.predict_proba(X), axis=1)

    def explain(self, features: dict, top_n: int = 5) -> list:
        """Generate feature contribution explanation for a single customer.
        Returns list of dicts: [{rule_id, description, contribution_pct, direction}]"""
        if not self.is_fitted:
            return []

        df = pd.DataFrame([{k: features.get(k, 0) for k in self.feature_names}])

        # Use feature importance x feature value as proxy for contribution
        X_filled = df.fillna(0).values[0]
        importances = self.model.feature_importances_

        contribs = []
        for i, fname in enumerate(self.feature_names):
            val = float(X_filled[i])
            imp = float(importances[i])
            contribs.append({
                'feature': fname,
                'value': val,
                'importance': imp,
                'contribution': val * imp
            })

        # Sort by contribution magnitude
        contribs.sort(key=lambda x: abs(x['contribution']), reverse=True)
        top = contribs[:top_n]

        # Map to human-readable explanations
        explanations = []
        for c in top:
            desc = _feature_to_description(c['feature'], c['value'])
            if desc:
                explanations.append({
                    'rule_id': f"ML_{c['feature'].upper()[:8]}",
                    'description': desc,
                    'feature': c['feature'],
                    'value': round(c['value'], 4),
                    'importance_pct': round(c['importance'] * 100, 1),
                    'severity': (
                        'high' if c['importance'] > 0.1
                        else ('medium' if c['importance'] > 0.05 else 'low')
                    ),
                    'points': int(c['importance'] * 100)
                })

        return explanations


def _feature_to_description(feature: str, value: float) -> str:
    """Convert feature name + value to Vietnamese description."""
    mapping = {
        'max_debt_group': lambda v: (
            f"Nợ nhóm {int(v)} - Nguy cơ mất vốn" if v >= 3
            else f"Nhóm nợ {int(v)} (bình thường)"
        ),
        'avg_debt_group': lambda v: f"Trung bình nhóm nợ: {v:.1f}",
        'num_loans': lambda v: f"Số khoản vay: {int(v)}",
        'total_outstanding_bn': lambda v: f"Tổng dư nợ: {v:.1f} tỷ VND",
        'restructured_ratio': lambda v: (
            f"Tỷ lệ nợ cơ cấu: {v*100:.0f}%" if v > 0 else None
        ),
        'cash_withdrawal_ratio': lambda v: (
            f"Tỷ lệ rút tiền mặt ngay sau giải ngân: {v*100:.0f}%" if v > 0.5 else None
        ),
        'time_to_withdrawal_h': lambda v: (
            f"Rút tiền sau {v:.0f}h giải ngân (nghi vấn)" if v < 48 else None
        ),
        'round_txn_ratio': lambda v: (
            f"Tỷ lệ giao dịch số chẵn đáng ngờ: {v*100:.0f}%" if v > 0.6 else None
        ),
        'txn_velocity': lambda v: f"Tốc độ giao dịch: {v:.1f} txn/tháng",
        'tax_status_risk': lambda v: (
            ["MST đang hoạt động", "MST tạm ngừng", "MST bỏ trốn thuế", "MST bị đóng"][int(min(v, 3))]
            if v >= 0 else None
        ),
        'invoice_cancel_rate': lambda v: (
            f"Tỷ lệ hủy HĐ điện tử: {v*100:.0f}%" if v > 0.3 else None
        ),
        'invoice_suspicious_rate': lambda v: (
            f"Tỷ lệ HĐ đáng ngờ: {v*100:.0f}%" if v > 0.2 else None
        ),
        'si_employee_ratio': lambda v: (
            f"Bất thường BHXH: thực tế/khai báo = {v:.0%}" if v < 0.6 else None
        ),
        'vendor_hub_degree': lambda v: (
            f"Kết nối Hub nhà cung cấp đáng ngờ ({int(v)} vendors)" if v > 0 else None
        ),
        'vendor_hub_amount_bn': lambda v: (
            f"Tổng tiền qua Hub vendor: {v:.1f} tỷ" if v > 0 else None
        ),
        'has_overdue_history': lambda v: (
            "Lịch sử quá hạn tại TCTD khác" if v > 0 else None
        ),
        'cic_bad_debt_bn': lambda v: (
            f"Nợ xấu tại TCTD khác: {v:.1f} tỷ" if v > 0 else None
        ),
        'avg_ltv': lambda v: (
            f"Tỷ lệ Vay/TSĐB trung bình: {v*100:.0f}%" if v > 0.8 else None
        ),
        'max_ltv': lambda v: (
            f"Tỷ lệ Vay/TSĐB cao nhất: {v*100:.0f}%" if v > 0.85 else None
        ),
        'has_trading_no_logistics': lambda v: (
            "Không có vận đơn phù hợp mục đích vay" if v > 0 else None
        ),
        'credit_rating_score': lambda v: (
            ["Xếp hạng A (Tốt)", "Xếp hạng B (Khá)", "Xếp hạng C (Trung bình)", "Xếp hạng D (Yếu)"][int(min(v, 3))]
        ),
        'is_corporate': lambda v: (
            "Khách hàng doanh nghiệp" if v > 0 else "Khách hàng cá nhân"
        ),
        'num_credit_institutions': lambda v: f"Số TCTD: {int(v)}",
        'logistics_count': lambda v: (
            f"Số vận đơn: {int(v)}" if v > 0 else None
        ),
    }
    fn = mapping.get(feature)
    if fn is None:
        return None
    try:
        return fn(value)
    except Exception:
        return None
