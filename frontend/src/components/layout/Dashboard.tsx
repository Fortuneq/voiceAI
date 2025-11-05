import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { ApiService } from '../../services/api';
import type { Manager, PerformanceMetric, CallMetrics, ChecklistStageDetail } from '../../types';

export const Dashboard: React.FC = () => {
  const [managers, setManagers] = useState<Manager[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [callMetrics, setCallMetrics] = useState<CallMetrics | null>(null);
  const [checklistStages, setChecklistStages] = useState<ChecklistStageDetail[]>([]);
  const [selectedManager, setSelectedManager] = useState<Manager | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [managersRes, metricsRes, callMetricsRes, checklistRes] = await Promise.all([
          ApiService.getManagersStats(),
          ApiService.getPerformanceMetrics(),
          ApiService.getCallMetrics(),
          ApiService.getChecklistStages(30),
        ]);

        console.log('API Responses:', { managersRes, metricsRes, callMetricsRes, checklistRes });

        // Set managers data (even if it's mock data on API failure)
        if (managersRes.data && managersRes.data.managers) {
          console.log('Setting managers:', managersRes.data.managers, 'success:', managersRes.success);
          setManagers(managersRes.data.managers);
          if (!managersRes.success) {
            console.warn('Using mock data for managers:', managersRes.message);
          }
        } else {
          console.error('Failed to load managers:', managersRes.message);
        }

        // Set metrics data (even if it's mock data on API failure)
        if (metricsRes.data) {
          console.log('Setting metrics:', metricsRes.data, 'success:', metricsRes.success);
          setMetrics(metricsRes.data);
          if (!metricsRes.success) {
            console.warn('Using mock data for metrics:', metricsRes.message);
          }
        } else {
          console.error('Failed to load metrics:', metricsRes.message);
        }

        // Set call metrics data (even if it's mock data on API failure)
        if (callMetricsRes.data) {
          console.log('Setting call metrics:', callMetricsRes.data, 'success:', callMetricsRes.success);
          setCallMetrics(callMetricsRes.data);
          if (!callMetricsRes.success) {
            console.warn('Using mock data for call metrics:', callMetricsRes.message);
          }
        } else {
          console.error('Failed to load call metrics:', callMetricsRes.message);
        }

        // Set checklist stages data
        if (checklistRes.data) {
          console.log('Setting checklist stages:', checklistRes.data, 'success:', checklistRes.success);
          setChecklistStages(checklistRes.data);
          if (!checklistRes.success) {
            console.warn('Failed to load checklist stages:', checklistRes.message);
          }
        } else {
          console.error('Failed to load checklist stages:', checklistRes.message);
        }
      } catch (err) {
        setError('Ошибка загрузки данных. Попробуйте обновить страницу.');
        console.error('Dashboard data loading error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const handleManagerSelect = (manager: Manager) => {
    setSelectedManager(selectedManager?.id === manager.id ? null : manager);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full mx-4">
          <div className="text-red-600 text-center mb-4">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-semibold mb-2">Ошибка загрузки</h2>
            <p className="text-gray-600">{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Обновить страницу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header 
        callMetrics={callMetrics}
        isLoading={isLoading}
      />
      
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          managers={managers}
          selectedManager={selectedManager}
          onManagerSelect={handleManagerSelect}
          isLoading={isLoading}
        />
        
        <MainContent
          metrics={metrics}
          managers={managers}
          selectedManager={selectedManager}
          checklistStages={checklistStages}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};