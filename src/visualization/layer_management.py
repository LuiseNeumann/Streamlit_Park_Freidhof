import folium
from folium.plugins import HeatMap
import pandas as pd
import geopandas as gpd
import logging
from typing import Dict, Any, List
from config.settings import Config
from src.visualization.popup_content import PopupCreator
from src.utils.calculations import WorkforceCalculator

logger = logging.getLogger(__name__)

class LayerManager:
    """Manages different layers for the Folium map."""
    
    def __init__(self):
        self.popup_creator = PopupCreator()
    
    def add_markers_layer(self, group: folium.Map, data: pd.DataFrame, 
                         layer_name: str, color_large: str, color_small: str, 
                         size_threshold: float) -> folium.FeatureGroup:
        """
        Add markers layer to the map.
        
        Args:
            map_obj: Folium map object
            data: DataFrame with location data
            layer_name: Name of the layer
            color_large: Color for large markers
            color_small: Color for small markers
            size_threshold: Size threshold for marker categorization
            
        Returns:
            FeatureGroup layer
        """
        try:
            layer = folium.FeatureGroup(name=layer_name)
            
            for _, row in data.iterrows():
                popup_content = self.popup_creator.create_basic_popup(row)
                icon_color = color_large if row['area_ha'] > size_threshold else color_small
                icon_type = "info-sign" if row['area_ha'] > size_threshold else None
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_content, max_width=Config.POPUP_MAX_WIDTH),
                    tooltip=row['name'],
                    icon=folium.Icon(color=icon_color, icon=icon_type),
                ).add_to(layer)
            
            layer.add_to(group)
            logger.info(f"Added {len(data)} markers to layer '{layer_name}'")
            return layer
            
        except Exception as e:
            logger.error(f"Error adding markers layer '{layer_name}': {e}")
            return folium.FeatureGroup(name=layer_name)

    def add_camping_markers_layer(self, map_obj: folium.Map, data: pd.DataFrame, 
                         layer_name: str, color_large: str, color_small: str, 
                         size_threshold: float) -> folium.FeatureGroup:
        """
        Add markers layer to the map.
        
        Args:
            map_obj: Folium map object
            data: DataFrame with location data
            layer_name: Name of the layer
            color_large: Color for large markers
            color_small: Color for small markers
            size_threshold: Size threshold for marker categorization
            
        Returns:
            FeatureGroup layer
        """
        try:
            layer = folium.FeatureGroup(name=layer_name)
            
            for _, row in data.iterrows():
                popup_content = self.popup_creator.create_basic_popup_camping(row)
                icon_color = color_large if row['area_ha'] > size_threshold else color_small
                icon_type = "info-sign" if row['area_ha'] > size_threshold else None
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_content, max_width=Config.POPUP_MAX_WIDTH),
                    tooltip=row['name'],
                    icon=folium.Icon(color=icon_color, icon=icon_type),
                ).add_to(layer)
            
            layer.add_to(map_obj)
            logger.info(f"Added {len(data)} markers to layer '{layer_name}'")
            return layer
            
        except Exception as e:
            logger.error(f"Error adding markers layer '{layer_name}': {e}")
            return folium.FeatureGroup(name=layer_name)
    
    def add_geometry_layer(self, map_obj: folium.Map, data: pd.DataFrame, 
                          layer_name: str, color: str = "green") -> folium.FeatureGroup:
        """
        Add geometry layer to the map.
        
        Args:
            map_obj: Folium map object
            data: DataFrame with geometry data
            layer_name: Name of the layer
            color: Color for the geometries
            
        Returns:
            FeatureGroup layer
        """
        try:
            layer = folium.FeatureGroup(name=layer_name)
            
            for _, row in data.iterrows():
                geom = row["geometry"]
                if not geom or geom.is_empty:
                    continue
                    
                popup_content = f"<b>{row['name']}</b><br>Größe: {row['area_ha']:.2f} ha"
                
                if geom.geom_type == "Polygon":
                    self._add_polygon(layer, geom, popup_content, color)
                elif geom.geom_type == "MultiPolygon":
                    for polygon in geom.geoms:
                        self._add_polygon(layer, polygon, popup_content, color)
            
            layer.add_to(map_obj)
            logger.info(f"Added geometry layer '{layer_name}' with {len(data)} features")
            return layer
            
        except Exception as e:
            logger.error(f"Error adding geometry layer '{layer_name}': {e}")
            return folium.FeatureGroup(name=layer_name)
    
    def _add_polygon(self, layer: folium.FeatureGroup, polygon, 
                    popup_content: str, color: str):
        """
        Helper function to add a polygon to the layer.
        
        Args:
            layer: FeatureGroup layer
            polygon: Shapely polygon object
            popup_content: HTML content for popup
            color: Color for the polygon
        """
        try:
            folium.Polygon(
                locations=[(point[1], point[0]) for point in polygon.exterior.coords],
                color=color,
                weight=1,
                fill=True,
                fill_opacity=Config.POLYGON_OPACITY,
                popup=folium.Popup(popup_content, max_width=Config.POPUP_MAX_WIDTH)
            ).add_to(layer)
        except Exception as e:
            logger.error(f"Error adding polygon: {e}")
    
    def add_summary_layer(self, map_obj: folium.Map, parks_data: pd.DataFrame, 
                         cemetery_data: pd.DataFrame,camping_data: pd.DataFrame, size_threshold: float) -> folium.FeatureGroup:
        """
        Add city summary layer to the map.
        
        Args:
            map_obj: Folium map object
            parks_data: Parks DataFrame
            cemetery_data: Cemetery DataFrame
            camping_data: Camping DataFrame
            size_threshold: Size threshold for calculations
            
        Returns:
            FeatureGroup layer
        """
        try:
            layer = folium.FeatureGroup(name="Stadt (Zusammenfassung)")
            
            # Add worker and bike calculations if not present
            if 'arbeiter' not in parks_data.columns:
                parks_data['arbeiter'] = parks_data['area_ha'].apply(
                    self.popup_creator.calculator.calculate_required_workers
                )
                parks_data['fahrraeder'] = parks_data['arbeiter'].apply(
                    self.popup_creator.calculator.calculate_required_bikes
                )
            
            if 'arbeiter' not in cemetery_data.columns:
                cemetery_data['arbeiter'] = cemetery_data['area_ha'].apply(
                    self.popup_creator.calculator.calculate_required_workers
                )
                cemetery_data['fahrraeder'] = cemetery_data['arbeiter'].apply(
                    self.popup_creator.calculator.calculate_required_bikes
                )

            if 'arbeiter' not in camping_data.columns:
                camping_data['arbeiter'] = camping_data['area_ha'].apply(
                    self.popup_creator.calculator.calculate_required_workers
                )
                camping_data['fahrraeder'] = self.popup_creator.calculator.calculate_static_bikes()
            
            # Get unique cities
            unique_cities = set(parks_data["city"]).union(set(cemetery_data["city"]))
            
            for city in unique_cities:
                city_park_data = parks_data[parks_data["city"] == city]
                city_cemetery_data = cemetery_data[cemetery_data["city"] == city]
                city_camping_data = camping_data[camping_data["stadt"] == city]
                
                # Calculate city center
                avg_lat, avg_lon = self._calculate_city_center(city_park_data, city_cemetery_data, city_camping_data)
                if avg_lat is None or avg_lon is None:
                    continue
                
                # Create popup content
                popup_content = self.popup_creator.create_city_summary_popup(
                    city, city_park_data, city_cemetery_data,city_camping_data, size_threshold
                )
                
                folium.Marker(
                    location=[avg_lat, avg_lon],
                    popup=folium.Popup(popup_content, max_width=Config.POPUP_MAX_WIDTH),
                    icon=folium.Icon(color="green", icon="flag")
                ).add_to(layer)
            
            layer.add_to(map_obj)
            logger.info(f"Added summary layer with {len(unique_cities)} cities")
            return layer
            
        except Exception as e:
            logger.error(f"Error adding summary layer: {e}")
            return folium.FeatureGroup(name="Stadt (Zusammenfassung)")
    
    def _calculate_city_center(self, city_park_data: pd.DataFrame, 
                              city_cemetery_data: pd.DataFrame, city_camping_data: pd.DataFrame) -> tuple:
        """
        Calculate the center coordinates of a city.
        
        Args:
            city_park_data: Parks data for the city
            city_cemetery_data: Cemetery data for the city
            
        Returns:
            Tuple of (latitude, longitude) or (None, None)
        """
        try:
            if not city_park_data.empty and not city_cemetery_data.empty and not city_camping_data.empty:
                avg_lat = (city_park_data["latitude"].mean() + city_cemetery_data["latitude"].mean()+city_camping_data["latitude"].mean()) / 2
                avg_lon = (city_park_data["longitude"].mean() + city_cemetery_data["longitude"].mean()+city_camping_data["latitude"].mean()) / 2
            elif not city_park_data.empty:
                avg_lat = city_park_data["latitude"].mean()
                avg_lon = city_park_data["longitude"].mean()
            elif not city_cemetery_data.empty:
                avg_lat = city_cemetery_data["latitude"].mean()
                avg_lon = city_cemetery_data["longitude"].mean()
            elif not city_camping_data.empty:
                avg_lat = city_camping_data["latitude"].mean()
                avg_lon = city_camping_data["longitude"].mean()
            else:
                return None, None, None
            
            return avg_lat, avg_lon
            
        except Exception as e:
            logger.error(f"Error calculating city center: {e}")
            return None, None
    
    def add_heatmap_layers(self, map_obj: folium.Map, heatmap_data: Dict[str, pd.DataFrame]):
        """
        Add heatmap layers to the map.
        
        Args:
            map_obj: Folium map object
            heatmap_data: Dictionary with heatmap DataFrames
        """
        try:
            # Green areas heatmap
            if not heatmap_data["green_areas"].empty:
                green_df = heatmap_data["green_areas"]
                max_flaeche = green_df['grünfläche_m2'].max()
                
                heat_data = [
                    [row['Latitude'], row['Longitude'], row['grünfläche_m2'] / max_flaeche] 
                    for _, row in green_df.iterrows()
                ]
                
                heatmap_layer = folium.FeatureGroup(name="Heatmap (Parkfläche)")
                HeatMap(
                    heat_data, 
                    radius=Config.HEATMAP_RADIUS, 
                    blur=Config.HEATMAP_BLUR, 
                    max_zoom=10
                ).add_to(heatmap_layer)
                heatmap_layer.add_to(map_obj)
                logger.info("Added green areas heatmap")
            
            # Bike demand heatmap
            if not heatmap_data["bike_demand"].empty:
                bike_df = heatmap_data["bike_demand"]
                bike_heat_data = [
                    [float(row["latitude"]), float(row["longitude"]), float(row["total_bike"])]
                    for _, row in bike_df.iterrows()
                ]
                
                bike_heatmap_layer = folium.FeatureGroup(name="Fahrradbedarf Heatmap")
                HeatMap(
                    bike_heat_data, 
                    radius=20, 
                    max_zoom=13, 
                    blur=Config.HEATMAP_BLUR, 
                    min_opacity=0.5
                ).add_to(bike_heatmap_layer)
                bike_heatmap_layer.add_to(map_obj)
                logger.info("Added bike demand heatmap")
                
        except Exception as e:
            logger.error(f"Error adding heatmap layers: {e}")

    def add_heatmap_layer_camping(self, map_obj: folium.Map, camping_heatmap_data: Dict[str, pd.DataFrame]): 
        """
        Add heatmap layers to the map.
        
        Args:
            map_obj: Folium map object
            heatmap_data: Dictionary with heatmap DataFrames
        """

        try:
            logger.debug(f"Available keys in camping_heatmap_data: {list(camping_heatmap_data.keys())}")

            #camping_df = camping_heatmap_data["camping_areas"]
            #logger.debug(f"Camping DataFrame columns: {camping_df.columns.tolist()}")

            #camping_df = camping_heatmap_data["camping_heatmap"]

            if not camping_heatmap_data["camping_heatmap"].empty:
                camping_df = camping_heatmap_data["camping_heatmap"]
            
                if camping_df.empty:
                    logger.warning("Camping DataFrame is empty.")
                    return
    
                if 'area_ha' not in camping_df.columns:
                    logger.error("Missing 'area_ha' column in camping DataFrame.")
                    return
                max_flaeche = camping_df['area_ha'].max()
                
                camping_heat_data = [
                    [row['latitude'], row['longitude'], row['area_ha'] / max_flaeche] 
                    for _, row in camping_df.iterrows()
                ]
                
                heatmap_layer = folium.FeatureGroup(name="Heatmap (Camping)")
                HeatMap(
                    camping_heat_data, 
                    radius=Config.HEATMAP_RADIUS, 
                    blur=Config.HEATMAP_BLUR, 
                    max_zoom=10
                ).add_to(heatmap_layer)
                heatmap_layer.add_to(map_obj)
                logger.info("Added camping areas heatmap")

        except Exception as e:
            logger.error(f"Error adding heatmap camping layers: {e}")
    
    def add_federal_states_layer(self, map_obj: folium.Map, federal_states_data: Dict[str, Any], 
                                cities_data: pd.DataFrame, camping_data:pd.DataFrame) -> folium.FeatureGroup:
        """
        Add federal states layer to the map.
        
        Args:
            map_obj: Folium map object
            federal_states_data: Federal states data dictionary
            cities_data: Cities DataFrame
            
        Returns:
            FeatureGroup layer
        """
        try:
            layer = folium.FeatureGroup(name="Bundesland")
            
            def style_function(feature):
                return {
                    "fillColor": federal_states_data["color_map"].get(
                        feature["properties"]["NAME_1"], "gray"
                    ),
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": Config.POLYGON_OPACITY
                }
            
            def highlight_function(feature):
                return {"weight": 3, "fillOpacity": 0.7}
            
            for feature in federal_states_data["geojson"]["features"]:
                bundesland_name = feature["properties"]["NAME_1"]
                popup_text = f"<b>{bundesland_name}</b><br><br>{self._get_city_list(bundesland_name, cities_data,camping_data)}"
                
                folium.GeoJson(
                    feature,
                    name=bundesland_name,
                    style_function=style_function,
                    highlight_function=highlight_function,
                    tooltip=folium.GeoJsonTooltip(fields=["NAME_1"], aliases=["Bundesland:"]),
                    popup=folium.Popup(popup_text, max_width=Config.POPUP_MAX_WIDTH)
                ).add_to(layer)
            
            layer.add_to(map_obj)
            logger.info("Added federal states layer")
            return layer
            
        except Exception as e:
            logger.error(f"Error adding federal states layer: {e}")
            return folium.FeatureGroup(name="Bundesland")
    
    def _get_city_list(self, bundesland: str, cities_data: pd.DataFrame, camping_data: pd.DataFrame) -> str:
        """
        Create city list for federal state popup.
        
        Args:
            bundesland: Federal state name
            cities_data: Cities DataFrame
            
        Returns:
            HTML string with city table
        """
        try:
            cities = cities_data[cities_data["Bundesland"] == bundesland]
            if cities.empty:
                return "Keine Städte gefunden"
            
            bundesland_link = bundesland.replace(" ", "_") + ".html"
            
            # Calculate statistics
            total_parks = cities.get("Anzahl Parks", pd.Series([0])).sum()
            total_parks_area = cities.get("Gesamtfläche Parks (ha)", pd.Series([0])).sum()
            total_cemeteries = cities.get("Anzahl Friedhöfe", pd.Series([0])).sum()
            total_cemetery_area = cities.get("Gesamtfläche Friedhöfe (ha)", pd.Series([0])).sum()
            total_bike_potential = cities.get("Fahrrad Potenzial", pd.Series([0])).sum()
            
            table_html = f"""
            <table border='1' style='border-collapse: collapse; width: 100%;'>
            <caption style="font-weight:bold; margin-bottom:5px;">
                <a href="{bundesland_link}" target="_blank">➤ Karte für {bundesland} öffnen</a>
            </caption>
            <tr>
                <th>Stadt</th><th>Einwohner</th><th>Parks</th><th>Parkfläche (ha)</th>
                <th>Friedhöfe</th><th>Friedhofsfläche (ha)</th><th>Fahrrad Potenzial</th>
            </tr>
            """
            
            for _, row in cities.iterrows():
                table_html += f"""
                <tr>
                    <td>{row.get('Stadt', '')}</td>
                    <td>{row.get('Einwohner', '')}</td>
                    <td>{row.get('Anzahl Parks', 0)}</td>
                    <td>{row.get('Gesamtfläche Parks (ha)', 0)}</td>
                    <td>{row.get('Anzahl Friedhöfe', 0)}</td>
                    <td>{row.get('Gesamtfläche Friedhöfe (ha)', 0)}</td>
                    <td>{row.get('Fahrrad Potenzial', 0)}</td>
                </tr>
                """
            
            # Summary row
            table_html += f"""
            <tr style="font-weight:bold; background-color: #f0f0f0;">
                <td>Gesamt</td><td>-</td><td>{total_parks}</td><td>{total_parks_area:.2f}</td>
                <td>{total_cemeteries}</td><td>{total_cemetery_area:.2f}</td><td>{total_bike_potential}</td>
            </tr>
            </table>
            """
            
            return table_html
            
        except Exception as e:
            logger.error(f"Error creating city list for {bundesland}: {e}")
            return "Fehler beim Laden der Städtedaten"