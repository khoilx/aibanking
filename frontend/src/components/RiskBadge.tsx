type RiskCategory = 'Green' | 'Amber' | 'Red' | string;

interface RiskBadgeProps {
  category: RiskCategory;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

const categoryConfig = {
  Green: {
    label: 'Thấp',
    bg: 'bg-emerald-500/15',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    dot: 'bg-emerald-400',
  },
  Amber: {
    label: 'Trung bình',
    bg: 'bg-amber-500/15',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    dot: 'bg-amber-400',
  },
  Red: {
    label: 'Cao',
    bg: 'bg-red-500/15',
    border: 'border-red-500/30',
    text: 'text-red-400',
    dot: 'bg-red-400',
  },
};

const sizeMap = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

export default function RiskBadge({ category, score, size = 'md' }: RiskBadgeProps) {
  const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.Green;
  const sizeClass = sizeMap[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium border ${config.bg} ${config.border} ${config.text} ${sizeClass}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {score !== undefined ? `${config.label} (${score})` : config.label}
    </span>
  );
}
