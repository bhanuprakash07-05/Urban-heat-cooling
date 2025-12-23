import os
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import transform
import json
import logging
from typing import Dict, List, Tuple, Optional
from geopy.distance import geodesic
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class GISProcessor:
    """
    Comprehensive GIS data processor for urban analysis.
    Integrates with OpenStreetMap, Delhi Open Data Portal, and Census data.
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.delhi_bounds = {
            'north': 28.88,
            'south': 28.40,
            'east': 77.35,
            'west': 76.84
        }
        
        # Cache for frequently used data
        self.building_cache = {}
        self.road_cache = {}
        self.landuse_cache = {}
    
    def fetch_building_data(self, bbox: Optional[Dict] = None) -> gpd.GeoDataFrame:
        """
        Fetch building footprints from OpenStreetMap via Overpass API.
        
        Args:
            bbox: Bounding box dictionary with north, south, east, west keys
            
        Returns:
            GeoDataFrame containing building polygons with attributes
        """
        if bbox is None:
            bbox = self.delhi_bounds
        
        try:
            # Overpass QL query for buildings
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["building"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
              relation["building"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
            );
            out geom;
            """
            
            response = requests.post(self.overpass_url, data={'data': overpass_query}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            buildings = []
            
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    # Convert OSM way to Shapely polygon
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) > 2:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])  # Close polygon
                        
                        building = {
                            'osm_id': element['id'],
                            'geometry': Polygon(coords),
                            'building_type': element.get('tags', {}).get('building', 'yes'),
                            'height': self._parse_height(element.get('tags', {}).get('height')),
                            'levels': self._parse_levels(element.get('tags', {}).get('building:levels')),
                            'area': 0,  # Will be calculated
                            'amenity': element.get('tags', {}).get('amenity'),
                            'commercial': element.get('tags', {}).get('shop') or element.get('tags', {}).get('office'),
                        }
                        buildings.append(building)
            
            # Create GeoDataFrame
            if buildings:
                gdf = gpd.GeoDataFrame(buildings)
                gdf = gdf.set_crs('EPSG:4326')
                
                # Calculate building areas in square meters
                gdf_utm = gdf.to_crs('EPSG:32643')  # UTM Zone 43N for Delhi
                gdf['area'] = gdf_utm.geometry.area
                
                # Classify building types
                gdf['building_class'] = gdf.apply(self._classify_building, axis=1)
                
                logger.info(f"Retrieved {len(gdf)} buildings from OpenStreetMap")
                return gdf
            else:
                return self._generate_mock_building_data(bbox)
                
        except Exception as e:
            logger.error(f"Error fetching building data: {str(e)}")
            return self._generate_mock_building_data(bbox)
    
    def fetch_road_network(self, bbox: Optional[Dict] = None) -> gpd.GeoDataFrame:
        """
        Fetch road network from OpenStreetMap.
        
        Args:
            bbox: Bounding box dictionary
            
        Returns:
            GeoDataFrame containing road network
        """
        if bbox is None:
            bbox = self.delhi_bounds
        
        try:
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["highway"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
            );
            out geom;
            """
            
            response = requests.post(self.overpass_url, data={'data': overpass_query}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            roads = []
            
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) > 1:
                        from shapely.geometry import LineString
                        
                        road = {
                            'osm_id': element['id'],
                            'geometry': LineString(coords),
                            'highway_type': element.get('tags', {}).get('highway'),
                            'name': element.get('tags', {}).get('name'),
                            'surface': element.get('tags', {}).get('surface'),
                            'lanes': self._parse_lanes(element.get('tags', {}).get('lanes')),
                            'maxspeed': self._parse_speed(element.get('tags', {}).get('maxspeed')),
                        }
                        roads.append(road)
            
            if roads:
                gdf = gpd.GeoDataFrame(roads)
                gdf = gdf.set_crs('EPSG:4326')
                
                # Calculate road lengths
                gdf_utm = gdf.to_crs('EPSG:32643')
                gdf['length'] = gdf_utm.geometry.length
                
                # Classify road hierarchy
                gdf['road_class'] = gdf['highway_type'].map(self._get_road_class)
                
                logger.info(f"Retrieved {len(gdf)} road segments from OpenStreetMap")
                return gdf
            else:
                return self._generate_mock_road_data(bbox)
                
        except Exception as e:
            logger.error(f"Error fetching road data: {str(e)}")
            return self._generate_mock_road_data(bbox)
    
    def fetch_landuse_data(self, bbox: Optional[Dict] = None) -> gpd.GeoDataFrame:
        """
        Fetch land use polygons from OpenStreetMap.
        
        Args:
            bbox: Bounding box dictionary
            
        Returns:
            GeoDataFrame containing land use polygons
        """
        if bbox is None:
            bbox = self.delhi_bounds
        
        try:
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["landuse"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
              relation["landuse"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
            );
            out geom;
            """
            
            response = requests.post(self.overpass_url, data={'data': overpass_query}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            landuses = []
            
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) > 2:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        landuse = {
                            'osm_id': element['id'],
                            'geometry': Polygon(coords),
                            'landuse': element.get('tags', {}).get('landuse'),
                            'natural': element.get('tags', {}).get('natural'),
                            'leisure': element.get('tags', {}).get('leisure'),
                            'amenity': element.get('tags', {}).get('amenity'),
                        }
                        landuses.append(landuse)
            
            if landuses:
                gdf = gpd.GeoDataFrame(landuses)
                gdf = gdf.set_crs('EPSG:4326')
                
                # Calculate areas
                gdf_utm = gdf.to_crs('EPSG:32643')
                gdf['area'] = gdf_utm.geometry.area
                
                # Standardize land use categories
                gdf['landuse_class'] = gdf.apply(self._classify_landuse, axis=1)
                
                logger.info(f"Retrieved {len(gdf)} land use polygons from OpenStreetMap")
                return gdf
            else:
                return self._generate_mock_landuse_data(bbox)
                
        except Exception as e:
            logger.error(f"Error fetching land use data: {str(e)}")
            return self._generate_mock_landuse_data(bbox)
    
    def fetch_green_spaces(self, bbox: Optional[Dict] = None) -> gpd.GeoDataFrame:
        """
        Fetch green spaces and parks from OpenStreetMap.
        
        Args:
            bbox: Bounding box dictionary
            
        Returns:
            GeoDataFrame containing green spaces
        """
        if bbox is None:
            bbox = self.delhi_bounds
        
        try:
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["leisure"~"^(park|garden|recreation_ground|playground)$"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
              way["natural"~"^(wood|forest|grassland)$"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
              way["landuse"~"^(forest|grass|meadow|recreation_ground)$"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
            );
            out geom;
            """
            
            response = requests.post(self.overpass_url, data={'data': overpass_query}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            green_spaces = []
            
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) > 2:
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        green_space = {
                            'osm_id': element['id'],
                            'geometry': Polygon(coords),
                            'type': (element.get('tags', {}).get('leisure') or 
                                   element.get('tags', {}).get('natural') or 
                                   element.get('tags', {}).get('landuse')),
                            'name': element.get('tags', {}).get('name'),
                            'access': element.get('tags', {}).get('access', 'public'),
                        }
                        green_spaces.append(green_space)
            
            if green_spaces:
                gdf = gpd.GeoDataFrame(green_spaces)
                gdf = gdf.set_crs('EPSG:4326')
                
                # Calculate areas
                gdf_utm = gdf.to_crs('EPSG:32643')
                gdf['area'] = gdf_utm.geometry.area
                
                logger.info(f"Retrieved {len(gdf)} green spaces from OpenStreetMap")
                return gdf
            else:
                return self._generate_mock_greenspace_data(bbox)
                
        except Exception as e:
            logger.error(f"Error fetching green space data: {str(e)}")
            return self._generate_mock_greenspace_data(bbox)
    
    def calculate_urban_morphology(self, buildings_gdf: gpd.GeoDataFrame, analysis_grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculate urban morphology indicators for each grid cell.
        
        Args:
            buildings_gdf: GeoDataFrame with building footprints
            analysis_grid: GeoDataFrame with analysis grid cells
            
        Returns:
            GeoDataFrame with morphology indicators added
        """
        try:
            # Ensure same CRS
            if buildings_gdf.crs != analysis_grid.crs:
                buildings_gdf = buildings_gdf.to_crs(analysis_grid.crs)
            
            results = []
            
            for idx, cell in analysis_grid.iterrows():
                cell_geom = cell.geometry
                
                # Find buildings within this cell
                intersecting_buildings = buildings_gdf[buildings_gdf.intersects(cell_geom)]
                
                if len(intersecting_buildings) > 0:
                    # Calculate morphology indicators
                    total_building_area = intersecting_buildings['area'].sum()
                    cell_area = cell_geom.area
                    
                    morphology = {
                        'building_density': total_building_area / cell_area,
                        'building_count': len(intersecting_buildings),
                        'avg_building_height': intersecting_buildings['height'].mean(),
                        'building_coverage_ratio': total_building_area / cell_area,
                        'avg_building_area': intersecting_buildings['area'].mean(),
                        'height_variation': intersecting_buildings['height'].std(),
                        'plot_ratio': self._calculate_plot_ratio(intersecting_buildings, cell_area),
                        'sky_view_factor': self._estimate_sky_view_factor(intersecting_buildings, cell_area),
                    }
                else:
                    # No buildings in this cell
                    morphology = {
                        'building_density': 0.0,
                        'building_count': 0,
                        'avg_building_height': 0.0,
                        'building_coverage_ratio': 0.0,
                        'avg_building_area': 0.0,
                        'height_variation': 0.0,
                        'plot_ratio': 0.0,
                        'sky_view_factor': 1.0,
                    }
                
                results.append(morphology)
            
            # Add results to analysis grid
            for key in results[0].keys():
                analysis_grid[key] = [result[key] for result in results]
            
            logger.info("Calculated urban morphology indicators")
            return analysis_grid
            
        except Exception as e:
            logger.error(f"Error calculating urban morphology: {str(e)}")
            return analysis_grid
    
    def calculate_proximity_metrics(self, points_gdf: gpd.GeoDataFrame, features_gdf: gpd.GeoDataFrame, feature_type: str) -> gpd.GeoDataFrame:
        """
        Calculate proximity metrics from points to features.
        
        Args:
            points_gdf: GeoDataFrame with point locations
            features_gdf: GeoDataFrame with features (roads, parks, etc.)
            feature_type: Type of feature for naming the distance column
            
        Returns:
            GeoDataFrame with distance metrics added
        """
        try:
            distances = []
            
            for idx, point in points_gdf.iterrows():
                # Calculate distance to nearest feature
                min_distance = float('inf')
                
                for _, feature in features_gdf.iterrows():
                    distance = point.geometry.distance(feature.geometry)
                    if distance < min_distance:
                        min_distance = distance
                
                # Convert to meters if needed
                if points_gdf.crs == 'EPSG:4326':
                    # Approximate conversion from degrees to meters at Delhi latitude
                    min_distance = min_distance * 111000
                
                distances.append(min_distance)
            
            # Add distance column
            points_gdf[f'distance_to_{feature_type}'] = distances
            
            logger.info(f"Calculated proximity to {feature_type}")
            return points_gdf
            
        except Exception as e:
            logger.error(f"Error calculating proximity to {feature_type}: {str(e)}")
            return points_gdf
    
    def create_analysis_grid(self, bbox: Dict, cell_size: float = 0.001) -> gpd.GeoDataFrame:
        """
        Create a regular grid for spatial analysis.
        
        Args:
            bbox: Bounding box dictionary
            cell_size: Grid cell size in degrees
            
        Returns:
            GeoDataFrame with grid cells
        """
        try:
            x_coords = np.arange(bbox['west'], bbox['east'], cell_size)
            y_coords = np.arange(bbox['south'], bbox['north'], cell_size)
            
            grid_cells = []
            cell_id = 0
            
            for x in x_coords:
                for y in y_coords:
                    cell = box(x, y, x + cell_size, y + cell_size)
                    grid_cells.append({
                        'cell_id': cell_id,
                        'geometry': cell,
                        'center_lat': y + cell_size/2,
                        'center_lng': x + cell_size/2
                    })
                    cell_id += 1
            
            gdf = gpd.GeoDataFrame(grid_cells)
            gdf = gdf.set_crs('EPSG:4326')
            
            logger.info(f"Created analysis grid with {len(gdf)} cells")
            return gdf
            
        except Exception as e:
            logger.error(f"Error creating analysis grid: {str(e)}")
            return gpd.GeoDataFrame()
    
    def _parse_height(self, height_str: Optional[str]) -> float:
        """Parse building height from OSM tags."""
        if not height_str:
            return np.random.uniform(8, 25)  # Default height range
        
        try:
            # Remove units and convert to float
            height_str = height_str.lower().replace('m', '').replace(' ', '')
            return float(height_str)
        except:
            return np.random.uniform(8, 25)
    
    def _parse_levels(self, levels_str: Optional[str]) -> int:
        """Parse building levels from OSM tags."""
        if not levels_str:
            return np.random.randint(2, 8)
        
        try:
            return int(levels_str)
        except:
            return np.random.randint(2, 8)
    
    def _parse_lanes(self, lanes_str: Optional[str]) -> int:
        """Parse number of lanes from OSM tags."""
        if not lanes_str:
            return 2  # Default
        
        try:
            return int(lanes_str)
        except:
            return 2
    
    def _parse_speed(self, speed_str: Optional[str]) -> int:
        """Parse speed limit from OSM tags."""
        if not speed_str:
            return 50  # Default speed limit
        
        try:
            return int(speed_str.replace(' km/h', '').replace('kmh', ''))
        except:
            return 50
    
    def _classify_building(self, row) -> str:
        """Classify building type based on OSM tags."""
        building_type = row.get('building_type', 'yes')
        
        if building_type in ['house', 'detached', 'semi_detached', 'terrace']:
            return 'residential'
        elif building_type in ['office', 'commercial', 'retail', 'shop']:
            return 'commercial'
        elif building_type in ['industrial', 'warehouse', 'factory']:
            return 'industrial'
        elif building_type in ['school', 'hospital', 'university', 'government']:
            return 'institutional'
        else:
            # Use area-based heuristic
            area = row.get('area', 0)
            if area < 200:
                return 'residential'
            elif area < 1000:
                return 'commercial'
            else:
                return 'industrial'
    
    def _get_road_class(self, highway_type: str) -> int:
        """Get road hierarchy class."""
        road_hierarchy = {
            'motorway': 1, 'trunk': 1,
            'primary': 2, 'secondary': 2,
            'tertiary': 3, 'residential': 4,
            'service': 5, 'footway': 6, 'cycleway': 6
        }
        return road_hierarchy.get(highway_type, 4)
    
    def _classify_landuse(self, row) -> str:
        """Classify land use into standard categories."""
        landuse = row.get('landuse')
        natural = row.get('natural')
        leisure = row.get('leisure')
        
        if landuse in ['residential']:
            return 'residential'
        elif landuse in ['commercial', 'retail']:
            return 'commercial'
        elif landuse in ['industrial']:
            return 'industrial'
        elif landuse in ['forest', 'grass', 'meadow'] or natural in ['wood', 'forest', 'grassland'] or leisure in ['park', 'garden']:
            return 'green_space'
        else:
            return 'mixed'
    
    def _calculate_plot_ratio(self, buildings: gpd.GeoDataFrame, cell_area: float) -> float:
        """Calculate plot ratio (total floor area / land area)."""
        total_floor_area = (buildings['area'] * buildings['levels']).sum()
        return total_floor_area / cell_area if cell_area > 0 else 0
    
    def _estimate_sky_view_factor(self, buildings: gpd.GeoDataFrame, cell_area: float) -> float:
        """Estimate sky view factor based on building coverage and heights."""
        if len(buildings) == 0:
            return 1.0
        
        coverage = buildings['area'].sum() / cell_area
        avg_height = buildings['height'].mean()
        
        # Simplified sky view factor estimation
        svf = 1.0 - (coverage * 0.7) - (avg_height / 100 * 0.1)
        return max(0.1, min(1.0, svf))
    
    def _generate_mock_building_data(self, bbox: Dict) -> gpd.GeoDataFrame:
        """Generate mock building data for testing."""
        buildings = []
        n_buildings = 500
        
        for i in range(n_buildings):
            # Random location within bbox
            lon = np.random.uniform(bbox['west'], bbox['east'])
            lat = np.random.uniform(bbox['south'], bbox['north'])
            
            # Random building size
            size = np.random.uniform(10, 100)  # meters
            height = np.random.uniform(8, 50)
            levels = int(height / 3.5)
            
            # Create building polygon (simplified as square)
            offset = size / 111000  # Convert meters to degrees
            building_geom = box(lon - offset/2, lat - offset/2, lon + offset/2, lat + offset/2)
            
            building = {
                'osm_id': i,
                'geometry': building_geom,
                'building_type': np.random.choice(['house', 'office', 'commercial', 'industrial']),
                'height': height,
                'levels': levels,
                'area': size * size,
                'building_class': np.random.choice(['residential', 'commercial', 'industrial'])
            }
            buildings.append(building)
        
        gdf = gpd.GeoDataFrame(buildings)
        gdf = gdf.set_crs('EPSG:4326')
        return gdf
    
    def _generate_mock_road_data(self, bbox: Dict) -> gpd.GeoDataFrame:
        """Generate mock road network for testing."""
        from shapely.geometry import LineString
        
        roads = []
        n_roads = 100
        
        for i in range(n_roads):
            # Create random road segments
            start_lon = np.random.uniform(bbox['west'], bbox['east'])
            start_lat = np.random.uniform(bbox['south'], bbox['north'])
            end_lon = start_lon + np.random.uniform(-0.01, 0.01)
            end_lat = start_lat + np.random.uniform(-0.01, 0.01)
            
            road_geom = LineString([(start_lon, start_lat), (end_lon, end_lat)])
            
            road = {
                'osm_id': i,
                'geometry': road_geom,
                'highway_type': np.random.choice(['primary', 'secondary', 'residential', 'tertiary']),
                'name': f'Road {i}',
                'lanes': np.random.randint(2, 6),
                'road_class': np.random.randint(2, 5)
            }
            roads.append(road)
        
        gdf = gpd.GeoDataFrame(roads)
        gdf = gdf.set_crs('EPSG:4326')
        return gdf
    
    def _generate_mock_landuse_data(self, bbox: Dict) -> gpd.GeoDataFrame:
        """Generate mock land use data for testing."""
        landuses = []
        n_landuses = 50
        
        for i in range(n_landuses):
            # Random location and size
            center_lon = np.random.uniform(bbox['west'], bbox['east'])
            center_lat = np.random.uniform(bbox['south'], bbox['north'])
            size = np.random.uniform(0.002, 0.01)  # Size in degrees
            
            landuse_geom = box(center_lon - size/2, center_lat - size/2, 
                             center_lon + size/2, center_lat + size/2)
            
            landuse = {
                'osm_id': i,
                'geometry': landuse_geom,
                'landuse': np.random.choice(['residential', 'commercial', 'industrial', 'forest']),
                'landuse_class': np.random.choice(['residential', 'commercial', 'industrial', 'green_space']),
                'area': (size * 111000) ** 2  # Approximate area in square meters
            }
            landuses.append(landuse)
        
        gdf = gpd.GeoDataFrame(landuses)
        gdf = gdf.set_crs('EPSG:4326')
        return gdf
    
    def _generate_mock_greenspace_data(self, bbox: Dict) -> gpd.GeoDataFrame:
        """Generate mock green space data for testing."""
        green_spaces = []
        n_parks = 20
        
        for i in range(n_parks):
            center_lon = np.random.uniform(bbox['west'], bbox['east'])
            center_lat = np.random.uniform(bbox['south'], bbox['north'])
            size = np.random.uniform(0.001, 0.005)
            
            park_geom = box(center_lon - size/2, center_lat - size/2,
                           center_lon + size/2, center_lat + size/2)
            
            park = {
                'osm_id': i,
                'geometry': park_geom,
                'type': np.random.choice(['park', 'garden', 'forest', 'grass']),
                'name': f'Park {i}',
                'area': (size * 111000) ** 2
            }
            green_spaces.append(park)
        
        gdf = gpd.GeoDataFrame(green_spaces)
        gdf = gdf.set_crs('EPSG:4326')
        return gdf