import { Bell, Search, RefreshCw } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard Tổng quan',
  '/branches': 'Quản lý Chi nhánh',
  '/customers': 'Danh sách Khách hàng',
  '/misuse': 'Phân tích Sai mục đích Vốn vay',
  '/cases': 'Quản lý Case Kiểm toán',
};

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const getTitle = () => {
    if (location.pathname.startsWith('/branches/')) return 'Chi tiết Chi nhánh';
    if (location.pathname.startsWith('/customers/')) return 'Chi tiết Khách hàng';
    return pageTitles[location.pathname] || 'Audit AI';
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/customers?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const now = new Date();
  const timeStr = now.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });

  return (
    <header
      className="fixed top-0 right-0 z-40 flex items-center justify-between px-6 py-4"
      style={{
        left: '256px',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      }}
    >
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-white">{getTitle()}</h1>
        <p className="text-xs text-slate-400 mt-0.5">Cập nhật lần cuối: {timeStr}</p>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm kiếm KH, CIF..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-9 w-64 text-sm"
          />
        </form>

        {/* Refresh button */}
        <button
          onClick={() => window.location.reload()}
          className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          title="Làm mới"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all">
          <Bell className="w-4 h-4" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center font-bold">3</span>
        </button>

        {/* Avatar */}
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-sm font-bold text-white cursor-pointer">
          A
        </div>
      </div>
    </header>
  );
}
