import React from 'react';
import { clsx } from 'clsx';
import { ProgressBar } from './ProgressBar';
import type { PerformanceChartProps } from '../../types';

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  title,
  className,
}) => {
  const maxValue = Math.max(...data.map(item => item.value));
  
  const getColorVariant = (value: number): 'success' | 'primary' | 'warning' | 'danger' => {
    if (value >= 90) return 'success';
    if (value >= 80) return 'primary';
    if (value >= 70) return 'warning';
    return 'danger';
  };

  const getRankSuffix = (index: number) => {
    const rank = index + 1;
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Title */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="text-sm text-gray-500">
          Всего менеджеров: {data.length}
        </div>
      </div>

      {/* Chart */}
      <div className="space-y-4">
        {data.map((item, index) => (
          <div
            key={`${item.label}-${index}`}
            className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {/* Rank */}
            <div className="flex-shrink-0 w-8 text-center">
              <span className="text-sm font-medium text-gray-600">
                {getRankSuffix(index)}
              </span>
            </div>

            {/* Manager Name */}
            <div className="flex-shrink-0 w-24">
              <div className="text-sm font-medium text-gray-900 truncate">
                {item.label}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="flex-1 px-2">
              <ProgressBar
                value={item.value}
                max={maxValue}
                color={getColorVariant(item.value)}
                size="md"
              />
            </div>

            {/* Score */}
            <div className="flex-shrink-0 w-12 text-right">
              <span className={clsx(
                'text-sm font-bold',
                item.value >= 90 ? 'text-green-600' :
                item.value >= 80 ? 'text-blue-600' :
                item.value >= 70 ? 'text-yellow-600' : 'text-red-600'
              )}>
                {Number(item.value).toFixed(1)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-xs text-gray-600">90+ Отлично</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
          <span className="text-xs text-gray-600">80-89 Хорошо</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <span className="text-xs text-gray-600">70-79 Нормально</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-xs text-gray-600">&lt;70 Требует внимания</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-900">
              {(data.reduce((sum, item) => sum + item.value, 0) / data.length || 0).toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">Средний балл</div>
          </div>
          <div>
            <div className="text-lg font-bold text-green-600">
              {data.filter(item => item.value >= 80).length}
            </div>
            <div className="text-xs text-gray-500">Высокий результат</div>
          </div>
          <div>
            <div className="text-lg font-bold text-red-600">
              {data.filter(item => item.value < 70).length}
            </div>
            <div className="text-xs text-gray-500">Требует внимания</div>
          </div>
        </div>
      </div>
    </div>
  );
};