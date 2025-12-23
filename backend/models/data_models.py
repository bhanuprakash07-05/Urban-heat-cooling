from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
import uuid

db = SQLAlchemy()

class HeatData(db.Model):
    """Model for storing heat island data points."""
    __tablename__ = 'heat_data'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Geographic coordinates
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)
    
    # Temperature data
    temperature = db.Column(db.Float, nullable=False)
    temperature_source = db.Column(db.String(50))  # MODIS, Landsat, ground_sensor
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    data_quality = db.Column(db.Float)  # 0-1 quality score
    
    # Contextual data
    land_use = db.Column(db.String(50))  # residential, commercial, industrial, green_space
    building_density = db.Column(db.Float)  # 0-1 ratio
    vegetation_index = db.Column(db.Float)  # NDVI value
    elevation = db.Column(db.Float)  # meters above sea level
    
    # Analysis results
    cluster_id = db.Column(db.Integer)
    is_hotspot = db.Column(db.Boolean, default=False)
    hotspot_severity = db.Column(db.String(20))  # low, medium, high, critical
    
    # Relationships
    predictions = db.relationship('TemperaturePrediction', backref='heat_data', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'temperature': self.temperature,
            'temperature_source': self.temperature_source,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_quality': self.data_quality,
            'land_use': self.land_use,
            'building_density': self.building_density,
            'vegetation_index': self.vegetation_index,
            'elevation': self.elevation,
            'cluster_id': self.cluster_id,
            'is_hotspot': self.is_hotspot,
            'hotspot_severity': self.hotspot_severity
        }

class SatelliteData(db.Model):
    """Model for storing satellite imagery metadata."""
    __tablename__ = 'satellite_data'
    
    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # Satellite information
    satellite = db.Column(db.String(50), nullable=False)  # MODIS, Landsat8, Sentinel3
    sensor = db.Column(db.String(50))  # Terra, Aqua, OLI_TIRS, SLSTR
    
    # Acquisition details
    acquisition_date = db.Column(db.DateTime, nullable=False)
    path_row = db.Column(db.String(20))  # For Landsat
    tile_id = db.Column(db.String(20))  # For Sentinel
    
    # Geographic coverage
    bounds_north = db.Column(db.Float)
    bounds_south = db.Column(db.Float)
    bounds_east = db.Column(db.Float)
    bounds_west = db.Column(db.Float)
    
    # Quality metrics
    cloud_cover = db.Column(db.Float)  # Percentage
    quality_score = db.Column(db.Float)  # 0-1 overall quality
    
    # File information
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)  # bytes
    processed = db.Column(db.Boolean, default=False)
    
    # Processing metadata
    processing_level = db.Column(db.String(10))  # L1, L2, L3
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MLModel(db.Model):
    """Model for storing ML model metadata."""
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # classification, regression, clustering
    version = db.Column(db.String(20), nullable=False)
    
    # Performance metrics
    accuracy = db.Column(db.Float)
    mae = db.Column(db.Float)  # Mean Absolute Error
    rmse = db.Column(db.Float)  # Root Mean Square Error
    r2_score = db.Column(db.Float)  # R-squared
    
    # Model details
    algorithm = db.Column(db.String(100))  # CNN, RandomForest, etc.
    features = db.Column(JSON)  # List of input features
    hyperparameters = db.Column(JSON)  # Model configuration
    
    # File information
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    
    # Training information
    training_data_size = db.Column(db.Integer)
    training_duration = db.Column(db.Integer)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)

class TemperaturePrediction(db.Model):
    """Model for storing temperature predictions."""
    __tablename__ = 'temperature_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    heat_data_id = db.Column(db.Integer, db.ForeignKey('heat_data.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('ml_models.id'), nullable=False)
    
    # Prediction details
    predicted_temperature = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float)  # 0-1
    prediction_horizon = db.Column(db.Integer)  # hours into future
    
    # Input features used
    features_used = db.Column(JSON)
    
    # Timestamps
    prediction_time = db.Column(db.DateTime, default=datetime.utcnow)
    target_time = db.Column(db.DateTime)  # When prediction is for
    
    # Validation (if available)
    actual_temperature = db.Column(db.Float)
    error = db.Column(db.Float)  # Prediction error
    
    # Relationships
    model = db.relationship('MLModel', backref='predictions')

class Intervention(db.Model):
    """Model for storing cooling intervention recommendations."""
    __tablename__ = 'interventions'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_name = db.Column(db.String(200))
    
    # Intervention details
    intervention_type = db.Column(db.String(100), nullable=False)
    priority_score = db.Column(db.Float, nullable=False)
    
    # Multi-criteria scores
    temperature_reduction_score = db.Column(db.Float)
    cost_score = db.Column(db.Float)
    feasibility_score = db.Column(db.Float)
    community_impact_score = db.Column(db.Float)
    
    # Expected outcomes
    expected_cooling = db.Column(db.Float)  # Degrees Celsius
    affected_area = db.Column(db.Float)  # Square kilometers
    implementation_time = db.Column(db.Integer)  # months
    estimated_cost = db.Column(db.Float)  # USD
    annual_maintenance_cost = db.Column(db.Float)  # USD
    
    # Implementation details
    implementation_plan = db.Column(JSON)  # List of steps
    constraints = db.Column(JSON)  # List of constraints
    
    # Status tracking
    status = db.Column(db.String(50), default='recommended')  # recommended, approved, in_progress, completed
    approval_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    completion_percentage = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))  # System or user ID
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'name': self.location_name
            },
            'intervention_type': self.intervention_type,
            'priority_score': self.priority_score,
            'criteria_scores': {
                'temperature_reduction': self.temperature_reduction_score,
                'cost': self.cost_score,
                'feasibility': self.feasibility_score,
                'community_impact': self.community_impact_score
            },
            'expected_outcomes': {
                'cooling': self.expected_cooling,
                'area': self.affected_area,
                'implementation_time': self.implementation_time,
                'cost': self.estimated_cost,
                'maintenance_cost': self.annual_maintenance_cost
            },
            'implementation_plan': self.implementation_plan,
            'constraints': self.constraints,
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CitizenReport(db.Model):
    """Model for storing citizen heat reports."""
    __tablename__ = 'citizen_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Location information
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_description = db.Column(db.Text)
    
    # Report details
    reported_temperature = db.Column(db.Float)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20))  # low, medium, high, critical
    
    # Reporter information (anonymous)
    reporter_id = db.Column(db.String(100))  # Hash or anonymous ID
    contact_info = db.Column(db.String(200))  # Optional, encrypted
    
    # Verification and response
    status = db.Column(db.String(50), default='submitted')  # submitted, verified, investigating, resolved
    verified_by = db.Column(db.String(100))
    verification_date = db.Column(db.DateTime)
    response_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'description': self.location_description
            },
            'reported_temperature': self.reported_temperature,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'response_message': self.response_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OptimizationRun(db.Model):
    """Model for storing genetic algorithm optimization results."""
    __tablename__ = 'optimization_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Optimization parameters
    algorithm = db.Column(db.String(50), default='genetic_algorithm')
    population_size = db.Column(db.Integer)
    generations = db.Column(db.Integer)
    mutation_rate = db.Column(db.Float)
    crossover_rate = db.Column(db.Float)
    
    # Budget constraints
    total_budget = db.Column(db.Float)
    budget_utilized = db.Column(db.Float)
    
    # Results
    fitness_score = db.Column(db.Float)
    convergence_achieved = db.Column(db.Boolean)
    optimal_interventions = db.Column(JSON)  # List of selected interventions
    
    # Expected outcomes
    total_cooling_potential = db.Column(db.Float)
    population_benefited = db.Column(db.Integer)
    total_area_affected = db.Column(db.Float)
    
    # Performance metrics
    execution_time = db.Column(db.Float)  # seconds
    memory_usage = db.Column(db.Float)  # MB
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    notes = db.Column(db.Text)