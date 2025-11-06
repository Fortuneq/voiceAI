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

// Checklist stage details interface (matching backend)
export interface ChecklistStageDetail {
  stage_name: string;
  stage_total: number;
  max_possible: number;
  percentage: number;
  criteria_count: number;
  color: string;
}

// Checklist criteria details interface (matching backend)
export interface ChecklistCriteriaDetail {
  criteria_name: string;
  average_score: number;
  max_score: number;
  percentage: number;
  stage: string;
}

// Individual NEEDS IDENTIFICATION criteria interface for the 8 new fields
export interface NeedsIdentificationCriteria {
  need_company_activity: number;
  need_employee_count: number;
  need_sales_department: number;
  need_it_responsible: number;
  need_services_to_connect: number;
  need_additional_offices: number;
  need_equipment_required: number;
  need_workplace_wiring: number;
}

// Extended checklist analysis interface including all fields
export interface ChecklistAnalysis extends NeedsIdentificationCriteria {
  id: string;
  call_id: string;
  // Existing checklist fields
  greeting_total: number;
  contact_total: number;
  programming_total: number;
  need_total: number;
  presentation_total: number;
  objections_total: number;
  closing_total: number;
  // Metadata
  created_at: string;
  updated_at?: string;
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

export interface DetailedCriteriaCardProps {
  criteria: ChecklistCriteriaDetail;
  className?: string;
}

export interface ChecklistStageCardProps {
  stage: ChecklistStageDetail;
  onStageClick?: (stage: ChecklistStageDetail) => void;
  showDetails?: boolean;
  className?: string;
}

// Authentication types
export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'admin' | 'user';
  created_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
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