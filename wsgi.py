"""
WSGI entry point for Basketball Dashboard
This file provides a clean interface for gunicorn deployment
"""

from app import app, create_app

# Initialize the application
application = create_app()

if __name__ == "__main__":
    application.run() 