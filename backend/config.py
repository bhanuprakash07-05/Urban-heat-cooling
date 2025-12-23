import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://localhost/urban_cooling_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys for Real Data Sources
    NASA_EARTHDATA_USERNAME = os.environ.get('NASA_EARTHDATA_USERNAME')
    NASA_EARTHDATA_PASSWORD = os.environ.get('NASA_EARTHDATA_PASSWORD')
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    # Satellite Data Configuration
    MODIS_BASE_URL = 'https://modis.gsfc.nasa.gov/data/'
    LANDSAT_BASE_URL = 'https://earthexplorer.usgs.gov/'
    SENTINEL_BASE_URL = 'https://scihub.copernicus.eu/'
    
    # ML Model Configuration
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'models')
    CACHE_TIMEOUT = 3600  # 1 hour
    
    # Geographic Configuration (Delhi NCR)
    DEFAULT_REGION = {
        'name': 'Delhi NCR',
        'bounds': {
            'north': 28.88,
            'south': 28.40,
            'east': 77.35,
            'west': 76.84
        },
        'center': {
            'lat': 28.6139,
            'lng': 77.2090
        }
    }
    
    # Data Processing Configuration
    GRID_RESOLUTION = 100  # meters
    TEMPERATURE_THRESHOLD = 36  # Celsius for hotspot detection
    CLUSTERING_ALGORITHM = 'kmeans'
    N_CLUSTERS = 5
    
    # Optimization Configuration
    GA_POPULATION_SIZE = 50
    GA_GENERATIONS = 100
    GA_MUTATION_RATE = 0.1
    GA_CROSSOVER_RATE = 0.8
    
    # API Rate Limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///urban_cooling.db'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Real Data Source URLs and APIs
DATA_SOURCES = {
    'satellite': {
        'modis_thermal': {
            'url': 'https://modis.gsfc.nasa.gov/data/dataprod/mod11.php',
            'description': 'MODIS Land Surface Temperature',
            'resolution': '1km',
            'update_frequency': 'daily'
        },
        'landsat8_thermal': {
            'url': 'https://earthexplorer.usgs.gov/',
            'description': 'Landsat 8 Thermal Infrared',
            'resolution': '30m',
            'update_frequency': '16 days'
        },
        'sentinel3_thermal': {
            'url': 'https://scihub.copernicus.eu/',
            'description': 'Sentinel-3 Sea and Land Surface Temperature',
            'resolution': '1km',
            'update_frequency': 'daily'
        }
    },
    'weather': {
        'openweather': {
            'url': 'https://api.openweathermap.org/data/2.5/',
            'description': 'Real-time weather data',
            'api_key_required': True
        },
        'imd': {
            'url': 'https://mausam.imd.gov.in/imd_latest/contents/index_data.php',
            'description': 'India Meteorological Department',
            'api_key_required': False
        }
    },
    'gis': {
        'osm_overpass': {
            'url': 'https://overpass-api.de/api/interpreter',
            'description': 'OpenStreetMap data via Overpass API',
            'usage': 'Building footprints, land use, roads'
        },
        'delhi_open_data': {
            'url': 'https://data.gov.in/catalog/delhi',
            'description': 'Delhi Government Open Data',
            'usage': 'Administrative boundaries, demographics'
        }
    },
    'demographics': {
        'census_india': {
            'url': 'https://censusindia.gov.in/2011census/dchb/DCHB.html',
            'description': 'Census of India 2011',
            'usage': 'Population density, socio-economic data'
        }
    }
}

# API Endpoints for Real Data Collection
API_ENDPOINTS = {
    'modis_thermal': 'https://modis.gsfc.nasa.gov/data/dataprod/mod11.php',
    'openweather_current': 'https://api.openweathermap.org/data/2.5/weather',
    'openweather_forecast': 'https://api.openweathermap.org/data/2.5/forecast',
    'overpass_api': 'https://overpass-api.de/api/interpreter',
    'nasa_earthdata': 'https://earthdata.nasa.gov/eosdis/daacs',
    'usgs_earthexplorer': 'https://earthexplorer.usgs.gov/inventory/json/v/1.4.1/',
}

# Error Messages
ERROR_MESSAGES = {
    'data_fetch_failed': 'Failed to fetch data from external API',
    'model_not_found': 'Machine learning model not found',
    'invalid_coordinates': 'Invalid geographic coordinates provided',
    'api_rate_limit': 'API rate limit exceeded',
    'insufficient_data': 'Insufficient data for analysis'
}