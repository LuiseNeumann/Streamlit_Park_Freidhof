from pathlib import Path
from typing import List, Dict, Any

class Config:
    """Configuration settings for the Parks Visualization project."""
    
    # Directory paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # File paths
    PARKS_DATA_FILE = "Parks_Deutschland_all.csv"
    CEMETERY_DATA_FILE = "Friedhöfe_Deutschland_all.csv"
    CAMPING_DATA_FILE = "campingplaetze_mit_adressen.csv"
    CITIES_DATA_FILE = "staedte_erweitert.csv"
    FEDERAL_STATES_GEOJSON = "gadm41_DEU_1.json"
    GREEN_AREAS_CSV = "grünflächen_pro_stadt.csv"
    BIKE_HEATMAP_CSV = "bike_heatmap_data.csv"
    CAMPING_HEATMAP_CSV = "campingplaetze_mit_adressen.csv"
    
    # Visualization settings
    DEFAULT_SIZE_THRESHOLD = 3
    DEFAULT_ZOOM_START = 6
    DEFAULT_CENTER = [52.5162, 13.3777]  # Berlin coordinates
    
    # Colors
    FEDERAL_STATE_COLORS = [
        "#ff9999", "#66b3ff", "#99ff99", 
        "#ffcc99", "#c2c2f0", "#ffb3e6"
    ]
    
    MARKER_COLORS = {
        "parks_large": "orange",
        "parks_small": "yellow",
        "cemetery_large": "lightblue",
        "cemetery_small": "cadetblue"
    }
    
    # Calculation constants
    AREA_TO_MINUTES_FACTOR = 1.3  # minutes per m²
    WORKING_HOURS_PER_DAY = 5
    WORKING_DAYS_PER_YEAR = 220
    WORKERS_PER_BIKE = 2
    
    # Map styling
    POPUP_MAX_WIDTH = 400
    POLYGON_OPACITY = 0.5
    HEATMAP_RADIUS = 25
    HEATMAP_BLUR = 15