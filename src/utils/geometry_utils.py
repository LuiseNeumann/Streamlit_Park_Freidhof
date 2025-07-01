import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, Polygon
import logging

logger = logging.getLogger(__name__)

class GeometryProcessor:
    """Handles geometry processing operations."""
    
    @staticmethod
    def process_geometry_column(df: pd.DataFrame, geometry_col: str = "geometry") -> pd.DataFrame:
        """
        Process geometry column from WKT strings to shapely objects.
        
        Args:
            df: DataFrame with geometry column
            geometry_col: Name of geometry column
            
        Returns:
            DataFrame with processed geometries
        """
        try:
            df[geometry_col] = df[geometry_col].apply(
                lambda x: wkt.loads(x) if isinstance(x, str) else x
            )
            df = df.dropna(subset=[geometry_col])
            logger.info(f"Processed {len(df)} geometries")
            return df
        except Exception as e:
            logger.error(f"Error processing geometries: {e}")
            return df
    
    @staticmethod
    def create_geodataframe(df: pd.DataFrame, geometry_col: str = "geometry") -> gpd.GeoDataFrame:
        """
        Create GeoDataFrame from DataFrame with geometry column.
        
        Args:
            df: Source DataFrame
            geometry_col: Name of geometry column
            
        Returns:
            GeoDataFrame with valid geometries
        """
        try:
            gdf = gpd.GeoDataFrame(df, geometry=geometry_col, crs="EPSG:4326")
            gdf = gdf[gdf.geometry.is_valid]
            logger.info(f"Created GeoDataFrame with {len(gdf)} valid geometries")
            return gdf
        except Exception as e:
            logger.error(f"Error creating GeoDataFrame: {e}")
            return gpd.GeoDataFrame()
    
    @staticmethod
    def calculate_center_coordinates(gdf: gpd.GeoDataFrame) -> tuple:
        """
        Calculate center coordinates from GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame with latitude/longitude columns
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if calculation fails
        """
        try:
            if gdf.empty:
                return None, None
                
            avg_lat = gdf["latitude"].mean()
            avg_lon = gdf["longitude"].mean()
            
            if pd.isna(avg_lat) or pd.isna(avg_lon):
                return None, None
                
            logger.debug(f"Calculated center: ({avg_lat}, {avg_lon})")
            return avg_lat, avg_lon
            
        except Exception as e:
            logger.error(f"Error calculating center coordinates: {e}")
            return None, None