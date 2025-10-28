import type {
  Manager,
  CallMetrics,
  PerformanceMetric,
  ApiResponse,
  ManagerStatsResponse,
  ProcessingStatusResponse,
  ProcessingStatus,
  PerformanceChart,
} from '../types';

// Mock data
const mockManagers: Manager[] = [
  {
    id: '1',
    name: 'Александр Петров',
    aiScore: 87,
    checklistScore: 92,
    trend: 'up',
    callsAnalyzed: 245,
    lastActivity: '2024-01-15T10:30:00Z',
  },
  {
    id: '2',
    name: 'Мария Иванова',
    aiScore: 94,
    checklistScore: 89,
    trend: 'up',
    callsAnalyzed: 189,
    lastActivity: '2024-01-15T09:45:00Z',
  },
  {
    id: '3',
    name: 'Дмитрий Козлов',
    aiScore: 76,
    checklistScore: 78,
    trend: 'down',
    callsAnalyzed: 312,
    lastActivity: '2024-01-15T11:15:00Z',
  },
  {
    id: '4',
    name: 'Елена Смирнова',
    aiScore: 91,
    checklistScore: 85,
    trend: 'up',
    callsAnalyzed: 156,
    lastActivity: '2024-01-15T08:20:00Z',
  },
  {
    id: '5',
    name: 'Андрей Новиков',
    aiScore: 83,
    checklistScore: 81,
    trend: 'stable',
    callsAnalyzed: 278,
    lastActivity: '2024-01-15T12:00:00Z',
  },
  {
    id: '6',
    name: 'Ольга Федорова',
    aiScore: 88,
    checklistScore: 93,
    trend: 'up',
    callsAnalyzed: 203,
    lastActivity: '2024-01-15T10:45:00Z',
  },
  {
    id: '7',
    name: 'Сергей Волков',
    aiScore: 79,
    checklistScore: 74,
    trend: 'down',
    callsAnalyzed: 234,
    lastActivity: '2024-01-15T09:30:00Z',
  },
  {
    id: '8',
    name: 'Анна Морозова',
    aiScore: 96,
    checklistScore: 91,
    trend: 'up',
    callsAnalyzed: 167,
    lastActivity: '2024-01-15T11:30:00Z',
  },
  {
    id: '9',
    name: 'Михаил Лебедев',
    aiScore: 72,
    checklistScore: 76,
    trend: 'stable',
    callsAnalyzed: 289,
    lastActivity: '2024-01-15T08:45:00Z',
  },
  {
    id: '10',
    name: 'Татьяна Соколова',
    aiScore: 85,
    checklistScore: 88,
    trend: 'up',
    callsAnalyzed: 198,
    lastActivity: '2024-01-15T10:15:00Z',
  },
];

const mockPerformanceMetrics: PerformanceMetric[] = [
  {
    id: '1',
    title: 'Установил раппорт',
    value: 85,
    target: 90,
    trend: 'up',
    category: 'rapport',
  },
  {
    id: '2',
    title: 'Выяснил бюджет',
    value: 72,
    target: 80,
    trend: 'down',
    category: 'budget',
  },
  {
    id: '3',
    title: 'Презентовал продукт',
    value: 91,
    target: 85,
    trend: 'up',
    category: 'presentation',
  },
  {
    id: '4',
    title: 'Отработал возражения',
    value: 68,
    target: 75,
    trend: 'stable',
    category: 'objection',
  },
  {
    id: '5',
    title: 'Закрыл сделку',
    value: 79,
    target: 85,
    trend: 'up',
    category: 'close',
  },
  {
    id: '6',
    title: 'Договорился о встрече',
    value: 83,
    target: 80,
    trend: 'up',
    category: 'follow-up',
  },
  {
    id: '7',
    title: 'Качество речи',
    value: 87,
    target: 85,
    trend: 'stable',
    category: 'presentation',
  },
  {
    id: '8',
    title: 'Время разговора',
    value: 76,
    target: 70,
    trend: 'up',
    category: 'rapport',
  },
];

const mockCallMetrics: CallMetrics = {
  totalCalls: 2847,
  processedCalls: 2734,
  pendingCalls: 98,
  errorCalls: 15,
  averageScore: 84.3,
  lastUpdated: '2024-01-15T12:00:00Z',
};

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// API service class
export class ApiService {
  private static baseUrl = 'http://localhost:8000/api';

  // Get managers statistics
  static async getManagersStats(): Promise<ApiResponse<ManagerStatsResponse>> {
    try {
      const response = await fetch(`${this.baseUrl}/managers/stats`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Transform API data to frontend format
      const managers: Manager[] = data.map((manager: any) => ({
        id: manager.id,
        name: manager.name,
        aiScore: Math.round(manager.ai_score),
        checklistScore: Math.round(manager.checklist_score),
        trend: manager.trend,
        callsAnalyzed: manager.total_calls,
        lastActivity: manager.last_call_date || new Date().toISOString(),
      }));
      
      return {
        success: true,
        data: {
          managers,
          totalManagers: managers.length,
        },
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching managers stats:', error);
      // Fallback to mock data on error
      return {
        success: false,
        data: {
          managers: mockManagers,
          totalManagers: mockManagers.length,
        },
        message: 'Failed to fetch real data, showing mock data',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Get performance metrics
  static async getPerformanceMetrics(): Promise<ApiResponse<PerformanceMetric[]>> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Transform API data to frontend format
      const metrics: PerformanceMetric[] = data.map((metric: any, index: number) => ({
        id: String(index + 1),
        title: metric.name,
        value: Math.round(metric.value),
        target: Math.round(metric.value * 1.1), // Assume target is 10% higher
        trend: metric.trend > 0 ? 'up' : metric.trend < 0 ? 'down' : 'stable',
        category: this.getCategoryFromMetricName(metric.name),
      }));
      
      return {
        success: true,
        data: metrics,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      // Fallback to mock data on error
      return {
        success: false,
        data: mockPerformanceMetrics,
        message: 'Failed to fetch real data, showing mock data',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Get call metrics
  static async getCallMetrics(): Promise<ApiResponse<CallMetrics>> {
    try {
      const response = await fetch(`${this.baseUrl}/processing-status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ProcessingStatus = await response.json();
      
      // Transform API data to CallMetrics format
      const callMetrics: CallMetrics = {
        totalCalls: data.total_files,
        processedCalls: data.completed,
        pendingCalls: data.processing + data.discovered,
        errorCalls: data.failed,
        averageScore: 0, // Would need additional endpoint for this
        lastUpdated: new Date().toISOString(),
      };
      
      return {
        success: true,
        data: callMetrics,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching call metrics:', error);
      return {
        success: false,
        data: mockCallMetrics,
        message: 'Failed to fetch real data, showing mock data',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Get performance chart data
  static async getPerformanceChartData(): Promise<ApiResponse<PerformanceChart[]>> {
    try {
      const response = await fetch(`${this.baseUrl}/performance-chart`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: PerformanceChart[] = await response.json();
      
      return {
        success: true,
        data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching performance chart data:', error);
      return {
        success: false,
        data: [],
        message: 'Failed to fetch performance chart data',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Get processing status
  static async getProcessingStatus(): Promise<ApiResponse<ProcessingStatusResponse>> {
    try {
      const response = await fetch(`${this.baseUrl}/processing-status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Calculate status based on API data
      const totalFiles = data.total_files || 0;
      const completed = data.completed || 0;
      const processing = data.processing || 0;
      const failed = data.failed || 0;
      
      let status: ProcessingStatusResponse['status'] = 'completed';
      let progress = 100;
      
      if (processing > 0) {
        status = 'processing';
        progress = totalFiles > 0 ? Math.round((completed / totalFiles) * 100) : 0;
      } else if (failed > 0) {
        status = 'error';
      }
      
      return {
        success: true,
        data: {
          status,
          progress,
          estimatedCompletion: status === 'processing' ? 
            new Date(Date.now() + 300000).toISOString() : undefined,
        },
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching processing status:', error);
      return {
        success: false,
        data: {
          status: 'error',
          progress: 0,
        },
        message: 'Failed to fetch processing status',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Health check
  static async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      return {
        success: true,
        data: { status: data.status },
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error in health check:', error);
      return {
        success: false,
        data: { status: 'error' },
        message: 'Health check failed',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Get manager details
  static async getManagerDetails(managerId: string): Promise<ApiResponse<Manager | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/manager/${managerId}/details`);
      if (!response.ok) {
        if (response.status === 404) {
          return {
            success: false,
            data: null,
            message: 'Manager not found',
            timestamp: new Date().toISOString(),
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      const manager: Manager = {
        id: data.id,
        name: data.name,
        aiScore: Math.round(data.statistics?.avg_ai_score || 0),
        checklistScore: Math.round(data.statistics?.avg_checklist_score || 0),
        trend: 'stable', // Could be calculated from statistics
        callsAnalyzed: data.statistics?.total_calls || 0,
        lastActivity: data.statistics?.last_call_date || new Date().toISOString(),
      };
      
      return {
        success: true,
        data: manager,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error fetching manager details:', error);
      return {
        success: false,
        data: null,
        message: 'Failed to fetch manager details',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Helper method to map metric names to categories
  private static getCategoryFromMetricName(name: string): PerformanceMetric['category'] {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('раппорт') || lowerName.includes('rapport')) return 'rapport';
    if (lowerName.includes('бюджет') || lowerName.includes('budget')) return 'budget';
    if (lowerName.includes('презент') || lowerName.includes('present')) return 'presentation';
    if (lowerName.includes('возраж') || lowerName.includes('objection')) return 'objection';
    if (lowerName.includes('закр') || lowerName.includes('close')) return 'close';
    return 'follow-up';
  }
}

// Export individual functions for easier importing
export const {
  getManagersStats,
  getPerformanceMetrics,
  getCallMetrics,
  getPerformanceChartData,
  getProcessingStatus,
  healthCheck,
  getManagerDetails,
} = ApiService;