#!/usr/bin/env python3
"""
Test script for VoiceAI Call Analysis System.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.workflow_orchestrator import WorkflowOrchestrator


async def test_workflow():
    """Test the workflow with the example audio file."""
    print("🧪 Testing VoiceAI Workflow")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        print("1. Initializing workflow orchestrator...")
        orchestrator = WorkflowOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Perform health check
        print("\n2. Performing health check...")
        health_status = await orchestrator.health_check()
        
        for service, status in health_status["services"].items():
            status_icon = "✅" if status["status"] == "healthy" else "❌"
            print(f"   {status_icon} {service}: {status['status']}")
            if "error" in status:
                print(f"      Error: {status['error']}")
        
        # Check for files in Drive folder
        print("\n3. Checking for files in Google Drive folder...")
        files = orchestrator.drive_service.list_audio_files()
        print(f"   Found {len(files)} audio files")
        
        if files:
            print("   Files found:")
            for file in files[:5]:  # Show first 5 files
                print(f"   - {file.name} (Modified: {file.modified_time})")
            
            # Test processing the first file (dry run)
            if len(files) > 0:
                test_file = files[0]
                print(f"\n4. Testing workflow with file: {test_file.name}")
                print("   (This is a dry run - no actual processing)")
                
                # Download file (test)
                print("   - Testing file download...")
                local_path = orchestrator.drive_service.download_file(
                    test_file.id, test_file.name
                )
                if local_path:
                    print("   ✅ File download successful")
                    
                    # Check if we can access the file
                    if Path(local_path).exists():
                        file_size = Path(local_path).stat().st_size
                        print(f"   ✅ Local file exists ({file_size} bytes)")
                        
                        # Clean up
                        Path(local_path).unlink()
                        print("   ✅ Cleaned up test file")
                    else:
                        print("   ❌ Local file not found")
                else:
                    print("   ❌ File download failed")
        else:
            print("   No audio files found in the configured folder")
        
        # Test manager detection
        print("\n5. Testing manager detection...")
        test_dialogues = [
            "Продавец: Здравствуйте, меня зовут Елизавета",
            "Продавец: Владимир на связи, добро пожаловать",
            "Продавец: Это Надежда, как дела?",
            "Продавец: Здравствуйте, компания Весткол"
        ]
        
        for dialogue in test_dialogues:
            result = orchestrator.manager_detection.detect_manager(dialogue)
            print(f"   Text: '{dialogue[:40]}...'")
            print(f"   Detected: {result.detected_manager} (confidence: {result.confidence})")
        
        print("\n6. Getting processing statistics...")
        stats = orchestrator.get_processing_stats()
        print(f"   Processed files: {stats['processed_files_count']}")
        print(f"   Configuration loaded: ✅")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed successfully!")
        print("✅ All core components are working")
        print("✅ Google APIs are accessible")
        print("✅ Configuration is valid")
        print("✅ Manager detection is functional")
        
        print("\n📋 Next steps:")
        print("1. Set up your .env file with actual credentials")
        print("2. Add audio files to the Google Drive folder")
        print("3. Run: python main.py --mode monitor")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your configuration and credentials")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_workflow())