import React from 'react';
import { clsx } from 'clsx';
import { ProgressBar } from './ProgressBar';
import { CheckCircle, AlertTriangle, XCircle, ChevronRight } from 'lucide-react';
import type { ChecklistStageDetail } from '../../types';

interface ChecklistStageCardProps {
  stage: ChecklistStageDetail;
  onStageClick?: (stage: ChecklistStageDetail) => void;
  showDetails?: boolean;
  className?: string;
}

export const ChecklistStageCard: React.FC<ChecklistStageCardProps> = ({
  stage,
  onStageClick,
  showDetails = false,
  className,
}) => {
  const getIcon = () => {
    switch (stage.color) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'danger':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getColorVariant = (): 'success' | 'primary' | 'warning' | 'danger' => {
    switch (stage.color) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'danger':
        return 'danger';
      default:
        return 'primary';
    }
  };

  const getBorderColor = () => {
    switch (stage.color) {
      case 'success':
        return 'border-green-200 hover:border-green-300';
      case 'warning':
        return 'border-yellow-200 hover:border-yellow-300';
      case 'danger':
        return 'border-red-200 hover:border-red-300';
      default:
        return 'border-gray-200 hover:border-gray-300';
    }
  };

  const handleClick = () => {
    if (onStageClick) {
      onStageClick(stage);
    }
  };

  return (
    <div 
      className={clsx(
        'bg-white rounded-lg p-6 border transition-all duration-200 hover:shadow-md',
        getBorderColor(),
        onStageClick && 'cursor-pointer hover:bg-gray-50',
        className
      )}
      onClick={handleClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {stage.stage_name}
            </h3>
            <p className="text-sm text-gray-500">
              {stage.criteria_count} критериев
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className={clsx(
              'text-2xl font-bold',
              stage.color === 'success' ? 'text-green-600' :
              stage.color === 'warning' ? 'text-yellow-600' :
              stage.color === 'danger' ? 'text-red-600' : 'text-gray-600'
            )}>
              {stage.percentage.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              эффективность
            </div>
          </div>
          
          {onStageClick && (
            <ChevronRight className={clsx(
              'w-5 h-5 transition-transform duration-200',
              showDetails ? 'rotate-90' : '',
              stage.color === 'success' ? 'text-green-500' :
              stage.color === 'warning' ? 'text-yellow-500' :
              stage.color === 'danger' ? 'text-red-500' : 'text-gray-400'
            )} />
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <ProgressBar
          value={stage.percentage}
          max={100}
          color={getColorVariant()}
          size="md"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {stage.stage_total.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">
            Средний балл
          </div>
        </div>
        <div>
          <div className="text-lg font-semibold text-gray-600">
            {stage.max_possible.toFixed(0)}
          </div>
          <div className="text-xs text-gray-500">
            Максимум
          </div>
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="mt-4 text-center">
        <span className={clsx(
          'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium',
          stage.color === 'success' ? 'bg-green-50 text-green-700' :
          stage.color === 'warning' ? 'bg-yellow-50 text-yellow-700' :
          stage.color === 'danger' ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-700'
        )}>
          {stage.percentage >= 80 ? 'Отличный результат' :
           stage.percentage >= 60 ? 'Хороший результат' :
           'Требует улучшения'}
        </span>
      </div>
    </div>
  );
};