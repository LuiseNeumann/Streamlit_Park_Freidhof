import folium
from folium.plugins import HeatMap
from folium import Map, LayerControl, Html, Element
import pandas as pd
import geopandas as gpd
import json
import logging
from typing import Dict, Any, List
from branca.element import Element
from config.settings import Config
from src.utils.calculations import WorkforceCalculator
from src.visualization.popup_content import PopupCreator
from src.visualization.layer_management import LayerManager

logger = logging.getLogger(__name__)

class MapBuilder:
    """Handles the creation and management of folium maps."""
    
    def __init__(self):
        self.calculator = WorkforceCalculator()
        self.popup_creator = PopupCreator()
        self.layer_management = LayerManager()
    
    def create_base_map(self, center: List[float] = None, zoom_start: int = None) -> folium.Map:
        """
        Create a base folium map.
        
        Args:
            center: Map center coordinates [lat, lon]
            zoom_start: Initial zoom level
            
        Returns:
            Folium map object
        """
        center = center or Config.DEFAULT_CENTER
        zoom_start = zoom_start or Config.DEFAULT_ZOOM_START
        
        map_obj = folium.Map(location=center, zoom_start=zoom_start)
        logger.info(f"Created base map centered at {center} with zoom {zoom_start}")
        return map_obj
    
    def build_main_map(self, parks_data: Dict[str, Any], cemetery_data: Dict[str, Any], camping_data:Dict[str,Any],
                      cities_data: pd.DataFrame, federal_states_data: Dict[str, Any],
                      heatmap_data: Dict[str, pd.DataFrame], camping_heatmap_data:Dict[str, pd.DataFrame], size_threshold: float = 3) -> folium.Map:
        """
        Build the main map with all layers.
        
        Args:
            parks_data: Parks data dictionary
            cemetery_data: Cemetery data dictionary
            camoing_data: Camping data dictionary
            cities_data: Cities DataFrame
            federal_states_data: Federal states data dictionary
            heatmap_data: Heatmap data dictionary
            size_threshold: Size threshold for marker categorization
            
        Returns:
            Complete Folium Map object
        """
        try:
            logger.info("Building main map with all layers...")
            
            # Create base map
            map_obj = self.create_base_map()
            
            # Add federal states layer
            self.layer_management.add_federal_states_layer(map_obj, federal_states_data, cities_data, camping_data)
            
            # ========= Create Layer Groups =========
            # Parks
            parks_heatmap = folium.FeatureGroup(name="Parks Heatmap", overlay=True, control=True)
            parks_polygone = folium.FeatureGroup(name="Polygone Parks", overlay=True, control=True)
            parks_pins = folium.FeatureGroup(name="Park Pins", overlay=True, control=True)

            # Friedhöfe
            friedhof_heatmap = folium.FeatureGroup(name="Friedhof Heatmap", overlay=True, control=True)
            polygon_friedhof = folium.FeatureGroup(name="Polygone Friedhöfe", overlay=True, control=True)
            friedhof_pins = folium.FeatureGroup(name="Friedhof Pins", overlay=True, control=True)

            # Camping
            camping_heatmap = folium.FeatureGroup(name="Camping Heatmap", overlay=True, control=True)
            camping_polygone = folium.FeatureGroup(name="Polygone Camping", overlay=True, control=True)
            camping_pins = folium.FeatureGroup(name="Campingplätze", overlay=True, control=True)

         
            
            #-----------Pins & Ploygone---------------------
            # Add parks layers
            if not parks_data["df"].empty:
                self.layer_management.add_markers_layer(
                    parks_pins, parks_data["df"], "Parks (Pins)", 
                    Config.MARKER_COLORS["parks_large"], 
                    Config.MARKER_COLORS["parks_small"], 
                    size_threshold
                )
                self.layer_management.add_geometry_layer(
                    parks_polygone, parks_data["df"], "Parks (Polygone)", "green"
                )
                self.layer_management.add_heatmap_layers(parks_heatmap, heatmap_data)

            
            # Add cemetery layers
            if not cemetery_data["df"].empty:
                self.layer_management.add_markers_layer(
                    friedhof_pins, cemetery_data["df"], "Friedhöfe (Pins)", 
                    Config.MARKER_COLORS["cemetery_large"], 
                    Config.MARKER_COLORS["cemetery_small"], 
                    size_threshold
                )
                self.layer_management.add_geometry_layer(
                    polygon_friedhof, cemetery_data["df"], "Friedhöfe (Polygone)", "blue"
                )
                self.layer_management.add_heatmap_layers(friedhof_heatmap, heatmap_data)

            # Add camping layers
            if not camping_data["df"].empty:
                self.layer_management.add_camping_markers_layer(
                    camping_pins, camping_data["df"], "Camping (Pins)",
                    Config.MARKER_COLORS["cemetery_large"], 
                    Config.MARKER_COLORS["cemetery_small"], 
                    size_threshold 
                )
                self.layer_management.add_geometry_layer(
                    camping_polygone, camping_data["df"], "Camping (Polygone)", "blue"
                )
                #Add heatmap camping
                self.layer_management.add_heatmap_layer_camping(camping_heatmap,camping_heatmap_data)
            
            # ========= Add Groups to Map =========
            for layer in [
                parks_heatmap, parks_polygone, parks_pins,
                friedhof_heatmap, polygon_friedhof, friedhof_pins,
                camping_heatmap, camping_polygone, camping_pins
            ]:
                map_obj.add_child(layer)

            # Add summary layer
            if not parks_data["df"].empty or not cemetery_data["df"].empty or not camping_data["df"].empty:
                self.layer_management.add_summary_layer(
                    map_obj, parks_data["df"], cemetery_data["df"],camping_data["df"], size_threshold
                )
            

            # Add styling and controls
            self.add_custom_css(map_obj)
            self.add_legend(map_obj, parks_data["df"], cemetery_data["df"], camping_data["df"])
            folium.LayerControl(collapsed=False).add_to(map_obj)
            
            logger.info("Main map built successfully")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error building main map: {e}")
            return self.create_base_map()
    
    def build_bundesland_map(self, bundesland: str, parks_data: gpd.GeoDataFrame, 
                           cemetery_data: gpd.GeoDataFrame,camping_data: gpd.GeoDataFrame, bundesland_geometry: gpd.GeoDataFrame,
                           size_threshold: float = 3) -> folium.Map:
        """
        Build a map for a specific federal state.
        
        Args:
            bundesland: Federal state name
            parks_data: Parks GeoDataFrame for the state
            cemetery_data: Cemetery GeoDataFrame for the state
            bundesland_geometry: Geometry of the federal state
            size_threshold: Size threshold for marker categorization
            
        Returns:
            Folium Map object for the federal state
        """
        try:
            logger.info(f"Building map for {bundesland}...")
            
            # Calculate center coordinates
            center = self._calculate_bundesland_center(parks_data, cemetery_data, camping_data)
            
            # Create map
            map_obj = self.create_base_map(center=center, zoom_start=8)
            
            # Add federal state polygon
            if not bundesland_geometry.empty:
                folium.GeoJson(
                    bundesland_geometry.__geo_interface__,
                    name=bundesland,
                    style_function=lambda x: {
                        "fillColor": "#3388ff", "color": "#000000",
                        "weight": 2, "fillOpacity": 0.2
                    }
                ).add_to(map_obj)
            
            # Add data layers
            if not parks_data.empty:
                self.layer_management.add_markers_layer(
                    map_obj, parks_data, "Park Pins", 
                    Config.MARKER_COLORS["parks_large"], 
                    Config.MARKER_COLORS["parks_small"], 
                    size_threshold
                )
                self.layer_management.add_geometry_layer(
                    map_obj, parks_data, "Park Polygone", "green"
                )
            # cemetry data
            if not cemetery_data.empty:
                self.layer_management.add_markers_layer(
                    map_obj, cemetery_data, "Friedhof Pins", 
                    Config.MARKER_COLORS["cemetery_large"], 
                    Config.MARKER_COLORS["cemetery_small"], 
                    size_threshold
                )
                self.layer_management.add_geometry_layer(
                    map_obj, cemetery_data, "Friedhöfe Polygone", "blue"
                )
            
            # camping data
            if not camping_data.empty:
                self.layer_management.add_markers_layer(
                    map_obj, camping_data, "Camping Pins", 
                    Config.MARKER_COLORS["cemetery_large"], 
                    Config.MARKER_COLORS["cemetery_small"], 
                    size_threshold
                )
                self.layer_management.add_geometry_layer(
                    map_obj, camping_data, "Camping Polygone", "blue"
                )
            
            # Add statistics overlay
            stats = self._calculate_bundesland_stats(parks_data, cemetery_data, camping_data)
            self._add_bundesland_overlay(map_obj, bundesland, stats)
            
            # Add controls
            self.add_custom_css(map_obj)
            folium.LayerControl().add_to(map_obj)
            
            logger.info(f"Map for {bundesland} built successfully")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error building map for {bundesland}: {e}")
            return self.create_base_map()
    
    def _calculate_bundesland_center(self, parks_data: gpd.GeoDataFrame, 
                                   cemetery_data: gpd.GeoDataFrame, camping_data: gpd.GeoDataFrame,) -> List[float]:
        """
        Calculate center coordinates for a federal state.
        
        Args:
            parks_data: Parks GeoDataFrame
            cemetery_data: Cemetery GeoDataFrame
            
        Returns:
            List of [latitude, longitude]
        """
        try:
            all_points = []
            
            if not parks_data.empty:
                all_points.extend(
                    [(row['latitude'], row['longitude']) for _, row in parks_data.iterrows()]
                )
            
            if not cemetery_data.empty:
                all_points.extend(
                    [(row['latitude'], row['longitude']) for _, row in cemetery_data.iterrows()]
                )
            
            if not camping_data.empty:
                all_points.extend(
                    [(row['latitude'], row['longitude']) for _, row in camping_data.iterrows()]
                )
            
            if not all_points:
                return Config.DEFAULT_CENTER
            
            center_lat = sum(p[0] for p in all_points) / len(all_points)
            center_lon = sum(p[1] for p in all_points) / len(all_points)
            
            return [center_lat, center_lon]
            
        except Exception as e:
            logger.error(f"Error calculating federal state center: {e}")
            return Config.DEFAULT_CENTER
    
    def _calculate_bundesland_stats(self, parks_data: gpd.GeoDataFrame, 
                                   cemetery_data: gpd.GeoDataFrame, camping_data: gpd.GeoDataFrame,) -> Dict[str, Any]:
        """
        Calculate statistics for a federal state.
        
        Args:
            parks_data: Parks GeoDataFrame
            cemetery_data: Cemetery GeoDataFrame
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Calculate bike potential
            parks_bike_potential = 0
            if not parks_data.empty:
                parks_bike_potential = parks_data['area_ha'].apply(
                    lambda x: self.calculator.calculate_required_bikes(
                        self.calculator.calculate_required_workers(x)
                    )
                ).sum()
            
            cemetery_bike_potential = 0
            if not cemetery_data.empty:
                cemetery_bike_potential = cemetery_data['area_ha'].apply(
                    lambda x: self.calculator.calculate_required_bikes(
                        self.calculator.calculate_required_workers(x)
                    )
                ).sum()
            
            return {
                'parks_anzahl': len(parks_data),
                'parks_flaeche': parks_data['area_ha'].sum() if not parks_data.empty else 0,
                'friedhoefe_anzahl': len(cemetery_data),
                'friedhoefe_flaeche': cemetery_data['area_ha'].sum() if not cemetery_data.empty else 0,
                'fahrradpotenzial': parks_bike_potential + cemetery_bike_potential,
                'camping_anzahl': len(camping_data),
                'camping_flaeche': camping_data['area_ha'].sum() if not camping_data.empty else 0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating federal state statistics: {e}")
            return {
                'parks_anzahl': 0,
                'parks_flaeche': 0,
                'friedhoefe_anzahl': 0,
                'friedhoefe_flaeche': 0,
                'fahrradpotenzial': 0
            }
    
    def _add_bundesland_overlay(self, map_obj: folium.Map, bundesland: str, 
                               stats: Dict[str, Any]):
        """
        Add statistics overlay for federal state map.
        
        Args:
            map_obj: Folium map object
            bundesland: Federal state name
            stats: Statistics dictionary
        """
        try:
            overlay_html = f"""
            <div style="
                position: fixed; bottom: 10px; right: 10px; z-index: 9999;
                background-color: white; padding: 10px; border: 2px solid #444;
                border-radius: 8px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-size: 12px; width: 220px;
            ">
                <b>{bundesland}</b><br>
                Parks: {stats['parks_anzahl']}<br>
                Parkfläche: {stats['parks_flaeche']:.2f} ha<br>
                Friedhöfe: {stats['friedhoefe_anzahl']}<br>
                Friedhofsfläche: {stats['friedhoefe_flaeche']:.2f} ha<br>
                Fahrradpotenzial: {stats['fahrradpotenzial']} Räder
                Camping: {stats['camping_anzahl']}<br>
                Campingfläche: {stats['camping_flaeche']:.2f} ha<br>
            </div>
            """
            Element(overlay_html).add_to(map_obj.get_root().html)
            
        except Exception as e:
            logger.error(f"Error adding federal state overlay: {e}")

    
    def add_legend(self, map_obj: folium.Map, parks_data: pd.DataFrame, 
                   cemetery_data: pd.DataFrame, camping_data: gpd.GeoDataFrame,):
        """
        Add legend to the map.
        
        Args:
            map_obj: Folium map object
            parks_data: Parks DataFrame
            cemetery_data: Cemetery DataFrame
        """
        try:
            gesamt_parkflaeche = parks_data['area_ha'].sum() if not parks_data.empty else 0
            gesamt_friedhofsflaeche = cemetery_data['area_ha'].sum() if not cemetery_data.empty else 0
            gesamt_campingflaeche = camping_data['area_ha'].sum() if not camping_data.empty else 0
            
            # Calculate total bikes
            total_park_workers = 0
            total_cemetery_workers = 0
            
            if not parks_data.empty:
                total_park_workers = parks_data['area_ha'].apply(
                    self.calculator.calculate_required_workers
                ).sum()
            
            if not cemetery_data.empty:
                total_cemetery_workers = cemetery_data['area_ha'].apply(
                    self.calculator.calculate_required_workers
                ).sum()
            
            gesamt_fahrraeder = self.calculator.calculate_required_bikes(
                total_park_workers + total_cemetery_workers
            )

            #gesamt_camping_fahrraeder = self.calculator.calculate_static_bikes.sum()
            
            html = f"""
            <div style="
                position: fixed; bottom: 20px; right: 20px; z-index: 9999;
                background-color: rgba(255, 255, 255, 0.9); border: 1px solid #ccc;
                border-radius: 10px; padding: 15px; font-family: Arial, sans-serif;
                font-size: 14px; box-shadow: 0 0 10px rgba(0,0,0,0.2); max-width: 400px;
            ">
                <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 16px;">
                Deutschland – Städte über 50.000 Einwohner
            </h4>
            <p>Anzahl der Parks: <strong>{len(parks_data)}</strong></p>
            <p>Parkfläche gesamt: <strong>{gesamt_parkflaeche:.2f} ha</strong></p>
            <p>Anzahl Friedhöfe: <strong>{len(cemetery_data)}</strong></p>
            <p>Friedhofsfläche gesamt: <strong>{gesamt_friedhofsflaeche:.2f} ha</strong></p>
            <p>Potenzial Fahrräder: <strong>{gesamt_fahrraeder}</strong></p>

            <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 16px;">
                Deutschland – Campingplätze über 10 ha
            </h4>

            <p>Anzahl Campingplätze: <strong>{len(camping_data)}</strong></p>
            <p>Campingfläche gesamt: <strong>{gesamt_campingflaeche:.2f} ha</strong></p>
            <p>Potenzial Fahrräder Campingplätze: <strong>{len(camping_data)*2}</strong></p>
        </div>
        """
        
            Element(html).add_to(map_obj.get_root().html)
            logger.info("Legend added to map successfully")
        
        except Exception as e:
            logger.error(f"Error adding legend to map: {e}")

    def add_custom_css(self, map_obj: folium.Map):
        """Fügt benutzerdefiniertes CSS hinzu"""
        css = """
        <style>
            .leaflet-control-layers label {
                font-size: 18px !important; font-weight: bold;
                margin-bottom: 10px; display: block;
            }
           .leaflet-control-layers input[type="checkbox"] {
                width: 18px; height: 18px; accent-color: #1e90ff;
            }
            .leaflet-control-layers label:hover {
                background-color: rgba(30, 144, 255, 0.1); cursor: pointer;
                border-radius: 5px; padding: 2px 5px;
            }
            .leaflet-control-layers { transition: all 0.3s ease; }
            .leaflet-control-layers:hover {
                transform: scale(1.02); box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            }
        </style>
    """
        Element(css).add_to(map_obj.get_root().html)
