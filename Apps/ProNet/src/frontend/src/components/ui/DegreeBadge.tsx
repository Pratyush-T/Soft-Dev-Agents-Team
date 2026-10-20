import React from 'react';
import { DegreeType } from '../../types/api';

export interface DegreeBadgeProps {
  degree: DegreeType;
  className?: string;
}

export const DegreeBadge: React.FC<DegreeBadgeProps> = ({ degree, className = '' }) => {
  const badgeStyles = {
    '1st': 'bg-emerald-50 text-emerald-700 border border-emerald-300',
    '2nd': 'bg-blue-50 text-blue-700 border border-blue-300',
    '3rd+': 'bg-surface-100 text-surface-600 border border-surface-300',
  };

  return (
    <span
      className={`inline-flex items-center text-[11px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wider select-none ${badgeStyles[degree] || badgeStyles['3rd+']} ${className}`}
      title={`${degree} Degree Connection`}
    >
      {degree}
    </span>
  );
};
