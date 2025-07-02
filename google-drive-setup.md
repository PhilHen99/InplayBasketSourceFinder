# 🚀 Google Drive Integration Setup

## The Google Drive functionality is already built into your app! Here's how to enable it:

### Step 1: Set Environment Variables (Heroku)

```bash
# Enable Google Drive as the data source
heroku config:set DATA_PROVIDER=google_drive --app your-app-name

# Set your Google Drive file ID (get from sharing URL)
heroku config:set GOOGLE_DRIVE_FILE_ID=your_file_id_here --app your-app-name

# Set credentials path
heroku config:set GOOGLE_CREDENTIALS_PATH=./google-service-account.json --app your-app-name

# Set refresh interval (1440 = 24 hours)
heroku config:set DATA_REFRESH_INTERVAL=1440 --app your-app-name
```

### Step 2: Get Your Google Drive File ID

1. Go to your Google Drive file
2. Right-click → "Get shareable link"
3. Copy the file ID from the URL:
   `https://drive.google.com/file/d/1ABC123xyz.../view`
   Your file ID is: `1ABC123xyz...`

### Step 3: Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API
4. Create a Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Download the JSON credentials file
5. Share your Excel file with the service account email

### Step 4: Add Credentials to Heroku

```bash
# Upload the service account JSON file
heroku config:set GOOGLE_CREDENTIALS_JSON="$(cat path/to/your/service-account.json)" --app your-app-name
```

### Step 5: Update Your App to Use Credentials

The app will automatically use Google Drive when these variables are set!

## 🔄 Benefits of Google Drive Integration

- ✅ **Real-time updates**: Change the Excel file in Google Drive, app updates automatically
- ✅ **Team collaboration**: Multiple people can update the data
- ✅ **Version control**: Google Drive keeps version history
- ✅ **Automatic fallback**: If Google Drive fails, uses local Excel file 