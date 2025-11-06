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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
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
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://147.45.210.20:8000", "http://dashboard.aloda.agency", "https://dashboard.aloda.agency"],  # React dev servers and production
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


def get_real_checklist_criteria(stage: str, days: int) -> List[ChecklistCriteriaDetail]:
    """Get real checklist criteria from database."""
    if not db_service:
        return []
    
    # Define criteria mappings for each stage (using real database field names)
    stage_criteria = {
        'greeting': [
            ('greeting_corporate_greeting', 'Корпоративное приветствие'),
            ('greeting_tone_friendly', 'Дружелюбный тон'),
            ('greeting_states_purpose', 'Указывает цель звонка'),
            ('greeting_time_before_manager', 'Время до разговора с менеджером'),
            ('greeting_no_address_phrase', 'Не использует обращения-клише'),
            ('greeting_no_convenient_phrase', 'Не спрашивает об удобстве'),
            ('greeting_no_rush_words', 'Не торопит клиента'),
        ],
        'contact': [
            ('contact_addresses_by_name', 'Обращается по имени'),
            ('contact_uses_small_talk', 'Использует светскую беседу'),
            ('contact_gives_compliment', 'Делает комплименты'),
            ('contact_uses_humor', 'Использует юмор'),
            ('contact_communicates_equal', 'Общается на равных'),
            ('contact_avoids_formal_tone', 'Избегает формального тона'),
            ('contact_simple_language', 'Использует простой язык'),
            ('contact_no_interrupt', 'Не перебивает клиента'),
        ],
        'need': [
            ('need_asks_required_questions', 'Задает необходимые вопросы'),
            ('need_finds_business_area', 'Выясняет сферу деятельности'),
            ('need_company_activity', 'Выяснил чем занимается компания, какая сфера деятельности'),
            ('need_employee_count', 'Какое количество сотрудников будет пользоваться услугами связи'),
            ('need_sales_department', 'Есть ли отдел продаж в компании'),
            ('need_it_responsible', 'Кто отвечает за IT инфраструктуру в компании'),
            ('need_services_to_connect', 'Какие сервисы планируете подключать к интернету - почта, видеонаблюдение, телефония'),
            ('need_additional_offices', 'Есть ли в компании дополнительные офисы в Москве или в других городах'),
            ('need_equipment_required', 'Оборудование потребуется или нет'),
            ('need_workplace_wiring', 'Требуется ли разводка для рабочих мест'),
        ],
        'presentation': [
            ('presentation_presents_company', 'Представляет компанию'),
            ('presentation_services_with_benefits', 'Объясняет услуги с преимуществами'),
            ('presentation_mentions_cases', 'Упоминает успешные кейсы'),
            ('presentation_knows_product', 'Знает продукт'),
            ('presentation_offers_proposal', 'Предлагает коммерческое предложение'),
        ],
        'objections': [
            ('objections_agrees_empathizes', 'Соглашается и проявляет эмпатию'),
            ('objections_no_argue', 'Не спорит с клиентом'),
            ('objections_arguments_match', 'Аргументы соответствуют возражению'),
            ('objections_handles_fully', 'Полностью отрабатывает возражения'),
            ('objections_offers_proposal', 'Предлагает решение после возражений'),
        ],
        'closing': [
            ('closing_asks_questions_remain', 'Спрашивает остались ли вопросы'),
            ('closing_summarizes_conversation', 'Подводит итоги разговора'),
            ('closing_states_next_steps', 'Указывает следующие шаги'),
            ('closing_asks_service_date', 'Уточняет дату подключения услуг'),
            ('closing_clarifies_proposal_send', 'Уточняет отправку предложения'),
            ('closing_leaves_contacts', 'Оставляет контакты'),
        ]
    }
    
    if stage not in stage_criteria:
        return []
    
    criteria_list = []
    session = db_service.get_session()
    
    try:
        from sqlalchemy import func, text
        from database_models import ChecklistAnalysis, CallRecord
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for field_name, display_name in stage_criteria[stage]:
            # Get average score for this criterion
            query = text(f'''
                SELECT AVG({field_name}) as avg_score, COUNT({field_name}) as count_records
                FROM checklist_analysis ca
                JOIN call_records cr ON ca.call_record_id = cr.id
                WHERE cr.call_date >= :cutoff_date AND {field_name} IS NOT NULL
            ''')
            
            result = session.execute(query, {'cutoff_date': cutoff_date}).fetchone()
            
            if result and result[0] is not None:
                avg_score = float(result[0])
                count_records = int(result[1])
                max_score = 1.0
                percentage = (avg_score / max_score) * 100
                
                criteria_list.append(ChecklistCriteriaDetail(
                    criteria_name=display_name,
                    average_score=avg_score,
                    max_score=max_score,
                    percentage=percentage,
                    stage=stage
                ))
    
    except Exception as e:
        print(f"Error getting criteria for stage {stage}: {e}")
    finally:
        session.close()
    
    return criteria_list


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
            'need': {'name': 'Выявление потребности', 'criteria': 10},
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


@app.get("/api/checklist-criteria/{stage}", response_model=List[ChecklistCriteriaDetail])
async def get_checklist_criteria_for_stage(
    stage: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user = Depends(get_current_user)
):
    """Get detailed criteria breakdown for a specific stage."""
    try:
        if not db_service:
            # Return mock data for NEEDS IDENTIFICATION 
            if stage == 'need':
                return [
                    ChecklistCriteriaDetail(
                        criteria_name="Выяснил чем занимается компания, какая сфера деятельности",
                        average_score=0.8,
                        max_score=1.0,
                        percentage=80.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Какое количество сотрудников будет пользоваться услугами связи",
                        average_score=0.7,
                        max_score=1.0,
                        percentage=70.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Есть ли отдел продаж в компании",
                        average_score=0.6,
                        max_score=1.0,
                        percentage=60.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Кто отвечает за IT инфраструктуру в компании",
                        average_score=0.5,
                        max_score=1.0,
                        percentage=50.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Какие сервисы планируете подключать к интернету - почта, видеонаблюдение, телефония",
                        average_score=0.9,
                        max_score=1.0,
                        percentage=90.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Есть ли в компании дополнительные офисы в Москве или в других городах",
                        average_score=0.4,
                        max_score=1.0,
                        percentage=40.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Оборудование потребуется или нет",
                        average_score=0.8,
                        max_score=1.0,
                        percentage=80.0,
                        stage="need"
                    ),
                    ChecklistCriteriaDetail(
                        criteria_name="Требуется ли разводка для рабочих мест",
                        average_score=0.3,
                        max_score=1.0,
                        percentage=30.0,
                        stage="need"
                    )
                ]
            # Return empty for other stages in mock mode
            return []
        
        # Real implementation - fetch detailed criteria from database
        criteria_details = get_real_checklist_criteria(stage, days)
        return criteria_details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get criteria details for stage {stage}: {str(e)}")


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


@app.post("/api/export-sheets")
async def export_to_google_sheets(
    manager_name: Optional[str] = Query(None, description="Manager name to export (all if not specified)"),
    current_user = Depends(get_current_admin_user)  # Admin only
):
    """Export database data to Google Sheets."""
    try:
        global orchestrator
        if not orchestrator:
            orchestrator = WorkflowOrchestrator()
        
        success = await orchestrator.export_to_google_sheets(manager_name)
        
        if success:
            message = f"Successfully exported data to Google Sheets"
            if manager_name:
                message += f" for manager: {manager_name}"
            else:
                message += " for all managers"
            
            return {
                "success": True,
                "message": message,
                "exported_manager": manager_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Export to Google Sheets failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Mount static files for frontend (after API routes to avoid conflicts)
frontend_dist_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_path / "assets")), name="assets")

    # Catch-all route for SPA - must be last
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React frontend for all non-API routes."""
        # Don't serve frontend for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the requested file
        file_path = frontend_dist_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html (SPA)
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")


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