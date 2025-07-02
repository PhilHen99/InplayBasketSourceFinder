from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import json
import os
import folium
import logging
from datetime import datetime, timedelta
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from typing import Optional

# Import our new modules
from config import config, load_country_coordinates
from services.data_integration import DataIntegrationService

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.secret_key
Bootstrap(app)

# Upload configuration (fallback for local files)
UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize services
data_service = DataIntegrationService()

# Global data storage
teams_data: Optional[pd.DataFrame] = None
countries = []
leagues = []
sports = []
country_coordinates = {}
last_data_refresh = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    """Load basketball teams data from configured source"""
    global teams_data, countries, leagues, sports, last_data_refresh
    
    try:
        if config.database.provider == 'local':
            # Load from local Excel file (fallback) - optimized for memory
            df = pd.read_excel("Basketball Sources Links.xlsx", 
                             dtype_backend='numpy_nullable',  # More memory efficient
                             engine='openpyxl')
        else:
            # Load from cloud provider
            df = data_service.fetch_excel_data(
                config.database.provider, 
                config.database.config
            )
        
        # Clean the data efficiently
        df = df.fillna('')
        
        # Memory optimization: only keep essential columns
        essential_cols = ['Team', 'Country', 'League', 'Sports', 'Twitter', 'Facebook', 'Instagram', 'Official Page', 'Other Links']
        available_cols = [col for col in essential_cols if col in df.columns]
        df = df[available_cols]
        
        teams_data = df

        # Update global filter options with memory optimization
        countries = sorted(df['Country'].unique().tolist())
        leagues = sorted(df['League'].unique().tolist())
        sports = sorted(df['Sports'].unique().tolist())

        last_data_refresh = datetime.now()
        
        logger.info(f"Successfully loaded {len(df)} teams from {config.database.provider}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        # Try to load fallback local file
        try:
            df = pd.read_excel("Basketball Sources Links.xlsx")
            df = df.fillna('')
            teams_data = df
            countries = sorted(df['Country'].unique())
            leagues = sorted(df['League'].unique())
            sports = sorted(df['Sports'].unique())
            last_data_refresh = datetime.now()
            logger.warning("Loaded fallback local data due to cloud provider error")
            return df
        except Exception as fallback_error:
            logger.error(f"Failed to load fallback data: {str(fallback_error)}")
            raise

def should_refresh_data():
    """Check if data should be refreshed based on configured interval"""
    if last_data_refresh is None:
        return True
    
    refresh_interval = timedelta(minutes=config.database.refresh_interval_minutes)
    return datetime.now() - last_data_refresh > refresh_interval

def get_country_coordinates():
    """Load country coordinates from JSON file"""
    global country_coordinates
    if not country_coordinates:
        country_coordinates = load_country_coordinates()
    return country_coordinates

def generate_map():
    """Generate the world map with team markers - optimized for cost reduction"""
    # Skip map generation if teams_data is None to save resources
    if teams_data is None:
        logger.warning("No teams data available for map generation")
        return
    
    # Check if map file exists and is recent (cache for 24 hours to reduce processing)
    map_file = 'static/map.html'
    if os.path.exists(map_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(map_file))
        if file_age.total_seconds() < 86400:  # 24 hours
            logger.info("Using cached map file to save resources")
            return
    
    # Create a lightweight map centered on a default location
    m = folium.Map(location=[20, 0], zoom_start=2, tiles='OpenStreetMap')
    
    coordinates = get_country_coordinates()
    
    # Optimize data processing for memory efficiency
    try:
        country_counts = teams_data['Country'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Count']
        
        # Limit markers to top 20 countries to reduce map size
        country_counts = country_counts.head(20)
        
        # Add markers to the map with optimized popup
        for _, row in country_counts.iterrows():
            country_name = row['Country']
            if country_name in coordinates:
                # Simplified popup for better performance
                popup_html = f"""
                <div style="width: 150px;">
                    <b>{country_name}</b><br>
                    {row['Count']} teams<br>
                    <a href="/?country={country_name}" target="_top">View</a>
                </div>
                """
                
                folium.Marker(
                    location=coordinates[country_name],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{country_name}: {row['Count']} teams",
                    icon=folium.Icon(color='orange', icon='info-sign')
                ).add_to(m)
        
        # Save map to a template file
        os.makedirs('static', exist_ok=True)
        m.save(map_file)
        logger.info("Map generated and cached successfully")
        
    except Exception as e:
        logger.error(f"Error generating map: {str(e)}")
        # Create a simple fallback map
        m.save('static/map.html')

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'data_provider': config.database.provider,
        'last_refresh': last_data_refresh.isoformat() if last_data_refresh else None
    })

@app.route('/')
def index():
    """Main dashboard page - optimized for cost reduction"""
    # Only refresh data if absolutely necessary (cost optimization)
    if should_refresh_data():
        try:
            load_data()
        except Exception as e:
            logger.error(f"Failed to refresh data: {str(e)}")
            flash(f"Warning: Using cached data due to refresh error", 'warning')
    
    # Generate map only if it doesn't exist or is very old (cost optimization)
    if not os.path.exists('static/map.html') or should_refresh_data():
        generate_map()
    
    return render_template('index.html', 
                          countries=countries,
                          leagues=leagues,
                          sports=sports,
                          last_refresh=last_data_refresh)

@app.route('/api/teams')
def get_teams():
    """API endpoint to get filtered teams data"""
    if teams_data is None:
        return jsonify({'error': 'No data available'}), 500
    
    # Get query parameters
    country = request.args.get('country', '')
    league = request.args.get('league', '')
    sport = request.args.get('sport', '')
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    
    # Filter data based on parameters
    filtered_data = teams_data
    
    if country:
        filtered_data = filtered_data[filtered_data['Country'] == country]
    
    if league:
        filtered_data = filtered_data[filtered_data['League'] == league]
    
    if sport:
        filtered_data = filtered_data[filtered_data['Sports'] == sport]
    
    if gender:
        # Filter by gender based on league names
        if gender == 'men':
            # Men's basketball: contains "NCAA" but not "Women"
            mask = (filtered_data['League'].str.contains('NCAA', case=False, na=False)) & \
                   (~filtered_data['League'].str.contains('Women', case=False, na=False))
            filtered_data = filtered_data[mask]
        elif gender == 'women':
            # Women's basketball: contains both "NCAA" and "Women"
            mask = (filtered_data['League'].str.contains('NCAA', case=False, na=False)) & \
                   (filtered_data['League'].str.contains('Women', case=False, na=False))
            filtered_data = filtered_data[mask]
    
    if search:
        # Support for multiple team searches (comma-separated)
        search_terms = [term.strip().lower() for term in search.split(',')]
        
        # Create a mask to filter teams that match any of the search terms
        mask = filtered_data['Team'].str.lower().apply(
            lambda x: any(term in x for term in search_terms)
        )
        
        filtered_data = filtered_data[mask]
    
    # Convert to list of dictionaries for JSON response
    teams_list = filtered_data.to_dict('records')
    
    return jsonify(teams_list)

@app.route('/team/<team_name>')
def team_detail(team_name):
    """Individual team detail page"""
    if teams_data is None:
        return "Data not available", 500
    
    # Find the team by name
    team = teams_data[teams_data['Team'] == team_name]
    
    if team.empty:
        return "Team not found", 404
    
    # Convert to dictionary for template
    team_data = team.iloc[0].to_dict()
    
    return render_template('team_detail.html', team=team_data)

@app.route('/map')
def map_view():
    """Dedicated map page"""
    # Generate the map
    generate_map()
    
    return render_template('map_container.html')

@app.route('/api/refresh-data', methods=['POST'])
def refresh_data():
    """API endpoint to manually refresh data"""
    try:
        load_data()
        generate_map()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'timestamp': last_data_refresh.isoformat(),
            'teams_count': len(teams_data)
        })
    except Exception as e:
        logger.error(f"Manual data refresh failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update-database', methods=['GET', 'POST'])
def update_database():
    """Legacy endpoint for local file uploads (fallback only)"""
    if config.database.provider != 'local':
        flash('Database updates are managed through cloud provider. Contact administrator.', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save as Basketball Sources Links.xlsx to overwrite the existing file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], "Basketball Sources Links.xlsx"))
            
            # Reload the data
            load_data()
            
            # Generate new map with updated data
            generate_map()
            
            flash('Database updated successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'danger')
            
    return render_template('update_database.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

def create_app():
    """Application factory for testing and deployment"""
    global teams_data, countries, leagues, sports, last_data_refresh
    
    # Initialize data on startup
    try:
        load_data()
        generate_map()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
    
    return app

# Initialize the application for production deployment
if not teams_data:
    try:
        load_data()
        generate_map()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")

if __name__ == '__main__':
    # Run the application
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    ) 