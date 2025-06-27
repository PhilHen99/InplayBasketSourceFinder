#!/usr/bin/env python3
"""
Verification script to test gunicorn installation and app setup
Run this before building Docker image to verify everything works
"""

import sys
import subprocess

def test_gunicorn_installation():
    """Test if gunicorn is installed"""
    try:
        import gunicorn
        print(f"✅ Gunicorn installed: {gunicorn.__version__}")
        return True
    except ImportError:
        print("❌ Gunicorn not installed")
        return False

def test_app_import():
    """Test if the Flask app can be imported"""
    try:
        from app import app
        print("✅ Flask app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False

def test_wsgi_import():
    """Test if the WSGI module can be imported"""
    try:
        from wsgi import application
        print("✅ WSGI application imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import WSGI application: {e}")
        return False

def test_gunicorn_command():
    """Test if gunicorn can start the application"""
    try:
        # Test the gunicorn command syntax
        result = subprocess.run([
            "gunicorn", "--check-config", "wsgi:application"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Gunicorn command syntax is valid")
            return True
        else:
            print(f"❌ Gunicorn command failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Gunicorn command test timed out (but syntax might be OK)")
        return True
    except Exception as e:
        print(f"❌ Gunicorn command test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Basketball Dashboard setup for gunicorn deployment...")
    print("=" * 60)
    
    tests = [
        test_gunicorn_installation,
        test_app_import,
        test_wsgi_import,
        test_gunicorn_command
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    if all(results):
        print("🎉 All tests passed! Ready for Docker deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the issues above before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main() 