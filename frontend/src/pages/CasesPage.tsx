import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList, Plus, Filter, AlertTriangle, Clock,
  CheckCircle, Loader, X, User, Calendar, ChevronRight
} from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { getCases, createCase, updateCase } from '../api/client';
import type { Case, CaseCreate } from '../types';

const STATUS_CONFIG = {
  todo: {
    label: 'Kế hoạch',
    color: 'blue',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    header: 'bg-blue-500/20 border-blue-500/30',
    icon: Clock,
  },
  in_progress: {
    label: 'Đang xử lý',
    color: 'amber',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    header: 'bg-amber-500/20 border-amber-500/30',
    icon: Loader,
  },
  pending_branch: {
    label: 'Chờ giải trình',
    color: 'orange',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/20',
    header: 'bg-orange-500/20 border-orange-500/30',
    icon: AlertTriangle,
  },
  closed: {
    label: 'Đóng',
    color: 'green',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    header: 'bg-emerald-500/20 border-emerald-500/30',
    icon: CheckCircle,
  },
};

const PRIORITY_CONFIG = {
  high: { label: 'Cao', bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
  medium: { label: 'Trung bình', bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  low: { label: 'Thấp', bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
};

type CaseStatus = 'todo' | 'in_progress' | 'pending_branch' | 'closed';

function CaseCard({ caseItem, onStatusChange }: { caseItem: Case; onStatusChange: () => void }) {
  const navigate = useNavigate();
  const priorityCfg = PRIORITY_CONFIG[caseItem.priority as keyof typeof PRIORITY_CONFIG] || PRIORITY_CONFIG.medium;
  const statuses: CaseStatus[] = ['todo', 'in_progress', 'pending_branch', 'closed'];

  const handleMove = async (newStatus: string) => {
    await updateCase(caseItem.case_id, { status: newStatus });
    onStatusChange();
  };

  return (
    <div className="glass-card p-4 space-y-3 cursor-pointer hover:border-white/20 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="text-xs font-mono text-slate-400">{caseItem.case_id}</div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${priorityCfg.bg} ${priorityCfg.text} ${priorityCfg.border}`}>
          {priorityCfg.label}
        </span>
      </div>

      {/* Customer */}
      <div onClick={() => navigate(`/customers/${caseItem.cif}`)}>
        <div className="text-sm font-semibold text-white hover:text-blue-400 transition-colors">
          {caseItem.customer_name}
        </div>
        <div className="text-xs text-slate-400 font-mono">{caseItem.cif}</div>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-300 line-clamp-2">{caseItem.description}</p>

      {/* Risk */}
      {caseItem.risk_category && (
        <RiskBadge category={caseItem.risk_category} score={caseItem.risk_score} size="sm" />
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-white/5">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <User className="w-3 h-3" />
          {caseItem.assigned_to || 'Chưa giao'}
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Calendar className="w-3 h-3" />
          {caseItem.created_date}
        </div>
      </div>

      {/* Move Buttons */}
      <div className="flex gap-1 flex-wrap">
        {statuses.filter(s => s !== caseItem.status).map(s => (
          <button
            key={s}
            onClick={(e) => { e.stopPropagation(); handleMove(s); }}
            className="text-xs px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all border border-white/5"
          >
            → {STATUS_CONFIG[s].label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterAssigned, setFilterAssigned] = useState('');
  const [newCase, setNewCase] = useState<CaseCreate>({
    cif: '',
    description: '',
    priority: 'medium',
    assigned_to: '',
  });

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await getCases({
        status: filterStatus || undefined,
        priority: filterPriority || undefined,
        assigned_to: filterAssigned || undefined,
        page_size: 200,
      });
      setCases(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [filterStatus, filterPriority, filterAssigned]);

  const casesByStatus = (status: CaseStatus) => cases.filter(c => c.status === status);

  const handleCreate = async () => {
    if (!newCase.cif || !newCase.description) return;
    await createCase(newCase);
    setShowModal(false);
    setNewCase({ cif: '', description: '', priority: 'medium', assigned_to: '' });
    fetchCases();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header Bar */}
      <div className="glass-card p-4 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Filter className="w-4 h-4" />
          <span>Lọc:</span>
        </div>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="input-field text-sm py-1.5"
        >
          <option value="">Tất cả độ ưu tiên</option>
          <option value="high">Cao</option>
          <option value="medium">Trung bình</option>
          <option value="low">Thấp</option>
        </select>
        <select
          value={filterAssigned}
          onChange={(e) => setFilterAssigned(e.target.value)}
          className="input-field text-sm py-1.5"
        >
          <option value="">Tất cả người phụ trách</option>
          <option value="ktv_nguyenan">Nguyễn An</option>
          <option value="ktv_tranthi">Trần Thị Bích</option>
          <option value="ktv_pham">Phạm Văn Kiểm</option>
        </select>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-slate-400">{total} case tổng</span>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary"
          >
            <Plus className="w-4 h-4" />
            Tạo Case mới
          </button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-4 gap-4">
        {(['todo', 'in_progress', 'pending_branch', 'closed'] as CaseStatus[]).map((status) => {
          const cfg = STATUS_CONFIG[status];
          const Icon = cfg.icon;
          const statusCases = casesByStatus(status);

          return (
            <div key={status} className="space-y-3">
              {/* Column Header */}
              <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${cfg.header}`}>
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${
                      cfg.color === 'blue' ? 'text-blue-400' :
                      cfg.color === 'amber' ? 'text-amber-400' :
                      cfg.color === 'orange' ? 'text-orange-400' : 'text-emerald-400'
                    }`}
                  />
                  <span className="text-sm font-semibold text-white">{cfg.label}</span>
                </div>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  cfg.color === 'blue' ? 'bg-blue-500/30 text-blue-300' :
                  cfg.color === 'amber' ? 'bg-amber-500/30 text-amber-300' :
                  cfg.color === 'orange' ? 'bg-orange-500/30 text-orange-300' :
                  'bg-emerald-500/30 text-emerald-300'
                }`}>
                  {statusCases.length}
                </span>
              </div>

              {/* Case Cards */}
              <div className="space-y-3">
                {statusCases.map((c) => (
                  <CaseCard key={c.case_id} caseItem={c} onStatusChange={fetchCases} />
                ))}
                {statusCases.length === 0 && (
                  <div className="text-center py-8 text-slate-500 text-sm">
                    Không có case
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Case Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
          <div className="glass-card-light bg-slate-800 border border-white/20 p-6 w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Tạo Case mới</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">CIF Khách hàng *</label>
                <input
                  type="text"
                  placeholder="VD: CIF_MINHPHAT"
                  value={newCase.cif}
                  onChange={(e) => setNewCase({ ...newCase, cif: e.target.value })}
                  className="input-field w-full"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Mô tả *</label>
                <textarea
                  placeholder="Mô tả chi tiết vấn đề cần kiểm tra..."
                  value={newCase.description}
                  onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
                  className="input-field w-full h-24 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Độ ưu tiên</label>
                  <select
                    value={newCase.priority}
                    onChange={(e) => setNewCase({ ...newCase, priority: e.target.value })}
                    className="input-field w-full"
                  >
                    <option value="high">Cao</option>
                    <option value="medium">Trung bình</option>
                    <option value="low">Thấp</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Người phụ trách</label>
                  <select
                    value={newCase.assigned_to || ''}
                    onChange={(e) => setNewCase({ ...newCase, assigned_to: e.target.value })}
                    className="input-field w-full"
                  >
                    <option value="">Chưa giao</option>
                    <option value="ktv_nguyenan">Nguyễn An</option>
                    <option value="ktv_tranthi">Trần Thị Bích</option>
                    <option value="ktv_pham">Phạm Văn Kiểm</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">
                Hủy
              </button>
              <button onClick={handleCreate} className="btn-primary flex-1 justify-center">
                <Plus className="w-4 h-4" />
                Tạo Case
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
