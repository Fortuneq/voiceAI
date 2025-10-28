#!/usr/bin/env python3
"""
VoiceAI Call Analysis System - Main Entry Point

This application replicates the n8n workflow for automated call analysis.
It monitors Google Drive for new audio files, transcribes them, analyzes
call quality, and saves results to Google Sheets.
"""

import asyncio
import argparse
import sys
from pathlib import Path

from loguru import logger

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.workflow_orchestrator import WorkflowOrchestrator


def setup_logging():
    """Configure logging for the application."""
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "voiceai.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days",
        compression="zip"
    )


async def main():
    """Main application entry point."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="VoiceAI Call Analysis System - Replicates n8n workflow"
    )
    parser.add_argument(
        "--mode",
        choices=["monitor", "process-file", "analyze-file", "health-check", "stats"],
        default="monitor",
        help="Operation mode (default: monitor)"
    )
    parser.add_argument(
        "--file-id",
        help="Google Drive file ID to process (for process-file mode)"
    )
    parser.add_argument(
        "--output-file",
        help="Output JSON file path for analyze-file mode (default: analysis_result.json)",
        default="analysis_result.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually processing files"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("VoiceAI Call Analysis System Starting")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Drive Folder ID: {config.google_drive_folder_id}")
    logger.info(f"Spreadsheet ID: {config.google_spreadsheet_id}")
    logger.info(f"OpenAI Model: {config.openai_model}")
    logger.info("=" * 60)
    
    try:
        orchestrator = WorkflowOrchestrator()
        
        if args.mode == "monitor":
            logger.info("Starting continuous monitoring mode")
            if args.dry_run:
                logger.info("DRY RUN MODE - No files will be processed")
                # In dry run, just check for new files without processing
                while True:
                    new_files = orchestrator.drive_service.get_new_files()
                    if new_files:
                        logger.info(f"Would process {len(new_files)} files:")
                        for file in new_files:
                            logger.info(f"  - {file.name} (ID: {file.id})")
                    await asyncio.sleep(config.poll_interval_seconds)
            else:
                await orchestrator.run_continuous_monitoring()
        
        elif args.mode == "process-file":
            if not args.file_id:
                logger.error("File ID is required for process-file mode")
                sys.exit(1)
            
            logger.info(f"Processing single file with ID: {args.file_id}")
            if args.dry_run:
                logger.info("DRY RUN MODE - File will not be processed")
                metadata = orchestrator.drive_service.get_file_metadata(args.file_id)
                if metadata:
                    logger.info(f"Would process file: {metadata['name']}")
                else:
                    logger.error("File not found or not accessible")
            else:
                result = await orchestrator.process_file_by_id(args.file_id)
                if result:
                    logger.info("File processed successfully")
                    logger.info(f"Manager: {result.detected_manager}")
                    logger.info(f"Quality Score: {result.quality_scores.total_score}")
                else:
                    logger.error("File processing failed")
                    sys.exit(1)
        
        elif args.mode == "analyze-file":
            if not args.file_id:
                logger.error("File ID is required for analyze-file mode")
                sys.exit(1)
            
            logger.info(f"Analyzing single file with ID: {args.file_id}")
            logger.info(f"Output will be saved to: {args.output_file}")
            
            result = await orchestrator.analyze_file_to_json(args.file_id, args.output_file)
            if result:
                logger.info("File analyzed successfully")
                logger.info(f"Results saved to: {args.output_file}")
                logger.info(f"Manager: {result.detected_manager}")
                logger.info(f"Quality Score: {result.quality_scores.total_score}")
            else:
                logger.error("File analysis failed")
                sys.exit(1)
        
        elif args.mode == "health-check":
            logger.info("Performing health check")
            health_status = await orchestrator.health_check()
            
            print("\n" + "=" * 50)
            print("HEALTH CHECK RESULTS")
            print("=" * 50)
            
            for service, status in health_status["services"].items():
                status_icon = "✅" if status["status"] == "healthy" else "❌"
                print(f"{status_icon} {service.upper()}: {status['status']}")
                if "error" in status:
                    print(f"   Error: {status['error']}")
                elif "files_found" in status:
                    print(f"   Files found: {status['files_found']}")
                elif "headers_count" in status:
                    print(f"   Headers count: {status['headers_count']}")
            
            print("\n" + "=" * 50)
        
        elif args.mode == "stats":
            logger.info("Getting processing statistics")
            stats = orchestrator.get_processing_stats()
            
            print("\n" + "=" * 50)
            print("PROCESSING STATISTICS")
            print("=" * 50)
            print(f"Processed files: {stats['processed_files_count']}")
            print(f"Last check: {stats['last_processing_time']}")
            print("\nConfiguration:")
            for key, value in stats['configuration'].items():
                print(f"  {key}: {value}")
            print("=" * 50)
    
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        logger.info("VoiceAI Call Analysis System shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())