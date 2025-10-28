# VoiceAI Call Analysis System

A Python application that replicates the n8n workflow for automated call analysis. It monitors Google Drive for new audio files, transcribes them using OpenAI, analyzes call quality, and saves results to Google Sheets.

## 🎯 Features

- **Automatic Google Drive Monitoring**: Continuously monitors a specified Google Drive folder for new audio files
- **OpenAI Transcription**: Uses Whisper API for accurate speech-to-text conversion
- **Role Tagging**: Automatically identifies and tags speaker roles (Client/Seller) in dialogues
- **Call Quality Analysis**: Analyzes calls using structured checklists and scoring
- **Manager Detection**: Identifies which manager (Елизавета/Владимир/Надежда) was involved in the call
- **Google Sheets Integration**: Automatically saves results to appropriate sheets based on detected manager
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## 🛠 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd VoiceAi
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google API credentials**:
   - Create a Google Cloud project
   - Enable Google Drive API and Google Sheets API
   - Create a service account and download the JSON key file
   - Share your Google Drive folder and Google Sheets with the service account email

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials and IDs
   ```

## ⚙️ Configuration

Edit the `.env` file with your specific settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google APIs Configuration  
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/your/service-account-key.json

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=1qb_o_yLNWVR8_LK98zKHstuEDNxNmGJW

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=1V2ERVA_VOraJiRTxCrSW1AUQeBYUG3XkFldQQTqrU5w

# Manager sheet names
ELIZAVETA_SHEET_NAME=Входящие Елизавета
VLADIMIR_SHEET_NAME=Входящие Владимир
NADEZHDA_SHEET_NAME=Входящие Надежда
ANALYSIS_SHEET_NAME=Анализ звонков

# Processing settings
POLL_INTERVAL_SECONDS=60
AUDIO_TEMP_DIR=./temp_audio
LOG_LEVEL=INFO
```

## 🚀 Usage

### Continuous Monitoring Mode (Default)
Monitor Google Drive folder and process new files automatically:
```bash
python main.py --mode monitor
```

### Process Single File
Process a specific file by its Google Drive ID:
```bash
python main.py --mode process-file --file-id <google_drive_file_id>
```

### Health Check
Check the status of all services:
```bash
python main.py --mode health-check
```

### Processing Statistics
View processing statistics:
```bash
python main.py --mode stats
```

### Dry Run Mode
Test the system without actually processing files:
```bash
python main.py --mode monitor --dry-run
```

## 📋 Workflow Process

The application follows the exact same sequence as the original n8n workflow:

1. **Google Drive Trigger**: Monitors folder `1qb_o_yLNWVR8_LK98zKHstuEDNxNmGJW` for new/updated audio files
2. **File Download**: Downloads audio files to local temporary storage
3. **Transcription**: Uses OpenAI Whisper to convert audio to text
4. **Role Tagging**: Uses GPT-4o-mini to tag dialogue with "Продавец:" and "Клиент:" labels
5. **Quality Analysis**: Analyzes call quality using structured checklist and returns JSON scores
6. **Manager Detection**: Uses regex patterns to detect manager names (Елизавета/Владимир/Надежда)
7. **Results Storage**: Saves analysis results to appropriate Google Sheets based on detected manager

## 📊 Output Format

### Call Quality Scores
The system generates structured JSON scores following the exact format from the n8n workflow:

```json
{
  "Тип звонка": "Исходящий",
  "Этап ПРИВЕТСТВИЕ": {
    "Корпоративное приветсвие": 1,
    "Тон добродушный, приветливый, есть улыбка в голосе": 0.5,
    "Не тараторит, не съедает слова": 1,
    "Итого": 2.5
  },
  "ВСЕГО": 16.5
}
```

### Google Sheets Integration
Results are automatically saved to the appropriate sheet based on the detected manager:
- **Входящие Елизавета**: For calls involving Елизавета
- **Входящие Владимир**: For calls involving Владимир  
- **Входящие Надежда**: For calls involving Надежда
- **Анализ звонков**: For detailed analysis results

## 🧰 Architecture

```
src/
├── config.py              # Configuration management
├── models.py               # Data models
├── google_drive_service.py # Google Drive API integration
├── openai_service.py       # OpenAI API integration  
├── manager_detection.py    # Manager detection logic
├── google_sheets_service.py # Google Sheets API integration
└── workflow_orchestrator.py # Main workflow coordination
```

## 🔧 Prompts and Configuration

The application uses the exact same prompts and configurations as the original n8n workflow:

- **Role Tagging Prompt**: Identical system prompt for identifying speaker roles
- **Quality Analysis Prompt**: Exact same checklist and JSON schema
- **Manager Detection**: Same regex patterns for name detection
- **Google Sheets Mapping**: Identical column mappings and data flow

## 📝 Logging

Logs are saved to:
- Console: Real-time colored output
- `logs/voiceai.log`: Rotating daily logs with 7-day retention

Log levels: DEBUG, INFO, WARNING, ERROR

## ⚡ Error Handling

- Comprehensive error handling for all API calls
- Automatic retry logic for transient failures
- Graceful degradation when services are unavailable
- Detailed error logging for troubleshooting

## 🔐 Security

- Service account authentication for Google APIs
- API keys stored in environment variables
- Temporary file cleanup after processing
- Read-only access to Google Drive (except for the monitored folder)

## 📋 Requirements

- Python 3.10+
- OpenAI API account with credits
- Google Cloud Platform account with enabled APIs
- Google Drive folder access
- Google Sheets access

## 🐛 Troubleshooting

1. **Google API Errors**: Ensure service account has proper permissions
2. **OpenAI Errors**: Check API key and credit balance
3. **File Processing Errors**: Verify audio file formats are supported
4. **Sheet Writing Errors**: Confirm sheet names match configuration

## 📈 Monitoring

The system provides:
- Real-time processing logs
- Health check endpoints
- Processing statistics
- File processing history

## 🔄 Workflow Comparison

This Python implementation maintains 100% functional parity with the original n8n workflow:

| n8n Node | Python Component | Function |
|----------|------------------|----------|
| Google Drive Trigger | GoogleDriveService.get_new_files() | Monitor folder for changes |
| Download file | GoogleDriveService.download_file() | Download audio files |
| Transcribe | OpenAIService.transcribe_audio() | Audio to text conversion |
| Message a model | OpenAIService.tag_dialogue_roles() | Role tagging with exact prompt |
| AI Agent2 | OpenAIService.analyze_call_quality() | Quality analysis with JSON schema |
| Switch | ManagerDetectionService.detect_manager() | Manager name detection |
| Google Sheets Append | GoogleSheetsService.append_call_analysis() | Save results to sheets |

The system ensures exact replication of all prompts, data flows, and output formats from the original n8n workflow.# voiceAI
