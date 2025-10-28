"""
Google Drive service for monitoring and downloading audio files.
"""

import os
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from loguru import logger

from config import config
from models import AudioFile


class GoogleDriveService:
    """Service for interacting with Google Drive API."""
    
    def __init__(self, database_service=None):
        """Initialize Google Drive service."""
        self.credentials = self._get_credentials()
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = config.google_drive_folder_id
        self.processed_files: Dict[str, datetime] = {}  # Legacy tracking
        self.database_service = database_service
        
    def _get_credentials(self) -> Credentials:
        """Get Google API credentials from service account file."""
        try:
            credentials = Credentials.from_service_account_file(
                config.google_service_account_file,
                scopes=[
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            logger.info("Successfully loaded Google Drive credentials")
            return credentials
        except Exception as e:
            logger.error(f"Failed to load Google Drive credentials: {e}")
            raise
    
    def list_audio_files(self) -> List[AudioFile]:
        """List all audio files in the monitored folder."""
        try:
            # Query for audio files in the specific folder
            query = (
                f"'{self.folder_id}' in parents and "
                f"(mimeType contains 'audio/' or "
                f"name contains '.mp3' or "
                f"name contains '.wav' or "
                f"name contains '.m4a' or "
                f"name contains '.flac') and "
                f"trashed = false"
            )
            
            results = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, modifiedTime, size, mimeType)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            audio_files = []
            
            for file_info in files:
                try:
                    # Parse modification time
                    modified_time = datetime.fromisoformat(
                        file_info['modifiedTime'].replace('Z', '+00:00')
                    )
                    
                    audio_file = AudioFile(
                        id=file_info['id'],
                        name=file_info['name'],
                        modified_time=modified_time,
                        size=int(file_info.get('size', 0)),
                        mime_type=file_info.get('mimeType', 'unknown')
                    )
                    audio_files.append(audio_file)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse file info for {file_info.get('name', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(audio_files)} audio files in Drive folder")
            return audio_files
            
        except Exception as e:
            logger.error(f"Failed to list audio files: {e}")
            return []
    
    def get_new_files(self) -> List[AudioFile]:
        """Get files that haven't been processed yet."""
        all_files = self.list_audio_files()
        new_files = []
        
        for file in all_files:
            # Use database tracking if available, otherwise fall back to legacy method
            if self.database_service:
                # Mark file as discovered in database
                is_new = self.database_service.mark_file_discovered(
                    file.id, file.name, file.modified_time
                )
                
                # Check if file needs processing (new or not completed)
                if not self.database_service.is_file_processed(file.id):
                    new_files.append(file)
            else:
                # Legacy method - check in-memory tracking
                if (file.id not in self.processed_files or 
                    file.modified_time > self.processed_files[file.id]):
                    new_files.append(file)
        
        if new_files:
            logger.info(f"Found {len(new_files)} new/modified files to process")
        
        return new_files
    
    def discover_all_files(self) -> int:
        """Discover all files in Drive and add to database tracking. Returns count of new files."""
        if not self.database_service:
            logger.warning("Database service not available for file discovery")
            return 0
        
        all_files = self.list_audio_files()
        new_files_count = 0
        
        logger.info(f"Discovering {len(all_files)} files in Google Drive folder")
        
        for file in all_files:
            is_new = self.database_service.mark_file_discovered(
                file.id, file.name, file.modified_time
            )
            if is_new:
                new_files_count += 1
        
        logger.info(f"Discovery complete: {new_files_count} new files found")
        return new_files_count
    
    def download_file(self, file_id: str, file_name: str) -> Optional[str]:
        """Download a file from Google Drive to local storage."""
        try:
            # Create safe filename
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            local_path = Path(config.audio_temp_dir) / safe_filename
            
            # Check if file already exists
            if local_path.exists():
                logger.info(f"File {safe_filename} already exists locally")
                return str(local_path)
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            
            with open(local_path, 'wb') as local_file:
                downloader = MediaIoBaseDownload(local_file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.info(f"Successfully downloaded {file_name} to {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to download file {file_name}: {e}")
            return None
    
    def mark_file_processed(self, file_id: str, modified_time: datetime):
        """Mark a file as processed."""
        self.processed_files[file_id] = modified_time
        logger.debug(f"Marked file {file_id} as processed")
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files."""
        try:
            temp_dir = Path(config.audio_temp_dir)
            if not temp_dir.exists():
                return
            
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        logger.debug(f"Cleaned up old temp file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path.name}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metadata for a specific file."""
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id, name, size, mimeType, modifiedTime, createdTime, parents"
            ).execute()
            
            return file_metadata
            
        except Exception as e:
            logger.error(f"Failed to get file metadata for {file_id}: {e}")
            return None