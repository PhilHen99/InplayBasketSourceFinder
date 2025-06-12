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
            # Load from local Excel file (fallback)
    df = pd.read_excel("Basketball Sources Links.xlsx")
        else:
            # Load from cloud provider
            df = data_service.fetch_excel_data(
                config.database.provider, 
                config.database.config
            )
        
        # Clean the data
    df = df.fillna('')
        teams_data = df

        # Update global filter options
countries = sorted(teams_data['Country'].unique())
leagues = sorted(teams_data['League'].unique())
sports = sorted(teams_data['Sports'].unique())

        last_data_refresh = datetime.now()
        
        logger.info(f"Successfully loaded {len(teams_data)} teams from {config.database.provider}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        # Try to load fallback local file
        try:
            df = pd.read_excel("Basketball Sources Links.xlsx")
            df = df.fillna('')
            teams_data = df
            countries = sorted(teams_data['Country'].unique())
            leagues = sorted(teams_data['League'].unique())
            sports = sorted(teams_data['Sports'].unique())
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
    """Generate the world map with team markers"""
    # Create a map centered on a default location
    m = folium.Map(location=[20, 0], zoom_start=2)
    
    coordinates = get_country_coordinates()
    
    if teams_data is None:
        logger.warning("No teams data available for map generation")
        return
    
    country_counts = teams_data['Country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Count']
    
    # Add markers to the map
    for _, row in country_counts.iterrows():
        country_name = row['Country']
        if country_name in coordinates:
            # Create a clickable popup with JavaScript that sets the country filter
            popup_html = f"""
            <div style="width: 200px;">
                <h4>{country_name}</h4>
                <p>{row['Count']} All teams and leagues</p>
                <button onclick="window.parent.filterByCountry('{country_name}')" class="btn btn-primary btn-sm">
                    View Teams
                </button>
            </div>
            """
            
            folium.Marker(
                location=coordinates[country_name],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{country_name}: {row['Count']} teams",
                icon=folium.Icon(color='orange', icon='info-sign')
            ).add_to(m)
    
    # Custom JavaScript to communicate with parent window
    custom_js = """
    <script>
    function filterByCountry(country) {
        if (window.parent && window.parent.filterByCountry) {
            window.parent.filterByCountry(country);
        } else {
            window.open('/?country=' + encodeURIComponent(country), '_blank');
        }
    }
    </script>
    """
    
    # Add the JavaScript to the map
    m.get_root().html.add_child(folium.Element(custom_js))
    
    # Save map to a template file
    os.makedirs('static', exist_ok=True)
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
    """Main dashboard page"""
    # Check if we need to refresh data
    if should_refresh_data():
        try:
            load_data()
        except Exception as e:
            logger.error(f"Failed to refresh data: {str(e)}")
            flash(f"Warning: Using cached data due to refresh error", 'warning')
    
    # Generate the map each time the index is loaded
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
    
    # Filter data based on parameters
    filtered_data = teams_data
    
    if country:
        filtered_data = filtered_data[filtered_data['Country'] == country]
    
    if league:
        filtered_data = filtered_data[filtered_data['League'] == league]
    
    if sport:
        filtered_data = filtered_data[filtered_data['Sports'] == sport]
    
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