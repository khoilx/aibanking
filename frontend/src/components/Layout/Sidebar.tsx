import { NavLink, useLocation } from 'react-router-dom';
import {
  Shield, LayoutDashboard, Building2, Users,
  AlertTriangle, ClipboardList, LogOut, ChevronRight
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { path: '/branches', label: 'Chi nhánh', icon: Building2 },
  { path: '/customers', label: 'Khách hàng', icon: Users },
  { path: '/misuse', label: 'Phân tích Sai mục đích', icon: AlertTriangle },
  { path: '/cases', label: 'Quản lý Case', icon: ClipboardList },
];

export default function Sidebar() {
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('auth_user') || '{}');

  return (
    <aside className="fixed left-0 top-0 h-full w-64 flex flex-col z-50"
      style={{
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)'
      }}>

      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
        <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
          <Shield className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <div className="font-bold text-white text-lg leading-tight">Audit AI</div>
          <div className="text-xs text-slate-400">Kiểm toán Ngân hàng</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 mb-3">
          Chức năng chính
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.exact
            ? location.pathname === item.path
            : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="flex-1 text-sm font-medium">{item.label}</span>
              {isActive && <ChevronRight className="w-4 h-4 opacity-50" />}
            </NavLink>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="px-3 py-4 border-t border-white/5">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-sm font-bold text-white">
            {(user.full_name || user.username || 'A')[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">
              {user.full_name || user.username || 'Admin'}
            </div>
            <div className="text-xs text-slate-400 capitalize">{user.role || 'admin'}</div>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
              window.location.href = '/login';
            }}
            className="text-slate-400 hover:text-red-400 transition-colors"
            title="Đăng xuất"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
