# 🏀 Basketball Dashboard - Heroku Deployment

A professional basketball teams dashboard with gender filtering and interactive maps, optimized for **$7/month Heroku deployment**.

## ✨ Features

- 🔍 **Smart Filtering**: Search teams by country, league, sport, and gender
- 🎨 **Gender Color Coding**: Pastel blue for men's teams, pastel pink for women's teams  
- 🗺️ **Interactive Map**: Click countries to filter teams by location
- 📱 **Mobile Responsive**: Works perfectly on all devices
- ☁️ **Cloud Ready**: Supports Google Drive, SharePoint, AWS S3 data sources

## 🚀 Quick Deploy to Heroku (Only $7/month!)

### Prerequisites
- GitHub Student Pack ($13/month credits)
- Heroku CLI installed
- Git repository

### Option 1: Automated Deployment
```bash
# Login to Heroku
heroku login

# Run the optimized deployment script
chmod +x deploy-optimized.sh
./deploy-optimized.sh
```

### Option 2: Step-by-Step
```bash
# Create Heroku app
heroku create your-app-name

# Optimize for cost (reduces to $7/month)
python optimize-for-heroku.py

# Deploy
git push heroku main
```

### Option 3: Manual Setup
```bash
heroku create your-app-name
heroku ps:scale web=1:hobby --app your-app-name  # $7/month dyno
heroku config:set DATA_REFRESH_INTERVAL=1440 --app your-app-name
git push heroku main
heroku open --app your-app-name
```

## 💰 Cost Breakdown

| Component | Cost | Features |
|-----------|------|----------|
| **Hobby Dyno** | $7/month | Auto-sleep after 30min, 10-30s wake time |
| **Remaining Budget** | $6/month | Available for add-ons/experiments |
| **Total Student Pack Usage** | 54% | Well within $13/month budget |

## 📁 Project Structure

```
basketball-dashboard/
├── app.py                    # Main Flask application
├── Procfile                  # Heroku configuration
├── runtime.txt               # Python version
├── requirements.txt          # Dependencies (optimized)
├── wsgi.py                   # WSGI entry point
├── config.py                 # App configuration
├── Basketball Sources Links.xlsx # Data file
├── templates/                # HTML templates
├── static/                   # CSS & JS files
├── services/                 # Data integration
├── data/                     # Country coordinates
└── deploy-optimized.sh       # Deployment script
```

## 🔧 Configuration

### Environment Variables
```bash
# Basic settings
SECRET_KEY=your-secure-key
DATA_PROVIDER=local  # or google_drive, sharepoint, aws_s3
DATA_REFRESH_INTERVAL=1440  # 24 hours

# Cost optimizations
ENABLE_CACHING=true
CACHE_TIMEOUT=86400
LAZY_LOAD_MAP=true
REDUCE_MEMORY=true
```

### Google Drive Integration (Optional)
See `google-drive-setup.md` for complete setup instructions.

## 🎯 Gender Filtering

The app automatically detects:
- **Men's Basketball**: NCAA leagues without "Women" 
- **Women's Basketball**: NCAA Women leagues
- **Color Coding**: Blue borders/badges for men, pink for women

## 🛠️ Development

```bash
# Local development
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

## 📊 Performance Features

- ✅ **Smart Caching**: Map cached for 24 hours
- ✅ **Memory Optimization**: Only loads essential data columns  
- ✅ **Lazy Loading**: Components load only when needed
- ✅ **Efficient Filtering**: Client-side + server-side optimization

## 🔗 Links

- **Live Demo**: `https://your-app-name.herokuapp.com`
- **Heroku Dashboard**: `https://dashboard.heroku.com/apps/your-app-name`
- **GitHub Repository**: `https://github.com/PhilHen99/InplayBasketSourceFinder`

## 📞 Support

- Cost optimization help: See `cost-optimization.md`
- Deployment issues: Check `heroku logs --tail`
- Feature requests: Open GitHub issue

---

**🎉 Total cost: Only $7/month for a professional basketball dashboard!** 