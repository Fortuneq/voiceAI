import React from 'react';
import { clsx } from 'clsx';
import { ProgressBar } from './ProgressBar';
import { CheckCircle, AlertTriangle, XCircle, Target } from 'lucide-react';
import type { ChecklistCriteriaDetail } from '../../types';

interface DetailedCriteriaCardProps {
  criteria: ChecklistCriteriaDetail;
  className?: string;
}

export const DetailedCriteriaCard: React.FC<DetailedCriteriaCardProps> = ({
  criteria,
  className,
}) => {
  const getIcon = () => {
    if (criteria.percentage >= 80) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    } else if (criteria.percentage >= 60) {
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    } else {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getColorVariant = (): 'success' | 'primary' | 'warning' | 'danger' => {
    if (criteria.percentage >= 80) {
      return 'success';
    } else if (criteria.percentage >= 60) {
      return 'warning';
    } else {
      return 'danger';
    }
  };

  const getBorderColor = () => {
    if (criteria.percentage >= 80) {
      return 'border-green-200 hover:border-green-300 bg-green-50';
    } else if (criteria.percentage >= 60) {
      return 'border-yellow-200 hover:border-yellow-300 bg-yellow-50';
    } else {
      return 'border-red-200 hover:border-red-300 bg-red-50';
    }
  };

  const getTextColor = () => {
    if (criteria.percentage >= 80) {
      return 'text-green-700';
    } else if (criteria.percentage >= 60) {
      return 'text-yellow-700';
    } else {
      return 'text-red-700';
    }
  };

  return (
    <div className={clsx(
      'rounded-lg p-4 border transition-all duration-200 hover:shadow-sm',
      getBorderColor(),
      className
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-2 flex-1">
          {getIcon()}
          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-medium text-gray-900 leading-5">
              {criteria.criteria_name}
            </h4>
            <p className="text-xs text-gray-500 mt-1">
              Стадия: {criteria.stage}
            </p>
          </div>
        </div>
        
        <div className="text-right ml-3">
          <div className={clsx('text-lg font-bold', getTextColor())}>
            {criteria.percentage.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            выполнение
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <ProgressBar
          value={criteria.percentage}
          max={100}
          color={getColorVariant()}
          size="sm"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-1">
            <Target className="w-3 h-3 text-gray-400" />
            <span className="text-sm font-semibold text-gray-900">
              {criteria.average_score.toFixed(2)}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Средний балл
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm font-semibold text-gray-600">
            {criteria.max_score.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">
            Максимум
          </div>
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="mt-3 text-center">
        <span className={clsx(
          'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
          criteria.percentage >= 80 ? 'bg-green-100 text-green-800' :
          criteria.percentage >= 60 ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        )}>
          {criteria.percentage >= 80 ? 'Отлично' :
           criteria.percentage >= 60 ? 'Хорошо' :
           'Требует внимания'}
        </span>
      </div>
    </div>
  );
};