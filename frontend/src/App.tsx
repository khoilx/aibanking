import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Sidebar from './components/Layout/Sidebar';
import TopBar from './components/Layout/TopBar';
import DashboardPage from './pages/DashboardPage';
import BranchPage from './pages/BranchPage';
import CustomerPage from './pages/CustomerPage';
import MisusePage from './pages/MisusePage';
import CasesPage from './pages/CasesPage';
import { Shield, Eye, EyeOff } from 'lucide-react';
import { login } from './api/client';

function LoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await login(username, password);
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('auth_user', JSON.stringify(response.user));
      window.location.href = '/';
    } catch (err) {
      setError('Đăng nhập thất bại. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500/20 border border-blue-500/30 mb-4">
            <Shield className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold text-white">Audit AI</h1>
          <p className="text-slate-400 mt-1">Hệ thống Kiểm toán Ngân hàng Thông minh</p>
        </div>

        {/* Login Form */}
        <div className="glass-card p-8 space-y-5">
          <h2 className="text-lg font-semibold text-white">Đăng nhập</h2>

          {/* Demo credentials hint */}
          <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 space-y-1">
            <div className="font-medium">Tài khoản demo:</div>
            <div className="font-mono">admin / admin123 (Quản trị viên)</div>
            <div className="font-mono">ktv_nguyenan / pass123 (Kiểm toán viên)</div>
            <div className="font-mono">manager_le / pass123 (Quản lý)</div>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1.5">Tên đăng nhập</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field w-full"
                placeholder="Nhập tên đăng nhập"
                required
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1.5">Mật khẩu</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field w-full pr-10"
                  placeholder="Nhập mật khẩu"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              ) : (
                'Đăng nhập'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Banking Audit AI System v1.0.0 - Confidential
        </p>
      </div>
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <TopBar />
        <main className="pt-20 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/branches"
          element={
            <ProtectedRoute>
              <BranchPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/branches/:branchId"
          element={
            <ProtectedRoute>
              <BranchPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/customers"
          element={
            <ProtectedRoute>
              <CustomerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/customers/:cif"
          element={
            <ProtectedRoute>
              <CustomerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/misuse"
          element={
            <ProtectedRoute>
              <MisusePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cases"
          element={
            <ProtectedRoute>
              <CasesPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
