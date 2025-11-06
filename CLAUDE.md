# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoiceAI Call Analysis System is a comprehensive Python-based solution that automatically analyzes audio call recordings using AI. The system monitors Google Drive for audio files, transcribes them using OpenAI Whisper, analyzes call quality with GPT-4, stores manager performance metrics, and provides a real-time dashboard interface.

## Architecture

### Backend (Python)
- **Main Entry Point**: `main.py` - Command-line interface with multiple operation modes
- **API Server**: `src/api_server.py` - FastAPI REST API serving the frontend
- **Core Services**:
  - `src/workflow_orchestrator.py` - Main coordinator for the entire analysis process
  - `src/database_service.py` - Database operations and manager statistics
  - `src/google_drive_service.py` - Monitors and downloads audio files
  - `src/openai_service.py` - Handles transcription and AI analysis
  - `src/manager_detection.py` - Identifies managers from call transcripts
  - `src/google_sheets_service.py` - Legacy Google Sheets integration

### Frontend (React + TypeScript)
- **Main App**: `frontend/src/App.tsx` - Root component with auth provider
- **Dashboard**: `frontend/src/components/layout/Dashboard.tsx` - Main dashboard layout
- **Components**: Authentication, metrics cards, charts, manager tables in `frontend/src/components/`
- **Styling**: Tailwind CSS with responsive design

### Database
- **Models**: `src/database_models.py` - SQLAlchemy models for managers, calls, analysis
- **Migrations**: `database_migrations/` - Database schema changes
- **Support**: SQLite (default), PostgreSQL, MySQL

## Development Commands

### Starting the Full Application
```bash
# Start both backend and frontend servers
./start_dashboard.sh

# Manual startup:
# Backend API server (FastAPI)
python src/api_server.py

# Frontend development server (in frontend/ directory)
cd frontend && npm run dev
```

### Main Application Modes
```bash
# Continuous monitoring of Google Drive (production)
python main.py --mode monitor

# Dry run monitoring (test without processing)
python main.py --mode monitor --dry-run

# Process specific file by Google Drive ID
python main.py --mode process-file --file-id <drive-file-id>

# Analyze file and save to JSON
python main.py --mode analyze-file --file-id <file-id> --output-file result.json

# System health check
python main.py --mode health-check

# Processing statistics
python main.py --mode stats

# File processing status
python main.py --mode processing-status
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Lint TypeScript/React code
npm run lint

# Preview production build
npm run preview
```

### Database Operations
```bash
# Initialize database schema
python setup_database.py

# Create admin user
python src/create_admin_user.py

# Migrate from SQLite to PostgreSQL
python migrate_to_postgresql.py
```

## Configuration

### Required Environment Variables (.env)
```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Google Services
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id

# Database
DATABASE_URL=sqlite:///./voiceai_calls.db
SAVE_TO_DATABASE=true
SAVE_TO_SHEETS=false

# Processing
POLL_INTERVAL_SECONDS=60
LOG_LEVEL=INFO
```

### Key Configuration Files
- `.env` - Environment variables (create from README examples)
- `src/config.py` - Application configuration loading
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration

## Development Workflows

### Adding New Manager Analysis Features
1. Update `src/manager_detection.py` with new manager patterns
2. Extend `src/database_models.py` if new fields needed
3. Update `src/database_service.py` for new statistics methods
4. Modify `src/api_server.py` endpoints if frontend integration required
5. Update frontend components in `frontend/src/components/` for UI changes

### Extending AI Analysis
1. Modify prompts in `src/openai_service.py`
2. Update `src/models.py` for new analysis result structures
3. Extend database models in `src/database_models.py`
4. Update API responses in `src/api_server.py`

### Frontend Component Development
- Follow existing patterns in `frontend/src/components/`
- Use TypeScript interfaces from `frontend/src/types/`
- Implement responsive design with Tailwind CSS
- Use React.memo for performance optimization
- Follow component structure: auth/, layout/, ui/

## Testing and Quality

### Health Checks
```bash
# Full system health check
python main.py --mode health-check
```

### Error Monitoring
- Logs stored in `logs/voiceai.log` with 7-day rotation
- Console logs with color-coded levels
- Database error handling with rollback

### Performance Monitoring
- File processing takes ~2-3 minutes per call
- Anti-reprocessing system prevents duplicate analysis
- Database connection pooling for concurrent access

## Key Features to Understand

### File Processing Pipeline
1. Google Drive monitoring with polling
2. Audio transcription via OpenAI Whisper
3. Manager detection from transcript content
4. Structured checklist analysis (33 criteria across 7 stages)
5. AI quality analysis (7 evaluation areas, 0-100 scores)
6. Database storage with computed metrics

### Dashboard Capabilities
- Real-time manager performance tracking
- Interactive metrics grid with color coding
- Performance charts with responsive design
- Authentication with JWT tokens
- Admin-only features for data export

### Database Schema
- `managers` - Manager profiles and status
- `call_records` - Basic call information
- `checklist_analysis` - Detailed 33-criteria scoring
- `ai_analysis` - AI evaluation results
- `processed_files` - File tracking for reprocessing prevention

## Deployment

### Development
- Use `./start_dashboard.sh` for local development
- Frontend runs on port 3000/3001/5173, backend on port 8000
- SQLite database for local development

### Production
- See `DEPLOYMENT_GUIDE.md` for Docker deployment
- PostgreSQL recommended for production
- nginx reverse proxy configuration included
- SSL certificate setup with Let's Encrypt

## URLs and Access Points

- **Frontend Dashboard**: http://localhost:3001
- **API Server**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs
- **Production**: https://dashboard.aloda.agency (when deployed)

## Important Notes

- Never commit `.env` files or Google service account JSON files
- Use dry-run mode for testing changes to prevent unwanted processing
- Database migrations should be tested thoroughly before production
- Frontend build must be completed before API server can serve static files
- Manager detection patterns may need updates for new team members