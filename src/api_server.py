#!/usr/bin/env python3
"""
API Server for VoiceAI Call Analysis System Frontend.

Provides REST API endpoints for the React frontend to consume.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import uvicorn

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from workflow_orchestrator import WorkflowOrchestrator
from config import config
from auth_utils import (
    UserLogin, UserRegister, UserResponse, Token,
    get_current_user, get_current_admin_user, get_current_user_optional,
    login_user, register_user, create_user_response
)

# Initialize FastAPI app
app = FastAPI(
    title="VoiceAI Call Analysis API",
    description="REST API for VoiceAI Call Analysis Dashboard",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = DatabaseService() if config.save_to_database else None
orchestrator = None

# Pydantic models for API responses
class ManagerStat(BaseModel):
    id: str
    name: str
    ai_score: float
    checklist_score: float
    total_calls: int
    inbound_calls: int
    outbound_calls: int
    last_call_date: Optional[datetime]
    trend: str  # "up", "down", "stable"

class MetricData(BaseModel):
    name: str
    value: float
    trend: Optional[float]
    color: str  # "success", "warning", "danger"

class ProcessingStatus(BaseModel):
    total_files: int
    completed: int
    processing: int
    discovered: int
    failed: int
    unprocessed: int

class HealthStatus(BaseModel):
    status: str
    services: Dict[str, Dict[str, Any]]
    timestamp: str

class PerformanceChart(BaseModel):
    manager_name: str
    score: float
    color: str

class ChecklistStageDetail(BaseModel):
    stage_name: str
    stage_total: float
    max_possible: float
    percentage: float
    criteria_count: int
    color: str

class ChecklistCriteriaDetail(BaseModel):
    criteria_name: str
    average_score: float
    max_score: float
    percentage: float
    stage: str


# API Endpoints

# Authentication endpoints
@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Authenticate user and return JWT token."""
    if not db_service:
        raise HTTPException(status_code=503, detail="Database service not available")
    
    return login_user(user_data, db_service)

@app.post("/api/auth/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    current_user = Depends(get_current_admin_user)  # Only admins can create users
):
    """Register a new user (admin only)."""
    if not db_service:
        raise HTTPException(status_code=503, detail="Database service not available")
    
    user = register_user(user_data, db_service)
    return create_user_response(user)

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current authenticated user information."""
    return create_user_response(current_user)

@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    """Check system health and service status."""
    try:
        global orchestrator
        if not orchestrator:
            orchestrator = WorkflowOrchestrator()
        
        health_data = await orchestrator.health_check()
        return HealthStatus(
            status=health_data.get("status", "unknown"),
            services=health_data.get("services", {}),
            timestamp=health_data.get("timestamp", datetime.now().isoformat())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/managers/stats", response_model=List[ManagerStat])
async def get_manager_statistics(
    days: int = Query(30, description="Number of days to analyze"),
    current_user = Depends(get_current_user)
):
    """Get performance statistics for all managers."""
    try:
        if not db_service:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        managers = db_service.get_all_managers()
        manager_stats = []
        
        for manager in managers:
            stats = db_service.get_manager_statistics(manager.name, days)
            
            # Calculate trend (simplified)
            trend = "stable"
            if stats.get("avg_ai_score", 0) > 75:
                trend = "up"
            elif stats.get("avg_ai_score", 0) < 50:
                trend = "down"
            
            manager_stat = ManagerStat(
                id=str(manager.id),
                name=manager.name,
                ai_score=stats.get("avg_ai_score", 0),
                checklist_score=stats.get("avg_checklist_score", 0),
                total_calls=stats.get("total_calls", 0),
                inbound_calls=stats.get("inbound_calls", 0),
                outbound_calls=stats.get("outbound_calls", 0),
                last_call_date=stats.get("last_call_date"),
                trend=trend
            )
            manager_stats.append(manager_stat)
        
        # Sort by AI score descending
        manager_stats.sort(key=lambda x: x.ai_score, reverse=True)
        return manager_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get manager statistics: {str(e)}")


@app.get("/api/metrics", response_model=List[MetricData])
async def get_system_metrics(current_user = Depends(get_current_user)):
    """Get overall system performance metrics."""
    try:
        if not db_service:
            # Return mock data if database not available
            return [
                MetricData(name="Установил раппорт", value=89.0, trend=3.0, color="success"),
                MetricData(name="Выяснил бюджет", value=69.0, trend=-2.0, color="warning"),
                MetricData(name="Презентовал продукт", value=78.0, trend=1.0, color="success"),
                MetricData(name="Обработал возражения", value=65.0, trend=-1.0, color="warning"),
                MetricData(name="Закрыл сделку", value=42.0, trend=5.0, color="danger"),
                MetricData(name="Средняя оценка AI", value=72.0, trend=2.0, color="success"),
                MetricData(name="Обработано звонков", value=156.0, trend=12.0, color="success"),
                MetricData(name="Время обработки", value=2.3, trend=-0.2, color="success"),
            ]
        
        # Get real checklist stage metrics from database
        stage_metrics = db_service.get_checklist_stage_metrics(30)
        
        if not stage_metrics:
            # Return empty metrics if no data
            return []
        
        # Create metric cards based on real checklist data
        metrics = []
        
        # Map checklist stages to Russian names and add metrics
        stage_names = {
            'greeting': 'Приветствие',
            'contact': 'Установление контакта', 
            'programming': 'Программирование',
            'need': 'Выявление потребности',
            'presentation': 'Презентация продукта',
            'objections': 'Обработка возражений',
            'closing': 'Закрытие сделки'
        }
        
        for stage, name in stage_names.items():
            if stage in stage_metrics:
                data = stage_metrics[stage]
                percentage = data['percentage']
                
                # Determine color based on performance
                if percentage >= 80:
                    color = "success"
                elif percentage >= 60:
                    color = "warning"
                else:
                    color = "danger"
                
                # Calculate trend (simplified - could be enhanced with historical data)
                trend = percentage - 70  # Assuming 70% is baseline
                
                metrics.append(MetricData(
                    name=name,
                    value=percentage,
                    trend=trend,
                    color=color
                ))
        
        # Add summary metrics
        all_percentages = [stage_metrics[stage]['percentage'] for stage in stage_metrics]
        avg_performance = sum(all_percentages) / len(all_percentages) if all_percentages else 0
        total_calls = sum(stage_metrics[stage]['total_calls'] for stage in stage_metrics) / len(stage_metrics) if stage_metrics else 0
        
        metrics.extend([
            MetricData(
                name="Общая эффективность",
                value=avg_performance,
                trend=avg_performance - 75,  # 75% baseline
                color="success" if avg_performance > 75 else "warning" if avg_performance > 60 else "danger"
            ),
            MetricData(
                name="Обработано звонков",
                value=float(total_calls),
                trend=5.0,  # Positive trend for call volume
                color="success"
            ),
        ])
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/api/processing-status", response_model=ProcessingStatus)
async def get_processing_status(current_user = Depends(get_current_user)):
    """Get file processing status summary."""
    try:
        if not db_service:
            # Return mock data if database not available
            return ProcessingStatus(
                total_files=25,
                completed=18,
                processing=2,
                discovered=4,
                failed=1,
                unprocessed=7
            )
        
        summary = db_service.get_processing_summary()
        return ProcessingStatus(
            total_files=summary.get("total_files", 0),
            completed=summary.get("completed", 0),
            processing=summary.get("processing", 0),
            discovered=summary.get("discovered", 0),
            failed=summary.get("failed", 0),
            unprocessed=summary.get("unprocessed", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@app.get("/api/performance-chart", response_model=List[PerformanceChart])
async def get_performance_chart_data(current_user = Depends(get_current_user)):
    """Get data for manager performance chart."""
    try:
        if not db_service:
            # Return mock data
            return [
                PerformanceChart(manager_name="Иванов", score=82.0, color="success"),
                PerformanceChart(manager_name="Петров", score=65.0, color="warning"),
                PerformanceChart(manager_name="Сидоров", score=78.0, color="success"),
                PerformanceChart(manager_name="Владимир", score=71.0, color="success"),
                PerformanceChart(manager_name="Елизавета", score=85.0, color="success"),
            ]
        
        managers = db_service.get_all_managers()
        chart_data = []
        
        for manager in managers:
            stats = db_service.get_manager_statistics(manager.name, 30)
            ai_score = stats.get("avg_ai_score", 0)
            
            # Determine color based on score
            if ai_score >= 80:
                color = "success"
            elif ai_score >= 60:
                color = "warning"
            else:
                color = "danger"
            
            chart_data.append(PerformanceChart(
                manager_name=manager.name,
                score=ai_score,
                color=color
            ))
        
        # Sort by score descending and take top 10
        chart_data.sort(key=lambda x: x.score, reverse=True)
        return chart_data[:10]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance chart data: {str(e)}")


@app.get("/api/checklist-stages", response_model=List[ChecklistStageDetail])
async def get_checklist_stage_details(
    days: int = Query(30, description="Number of days to analyze"),
    current_user = Depends(get_current_user)
):
    """Get detailed checklist stage breakdown."""
    try:
        if not db_service:
            # Return mock data
            return [
                ChecklistStageDetail(
                    stage_name="Приветствие",
                    stage_total=5.2,
                    max_possible=7.0,
                    percentage=74.3,
                    criteria_count=7,
                    color="warning"
                ),
                ChecklistStageDetail(
                    stage_name="Установление контакта",
                    stage_total=6.1,
                    max_possible=8.0,
                    percentage=76.3,
                    criteria_count=8,
                    color="warning"
                ),
            ]
        
        stage_metrics = db_service.get_checklist_stage_metrics(days)
        stage_details = []
        
        stage_info = {
            'greeting': {'name': 'Приветствие', 'criteria': 7},
            'contact': {'name': 'Установление контакта', 'criteria': 8},
            'programming': {'name': 'Программирование', 'criteria': 2},
            'need': {'name': 'Выявление потребности', 'criteria': 2},
            'presentation': {'name': 'Презентация продукта', 'criteria': 5},
            'objections': {'name': 'Обработка возражений', 'criteria': 5},
            'closing': {'name': 'Закрытие сделки', 'criteria': 6}
        }
        
        for stage, data in stage_metrics.items():
            if stage in stage_info:
                percentage = data['percentage']
                
                # Determine color
                if percentage >= 80:
                    color = "success"
                elif percentage >= 60:
                    color = "warning"
                else:
                    color = "danger"
                
                stage_details.append(ChecklistStageDetail(
                    stage_name=stage_info[stage]['name'],
                    stage_total=data['average_score'],
                    max_possible=data['max_possible'],
                    percentage=percentage,
                    criteria_count=stage_info[stage]['criteria'],
                    color=color
                ))
        
        return stage_details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get checklist stage details: {str(e)}")


@app.get("/api/manager/{manager_id}/details")
async def get_manager_details(
    manager_id: str,
    current_user = Depends(get_current_user)
):
    """Get detailed information for a specific manager."""
    try:
        if not db_service:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get manager by ID
        session = db_service.get_session()
        try:
            from database_models import Manager
            manager = session.query(Manager).filter(Manager.id == int(manager_id)).first()
            
            if not manager:
                raise HTTPException(status_code=404, detail="Manager not found")
            
            # Get detailed statistics
            stats = db_service.get_manager_statistics(manager.name, 30)
            
            return {
                "id": manager.id,
                "name": manager.name,
                "email": manager.email,
                "department": manager.department,
                "status": manager.status,
                "statistics": stats
            }
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get manager details: {str(e)}")


# Development endpoints for testing
@app.post("/api/analyze-file")
async def trigger_file_analysis(
    file_id: str,
    current_user = Depends(get_current_admin_user)  # Admin only
):
    """Trigger analysis of a specific file (for testing)."""
    try:
        global orchestrator
        if not orchestrator:
            orchestrator = WorkflowOrchestrator()
        
        result = await orchestrator.process_file_by_id(file_id)
        
        if result:
            return {
                "success": True,
                "message": f"File analyzed successfully",
                "manager": result.detected_manager,
                "score": result.quality_scores.total_score if result.quality_scores else 0
            }
        else:
            raise HTTPException(status_code=400, detail="File analysis failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    # Run the API server
    print("Starting VoiceAI API Server...")
    print(f"Database enabled: {config.save_to_database}")
    print(f"API will be available at: http://localhost:8000")
    print(f"API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )