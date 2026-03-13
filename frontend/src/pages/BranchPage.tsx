import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import {
  Building2, ArrowLeft, MapPin, User, AlertTriangle,
  TrendingUp, DollarSign, Users, ChevronRight
} from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { getBranches, getBranchDetail } from '../api/client';
import type { BranchSummary, BranchDetail } from '../types';

const formatVND = (amount: number) => {
  if (amount >= 1e12) return `${(amount / 1e12).toFixed(1)} nghìn tỷ`;
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(0)} tỷ`;
  return amount.toLocaleString('vi-VN');
};

const DEBT_GROUP_COLORS = {
  1: '#10b981',
  2: '#f59e0b',
  3: '#f97316',
  4: '#ef4444',
  5: '#7f1d1d',
};

const CATEGORY_COLORS: Record<string, string> = {
  BDS: '#3b82f6',
  'Nong nghiep': '#10b981',
  'Ban le': '#f59e0b',
  SX: '#8b5cf6',
};

export default function BranchPage() {
  const { branchId } = useParams();
  const navigate = useNavigate();
  const [branches, setBranches] = useState<BranchSummary[]>([]);
  const [detail, setDetail] = useState<BranchDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (branchId) {
      getBranchDetail(branchId)
        .then(setDetail)
        .finally(() => setLoading(false));
    } else {
      getBranches()
        .then(setBranches)
        .finally(() => setLoading(false));
    }
  }, [branchId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  // Branch List View
  if (!branchId) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
            <Building2 className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-semibold text-white">Danh sách Chi nhánh</h3>
            <span className="ml-auto text-sm text-slate-400">{branches.length} chi nhánh</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="table-header text-left">Chi nhánh</th>
                  <th className="table-header text-left">Khu vực</th>
                  <th className="table-header text-left">Giám đốc</th>
                  <th className="table-header text-right">Tổng dư nợ</th>
                  <th className="table-header text-center">Số KH</th>
                  <th className="table-header text-center">NPL (%)</th>
                  <th className="table-header text-center">Red Flag</th>
                  <th className="table-header text-center">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {branches.map((branch) => (
                  <tr
                    key={branch.branch_id}
                    className="table-row cursor-pointer"
                    onClick={() => navigate(`/branches/${branch.branch_id}`)}
                  >
                    <td className="table-cell">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-blue-400" />
                        </div>
                        <div>
                          <div className="font-medium text-white">{branch.branch_name}</div>
                          <div className="text-xs text-slate-400">{branch.branch_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="px-2 py-0.5 bg-slate-700/50 rounded text-xs text-slate-300">
                        {branch.region}
                      </span>
                    </td>
                    <td className="table-cell text-slate-300">{branch.branch_director}</td>
                    <td className="table-cell text-right font-mono text-blue-300">
                      {formatVND(branch.total_outstanding)}
                    </td>
                    <td className="table-cell text-center text-slate-300">{branch.total_customers}</td>
                    <td className="table-cell text-center">
                      <span className={`font-bold ${branch.npl_ratio > 3 ? 'text-red-400' : 'text-amber-400'}`}>
                        {branch.npl_ratio.toFixed(2)}%
                      </span>
                    </td>
                    <td className="table-cell text-center">
                      {branch.red_flag_count > 0 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full border border-red-500/30">
                          <AlertTriangle className="w-3 h-3" />
                          {branch.red_flag_count}
                        </span>
                      ) : (
                        <span className="text-emerald-400 text-xs">Ổn</span>
                      )}
                    </td>
                    <td className="table-cell text-center">
                      <ChevronRight className="w-4 h-4 text-slate-400 mx-auto" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // Branch Detail View
  if (!detail) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="glass-card p-6">
        <button
          onClick={() => navigate('/branches')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-4 text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Quay lại danh sách
        </button>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <Building2 className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">{detail.branch_info.branch_name}</h2>
              <div className="flex items-center gap-4 mt-1">
                <span className="flex items-center gap-1 text-sm text-slate-400">
                  <User className="w-3 h-3" />
                  {detail.branch_info.branch_director}
                </span>
                <span className="flex items-center gap-1 text-sm text-slate-400">
                  <MapPin className="w-3 h-3" />
                  {detail.branch_info.address}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-300">{formatVND(detail.total_outstanding)}</div>
            <div className="text-xs text-slate-400">Tổng dư nợ</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        {/* Portfolio Breakdown */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Phân bổ Danh mục Tín dụng</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={detail.portfolio_breakdown} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1e9).toFixed(0)} tỷ`}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="category"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={80}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '12px'
                }}
                formatter={(value: number) => [`${(value / 1e9).toFixed(0)} tỷ đồng`, 'Dư nợ']}
              />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {detail.portfolio_breakdown.map((entry, index) => (
                  <Cell key={index} fill={CATEGORY_COLORS[entry.category] || '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Debt Group Breakdown */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Phân bổ Nhóm Nợ</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={detail.debt_group_breakdown}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="group"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(v) => `Nhóm ${v}`}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1e9).toFixed(0)}B`}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '12px'
                }}
                formatter={(value: number) => [`${(value / 1e9).toFixed(0)} tỷ đồng`, 'Dư nợ']}
              />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {detail.debt_group_breakdown.map((entry) => (
                  <Cell key={entry.group} fill={DEBT_GROUP_COLORS[entry.group as keyof typeof DEBT_GROUP_COLORS] || '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-5 gap-1 mt-2">
            {detail.debt_group_breakdown.map((dg) => (
              <div key={dg.group} className="text-center">
                <div className="text-xs text-slate-400">Nhóm {dg.group}</div>
                <div className="text-xs font-bold text-white">{dg.count}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Top Risky Loans */}
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5">
            <h3 className="text-sm font-semibold text-white">Khoản vay Rủi ro cao</h3>
          </div>
          <div className="divide-y divide-white/5">
            {detail.top_risky_loans.slice(0, 6).map((loan) => (
              <div key={loan.loan_id} className="px-6 py-3 hover:bg-white/5 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 font-mono">{loan.loan_id}</div>
                    <div className="text-sm text-slate-200 mt-0.5">{loan.loan_purpose}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">
                      {(loan.outstanding_balance / 1e9).toFixed(0)} tỷ
                    </div>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      loan.debt_group >= 3 ? 'bg-red-500/20 text-red-400' :
                      loan.debt_group === 2 ? 'bg-amber-500/20 text-amber-400' :
                      'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      Nhóm {loan.debt_group}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Early Warnings */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Cảnh báo sớm</h3>
          <div className="space-y-3">
            {detail.early_warnings.map((warning, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-200">{warning}</p>
              </div>
            ))}
            {detail.early_warnings.length === 0 && (
              <div className="text-center py-8 text-slate-400 text-sm">
                Không có cảnh báo
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
