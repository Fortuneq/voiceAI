import React from 'react';
import { User, Bell, Settings, Activity } from 'lucide-react';
import type { CallMetrics } from '../../types';

interface HeaderProps {
  callMetrics: CallMetrics | null;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ callMetrics, isLoading }) => {
  const formatLastUpdated = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                VoiceAI Dashboard
              </h1>
              <p className="text-sm text-gray-500">
                Анализ звонков и производительность менеджеров
              </p>
            </div>
          </div>
        </div>

        {/* Status Info */}
        <div className="hidden md:flex items-center space-x-6">
          {isLoading ? (
            <div className="flex items-center space-x-2 text-gray-500">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
              <span className="text-sm">Загрузка данных...</span>
            </div>
          ) : callMetrics ? (
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-gray-600">
                  Обработано: <span className="font-medium text-gray-900">{callMetrics.processedCalls}</span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span className="text-gray-600">
                  В очереди: <span className="font-medium text-gray-900">{callMetrics.pendingCalls}</span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <span className="text-gray-600">
                  Обновлено: <span className="font-medium text-gray-900">{formatLastUpdated(callMetrics.lastUpdated)}</span>
                </span>
              </div>
            </div>
          ) : null}
        </div>

        {/* User Actions */}
        <div className="flex items-center space-x-3">
          <button 
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Уведомления"
          >
            <Bell className="w-5 h-5" />
          </button>
          
          <button 
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Настройки"
          >
            <Settings className="w-5 h-5" />
          </button>
          
          <div className="h-6 w-px bg-gray-200"></div>
          
          <button className="flex items-center space-x-3 p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-gray-900">Администратор</p>
              <p className="text-xs text-gray-500">admin@voiceai.ru</p>
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Status Info */}
      {!isLoading && callMetrics && (
        <div className="md:hidden mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Обработано: {callMetrics.processedCalls}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span>В очереди: {callMetrics.pendingCalls}</span>
            </div>
            <span className="text-gray-500">
              {formatLastUpdated(callMetrics.lastUpdated)}
            </span>
          </div>
        </div>
      )}
    </header>
  );
};