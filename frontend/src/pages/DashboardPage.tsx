import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, AlertCircle, DollarSign, Users,
  FileWarning, BarChart3, Activity, Shield
} from 'lucide-react';
import KPICard from '../components/KPICard';
import RiskBadge from '../components/RiskBadge';
import { getDashboardKPIs, getDashboardTrend, getTopRedFlags } from '../api/client';
import type { DashboardKPIs, TrendDataPoint, TopRedFlag } from '../types';

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const formatVND = (amount: number) => {
  if (amount >= 1e12) return `${(amount / 1e12).toFixed(1)} nghìn tỷ`;
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(0)} tỷ`;
  if (amount >= 1e6) return `${(amount / 1e6).toFixed(0)} triệu`;
  return amount.toLocaleString('vi-VN');
};

const formatCurrency = (value: number) => {
  return `${(value / 1e9).toFixed(0)} tỷ`;
};

export default function DashboardPage() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [trend, setTrend] = useState<TrendDataPoint[]>([]);
  const [redFlags, setRedFlags] = useState<TopRedFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpiData, trendData, flagData] = await Promise.all([
          getDashboardKPIs(),
          getDashboardTrend(),
          getTopRedFlags(),
        ]);
        setKpis(kpiData);
        setTrend(trendData);
        setRedFlags(flagData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  // Pie data for category breakdown (mock from trend)
  const pieData = [
    { name: 'BDS', value: 30 },
    { name: 'Nông nghiệp', value: 25 },
    { name: 'Bán lẻ', value: 25 },
    { name: 'Sản xuất', value: 20 },
  ];

  const monthLabels: Record<string, string> = {
    '01': 'T1', '02': 'T2', '03': 'T3', '04': 'T4',
    '05': 'T5', '06': 'T6', '07': 'T7', '08': 'T8',
    '09': 'T9', '10': 'T10', '11': 'T11', '12': 'T12'
  };

  const trendWithLabel = trend.map(d => ({
    ...d,
    label: monthLabels[d.month.split('-')[1]] || d.month,
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPI Grid */}
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <KPICard
          title="Tỷ lệ NPL"
          value={`${kpis?.npl_ratio.toFixed(2)}%`}
          subtitle="Nợ nhóm 3, 4, 5"
          icon={AlertCircle}
          color={kpis && kpis.npl_ratio > 3 ? 'red' : 'amber'}
          trend={0.4}
          trendLabel="so với tháng trước"
          alert
        />
        <KPICard
          title="Tỷ lệ Nợ Nhóm 2"
          value={`${kpis?.group2_ratio.toFixed(2)}%`}
          subtitle="Cần chú ý theo dõi"
          icon={TrendingUp}
          color={kpis && kpis.group2_ratio > 5 ? 'amber' : 'green'}
          trend={0.2}
          alert
        />
        <KPICard
          title="Tỷ lệ Cơ cấu Nợ"
          value={`${kpis?.restructured_ratio.toFixed(2)}%`}
          subtitle="Dư nợ đã cơ cấu lại"
          icon={Activity}
          color="purple"
          trend={-0.1}
        />
        <KPICard
          title="Bao phủ Nợ xấu LLCR"
          value={`${kpis?.llcr.toFixed(1)}%`}
          subtitle="Loan Loss Coverage Ratio"
          icon={Shield}
          color={kpis && kpis.llcr < 70 ? 'red' : 'green'}
          trend={1.2}
        />
        <KPICard
          title="Tổng Dư nợ"
          value={kpis ? formatVND(kpis.total_outstanding) : '0'}
          subtitle={`${kpis?.total_loans} khoản vay / ${kpis?.total_customers} KH`}
          icon={DollarSign}
          color="blue"
        />
        <KPICard
          title="Cảnh báo Rủi ro"
          value={kpis?.red_flag_count || 0}
          subtitle="Khách hàng Red Flag"
          icon={FileWarning}
          color="red"
          trend={2}
          alert
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-5 gap-6">
        {/* Trend Chart */}
        <div className="col-span-3 glass-card p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-semibold text-white">Xu hướng Chất lượng Tín dụng</h3>
              <p className="text-xs text-slate-400 mt-0.5">12 tháng gần nhất</p>
            </div>
            <BarChart3 className="w-5 h-5 text-slate-400" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendWithLabel}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="label"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  color: '#f1f5f9'
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(2)}%`,
                  name === 'npl_ratio' ? 'NPL (%)' : 'Nhóm 2 (%)'
                ]}
              />
              <Legend
                wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }}
                formatter={(value) => value === 'npl_ratio' ? 'Tỷ lệ NPL (%)' : 'Tỷ lệ Nhóm 2 (%)'}
              />
              <Line
                type="monotone"
                dataKey="npl_ratio"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="group2_ratio"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="col-span-2 glass-card p-6">
          <div className="mb-5">
            <h3 className="text-base font-semibold text-white">Phân bổ Danh mục</h3>
            <p className="text-xs text-slate-400 mt-0.5">Theo lĩnh vực đầu tư</p>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                dataKey="value"
                stroke="none"
              >
                {pieData.map((_, index) => (
                  <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: 'rgba(15,23,42,0.95)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '12px'
                }}
                formatter={(value: number) => [`${value}%`, 'Tỷ trọng']}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {pieData.map((item, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i] }} />
                  <span className="text-slate-300">{item.name}</span>
                </div>
                <span className="font-medium text-white">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Red Flags Table */}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div>
            <h3 className="text-base font-semibold text-white">Top Cảnh báo Rủi ro</h3>
            <p className="text-xs text-slate-400 mt-0.5">Khách hàng có điểm rủi ro cao nhất</p>
          </div>
          <Users className="w-5 h-5 text-slate-400" />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="table-header text-left">Khách hàng</th>
                <th className="table-header text-left">Chi nhánh</th>
                <th className="table-header text-right">Dư nợ</th>
                <th className="table-header text-center">Risk Score</th>
                <th className="table-header text-center">Phân loại</th>
                <th className="table-header text-left">Vi phạm nổi bật</th>
              </tr>
            </thead>
            <tbody>
              {redFlags.map((flag) => (
                <tr
                  key={flag.cif}
                  className="table-row cursor-pointer"
                  onClick={() => navigate(`/customers/${flag.cif}`)}
                >
                  <td className="table-cell">
                    <div className="font-medium text-white">{flag.customer_name}</div>
                    <div className="text-xs text-slate-400">{flag.cif}</div>
                  </td>
                  <td className="table-cell text-slate-300">{flag.branch_name}</td>
                  <td className="table-cell text-right font-mono text-blue-300">
                    {formatCurrency(flag.total_outstanding)}
                  </td>
                  <td className="table-cell text-center">
                    <div className="font-bold text-white">{flag.risk_score}</div>
                  </td>
                  <td className="table-cell text-center">
                    <RiskBadge category={flag.risk_category} />
                  </td>
                  <td className="table-cell">
                    <div className="text-xs text-slate-400 max-w-xs truncate">
                      {flag.top_rules[0] || '-'}
                    </div>
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
