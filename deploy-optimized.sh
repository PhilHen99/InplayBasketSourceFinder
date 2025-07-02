#!/bin/bash
# 🚀 Optimized Heroku Deployment Script for Student Budget
# This script deploys your Basketball Dashboard for only $7/month

echo "🏀 Basketball Dashboard - Optimized Heroku Deployment"
echo "💰 Target: $7/month (within $13 student budget)"
echo ""

# Check if user is logged into Heroku
if ! heroku whoami > /dev/null 2>&1; then
    echo "❌ Please login to Heroku first: heroku login"
    exit 1
fi

# Get app name from user
read -p "Enter your Heroku app name (or press Enter for auto-generated): " APP_NAME

# Create Heroku app
if [ -z "$APP_NAME" ]; then
    echo "🔧 Creating Heroku app with auto-generated name..."
    heroku create
    APP_NAME=$(heroku apps:info --json | python -c "import sys, json; print(json.load(sys.stdin)['name'])")
else
    echo "🔧 Creating Heroku app: $APP_NAME"
    heroku create $APP_NAME
fi

echo "✅ Created app: $APP_NAME"

# Set optimized environment variables
echo "🔧 Setting cost-optimized environment variables..."

heroku config:set \
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
    FLASK_DEBUG=false \
    ENVIRONMENT=production \
    DATA_PROVIDER=local \
    DATA_REFRESH_INTERVAL=1440 \
    ENABLE_CACHING=true \
    CACHE_TIMEOUT=86400 \
    LAZY_LOAD_MAP=true \
    REDUCE_MEMORY=true \
    WEB_CONCURRENCY=1 \
    PYTHONUNBUFFERED=1 \
    --app $APP_NAME

# Deploy the application
echo "🚀 Deploying application..."
git push heroku main

# Scale to hobby dyno for cost efficiency
echo "💰 Scaling to Hobby dyno ($7/month)..."
heroku ps:scale web=1:hobby --app $APP_NAME

# Open the application
echo "🎉 Deployment complete!"
echo ""
echo "📊 Cost Summary:"
echo "   💰 Monthly cost: $7 (Hobby dyno)"
echo "   📈 Student budget remaining: $6/month"
echo "   ⏰ Sleeps after 30 min (normal for hobby dyno)"
echo ""
echo "🔗 Your app is ready:"
echo "   🌐 URL: https://$APP_NAME.herokuapp.com"
echo "   📊 Dashboard: https://dashboard.heroku.com/apps/$APP_NAME"
echo ""

# Ask if user wants to open the app
read -p "Open your app now? (y/n): " OPEN_APP
if [[ $OPEN_APP =~ ^[Yy]$ ]]; then
    heroku open --app $APP_NAME
fi

echo "✅ Deployment successful! Your Basketball Dashboard is live for only $7/month!" 