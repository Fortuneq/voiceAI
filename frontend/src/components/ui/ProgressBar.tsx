import React from 'react';
import { clsx } from 'clsx';
import type { ProgressBarProps } from '../../types';

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  color = 'primary',
  size = 'md',
  showValue = false,
  className,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const colorClasses = {
    primary: 'bg-blue-600',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
  };

  const backgroundColorClasses = {
    primary: 'bg-blue-100',
    success: 'bg-green-100',
    warning: 'bg-yellow-100',
    danger: 'bg-red-100',
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={clsx('w-full', className)}>
      {showValue && (
        <div className="flex justify-between items-center mb-1">
          <span className={clsx('font-medium text-gray-700', textSizeClasses[size])}>
            {value}
          </span>
          <span className={clsx('text-gray-500', textSizeClasses[size])}>
            {max}
          </span>
        </div>
      )}
      
      <div
        className={clsx(
          'w-full rounded-full overflow-hidden',
          backgroundColorClasses[color],
          sizeClasses[size]
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={`Progress: ${value} of ${max}`}
      >
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-300 ease-out',
            colorClasses[color]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      {showValue && (
        <div className="mt-1 text-right">
          <span className={clsx('text-gray-500', textSizeClasses[size])}>
            {percentage.toFixed(0)}%
          </span>
        </div>
      )}
    </div>
  );
};