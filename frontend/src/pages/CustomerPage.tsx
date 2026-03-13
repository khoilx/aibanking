import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import {
  Users, Search, Filter, ArrowLeft, User, Building2,
  CreditCard, ArrowDownUp, Shield, AlertTriangle,
  Phone, Mail, Calendar, FileText, TrendingDown, CheckCircle, XCircle
} from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import RuleHitList from '../components/RuleHitList';
import { getCustomers, getCustomerDetail } from '../api/client';
import type { CustomerDetail } from '../types';

const formatVND = (amount: number) => {
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(1)} tỷ`;
  if (amount >= 1e6) return `${(amount / 1e6).toFixed(0)} triệu`;
  return amount.toLocaleString('vi-VN');
};

const DEBT_GROUP_COLORS: Record<number, string> = {
  1: '#10b981', 2: '#f59e0b', 3: '#f97316', 4: '#ef4444', 5: '#7f1d1d'
};

type Tab = 'overview' | 'loans' | 'transactions' | 'risk' | 'misuse';

export default function CustomerPage() {
  const { cif } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [customers, setCustomers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [riskFilter, setRiskFilter] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (cif) {
      getCustomerDetail(cif)
        .then(setDetail)
        .finally(() => setLoading(false));
    } else {
      setLoading(true);
      getCustomers({ search: search || undefined, risk_category: riskFilter || undefined, page, page_size: 20 })
        .then(data => {
          setCustomers(data.items);
          setTotal(data.total);
        })
        .finally(() => setLoading(false));
    }
  }, [cif, search, riskFilter, page]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  // Customer List View
  if (!cif) {
    return (
      <div className="space-y-4 animate-fade-in">
        {/* Filters */}
        <div className="glass-card p-4 flex items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm kiếm tên, CIF, MST..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="input-field pl-9 w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
              className="input-field"
            >
              <option value="">Tất cả mức độ</option>
              <option value="Green">Thấp (Green)</option>
              <option value="Amber">Trung bình (Amber)</option>
              <option value="Red">Cao (Red)</option>
            </select>
          </div>
          <span className="text-sm text-slate-400 ml-auto">{total} khách hàng</span>
        </div>

        {/* Table */}
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="table-header text-left">CIF</th>
                  <th className="table-header text-left">Tên khách hàng</th>
                  <th className="table-header text-left">Chi nhánh</th>
                  <th className="table-header text-right">Dư nợ</th>
                  <th className="table-header text-center">Nhóm nợ cao</th>
                  <th className="table-header text-center">Risk Score</th>
                  <th className="table-header text-center">Phân loại</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr
                    key={c.cif}
                    className="table-row cursor-pointer"
                    onClick={() => navigate(`/customers/${c.cif}`)}
                  >
                    <td className="table-cell font-mono text-slate-400 text-xs">{c.cif}</td>
                    <td className="table-cell">
                      <div className="font-medium text-white">{c.customer_name}</div>
                      <div className="text-xs text-slate-400">{c.customer_type === 'Corporate' ? 'Doanh nghiệp' : 'Cá nhân'}</div>
                    </td>
                    <td className="table-cell text-slate-300">{c.branch_name}</td>
                    <td className="table-cell text-right font-mono text-blue-300">
                      {formatVND(c.total_outstanding)}
                    </td>
                    <td className="table-cell text-center">
                      <span className={`text-sm font-bold ${c.max_debt_group >= 3 ? 'text-red-400' : c.max_debt_group === 2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        Nhóm {c.max_debt_group}
                      </span>
                    </td>
                    <td className="table-cell text-center font-bold text-white">{c.risk_score}</td>
                    <td className="table-cell text-center">
                      <RiskBadge category={c.risk_category} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
            <span className="text-sm text-slate-400">Trang {page} / {Math.ceil(total / 20)}</span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed text-sm py-1.5"
              >
                Trước
              </button>
              <button
                disabled={page >= Math.ceil(total / 20)}
                onClick={() => setPage(p => p + 1)}
                className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed text-sm py-1.5"
              >
                Tiếp
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Customer Detail View
  if (!detail) return null;

  const { customer_info: c, loans, off_balance, recent_transactions, risk_analysis, misuse_data } = detail;
  const totalOutstanding = loans.reduce((s, l) => s + l.outstanding_balance, 0);
  const maxDebtGroup = Math.max(...loans.map(l => l.debt_group), 1);

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'overview', label: 'Tổng quan', icon: User },
    { key: 'loans', label: 'Dư nợ', icon: CreditCard },
    { key: 'transactions', label: 'Giao dịch', icon: ArrowDownUp },
    { key: 'risk', label: 'Phân tích Rủi ro', icon: Shield },
    { key: 'misuse', label: 'Dữ liệu Sai mục đích', icon: AlertTriangle },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="glass-card p-6">
        <button
          onClick={() => navigate('/customers')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-4 text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Quay lại danh sách
        </button>

        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center">
              <User className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{c.customer_name}</h2>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <span className="text-xs font-mono text-slate-400">{c.cif}</span>
                <span className="text-xs px-2 py-0.5 bg-slate-700/50 rounded text-slate-300">
                  {c.customer_type === 'Corporate' ? 'Doanh nghiệp' : 'Cá nhân'}
                </span>
                <span className="text-xs px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-blue-300">
                  {c.segment}
                </span>
                <RiskBadge category={risk_analysis.risk_category} score={risk_analysis.total_score} />
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-300">{formatVND(totalOutstanding)}</div>
            <div className="text-xs text-slate-400">Tổng dư nợ</div>
            <div className={`text-sm font-medium mt-1 ${maxDebtGroup >= 3 ? 'text-red-400' : maxDebtGroup === 2 ? 'text-amber-400' : 'text-emerald-400'}`}>
              Nhóm nợ cao nhất: {maxDebtGroup}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="glass-card p-1 flex gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex-1 justify-center ${
                activeTab === tab.key
                  ? 'bg-blue-500/20 border border-blue-500/30 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Thông tin khách hàng</h3>
            <div className="space-y-3">
              {c.phone && (
                <div className="flex items-center gap-3 text-sm">
                  <Phone className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">Điện thoại:</span>
                  <span className="text-white">{c.phone}</span>
                </div>
              )}
              {c.email && (
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">Email:</span>
                  <span className="text-white">{c.email}</span>
                </div>
              )}
              {c.tax_id && (
                <div className="flex items-center gap-3 text-sm">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">MST:</span>
                  <span className="text-white font-mono">{c.tax_id}</span>
                </div>
              )}
              {c.id_number && (
                <div className="flex items-center gap-3 text-sm">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">CCCD:</span>
                  <span className="text-white font-mono">{c.id_number}</span>
                </div>
              )}
              {c.created_date && (
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">Ngày mở CIF:</span>
                  <span className="text-white">{c.created_date}</span>
                </div>
              )}
              <div className="flex items-center gap-3 text-sm">
                <Shield className="w-4 h-4 text-slate-400" />
                <span className="text-slate-400">Xếp hạng tín dụng:</span>
                <span className={`font-bold ${c.credit_rating === 'A' ? 'text-emerald-400' : c.credit_rating === 'B' ? 'text-blue-400' : c.credit_rating === 'C' ? 'text-amber-400' : 'text-red-400'}`}>
                  {c.credit_rating}
                </span>
              </div>
            </div>
          </div>
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Tóm tắt tín dụng</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-sm text-slate-400">Số khoản vay</span>
                <span className="font-bold text-white">{loans.length}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-sm text-slate-400">Tổng dư nợ</span>
                <span className="font-bold text-blue-300">{formatVND(totalOutstanding)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-sm text-slate-400">Nhóm nợ cao nhất</span>
                <span className={`font-bold ${maxDebtGroup >= 3 ? 'text-red-400' : maxDebtGroup === 2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  Nhóm {maxDebtGroup}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-sm text-slate-400">Cam kết ngoại bảng</span>
                <span className="font-bold text-white">{off_balance.length} khoản</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-slate-400">Risk Score</span>
                <RiskBadge category={risk_analysis.risk_category} score={risk_analysis.total_score} size="lg" />
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'loans' && (
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5">
            <h3 className="text-sm font-semibold text-white">Danh sách khoản vay & Cam kết ngoại bảng</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="table-header text-left">Mã khoản vay</th>
                  <th className="table-header text-left">Mục đích</th>
                  <th className="table-header text-left">Lĩnh vực</th>
                  <th className="table-header text-right">Số tiền vay</th>
                  <th className="table-header text-right">Dư nợ</th>
                  <th className="table-header text-center">Nhóm nợ</th>
                  <th className="table-header text-right">Lãi suất</th>
                  <th className="table-header text-center">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {loans.map((loan) => (
                  <tr key={loan.loan_id} className="table-row">
                    <td className="table-cell font-mono text-xs text-slate-400">{loan.loan_id}</td>
                    <td className="table-cell text-sm text-slate-200">{loan.loan_purpose}</td>
                    <td className="table-cell">
                      <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded">{loan.loan_category}</span>
                    </td>
                    <td className="table-cell text-right text-slate-300">{formatVND(loan.loan_amount)}</td>
                    <td className="table-cell text-right font-bold text-white">{formatVND(loan.outstanding_balance)}</td>
                    <td className="table-cell text-center">
                      <span className={`text-sm font-bold`} style={{ color: DEBT_GROUP_COLORS[loan.debt_group] }}>
                        Nhóm {loan.debt_group}
                      </span>
                    </td>
                    <td className="table-cell text-right text-slate-300">{loan.interest_rate?.toFixed(1)}%</td>
                    <td className="table-cell text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${loan.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : loan.status === 'restructured' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-400'}`}>
                        {loan.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {off_balance.map((ob) => (
                  <tr key={ob.off_balance_id} className="table-row">
                    <td className="table-cell font-mono text-xs text-slate-400">{ob.off_balance_id}</td>
                    <td className="table-cell text-sm text-purple-300">[Ngoại bảng] {ob.ob_type}</td>
                    <td className="table-cell">
                      <span className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded">Off-Balance</span>
                    </td>
                    <td className="table-cell text-right text-slate-300">{formatVND(ob.amount)}</td>
                    <td className="table-cell text-right text-slate-300">-</td>
                    <td className="table-cell text-center text-slate-400">-</td>
                    <td className="table-cell text-right text-slate-400">-</td>
                    <td className="table-cell text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${ob.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>
                        {ob.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'transactions' && (
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5">
            <h3 className="text-sm font-semibold text-white">20 Giao dịch gần nhất</h3>
          </div>
          <div className="divide-y divide-white/5">
            {recent_transactions.map((txn) => {
              const isDisb = txn.txn_type === 'disbursement';
              const isInterest = txn.txn_type === 'interest_payment';
              const isSuspicious = txn.description?.includes('tiền mặt');
              return (
                <div key={txn.txn_id} className={`px-6 py-4 flex items-center gap-4 ${isSuspicious ? 'bg-red-500/5' : 'hover:bg-white/3'} transition-colors`}>
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    isDisb ? 'bg-blue-500/20 text-blue-400' :
                    isInterest ? 'bg-amber-500/20 text-amber-400' :
                    isSuspicious ? 'bg-red-500/20 text-red-400' :
                    'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    <ArrowDownUp className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{txn.description}</span>
                      {isSuspicious && (
                        <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded border border-red-500/30">
                          Đáng ngờ
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {txn.txn_date} | {txn.channel} | {txn.txn_id}
                    </div>
                  </div>
                  <div className={`text-right font-mono font-bold ${isDisb ? 'text-blue-300' : isSuspicious ? 'text-red-300' : 'text-emerald-300'}`}>
                    {isDisb ? '+' : '-'}{formatVND(txn.amount)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'risk' && (
        <div className="space-y-6">
          {/* Risk Score */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">Điểm rủi ro tổng hợp</h3>
              <RiskBadge category={risk_analysis.risk_category} size="lg" />
            </div>
            <div className="flex items-center gap-6">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                  <circle
                    cx="60" cy="60" r="48" fill="none"
                    stroke={risk_analysis.risk_category === 'Red' ? '#ef4444' : risk_analysis.risk_category === 'Amber' ? '#f59e0b' : '#10b981'}
                    strokeWidth="12"
                    strokeLinecap="round"
                    strokeDasharray={`${(risk_analysis.total_score / 100) * 301.6} 301.6`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold text-white">{risk_analysis.total_score}</span>
                  <span className="text-xs text-slate-400">/100</span>
                </div>
              </div>
              <div className="flex-1">
                <div className="text-sm text-slate-400 mb-2">Phân loại rủi ro:</div>
                <div className="text-lg font-bold text-white mb-1">
                  {risk_analysis.risk_category === 'Red' ? 'Rủi ro Cao' :
                   risk_analysis.risk_category === 'Amber' ? 'Rủi ro Trung bình' : 'Rủi ro Thấp'}
                </div>
                <div className="text-sm text-slate-400">
                  {risk_analysis.rule_hits.length} quy tắc vi phạm được phát hiện
                </div>
              </div>
            </div>
          </div>

          {/* Rule Hits */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Vi phạm quy tắc</h3>
            <RuleHitList rules={risk_analysis.rule_hits} />
          </div>

          {/* CIC */}
          {risk_analysis.cic && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Dữ liệu CIC</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Dư nợ TCTD khác</span>
                    <span className="text-white font-mono">{formatVND(risk_analysis.cic.total_debt_other_banks)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Nhóm nợ tại TCTD khác</span>
                    <span className={risk_analysis.cic.debt_group_other_banks >= 3 ? 'text-red-400 font-bold' : 'text-white'}>
                      Nhóm {risk_analysis.cic.debt_group_other_banks}
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Số TCTD có quan hệ</span>
                    <span className="text-white">{risk_analysis.cic.number_of_credit_institutions}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Lịch sử quá hạn</span>
                    {risk_analysis.cic.has_overdue_history ? (
                      <span className="flex items-center gap-1 text-red-400"><XCircle className="w-3 h-3" /> Có</span>
                    ) : (
                      <span className="flex items-center gap-1 text-emerald-400"><CheckCircle className="w-3 h-3" /> Không</span>
                    )}
                  </div>
                </div>
              </div>
              {risk_analysis.cic.bad_debt_amount > 0 && (
                <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                  <div className="text-xs text-red-400">Nợ xấu tại TCTD khác: {formatVND(risk_analysis.cic.bad_debt_amount)}</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'misuse' && (
        <div className="space-y-6">
          {/* Tax Status */}
          {misuse_data.tax_status && (
            <div className={`glass-card p-6 ${
              misuse_data.tax_status.status === 'closed' ? 'border-red-500/30' :
              misuse_data.tax_status.status === 'evading' ? 'border-red-500/30' :
              misuse_data.tax_status.status === 'suspended' ? 'border-amber-500/30' : ''
            }`}>
              <h3 className="text-sm font-semibold text-white mb-4">Trạng thái Thuế</h3>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">{misuse_data.tax_status.company_name}</div>
                  <div className="text-xs text-slate-400 mt-1">MST: {misuse_data.tax_status.tax_id}</div>
                  <div className="text-xs text-slate-400">Ngày đăng ký: {misuse_data.tax_status.registration_date}</div>
                </div>
                <span className={`px-3 py-1.5 rounded-xl text-sm font-bold border ${
                  misuse_data.tax_status.status === 'active' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                  misuse_data.tax_status.status === 'closed' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                  misuse_data.tax_status.status === 'evading' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                  'bg-amber-500/20 text-amber-400 border-amber-500/30'
                }`}>
                  {misuse_data.tax_status.status === 'active' ? 'Hoạt động' :
                   misuse_data.tax_status.status === 'closed' ? 'Đã đóng' :
                   misuse_data.tax_status.status === 'evading' ? 'Bỏ trốn' : 'Tạm ngừng'}
                </span>
              </div>
            </div>
          )}

          {/* Invoice Summary */}
          {misuse_data.invoice_summary && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Hóa đơn điện tử</h3>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 rounded-xl bg-white/5">
                  <div className="text-2xl font-bold text-white">{misuse_data.invoice_summary.total}</div>
                  <div className="text-xs text-slate-400">Tổng HĐ</div>
                </div>
                <div className="text-center p-3 rounded-xl bg-emerald-500/10">
                  <div className="text-2xl font-bold text-emerald-400">{misuse_data.invoice_summary.total - misuse_data.invoice_summary.cancelled}</div>
                  <div className="text-xs text-slate-400">HĐ hợp lệ</div>
                </div>
                <div className="text-center p-3 rounded-xl bg-red-500/10">
                  <div className="text-2xl font-bold text-red-400">{misuse_data.invoice_summary.cancelled}</div>
                  <div className="text-xs text-slate-400">HĐ hủy</div>
                </div>
              </div>
              <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    misuse_data.invoice_summary.cancellation_rate > 0.5 ? 'bg-red-500' :
                    misuse_data.invoice_summary.cancellation_rate > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${misuse_data.invoice_summary.cancellation_rate * 100}%` }}
                />
              </div>
              <div className="text-xs text-slate-400 mt-1.5 text-right">
                Tỷ lệ hủy: {(misuse_data.invoice_summary.cancellation_rate * 100).toFixed(1)}%
                {misuse_data.invoice_summary.cancellation_rate > 0.5 && (
                  <span className="ml-2 text-red-400">⚠ Vượt ngưỡng</span>
                )}
              </div>
            </div>
          )}

          {/* SI Mismatch */}
          {misuse_data.si_mismatch && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Bảo hiểm Xã hội - {misuse_data.si_mismatch.report_period}</h3>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[{
                    name: 'Nhân sự',
                    declared: misuse_data.si_mismatch.declared_employees,
                    actual: misuse_data.si_mismatch.actual_employees,
                  }]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9', fontSize: '12px' }}
                    />
                    <Bar dataKey="declared" name="Khai báo" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="actual" name="Thực tế" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-around mt-2 text-center">
                <div>
                  <div className="text-xl font-bold text-blue-400">{misuse_data.si_mismatch.declared_employees}</div>
                  <div className="text-xs text-slate-400">Khai báo</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-red-400">{misuse_data.si_mismatch.actual_employees}</div>
                  <div className="text-xs text-slate-400">Thực tế</div>
                </div>
                <div>
                  <div className={`text-xl font-bold ${
                    misuse_data.si_mismatch.actual_employees / misuse_data.si_mismatch.declared_employees < 0.5
                      ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {misuse_data.si_mismatch.declared_employees > 0
                      ? `${((misuse_data.si_mismatch.actual_employees / misuse_data.si_mismatch.declared_employees) * 100).toFixed(0)}%`
                      : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-400">Tỷ lệ</div>
                </div>
              </div>
            </div>
          )}

          {/* Logistics */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Dữ liệu Logistics / Vận đơn</h3>
            <div className="flex items-center gap-4">
              <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${
                misuse_data.logistics_count === 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
              }`}>
                <TrendingDown className="w-8 h-8" />
              </div>
              <div>
                <div className="text-3xl font-bold text-white">{misuse_data.logistics_count}</div>
                <div className="text-sm text-slate-400">vận đơn/logistics records</div>
                {misuse_data.logistics_count === 0 && (
                  <div className="text-xs text-red-400 mt-1">Không có dữ liệu logistics - rủi ro cao</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
