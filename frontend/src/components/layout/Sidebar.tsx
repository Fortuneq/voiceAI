import React, { useState, useMemo } from 'react';
import { Search, TrendingUp, TrendingDown, Minus, ChevronUp, ChevronDown } from 'lucide-react';
import type { Manager, SortConfig } from '../../types';

interface SidebarProps {
  managers: Manager[];
  selectedManager: Manager | null;
  onManagerSelect: (manager: Manager) => void;
  isLoading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  managers,
  selectedManager,
  onManagerSelect,
  isLoading,
}) => {
  console.log('Sidebar received managers:', managers, 'isLoading:', isLoading);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'aiScore',
    direction: 'desc',
  });

  const handleSort = (key: keyof Manager) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  const filteredAndSortedManagers = useMemo(() => {
    let filtered = managers.filter(manager =>
      manager.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc'
          ? aValue - bValue
          : bValue - aValue;
      }

      return 0;
    });
  }, [managers, searchTerm, sortConfig]);

  const getTrendIcon = (trend: Manager['trend']) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      case 'stable':
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 80) return 'text-blue-600 bg-blue-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const SortIcon: React.FC<{ column: keyof Manager }> = ({ column }) => {
    if (sortConfig.key !== column) {
      return <ChevronUp className="w-4 h-4 text-gray-300" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp className="w-4 h-4 text-gray-600" />
      : <ChevronDown className="w-4 h-4 text-gray-600" />;
  };

  const LoadingSkeleton = () => (
    <div className="space-y-3">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="flex items-center justify-between p-3 bg-gray-100 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
              <div className="space-y-1">
                <div className="w-24 h-4 bg-gray-300 rounded"></div>
                <div className="w-16 h-3 bg-gray-300 rounded"></div>
              </div>
            </div>
            <div className="w-8 h-8 bg-gray-300 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Менеджеры ({managers.length})
        </h2>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Поиск менеджера..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Sort Controls */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center justify-between text-xs">
          <button
            onClick={() => handleSort('aiScore')}
            className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span>AI Оценка</span>
            <SortIcon column="aiScore" />
          </button>
          <button
            onClick={() => handleSort('checklistScore')}
            className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span>Чек-лист</span>
            <SortIcon column="checklistScore" />
          </button>
          <button
            onClick={() => handleSort('name')}
            className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span>Имя</span>
            <SortIcon column="name" />
          </button>
        </div>
      </div>

      {/* Managers List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          filteredAndSortedManagers.map((manager) => (
            <button
              key={manager.id}
              onClick={() => onManagerSelect(manager)}
              className={`w-full text-left p-3 rounded-lg border transition-all hover:shadow-sm ${
                selectedManager?.id === manager.id
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-medium text-gray-900 truncate">
                      {manager.name}
                    </h3>
                    {getTrendIcon(manager.trend)}
                  </div>
                  
                  <div className="mt-2 flex items-center space-x-3">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs text-gray-500">AI:</span>
                      <span className={`text-xs font-medium px-2 py-1 rounded ${getScoreColor(manager.aiScore)}`}>
                        {Number(manager.aiScore).toFixed(1)}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <span className="text-xs text-gray-500">Ч-Л:</span>
                      <span className={`text-xs font-medium px-2 py-1 rounded ${getScoreColor(manager.checklistScore)}`}>
                        {Number(manager.checklistScore).toFixed(1)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-1 text-xs text-gray-500">
                    {manager.callsAnalyzed} звонков
                  </div>
                </div>
              </div>
            </button>
          ))
        )}
        
        {!isLoading && filteredAndSortedManagers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Search className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p>Менеджеры не найдены</p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
              >
                Очистить поиск
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};