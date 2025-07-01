import sys
from pathlib import Path

# Projekt-Root ins sys.path hinzufügen
ROOT_DIR = Path(__file__).resolve().parents[2]  # geht 2 Ebenen hoch von /src/data_processing/
sys.path.append(str(ROOT_DIR))

import pandas as pd
import geopandas as gpd
import json
import random
import logging
from pathlib import Path
from typing import Dict, Any
from config.settings import Config
from src.utils.geometry_utils import GeometryProcessor

logger = logging.getLogger(__name__)

class DataLoader:
    """Handles loading and preprocessing of all data sources."""
    
    def __init__(self):
        self.geometry_processor = GeometryProcessor()
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Ensure output directory exists."""
        Config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    def load_csv_data(self, filename: str) -> pd.DataFrame:
        """
        Load CSV data with error handling.
        
        Args:
            filename: Name of CSV file in data directory
            
        Returns:
            Loaded DataFrame or empty DataFrame on error
        """
        filepath = Config.DATA_DIR / filename
        try:
            df = pd.read_csv(filepath)
            df.columns = df.columns.str.strip()
            
            # Convert phone to string if present
            if 'phone' in df.columns:
                df['phone'] = df['phone'].astype(str)
            
            logger.info(f"Loaded {len(df)} records from {filename}")
            return df
            
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return pd.DataFrame()
    
    def load_parks_data(self) -> Dict[str, Any]:
        """Load and process parks data."""
        logger.info("Loading parks data...")
        
        parks_df = self.load_csv_data(Config.PARKS_DATA_FILE)
        if parks_df.empty:
            return {"df": pd.DataFrame(), "gdf": gpd.GeoDataFrame()}
        
        # Process geometries
        parks_df = self.geometry_processor.process_geometry_column(parks_df)
        parks_gdf = self.geometry_processor.create_geodataframe(parks_df)
        
        return {"df": parks_df, "gdf": parks_gdf}
    
    def load_cemetery_data(self) -> Dict[str, Any]:
        """Load and process cemetery data."""
        logger.info("Loading cemetery data...")
        
        cemetery_df = self.load_csv_data(Config.CEMETERY_DATA_FILE)
        if cemetery_df.empty:
            return {"df": pd.DataFrame(), "gdf": gpd.GeoDataFrame()}
        
        # Process geometries
        cemetery_df = self.geometry_processor.process_geometry_column(cemetery_df)
        cemetery_gdf = self.geometry_processor.create_geodataframe(cemetery_df)
        
        return {"df": cemetery_df, "gdf": cemetery_gdf}
    
    def load_camping_data(self) -> Dict[str, Any]:
        """Load and process cemetery data."""
        logger.info("Loading cemetery data...")
        
        camping_df = self.load_csv_data(Config.CAMPING_DATA_FILE)
        if camping_df.empty:
            return {"df": pd.DataFrame(), "gdf": gpd.GeoDataFrame()}
        
        # Process geometries
        camping_df = self.geometry_processor.process_geometry_column(camping_df)
        camping_gdf = self.geometry_processor.create_geodataframe(camping_df)
        
        return {"df": camping_df, "gdf": camping_gdf}
    
    def load_cities_data(self) -> pd.DataFrame:
        """Load and process cities data."""
        logger.info("Loading cities data...")
        
        cities_df = self.load_csv_data(Config.CITIES_DATA_FILE)
        if cities_df.empty:
            return pd.DataFrame()
        
        # Clean and process cities data
        cities_df["Stadt"] = cities_df["Stadt"].str.strip()
        cities_df["Bundesland"] = cities_df["Bundesland"].str.strip()
        cities_df["Latitude"] = pd.to_numeric(cities_df["Latitude"], errors="coerce")
        cities_df["Longitude"] = pd.to_numeric(cities_df["Longitude"], errors="coerce")
        
        return cities_df
    
    def load_federal_states_data(self) -> Dict[str, Any]:
        """Load federal states GeoJSON data."""
        logger.info("Loading federal states data...")
        
        geojson_path = Config.DATA_DIR / Config.FEDERAL_STATES_GEOJSON
        
        try:
            # Load GeoJSON
            with open(geojson_path, encoding="utf-8") as f:
                geojson_data = json.load(f)
            
            # Load as GeoDataFrame
            bundeslaender_gdf = gpd.read_file(geojson_path)
            bundeslaender_gdf = bundeslaender_gdf.to_crs("EPSG:4326")
            
            # Create color mapping
            color_map = {
                feature["properties"]["NAME_1"]: random.choice(Config.FEDERAL_STATE_COLORS) 
                for feature in geojson_data["features"]
            }
            
            logger.info(f"Loaded {len(bundeslaender_gdf)} federal states")
            
            return {
                "geojson": geojson_data,
                "gdf": bundeslaender_gdf,
                "color_map": color_map
            }
            
        except FileNotFoundError:
            logger.error(f"Federal states file not found: {geojson_path}")
            return {"geojson": {}, "gdf": gpd.GeoDataFrame(), "color_map": {}}
        except Exception as e:
            logger.error(f"Error loading federal states data: {e}")
            return {"geojson": {}, "gdf": gpd.GeoDataFrame(), "color_map": {}}
    
    def load_heatmap_data(self) -> Dict[str, pd.DataFrame]:
        """Load heatmap data files."""
        logger.info("Loading heatmap data...")
        
        # Load green areas heatmap
        green_areas_df = self.load_csv_data(Config.GREEN_AREAS_CSV)
        if not green_areas_df.empty:
            green_areas_df = green_areas_df.dropna(subset=["Latitude", "Longitude", "grünfläche_m2"])
            green_areas_df = green_areas_df[green_areas_df["grünfläche_m2"] > 0]
        
        # Load bike heatmap
        bike_df = self.load_csv_data(Config.BIKE_HEATMAP_CSV)
        
        return {
            "green_areas": green_areas_df,
            "bike_demand": bike_df
        }
    
    def load_heatmap_camping_data(self) -> Dict[str, pd.DataFrame]:
        """Load heatmap data files."""
        logger.info("Loading heatmap data...")
        
        # Load camping fläche heatmap
        camping_df = self.load_csv_data(Config.CAMPING_HEATMAP_CSV)
        if not camping_df.empty:
            camping_df = camping_df.dropna(subset=["latitude", "longitude", "area_ha"])
            camping_df = camping_df[camping_df["area_ha"] > 0]
       
        return {
            "camping_areas": camping_df,
            "camping_heatmap":camping_df
        }

    def merge_with_bundesland(self, df: pd.DataFrame, cities_df: pd.DataFrame, df_city_column: str = 'city') -> pd.DataFrame:
        """
    Merge DataFrame with cities data to add Bundesland information.
    
    Args:
        df: DataFrame to enhance (parks or cemetery data)
        cities_df: Cities DataFrame with Bundesland information
        df_city_column: Column name in df that contains city names
        
    Returns:
        Enhanced DataFrame with Bundesland column
        """
        try:
            if df.empty or cities_df.empty:
                logger.warning("One of the DataFrames is empty, returning original df")
                return df
        
            # Make a copy to avoid modifying original
            df_enhanced = df.copy()
        
            # Clean city names in both dataframes for better matching
            df_enhanced[f'{df_city_column}_clean'] = df_enhanced[df_city_column].str.strip().str.lower()
            cities_clean = cities_df.copy()
            cities_clean['Stadt_clean'] = cities_clean['Stadt'].str.strip().str.lower()
        
            # Create mapping dictionary from cities data
            city_bundesland_mapping = dict(zip(cities_clean['Stadt_clean'], cities_clean['Bundesland']))
        
            # Map Bundesland using the cleaned city names
            df_enhanced['bundesland'] = df_enhanced[f'{df_city_column}_clean'].map(city_bundesland_mapping)
        
            # For unmatched cities, try fuzzy matching
            unmatched_mask = df_enhanced['bundesland'].isna()
            if unmatched_mask.sum() > 0:
                logger.info(f"Attempting fuzzy matching for {unmatched_mask.sum()} unmatched cities")
            
                for idx in df_enhanced[unmatched_mask].index:
                    city_name = df_enhanced.loc[idx, f'{df_city_column}_clean']
                    if pd.notna(city_name):
                        # Simple fuzzy matching - find closest city name
                        best_match = None
                        best_score = 0
                    
                        for available_city in cities_clean['Stadt_clean'].unique():
                            if pd.notna(available_city):
                                # Simple similarity score based on common characters
                                score = len(set(city_name) & set(available_city)) / max(len(set(city_name)), len(set(available_city)))
                                if score > best_score and score > 0.5:  # Threshold for fuzzy matching
                                    best_score = score
                                    best_match = available_city
                    
                        if best_match:
                            df_enhanced.loc[idx, 'bundesland'] = city_bundesland_mapping[best_match]
                            logger.debug(f"Fuzzy matched '{city_name}' -> '{best_match}' -> {city_bundesland_mapping[best_match]}")
        
            # Remove the temporary clean column
            df_enhanced = df_enhanced.drop(columns=[f'{df_city_column}_clean'])
        
            # Log statistics
            total_rows = len(df_enhanced)
            matched_rows = df_enhanced['bundesland'].notna().sum()
            logger.info(f"Bundesland merge results: {matched_rows}/{total_rows} ({matched_rows/total_rows*100:.1f}%) matched")
        
            # Show unmatched cities for debugging
            if matched_rows < total_rows:
                unmatched_cities = df_enhanced[df_enhanced['bundesland'].isna()][df_city_column].unique()[:5]
                logger.warning(f"Sample unmatched cities: {list(unmatched_cities)}")
        
            return df_enhanced
        
        except Exception as e:
            logger.error(f"Error merging with Bundesland data: {e}")
            return df

# Aktualisierte load_parks_data Methode:
    def load_parks_data(self) -> Dict[str, Any]:
        """Load and process parks data with Bundesland information."""
        logger.info("Loading parks data...")
    
        parks_df = self.load_csv_data(Config.PARKS_DATA_FILE)
        if parks_df.empty:
            return {"df": pd.DataFrame(), "gdf": gpd.GeoDataFrame()}
    
        # Load cities data for Bundesland mapping
        cities_df = self.load_cities_data()
    
        # Process geometries first
        parks_df = self.geometry_processor.process_geometry_column(parks_df)
        parks_gdf = self.geometry_processor.create_geodataframe(parks_df)
    
        # Add Bundesland information to both dataframes
        if not cities_df.empty:
            logger.info("Adding Bundesland information to parks data...")
        
            # Determine the correct city column name in parks data
            city_column = None
            possible_city_columns = ['city', 'City', 'name', 'Name', 'stadt', 'Stadt']
            for col in possible_city_columns:
                if col in parks_df.columns:
                    city_column = col
                    break
                    
            if city_column:
                parks_df = self.merge_with_bundesland(parks_df, cities_df, city_column)

                # Update GeoDataFrame as well
                if not parks_gdf.empty:
                    parks_gdf = self.merge_with_bundesland(parks_gdf, cities_df, city_column)
            else:
                logger.warning(f"No city column found in parks data. Available columns: {parks_df.columns.tolist()}")
        else:
            logger.warning("Cities data is empty, cannot add Bundesland information")

        return {"df": parks_df, "gdf": parks_gdf}

    # Aktualisierte load_cemetery_data Methode:
        def load_cemetery_data(self) -> Dict[str, Any]:
        """Load and process cemetery data with Bundesland information."""
        logger.info("Loading cemetery data...")
    
        cemetery_df = self.load_csv_data(Config.CEMETERY_DATA_FILE)
        if cemetery_df.empty:
            return {"df": pd.DataFrame(), "gdf": gpd.GeoDataFrame()}
    
        # Load cities data for Bundesland mapping
        cities_df = self.load_cities_data()
    
     # Process geometries first
        cemetery_df = self.geometry_processor.process_geometry_column(cemetery_df)
        cemetery_gdf = self.geometry_processor.create_geodataframe(cemetery_df)
    
    # Add Bundesland information to both dataframes
        if not cities_df.empty:
            logger.info("Adding Bundesland information to cemetery data...")
        
        # Determine the correct city column name in cemetery data
            city_column = None
            possible_city_columns = ['city', 'City', 'name', 'Name', 'stadt', 'Stadt']
            for col in possible_city_columns:
                if col in cemetery_df.columns:
                    city_column = col
                    break
        
            if city_column:
                cemetery_df = self.merge_with_bundesland(cemetery_df, cities_df, city_column)
            
                # Update GeoDataFrame as well
                if not cemetery_gdf.empty:
                    cemetery_gdf = self.merge_with_bundesland(cemetery_gdf, cities_df, city_column)
            else:
                logger.warning(f"No city column found in cemetery data. Available columns: {cemetery_df.columns.tolist()}")
        else:
            logger.warning("Cities data is empty, cannot add Bundesland information")
    
        return {"df": cemetery_df, "gdf": cemetery_gdf}
