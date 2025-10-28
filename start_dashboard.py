#!/usr/bin/env python3
"""
VoiceAI Dashboard Startup Script

Starts both the FastAPI backend server and the React frontend development server.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from threading import Thread

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting VoiceAI API Server...")
    try:
        # Start FastAPI server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "src.api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=Path(__file__).parent)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")
        return None

def start_frontend():
    """Start the React frontend development server."""
    print("⚛️  Starting React Frontend...")
    try:
        frontend_dir = Path(__file__).parent / "frontend"
        
        if not frontend_dir.exists():
            print(f"❌ Frontend directory not found: {frontend_dir}")
            return None
        
        # Check if node_modules exists, if not run npm install
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            install_process = subprocess.run([
                "npm", "install"
            ], cwd=frontend_dir, capture_output=True, text=True)
            
            if install_process.returncode != 0:
                print(f"❌ Failed to install dependencies: {install_process.stderr}")
                return None
        
        # Start development server
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=frontend_dir)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")
        return None

def main():
    """Main function to start both servers."""
    print("🎯 VoiceAI Call Analysis Dashboard")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/api_server.py").exists():
        print("❌ Please run this script from the VoiceAI project root directory")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend server
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
            print("✅ Backend server starting on http://localhost:8000")
            time.sleep(3)  # Give backend time to start
        
        # Start frontend server
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
            print("✅ Frontend server starting on http://localhost:3001")
        
        if not processes:
            print("❌ Failed to start any servers")
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("🎉 VoiceAI Dashboard is starting up!")
        print("📊 Dashboard: http://localhost:3001")
        print("🔌 API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        print("\n💡 Press Ctrl+C to stop all servers")
        
        # Wait for processes
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for process in processes[:]:
                    if process.poll() is not None:
                        print(f"⚠️  Process {process.pid} has stopped")
                        processes.remove(process)
                
                if not processes:
                    print("❌ All processes have stopped")
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutting down servers...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up processes
        for process in processes:
            try:
                print(f"🔄 Stopping process {process.pid}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"🔨 Force killing process {process.pid}...")
                process.kill()
            except Exception as e:
                print(f"⚠️  Error stopping process: {e}")
        
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()