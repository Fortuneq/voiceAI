import React from 'react';
import { MetricCard } from '../ui/MetricCard';
import { PerformanceChart } from '../ui/PerformanceChart';
import type { Manager, PerformanceMetric } from '../../types';

interface MainContentProps {
  metrics: PerformanceMetric[];
  managers: Manager[];
  selectedManager: Manager | null;
  isLoading: boolean;
}

export const MainContent: React.FC<MainContentProps> = ({
  metrics,
  managers,
  selectedManager,
  isLoading,
}) => {
  console.log('MainContent received:', { metrics, managers, selectedManager, isLoading });
  // Filter metrics for selected manager or show overall metrics
  const displayMetrics = selectedManager 
    ? metrics.map(metric => ({
        ...metric,
        // Simulate manager-specific metrics by adjusting values
        value: Math.max(0, Math.min(100, metric.value + (Math.random() - 0.5) * 20)),
      }))
    : metrics;

  // Prepare chart data for top performers
  const chartData = managers
    .sort((a, b) => b.aiScore - a.aiScore)
    .slice(0, 8)
    .map(manager => ({
      label: manager.name.split(' ')[0], // First name only for chart
      value: manager.aiScore,
      color: manager.aiScore >= 90 ? '#10b981' : manager.aiScore >= 80 ? '#3b82f6' : '#f59e0b',
    }));

  const LoadingSkeleton = () => (
    <div className="space-y-6">
      {/* Metrics Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-100 p-6 rounded-lg">
              <div className="w-24 h-4 bg-gray-300 rounded mb-4"></div>
              <div className="w-16 h-8 bg-gray-300 rounded mb-2"></div>
              <div className="w-20 h-3 bg-gray-300 rounded"></div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Chart Skeleton */}
      <div className="animate-pulse">
        <div className="bg-gray-100 p-6 rounded-lg">
          <div className="w-48 h-6 bg-gray-300 rounded mb-6"></div>
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="w-20 h-4 bg-gray-300 rounded"></div>
                <div className="flex-1 h-6 bg-gray-300 rounded"></div>
                <div className="w-8 h-4 bg-gray-300 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          {selectedManager ? (
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {selectedManager.name}
                </h1>
                <p className="text-gray-600">
                  Детальная статистика по менеджеру
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {selectedManager.aiScore}
                  </div>
                  <div className="text-xs text-gray-500">AI Оценка</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {selectedManager.checklistScore}
                  </div>
                  <div className="text-xs text-gray-500">Чек-лист</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-700">
                    {selectedManager.callsAnalyzed}
                  </div>
                  <div className="text-xs text-gray-500">Звонков</div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Общая статистика
              </h1>
              <p className="text-gray-600">
                Производительность всех менеджеров
              </p>
            </div>
          )}
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <div className="space-y-8">
            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {displayMetrics.map((metric) => (
                <MetricCard
                  key={metric.id}
                  metric={metric}
                  className="hover:shadow-lg transition-shadow"
                />
              ))}
            </div>

            {/* Performance Chart */}
            {!selectedManager && (
              <div className="bg-white rounded-lg shadow-sm">
                <PerformanceChart
                  data={chartData}
                  title="Топ менеджеров по AI оценке"
                  className="p-6"
                />
              </div>
            )}

            {/* Additional Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Summary Stats */}
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Сводная статистика
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Средняя AI оценка</span>
                    <span className="font-semibold text-gray-900">
                      {(managers.reduce((sum, m) => sum + m.aiScore, 0) / managers.length || 0).toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Средняя оценка чек-листа</span>
                    <span className="font-semibold text-gray-900">
                      {(managers.reduce((sum, m) => sum + m.checklistScore, 0) / managers.length || 0).toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Всего звонков</span>
                    <span className="font-semibold text-gray-900">
                      {managers.reduce((sum, m) => sum + m.callsAnalyzed, 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Активных менеджеров</span>
                    <span className="font-semibold text-gray-900">
                      {managers.length}
                    </span>
                  </div>
                </div>
              </div>

              {/* Trends */}
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Тренды производительности
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Растут</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600 font-semibold">
                        {managers.filter(m => m.trend === 'up').length}
                      </span>
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Стабильны</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-600 font-semibold">
                        {managers.filter(m => m.trend === 'stable').length}
                      </span>
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Снижаются</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-red-600 font-semibold">
                        {managers.filter(m => m.trend === 'down').length}
                      </span>
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};