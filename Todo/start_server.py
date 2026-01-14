import uvicorn
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, '.')

if __name__ == "__main__":
    # Set environment variables
    os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')
    os.environ.setdefault('BETTER_AUTH_SECRET', 'supersecretkeythatisatleast32characterslong')
    os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
    os.environ.setdefault('ENVIRONMENT', 'development')

    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"]
    )