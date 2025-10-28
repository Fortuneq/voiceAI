"""
Main workflow orchestrator for VoiceAI Call Analysis System.
"""

import asyncio
import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from loguru import logger

from .config import config
from .models import ProcessingResult, AudioFile
from .google_drive_service import GoogleDriveService
from .openai_service import OpenAIService
from .manager_detection import ManagerDetectionService
from .google_sheets_service import GoogleSheetsService


class WorkflowOrchestrator:
    """Main orchestrator that coordinates the entire call analysis workflow."""
    
    def __init__(self):
        """Initialize the workflow orchestrator with all services."""
        logger.info("Initializing VoiceAI Workflow Orchestrator")
        
        try:
            self.drive_service = GoogleDriveService()
            self.openai_service = OpenAIService()
            self.manager_detection = ManagerDetectionService()
            self.sheets_service = GoogleSheetsService()
            
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def run_continuous_monitoring(self):
        """
        Run continuous monitoring of Google Drive folder for new audio files.
        
        This replicates the n8n trigger functionality with polling.
        """
        logger.info("Starting continuous monitoring of Google Drive folder")
        logger.info(f"Monitoring folder ID: {config.google_drive_folder_id}")
        logger.info(f"Poll interval: {config.poll_interval_seconds} seconds")
        
        while True:
            try:
                await self.process_new_files()
                
                # Clean up old temp files periodically
                if datetime.now().minute % 30 == 0:  # Every 30 minutes
                    self.drive_service.cleanup_temp_files()
                
                # Wait for next poll
                await asyncio.sleep(config.poll_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Stopping monitoring due to user interrupt")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying
    
    async def process_new_files(self):
        """Process any new audio files found in the Drive folder."""
        try:
            new_files = self.drive_service.get_new_files()
            
            if not new_files:
                logger.debug("No new files to process")
                return
            
            logger.info(f"Processing {len(new_files)} new files")
            
            for audio_file in new_files:
                try:
                    await self.process_single_file(audio_file)
                    # Mark file as processed
                    self.drive_service.mark_file_processed(
                        audio_file.id, 
                        audio_file.modified_time
                    )
                except Exception as e:
                    logger.error(f"Failed to process file {audio_file.name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing new files: {e}")
    
    async def process_single_file(self, audio_file: AudioFile) -> Optional[ProcessingResult]:
        """
        Process a single audio file through the complete workflow.
        
        This replicates the exact n8n workflow sequence:
        1. Download file from Google Drive
        2. Transcribe audio using OpenAI
        3. Tag dialogue roles using GPT-4o-mini
        4. Analyze call quality using GPT-4o-mini  
        5. Detect manager from dialogue
        6. Save results to appropriate Google Sheets
        """
        logger.info(f"Processing audio file: {audio_file.name}")
        
        try:
            # Step 1: Download file from Google Drive
            logger.debug("Step 1: Downloading audio file")
            local_file_path = self.drive_service.download_file(
                audio_file.id, 
                audio_file.name
            )
            
            if not local_file_path:
                logger.error("Failed to download audio file")
                return None
            
            # Step 2: Transcribe audio using OpenAI
            logger.debug("Step 2: Transcribing audio")
            transcription = await self.openai_service.transcribe_audio(local_file_path)
            
            if not transcription:
                logger.error("Failed to transcribe audio")
                return None
            
            # Step 3: Tag dialogue roles using GPT-4o-mini 
            logger.debug("Step 3: Tagging dialogue with speaker roles")
            tagged_dialogue = await self.openai_service.tag_dialogue_roles(
                transcription.text
            )
            
            if not tagged_dialogue:
                logger.error("Failed to tag dialogue roles")
                return None
            
            # Step 4: Analyze call quality using GPT-4o-mini
            logger.debug("Step 4: Analyzing call quality")
            quality_analysis = await self.openai_service.analyze_call_quality(
                tagged_dialogue.content
            )
            
            if not quality_analysis:
                logger.error("Failed to analyze call quality")
                return None
            
            # Step 5: Detect manager from dialogue
            logger.debug("Step 5: Detecting manager")
            manager_result = self.manager_detection.detect_manager(
                tagged_dialogue.content
            )
            
            # Step 6: Structured detailed analysis
            logger.debug("Step 6: Performing structured analysis")
            detailed_analysis = await self.openai_service.structured_call_analysis(
                tagged_dialogue.content
            )
            
            # Create processing result
            result = ProcessingResult(
                audio_file=audio_file,
                transcription=transcription,
                tagged_dialogue=tagged_dialogue,
                quality_scores=quality_analysis,
                detailed_analysis=detailed_analysis,
                detected_manager=manager_result.detected_manager,
                processing_timestamp=datetime.now()
            )
            
            # Step 7: Save results to Google Sheets
            logger.debug("Step 7: Saving results to Google Sheets")
            
            # Save call quality analysis to manager-specific sheet
            success = self.sheets_service.append_call_analysis(result)
            if not success:
                logger.warning("Failed to save call analysis to sheets")
            
            # Save detailed analysis if available
            if detailed_analysis:
                detailed_success = self.sheets_service.append_detailed_analysis(result)
                if not detailed_success:
                    logger.warning("Failed to save detailed analysis to sheets")
            
            logger.info(f"Successfully processed {audio_file.name}")
            logger.info(f"Manager detected: {manager_result.detected_manager}")
            logger.info(f"Total call quality score: {quality_analysis.total_score}")
            
            # Clean up local file
            try:
                Path(local_file_path).unlink()
                logger.debug(f"Cleaned up local file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up local file: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {audio_file.name}: {e}")
            return None
    
    async def process_file_by_id(self, file_id: str) -> Optional[ProcessingResult]:
        """Process a specific file by its Google Drive ID."""
        try:
            # Get file metadata
            file_metadata = self.drive_service.get_file_metadata(file_id)
            if not file_metadata:
                logger.error(f"Could not get metadata for file ID: {file_id}")
                return None
            
            # Create AudioFile object
            audio_file = AudioFile(
                id=file_metadata['id'],
                name=file_metadata['name'],
                modified_time=datetime.fromisoformat(
                    file_metadata['modifiedTime'].replace('Z', '+00:00')
                ),
                size=int(file_metadata.get('size', 0)),
                mime_type=file_metadata.get('mimeType', 'unknown')
            )
            
            # Process the file
            return await self.process_single_file(audio_file)
            
        except Exception as e:
            logger.error(f"Error processing file by ID {file_id}: {e}")
            return None
    
    def get_processing_stats(self) -> dict:
        """Get statistics about processed files."""
        return {
            "processed_files_count": len(self.drive_service.processed_files),
            "last_processing_time": datetime.now().isoformat(),
            "configuration": {
                "drive_folder_id": config.google_drive_folder_id,
                "spreadsheet_id": config.google_spreadsheet_id,
                "poll_interval": config.poll_interval_seconds,
                "openai_model": config.openai_model
            }
        }
    
    async def health_check(self) -> dict:
        """Perform a health check of all services."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        try:
            # Check Google Drive service
            try:
                files = self.drive_service.list_audio_files()
                health_status["services"]["google_drive"] = {
                    "status": "healthy",
                    "files_found": len(files)
                }
            except Exception as e:
                health_status["services"]["google_drive"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Check Google Sheets service
            try:
                elizaveta_headers = self.sheets_service.get_worksheet_headers(
                    config.elizaveta_sheet_name
                )
                health_status["services"]["google_sheets"] = {
                    "status": "healthy",
                    "spreadsheet_accessible": True,
                    "headers_count": len(elizaveta_headers) if elizaveta_headers else 0
                }
            except Exception as e:
                health_status["services"]["google_sheets"] = {
                    "status": "error", 
                    "error": str(e)
                }
            
            # Check OpenAI service (simple test)
            health_status["services"]["openai"] = {
                "status": "configured",
                "model": config.openai_model
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            health_status["error"] = str(e)
        
        return health_status
    
    async def analyze_file_to_json(self, file_id: str, output_file: str) -> Optional[ProcessingResult]:
        """
        Analyze a specific file and save results to JSON file instead of Google Sheets.
        
        This performs the same analysis as process_single_file but saves to JSON.
        """
        logger.info(f"Analyzing file ID: {file_id} -> {output_file}")
        
        try:
            # Get file metadata
            file_metadata = self.drive_service.get_file_metadata(file_id)
            if not file_metadata:
                logger.error(f"Could not get metadata for file ID: {file_id}")
                return None
            
            # Create AudioFile object
            audio_file = AudioFile(
                id=file_metadata['id'],
                name=file_metadata['name'],
                modified_time=datetime.fromisoformat(
                    file_metadata['modifiedTime'].replace('Z', '+00:00')
                ),
                size=int(file_metadata.get('size', 0)),
                mime_type=file_metadata.get('mimeType', 'unknown')
            )
            
            # Step 1: Download file from Google Drive
            logger.debug("Step 1: Downloading audio file")
            local_file_path = self.drive_service.download_file(
                audio_file.id, 
                audio_file.name
            )
            
            if not local_file_path:
                logger.error("Failed to download audio file")
                return None
            
            # Step 2: Transcribe audio using OpenAI
            logger.debug("Step 2: Transcribing audio")
            transcription = await self.openai_service.transcribe_audio(local_file_path)
            
            if not transcription:
                logger.error("Failed to transcribe audio")
                return None
            
            # Step 3: Tag dialogue roles using GPT-4o-mini 
            logger.debug("Step 3: Tagging dialogue with speaker roles")
            tagged_dialogue = await self.openai_service.tag_dialogue_roles(
                transcription.text
            )
            
            if not tagged_dialogue:
                logger.error("Failed to tag dialogue roles")
                return None
            
            # Step 4: Analyze call quality using GPT-4o-mini
            logger.debug("Step 4: Analyzing call quality")
            quality_analysis = await self.openai_service.analyze_call_quality(
                tagged_dialogue.content
            )
            
            if not quality_analysis:
                logger.error("Failed to analyze call quality")
                return None
            
            # Step 5: Detect manager from dialogue
            logger.debug("Step 5: Detecting manager")
            manager_result = self.manager_detection.detect_manager(
                tagged_dialogue.content
            )
            
            # Step 6: Structured detailed analysis
            logger.debug("Step 6: Performing structured analysis")
            detailed_analysis = await self.openai_service.structured_call_analysis(
                tagged_dialogue.content
            )
            
            # Create processing result
            result = ProcessingResult(
                audio_file=audio_file,
                transcription=transcription,
                tagged_dialogue=tagged_dialogue,
                quality_scores=quality_analysis,
                detailed_analysis=detailed_analysis,
                detected_manager=manager_result.detected_manager,
                processing_timestamp=datetime.now()
            )
            
            # Save results to JSON file instead of Google Sheets
            logger.debug(f"Step 7: Saving results to JSON file: {output_file}")
            
            # Convert result to JSON-serializable format
            result_dict = {
                "file_info": {
                    "id": audio_file.id,
                    "name": audio_file.name,
                    "size": audio_file.size,
                    "mime_type": audio_file.mime_type,
                    "modified_time": audio_file.modified_time.isoformat()
                },
                "transcription": {
                    "text": transcription.text,
                    "duration": transcription.duration
                },
                "tagged_dialogue": {
                    "content": tagged_dialogue.content,
                    "timestamp": tagged_dialogue.timestamp.isoformat()
                },
                "quality_analysis": {
                    "call_type": quality_analysis.call_type,
                    "greeting_score": quality_analysis.greeting_score,
                    "contact_score": quality_analysis.contact_score,
                    "presentation_score": quality_analysis.presentation_score,
                    "objection_handling_score": quality_analysis.objection_handling_score,
                    "closing_score": quality_analysis.closing_score,
                    "greeting_stage_total": quality_analysis.greeting_stage_total,
                    "contact_stage_total": quality_analysis.contact_stage_total,
                    "presentation_stage_total": quality_analysis.presentation_stage_total,
                    "objection_stage_total": quality_analysis.objection_stage_total,
                    "closing_stage_total": quality_analysis.closing_stage_total,
                    "total_score": quality_analysis.total_score
                },
                "detailed_analysis": detailed_analysis.model_dump() if detailed_analysis else None,
                "detected_manager": manager_result.detected_manager,
                "processing_timestamp": result.processing_timestamp.isoformat()
            }
            
            # Write to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully analyzed {audio_file.name}")
            logger.info(f"Results saved to: {output_file}")
            logger.info(f"Manager detected: {manager_result.detected_manager}")
            logger.info(f"Total call quality score: {quality_analysis.total_score}")
            
            # Clean up local file
            try:
                Path(local_file_path).unlink()
                logger.debug(f"Cleaned up local file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up local file: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_id}: {e}")
            return None