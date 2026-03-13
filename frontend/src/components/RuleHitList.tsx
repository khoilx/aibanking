import { AlertTriangle, AlertCircle, Info, ShieldAlert } from 'lucide-react';
import type { RuleHit } from '../types';

interface RuleHitListProps {
  rules: RuleHit[];
  compact?: boolean;
}

const severityConfig = {
  high: {
    icon: ShieldAlert,
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    text: 'text-red-400',
    badge: 'bg-red-500/20 text-red-400',
    label: 'Cao',
  },
  medium: {
    icon: AlertTriangle,
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    text: 'text-amber-400',
    badge: 'bg-amber-500/20 text-amber-400',
    label: 'Trung bình',
  },
  low: {
    icon: Info,
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    text: 'text-blue-400',
    badge: 'bg-blue-500/20 text-blue-400',
    label: 'Thấp',
  },
};

export default function RuleHitList({ rules, compact = false }: RuleHitListProps) {
  if (rules.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
        <p className="text-sm">Không có vi phạm quy tắc nào</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {rules.map((rule, index) => {
        const config = severityConfig[rule.severity as keyof typeof severityConfig] || severityConfig.low;
        const Icon = config.icon;

        if (compact) {
          return (
            <div key={index} className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg} border ${config.border}`}>
              <Icon className={`w-4 h-4 ${config.text} flex-shrink-0`} />
              <span className="text-sm text-slate-200 flex-1">{rule.description}</span>
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${config.badge}`}>+{rule.points}</span>
            </div>
          );
        }

        return (
          <div key={index} className={`flex items-start gap-3 p-4 rounded-xl ${config.bg} border ${config.border}`}>
            <div className={`w-8 h-8 rounded-lg ${config.badge} flex items-center justify-center flex-shrink-0`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono font-bold text-slate-400">{rule.rule_id}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${config.badge} font-medium`}>
                  {config.label}
                </span>
              </div>
              <p className="text-sm text-slate-200">{rule.description}</p>
            </div>
            <div className={`text-lg font-bold ${config.text} flex-shrink-0`}>+{rule.points}</div>
          </div>
        );
      })}
    </div>
  );
}
