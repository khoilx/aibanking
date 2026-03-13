import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: number;
  trendLabel?: string;
  color?: 'blue' | 'red' | 'amber' | 'green' | 'purple';
  alert?: boolean;
}

const colorMap = {
  blue: {
    bg: 'from-blue-500/20 to-blue-600/10',
    border: 'border-blue-500/20',
    icon: 'bg-blue-500/20 text-blue-400',
    text: 'text-blue-400',
  },
  red: {
    bg: 'from-red-500/20 to-red-600/10',
    border: 'border-red-500/20',
    icon: 'bg-red-500/20 text-red-400',
    text: 'text-red-400',
  },
  amber: {
    bg: 'from-amber-500/20 to-amber-600/10',
    border: 'border-amber-500/20',
    icon: 'bg-amber-500/20 text-amber-400',
    text: 'text-amber-400',
  },
  green: {
    bg: 'from-emerald-500/20 to-emerald-600/10',
    border: 'border-emerald-500/20',
    icon: 'bg-emerald-500/20 text-emerald-400',
    text: 'text-emerald-400',
  },
  purple: {
    bg: 'from-purple-500/20 to-purple-600/10',
    border: 'border-purple-500/20',
    icon: 'bg-purple-500/20 text-purple-400',
    text: 'text-purple-400',
  },
};

export default function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendLabel,
  color = 'blue',
  alert = false,
}: KPICardProps) {
  const colors = colorMap[color];

  const TrendIcon = trend === undefined ? Minus : trend > 0 ? TrendingUp : TrendingDown;
  const trendColor = trend === undefined ? 'text-slate-400'
    : trend > 0 ? (alert ? 'text-red-400' : 'text-emerald-400')
    : (alert ? 'text-emerald-400' : 'text-red-400');

  return (
    <div className={`glass-card bg-gradient-to-br ${colors.bg} border ${colors.border} p-5 transition-all duration-300 hover:scale-[1.01] hover:shadow-xl`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl ${colors.icon} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trendColor}`}>
            <TrendIcon className="w-3 h-3" />
            <span>{Math.abs(trend).toFixed(1)}%</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm font-medium text-slate-300">{title}</div>
        {subtitle && (
          <div className="text-xs text-slate-400">{subtitle}</div>
        )}
        {trendLabel && (
          <div className={`text-xs ${trendColor}`}>{trendLabel}</div>
        )}
      </div>
    </div>
  );
}
