// Manager interface
export interface Manager {
  id: string;
  name: string;
  aiScore: number;
  checklistScore: number;
  trend: 'up' | 'down' | 'stable';
  callsAnalyzed: number;
  lastActivity: string;
}

// Call metrics interface
export interface CallMetrics {
  totalCalls: number;
  processedCalls: number;
  pendingCalls: number;
  errorCalls: number;
  averageScore: number;
  lastUpdated: string;
}

// API Processing Status interface (matching backend)
export interface ProcessingStatus {
  total_files: number;
  completed: number;
  processing: number;
  discovered: number;
  failed: number;
  unprocessed: number;
}

// API Performance Chart interface (matching backend)
export interface PerformanceChart {
  manager_name: string;
  score: number;
  color: string;
}

// Performance metrics for dashboard cards
export interface PerformanceMetric {
  id: string;
  title: string;
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
  category: 'rapport' | 'budget' | 'presentation' | 'objection' | 'close' | 'follow-up';
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface ManagerStatsResponse {
  managers: Manager[];
  totalManagers: number;
}

export interface ProcessingStatusResponse {
  status: 'processing' | 'completed' | 'error';
  progress: number;
  estimatedCompletion?: string;
}

// Chart data interface
export interface ChartData {
  label: string;
  value: number;
  color: string;
}

// Component prop types
export interface MetricCardProps {
  metric: PerformanceMetric;
  className?: string;
}

export interface ManagerTableProps {
  managers: Manager[];
  onManagerSelect?: (manager: Manager) => void;
  selectedManager?: Manager | null;
}

export interface PerformanceChartProps {
  data: ChartData[];
  title: string;
  className?: string;
}

export interface ProgressBarProps {
  value: number;
  max?: number;
  color?: 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  className?: string;
}

// Utility types
export type TrendDirection = 'up' | 'down' | 'stable';
export type MetricCategory = 'rapport' | 'budget' | 'presentation' | 'objection' | 'close' | 'follow-up';
export type ColorVariant = 'primary' | 'success' | 'warning' | 'danger';

// Filter and sort types
export interface SortConfig {
  key: keyof Manager;
  direction: 'asc' | 'desc';
}

export interface FilterConfig {
  search: string;
  scoreRange: [number, number];
  trend?: TrendDirection;
}