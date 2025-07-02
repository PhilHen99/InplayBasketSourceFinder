#!/usr/bin/env python3
"""
Heroku Environment Setup Helper
Run this script to set up environment variables for your Heroku app
"""

import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error: {result.stderr}")
            return False
        print(result.stdout)
        return True
    except Exception as e:
        print(f"Exception running command: {e}")
        return False

def main():
    app_name = input("Enter your Heroku app name: ").strip()
    
    if not app_name:
        print("App name is required!")
        sys.exit(1)
    
    print(f"\nSetting up environment variables for {app_name}...")
    
    # Basic Flask settings
    env_vars = {
        'SECRET_KEY': '1PjjPUPGodLjFhdE_3RxF9rMaLtWrGwPC',
        'FLASK_DEBUG': 'false',
        'ENVIRONMENT': 'production',
        'HOST': '0.0.0.0',
        'PORT': '5000',
        'LOG_LEVEL': 'INFO',
        'DATA_PROVIDER': 'local',  # Start with local, change later if needed
        'DATA_REFRESH_INTERVAL': '1440'
    }
    
    print("\n🔧 Setting environment variables...")
    for key, value in env_vars.items():
        command = f'heroku config:set {key}="{value}" --app {app_name}'
        print(f"Setting {key}...")
        if not run_command(command):
            print(f"Failed to set {key}")
    
    print("\n✅ Basic environment variables set!")
    print("\n⚠️  IMPORTANT: Change the SECRET_KEY to a secure random value:")
    print(f"   heroku config:set SECRET_KEY=\"$(python -c 'import secrets; print(secrets.token_urlsafe(32))')\" --app {app_name}")
    
    print("\n📝 Next steps:")
    print("1. Deploy your app: git push heroku main")
    print("2. Check logs: heroku logs --tail --app", app_name)
    print("3. Open your app: heroku open --app", app_name)

if __name__ == "__main__":
    main() 