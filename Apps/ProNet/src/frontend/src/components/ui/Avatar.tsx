import React, { useState } from 'react';

export interface AvatarProps {
  src: string | null;
  alt: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isOnline?: boolean;
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  size = 'md',
  isOnline = false,
  className = '',
}) => {
  const [hasError, setHasError] = useState(false);

  const sizeClasses = {
    xs: 'w-6 h-6 text-[10px]',
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-[72px] h-[72px] text-2xl font-bold',
  };

  const dotSizes = {
    xs: 'w-2 h-2 border',
    sm: 'w-2.5 h-2.5 border',
    md: 'w-3 h-3 border-2',
    lg: 'w-3.5 h-3.5 border-2',
    xl: 'w-4 h-4 border-2',
  };

  const getInitials = (name: string): string => {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <div className={`relative inline-block shrink-0 ${className}`}>
      {src && !hasError ? (
        <img
          src={src}
          alt={alt}
          onError={() => setHasError(true)}
          className={`${sizeClasses[size]} rounded-full object-cover border border-surface-200 bg-surface-100`}
        />
      ) : (
        <div
          className={`${sizeClasses[size]} rounded-full bg-brand-100 text-brand-800 font-semibold flex items-center justify-center border border-brand-200 select-none`}
        >
          {getInitials(alt)}
        </div>
      )}

      {isOnline && (
        <span
          className={`absolute bottom-0 right-0 ${dotSizes[size]} bg-success-600 border-white rounded-full`}
          title="Online"
        />
      )}
    </div>
  );
};
