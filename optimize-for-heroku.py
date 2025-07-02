#!/usr/bin/env python3
"""
Heroku Cost Optimization Script
Run this after deployment to optimize for the $13/month student budget
"""

import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    app_name = input("Enter your Heroku app name: ").strip()
    
    if not app_name:
        print("❌ App name is required!")
        sys.exit(1)
    
    print(f"\n🚀 Optimizing {app_name} for cost efficiency...")
    print("💰 Target: Stay within $13/month GitHub Student Pack budget\n")
    
    optimizations = [
        # Scale to hobby dyno (most important cost saving)
        (f'heroku ps:scale web=1:hobby --app {app_name}', 
         'Scale to Hobby dyno ($7/month instead of $25)'),
        
        # Optimize environment variables for cost
        (f'heroku config:set DATA_REFRESH_INTERVAL=1440 --app {app_name}', 
         'Set data refresh to daily (reduces processing)'),
        
        (f'heroku config:set ENABLE_CACHING=true --app {app_name}', 
         'Enable caching to reduce processing overhead'),
        
        (f'heroku config:set CACHE_TIMEOUT=86400 --app {app_name}', 
         'Set cache timeout to 24 hours'),
        
        (f'heroku config:set DATA_PROVIDER=local --app {app_name}', 
         'Use local Excel data (no cloud API costs)'),
        
        (f'heroku config:set LAZY_LOAD_MAP=true --app {app_name}', 
         'Enable lazy loading for maps'),
        
        (f'heroku config:set REDUCE_MEMORY=true --app {app_name}', 
         'Enable memory optimizations'),
        
        (f'heroku config:set WEB_CONCURRENCY=1 --app {app_name}', 
         'Optimize worker processes for hobby dyno'),
        
        (f'heroku config:set PYTHONUNBUFFERED=1 --app {app_name}', 
         'Optimize Python output buffering'),
        
        # Generate a secure secret key
        (f'heroku config:set SECRET_KEY="$(python -c "import secrets; print(secrets.token_urlsafe(32))")" --app {app_name}', 
         'Set secure secret key'),
    ]
    
    success_count = 0
    for command, description in optimizations:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n📊 Optimization Results:")
    print(f"✅ {success_count}/{len(optimizations)} optimizations applied")
    
    if success_count == len(optimizations):
        print("\n🎉 All optimizations applied successfully!")
        print("\n💰 Expected monthly cost: $7 (Hobby dyno)")
        print("📈 Remaining budget: $6/month for experiments")
        print("\n📝 Next steps:")
        print(f"   1. Deploy: git push heroku main")
        print(f"   2. Check logs: heroku logs --tail --app {app_name}")
        print(f"   3. Open app: heroku open --app {app_name}")
        print(f"   4. Monitor usage: heroku ps --app {app_name}")
        
        print("\n⚡ Performance Tips:")
        print("   • App sleeps after 30 min of inactivity (normal for hobby dyno)")
        print("   • First visit after sleep takes 10-30 seconds to wake up")
        print("   • Map and data are cached for 24 hours to save resources")
        print("   • Perfect for portfolio/demo projects!")
    else:
        print(f"\n⚠️  Some optimizations failed. Check the errors above.")
        print("You can run this script again or apply settings manually.")
    
    print(f"\n🔗 Monitor your app:")
    print(f"   Dashboard: https://dashboard.heroku.com/apps/{app_name}")
    print(f"   Billing: https://dashboard.heroku.com/account/billing")

if __name__ == "__main__":
    main() 