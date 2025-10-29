import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target } from 'lucide-react';
import { clsx } from 'clsx';
import { ProgressBar } from './ProgressBar';
import type { MetricCardProps } from '../../types';

export const MetricCard: React.FC<MetricCardProps> = ({ metric, className }) => {
  const getTrendIcon = () => {
    switch (metric.trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      case 'stable':
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendColor = () => {
    switch (metric.trend) {
      case 'up':
        return 'text-green-600 bg-green-50';
      case 'down':
        return 'text-red-600 bg-red-50';
      case 'stable':
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getValueColor = (): 'success' | 'warning' | 'danger' => {
    const percentage = (metric.value / metric.target) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 70) return 'warning';
    return 'danger';
  };

  const getCategoryColor = () => {
    const colors = {
      rapport: 'bg-blue-100 text-blue-800',
      budget: 'bg-green-100 text-green-800',
      presentation: 'bg-purple-100 text-purple-800',
      objection: 'bg-orange-100 text-orange-800',
      close: 'bg-red-100 text-red-800',
      'follow-up': 'bg-yellow-100 text-yellow-800',
    };
    return colors[metric.category] || 'bg-gray-100 text-gray-800';
  };

  const percentage = (metric.value / metric.target) * 100;

  return (
    <div className={clsx(
      'bg-white rounded-lg p-6 shadow-sm border border-gray-200 transition-all duration-200 hover:shadow-md',
      className
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-700 mb-1">
            {metric.title}
          </h3>
          <span className={clsx(
            'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
            getCategoryColor()
          )}>
            {metric.category}
          </span>
        </div>
        
        <div className={clsx(
          'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
          getTrendColor()
        )}>
          {getTrendIcon()}
        </div>
      </div>

      {/* Value Display */}
      <div className="space-y-3">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-3xl font-bold text-gray-900">
              {Number(metric.value).toFixed(1)}%
            </div>
            <div className="flex items-center text-sm text-gray-500 mt-1">
              <Target className="w-3 h-3 mr-1" />
              <span>Цель: {Number(metric.target).toFixed(1)}%</span>
            </div>
          </div>
          
          <div className="text-right">
            <div className={clsx(
              'text-sm font-medium',
              percentage >= 100 ? 'text-green-600' : 
              percentage >= 90 ? 'text-blue-600' : 
              percentage >= 70 ? 'text-yellow-600' : 'text-red-600'
            )}>
              {percentage >= 100 ? '+' : ''}{(percentage - 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">
              от цели
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <ProgressBar
          value={metric.value}
          max={metric.target}
          color={getValueColor()}
          size="md"
        />

        {/* Additional Info */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
          <span>Текущий результат</span>
          <span>
            {metric.value > metric.target ? 'Превышена цель' : 
             percentage >= 90 ? 'Близко к цели' :
             percentage >= 70 ? 'Требует внимания' : 'Критический уровень'}
          </span>
        </div>
      </div>
    </div>
  );
};