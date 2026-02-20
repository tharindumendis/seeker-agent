"""Run the Seeker Agent web server."""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from api.server import app
    
    print("=" * 70)
    print("🌐 Starting Seeker Agent Web Server")
    print("=" * 70)
    print()
    print("📍 Web Interface: http://localhost:8000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Alternative API docs: http://localhost:8000/redoc")
    print()
    print("=" * 70)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
