import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import {
  AlertTriangle, DollarSign, Users, ChevronDown, ChevronUp,
  Network, FileWarning
} from 'lucide-react';
import { getMisuseOverview, getMisuseVendorHubs } from '../api/client';
import type { MisuseOverview, VendorHub } from '../types';

const formatVND = (amount: number) => {
  if (amount >= 1e12) return `${(amount / 1e12).toFixed(1)} nghìn tỷ`;
  if (amount >= 1e9) return `${(amount / 1e9).toFixed(0)} tỷ`;
  if (amount >= 1e6) return `${(amount / 1e6).toFixed(0)} triệu`;
  return amount.toLocaleString('vi-VN');
};

const PATTERN_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#8b5cf6'];

export default function MisusePage() {
  const [overview, setOverview] = useState<MisuseOverview | null>(null);
  const [vendors, setVendors] = useState<VendorHub[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedVendor, setExpandedVendor] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMisuseOverview(), getMisuseVendorHubs()])
      .then(([ov, vd]) => {
        setOverview(ov);
        setVendors(vd);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  const barData = overview?.pattern_distribution.map(p => ({
    name: p.pattern,
    amount: p.total_amount,
    count: p.count,
  })) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPI Header */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {formatVND(overview?.total_flagged_outstanding || 0)}
              </div>
              <div className="text-sm text-slate-400">Dư nợ bị gắn cờ</div>
            </div>
          </div>
        </div>
        <div className="glass-card p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
              <Users className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{overview?.total_flagged_cases || 0}</div>
              <div className="text-sm text-slate-400">Khách hàng bị cảnh báo</div>
            </div>
          </div>
        </div>
        <div className="glass-card p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <FileWarning className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{overview?.pattern_distribution.length || 0}</div>
              <div className="text-sm text-slate-400">Loại pattern sai mục đích</div>
            </div>
          </div>
        </div>
      </div>

      {/* Pattern Distribution Chart */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-base font-semibold text-white">Phân bổ Pattern Sai mục đích Vốn vay</h3>
            <p className="text-xs text-slate-400 mt-0.5">Theo dư nợ bị ảnh hưởng</p>
          </div>
          <AlertTriangle className="w-5 h-5 text-amber-400" />
        </div>
        <div className="grid grid-cols-2 gap-6">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                tickFormatter={(v) => `${(v / 1e9).toFixed(0)}B`}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={110}
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
                {barData.map((_, index) => (
                  <Cell key={index} fill={PATTERN_COLORS[index % PATTERN_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="space-y-3">
            {overview?.pattern_distribution.map((p, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl"
                style={{ background: `${PATTERN_COLORS[i % PATTERN_COLORS.length]}15`, borderLeft: `3px solid ${PATTERN_COLORS[i % PATTERN_COLORS.length]}` }}>
                <div>
                  <div className="text-sm font-medium text-white">{p.pattern}</div>
                  <div className="text-xs text-slate-400">{p.count} khách hàng</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold" style={{ color: PATTERN_COLORS[i % PATTERN_COLORS.length] }}>
                    {formatVND(p.total_amount)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Vendor Hub Analysis */}
      <div className="glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
          <Network className="w-5 h-5 text-purple-400" />
          <div>
            <h3 className="text-base font-semibold text-white">Phân tích Hub Nhà cung cấp</h3>
            <p className="text-xs text-slate-400">Nhiều khách hàng cùng giao dịch một nhà cung cấp</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="table-header text-left">MST Nhà cung cấp</th>
                <th className="table-header text-left">Tên công ty</th>
                <th className="table-header text-center">Số KH kết nối</th>
                <th className="table-header text-right">Tổng giá trị HĐ</th>
                <th className="table-header text-center">Đánh giá</th>
                <th className="table-header text-center">Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor) => (
                <>
                  <tr
                    key={vendor.vendor_tax_id}
                    className="table-row cursor-pointer"
                    onClick={() => setExpandedVendor(
                      expandedVendor === vendor.vendor_tax_id ? null : vendor.vendor_tax_id
                    )}
                  >
                    <td className="table-cell font-mono text-slate-300">{vendor.vendor_tax_id}</td>
                    <td className="table-cell">
                      <div className="text-sm font-medium text-white">{vendor.company_name}</div>
                    </td>
                    <td className="table-cell text-center">
                      <span className={`text-lg font-bold ${vendor.connected_customers >= 3 ? 'text-red-400' : 'text-amber-400'}`}>
                        {vendor.connected_customers}
                      </span>
                    </td>
                    <td className="table-cell text-right font-mono text-blue-300">
                      {formatVND(vendor.total_amount)}
                    </td>
                    <td className="table-cell text-center">
                      {vendor.is_suspicious ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full border border-red-500/30">
                          <AlertTriangle className="w-3 h-3" />
                          Đáng ngờ
                        </span>
                      ) : (
                        <span className="text-xs text-amber-400">Cần theo dõi</span>
                      )}
                    </td>
                    <td className="table-cell text-center">
                      {expandedVendor === vendor.vendor_tax_id
                        ? <ChevronUp className="w-4 h-4 text-slate-400 mx-auto" />
                        : <ChevronDown className="w-4 h-4 text-slate-400 mx-auto" />
                      }
                    </td>
                  </tr>
                  {expandedVendor === vendor.vendor_tax_id && (
                    <tr key={`${vendor.vendor_tax_id}-expanded`}>
                      <td colSpan={6} className="px-6 py-4 bg-white/3">
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-slate-400 uppercase mb-3">
                            Khách hàng kết nối với nhà cung cấp này:
                          </div>
                          {vendor.customer_list.map((customer) => (
                            <div key={customer.cif} className="flex items-center justify-between py-2 px-4 rounded-lg bg-white/5">
                              <div>
                                <div className="text-sm font-medium text-white">{customer.customer_name}</div>
                                <div className="text-xs font-mono text-slate-400">{customer.cif}</div>
                              </div>
                              <div className="text-sm text-blue-300 font-mono">
                                {formatVND(customer.outstanding)} dư nợ
                              </div>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {vendors.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-400 text-sm">
                    Không có dữ liệu vendor hub
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
