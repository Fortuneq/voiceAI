# VoiceAI Database Configuration

This document describes the database setup and configuration for the VoiceAI Call Analysis System.

## Database Schema

The system uses a relational database to store call analysis metrics for multiple managers. The schema includes:

- **managers**: Store manager information (name, email, department)
- **call_records**: Store basic call information and transcription
- **checklist_analysis**: Store checklist-based analysis results (0/0.5/1 scoring)
- **ai_analysis**: Store AI-based analysis results (0-100 scoring)
- **legacy_quality_scores**: Store legacy quality scoring data

## Configuration

Database settings are configured in your `.env` file:

```env
# Database Configuration
DATABASE_URL=sqlite:///./voiceai_calls.db
SAVE_TO_DATABASE=true
SAVE_TO_SHEETS=false
```

### Database URL Examples

**SQLite (default):**
```
DATABASE_URL=sqlite:///./voiceai_calls.db
```

**PostgreSQL:**
```
DATABASE_URL=postgresql://username:password@localhost:5432/voiceai_db
```

**MySQL:**
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/voiceai_db
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database tables:**
   ```bash
   python setup_database.py
   ```

3. **Verify setup:**
   ```bash
   python main.py --mode health-check
   ```

## Usage

The system automatically saves call analysis results to the database when `SAVE_TO_DATABASE=true`.

### Dual Storage Mode

You can enable both database and Google Sheets storage:

```env
SAVE_TO_DATABASE=true
SAVE_TO_SHEETS=true
```

### Database-Only Mode

To use only database storage (recommended for production):

```env
SAVE_TO_DATABASE=true
SAVE_TO_SHEETS=false
```

## Data Structure

### Checklist Analysis
- 7 stages with multiple criteria each
- Scoring: 0 (not done), 0.5 (partially done), 1 (fully done)
- Automatic calculation of stage totals and overall score

### AI Analysis
- 7 evaluation criteria (contact establishment, qualification, etc.)
- Scoring: 0-100 scale
- Includes explanations for each score
- Additional fields: summary, client info, next steps

### Manager Performance
- Track calls per manager
- Calculate average scores over time
- Support for 30+ managers
- Inbound vs outbound call classification

## Database Views

The schema includes analytical views for reporting:

- **manager_performance_summary**: Aggregate performance metrics per manager
- **call_analysis_overview**: Complete call analysis data with computed scores

## Health Check

Use the health check command to verify database connectivity:

```bash
python main.py --mode health-check
```

This will show the status of all services including database connection and table counts.