import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import math
import hashlib
from src.visualization.layer_management import LayerManager
from src.visualization.map_builder import MapBuilder
#from src.visualization.popup_content import PopupCreator
from src.data_processing.data_loader import DataLoader
from config.settings import Config

import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import geopandas as gpd
from fuzzywuzzy import fuzz, process


# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parks_visualization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParksVisualization:
    """Hauptklasse für die Parks-Visualisierung"""

    def __init__(self):
        self.data_loader = DataLoader()
        self.map_builder = MapBuilder()
        self.map_builder.layer_management = LayerManager()
        logger.info("Initialized Parks Visualization Application")
    
    def load_all_data(self) -> Dict[str, Any]:
        """Load all required data for visualization."""
        logger.info("Loading all data sources...")
        
        # Load main datasets
        parks_data = self.data_loader.load_parks_data()
        cemetery_data = self.data_loader.load_cemetery_data()
        cities_data = self.data_loader.load_cities_data()
        federal_states_data = self.data_loader.load_federal_states_data()
        heatmap_data = self.data_loader.load_heatmap_data()
        camping_data = self.data_loader.load_camping_data()
        camping_heatmap_data = self.data_loader.load_heatmap_camping_data()
        
        return {
            "parks": parks_data,
            "cemetery": cemetery_data,
            "cities": cities_data,
            "federal_states": federal_states_data,
            "heatmap": heatmap_data,
            "camping": camping_data,
            "camping_heatmap": camping_heatmap_data

        }

    
    def create_main_map(self, data: Dict[str, Any], size_threshold: float = None) -> folium.Map:
        """Erstellt die Hauptkarte"""
        try:
            logger.info(f"Creating main map with size threshold: {size_threshold}")
    
            
            # Parks hinzufügen
            main_map = self.map_builder.build_main_map(
                parks_data=data["parks"],
                cemetery_data=data["cemetery"],
                camping_data=data["camping"],
                cities_data=data["cities"],
                federal_states_data=data["federal_states"],
                heatmap_data=data["heatmap"],
                camping_heatmap_data=data["camping_heatmap"],
                size_threshold=size_threshold
            )
            
            return main_map
            
        except Exception as e:
            logger.error(f"Error creating main map: {e}")
            raise
    
    def create_bundesland_maps(self, data: Dict[str, Any], size_threshold: float = None) -> Dict[str, folium.Map]:
        """Erstellt Karten für einzelne Bundesländer"""
        try:
            bundesland_maps = {}
            federal_states = data["federal_states"]["gdf"]["NAME_1"].unique()
            logger.info(f"Creating maps for {len(federal_states)} federal states")
            
            for bundesland in federal_states:
                try:
                    # Filter data for this federal state
                    parks_filtered = self._filter_data_by_bundesland(
                        data["parks"]["gdf"], bundesland
                    )
                    cemetery_filtered = self._filter_data_by_bundesland(
                        data["cemetery"]["gdf"], bundesland
                    )
                    camping_filtered = self._filter_data_by_bundesland(
                        data["camping"]["gdf"], bundesland
                    )
                    # Get federal state geometry
                    bundesland_geometry = data["federal_states"]["gdf"][
                        data["federal_states"]["gdf"]["NAME_1"] == bundesland
                    ]
                    
                    # Create the map
                    bundesland_map = self.map_builder.build_bundesland_map(
                        bundesland=bundesland,
                        parks_data=parks_filtered,
                        cemetery_data=cemetery_filtered,
                        camping_data=camping_filtered,
                        bundesland_geometry=bundesland_geometry,
                        size_threshold=size_threshold
                    )
                    
                    bundesland_maps[bundesland] = bundesland_map  

                
                except Exception as e:
                    logger.error(f"Error creating map for {bundesland}: {e}")
                    continue
            
            return bundesland_maps
            
            
        except Exception as e:
            logger.error(f"Error creating bundesland maps: {e}")
            return {}
        
    def _filter_data_by_bundesland(self, gdf, bundesland_name: str):
        """Filter GeoDataFrame by federal state name"""

        try:
            if gdf.empty or 'bundesland' not in gdf.columns:
                logger.warning(f"No 'bundesland' column found in data with columns: {gdf.columns.tolist()}")
                return gdf.iloc[0:0]
            
            return gdf[gdf['bundesland'] == bundesland_name].copy()
            
        except Exception as e:
            logger.error(f"Error filtering data for {bundesland_name}: {e}")
            return gdf.iloc[0:0]

    def run(self, size_threshold: float = None, create_bundesland_maps: bool = True) -> Dict[str, Any]:
        """
        Run the complete visualization pipeline.
        
        Args:
            size_threshold: Size threshold for marker categorization
            create_bundesland_maps: Whether to create individual federal state maps
            
        Returns:
            Dictionary with paths to created maps
        """
        try:
            logger.info("Starting Parks Visualization pipeline...")
            
            # Load all data
            data = self.load_all_data()
            
            # Validate data
            if data["parks"]["df"].empty and data["cemetery"]["df"].empty:
                logger.error("No parks or cemetery data loaded. Cannot create maps.")
                return {"error": "No data available"}
            
            results = {}
            
            # Create main map
            logger.info("Creating main Germany map...")
            main_map_path = self.create_main_map(data, size_threshold)
            results["main_map"] = main_map_path
            
            # Create federal state maps if requested
            if create_bundesland_maps:
                logger.info("Creating federal state maps...")
                bundesland_maps = self.create_bundesland_maps(data, size_threshold)
                results["bundesland_maps"] = bundesland_maps
            
            # Log summary
            total_parks = len(data["parks"]["df"])
            total_cemeteries = len(data["cemetery"]["df"])
            total_cities = len(data["cities"]) if not data["cities"].empty else 0
            total_camping =len(data["camping"])
            
            logger.info(f"""
            Visualization completed successfully!
            - Total parks: {total_parks}
            - Total cemeteries: {total_cemeteries}
            - Total cities: {total_cities}
            - Total camping: {total_camping}
            - Main map: {main_map_path}
            - Federal state maps: {len(results.get('bundesland_maps', {}))}
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in visualization pipeline: {e}")
            raise

# Session State Initialisierung
def init_session_state():
    """Initialisiert Session State Variablen"""
    if "slider_min" not in st.session_state:
        st.session_state.slider_min = 1.0
        st.session_state.slider_max = 20.0

    if "manual_min" not in st.session_state:
        st.session_state.manual_min = st.session_state.slider_min
        st.session_state.manual_max = st.session_state.slider_max

# Callback-Funktionen
def update_manual_from_slider():
    """Slider Änderung → Update Number Input"""
    st.session_state.manual_min = st.session_state.slider_min
    st.session_state.manual_max = st.session_state.slider_max

def update_slider_from_manual():
    """Number Input Änderung → Update Slider"""
    st.session_state.slider_min = st.session_state.manual_min
    st.session_state.slider_max = st.session_state.manual_max

# Berechnungsfunktionen
def berechne_arbeiter(area_ha: float, min_pro_m2: float, std_pro_tag: int, tage_pro_jahr: int) -> int:
    """Berechnet Anzahl benötigter Arbeiter basierend auf Flächengröße"""
    if area_ha <= 0:
        return 0
    
    area_m2 = area_ha * 10000
    minuten = area_m2 * min_pro_m2
    stunden = minuten / 60
    tage = stunden / std_pro_tag
    arbeiter = tage / tage_pro_jahr
    return max(1, math.ceil(arbeiter))

def berechne_fahrradanzahl(arbeiter: int, arbeiter_pro_rad: float, methode: str) -> float:
    """Berechnet Anzahl benötigter Fahrräder"""
    if arbeiter == 0:
        return 0
    
    fahrraeder = arbeiter / arbeiter_pro_rad
    
    if methode == "Aufrunden":
        return math.ceil(fahrraeder)
    elif methode == "Abrunden":
        return math.floor(fahrraeder)
    elif methode == "Gleitkomma":
        return round(fahrraeder, 2)
    return 0

def create_data_hash(df: pd.DataFrame, min_groesse: tuple, methode: str, 
                    min_pro_m2: float, std_pro_tag: int, tage_pro_jahr: int, 
                    arbeiter_pro_rad: float) -> str:
    """Erstellt einen Hash der relevanten Parameter für Cache-Invalidierung"""
    hash_string = f"{len(df)}_{min_groesse}_{methode}_{min_pro_m2}_{std_pro_tag}_{tage_pro_jahr}_{arbeiter_pro_rad}"
    return hashlib.md5(hash_string.encode()).hexdigest()

@st.cache_data
def load_and_process_data():
    """Lädt und verarbeitet die Daten (mit Caching)"""
    viz = ParksVisualization()
    return viz.load_all_data()

def calculate_bundesland_stats(processed_data, bundesland_name):
    """Berechnet Statistiken für ein bestimmtes Bundesland"""
    stats = {
        "total_locations": 0,
        "total_workers": 0,
        "total_bikes": 0,
        "total_area": 0.0,
        "parks_count": 0,
        "cemetery_count": 0,
        "camping_count": 0
    }
    
    # Prüfe alle Datensätze für das Bundesland
    datasets = [
        ("parks", processed_data["parks_filtered"]),
        ("cemetery", processed_data["cemetery_filtered"]),
        ("camping", processed_data["camping_filtered"])
    ]
    
    for dataset_name, df in datasets:
        if not df.empty and 'bundesland' in df.columns:
            bl_data = df[df['bundesland'] == bundesland_name]
            if not bl_data.empty:
                stats["total_locations"] += len(bl_data)
                stats["total_workers"] += bl_data['Arbeiter'].sum()
                stats["total_bikes"] += bl_data['Marktpotenzial'].sum()
                stats["total_area"] += bl_data['area_ha'].sum()
                stats[f"{dataset_name}_count"] = len(bl_data)
    
    return stats

def show_bundesland_details(processed_data, bundesland_name):
    """Zeigt detaillierte Daten für ein Bundesland"""
    datasets = [
        ("Parks", processed_data["parks_filtered"]),
        ("Friedhöfe", processed_data["cemetery_filtered"]),
        ("Campingplätze", processed_data["camping_filtered"])
    ]
    
    for name, df in datasets:
        if not df.empty and 'bundesland' in df.columns:
            bl_data = df[df['bundesland'] == bundesland_name]
            if not bl_data.empty:
                st.subheader(f"{name} in {bundesland_name} ({len(bl_data)} Standorte)")
                
                # Zeige relevante Spalten
                display_columns = ['name', 'area_ha', 'Arbeiter', 'Marktpotenzial']
                available_columns = [col for col in display_columns if col in bl_data.columns]
                
                if available_columns:
                    st.dataframe(bl_data[available_columns])
                    
                    # Statistiken
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Arbeiter:** {bl_data['Arbeiter'].sum()}")
                    with col2:
                        st.write(f"**Fahrräder:** {bl_data['Marktpotenzial'].sum()}")
                    with col3:
                        st.write(f"**Ø Fläche:** {bl_data['area_ha'].mean():.2f} ha")
                else:
                    st.write("Keine detaillierten Daten verfügbar")
                st.write("---")

def main():
    """Hauptfunktion der Streamlit-App"""
    st.set_page_config(page_title="Marktdurchdringungstool", layout="wide")
    st.title("Marktdurchdringungstool für Lastenräder")
    
    # Session State initialisieren
    init_session_state()
    
    # Daten laden (nur einmal)
    try:
        @st.cache_data
        def load_base_data():
            viz = ParksVisualization()
            return viz.load_all_data()
        
        base_data = load_base_data()
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return
    
    if base_data["parks"]["df"].empty:
        st.error("Keine Daten verfügbar!")
        return

    # Seitenleiste: Parameter
    st.sidebar.header("Parameter für Marktanalyse")
    st.sidebar.markdown("### Minimale Flächengröße (ha)")

    # Get max area for slider
    max_area = float(base_data["parks"]["df"]["area_ha"].max())

    # Slider für Flächenbereich
    area_range = st.sidebar.slider(
        "Flächenbereich wählen (ha)", 
        min_value=0.0, 
        max_value=max_area, 
        value=(st.session_state.slider_min, st.session_state.slider_max), 
        step=0.1,
        key="slider_range",
        on_change=update_manual_from_slider
    )

    # Eingabefelder
    st.sidebar.markdown("**Oder exakte Werte eingeben:**")
    st.sidebar.number_input(
        "Minimale Fläche (ha)", 
        min_value=0.0, 
        max_value=max_area, 
        step=0.1,
        key="manual_min",
        on_change=update_slider_from_manual
    )
    st.sidebar.number_input(
        "Maximale Fläche (ha)", 
        min_value=0.0, 
        max_value=max_area, 
        step=0.1,
        key="manual_max",
        on_change=update_slider_from_manual
    )
    min_groesse = (st.session_state.slider_min, st.session_state.slider_max)
    

    # Weitere Parameter
    min_pro_m2 = st.sidebar.slider("Arbeitszeit in Minuten pro m²", 0.5, 5.0, 1.3, 0.1)
    std_pro_tag = st.sidebar.slider("Aktive Arbeitsstunden pro Tag", 1, 10, 5)
    tage_pro_jahr = st.sidebar.slider("Arbeitstage pro Jahr pro Person", 100, 300, 220)
    arbeiter_pro_rad = st.sidebar.slider("Anzahl Arbeiter pro Fahrrad", 0.5, 5.0, 2.0, 0.1)

    # Berechnungsmethode
    methode = st.sidebar.radio("Berechnungsmethode für Fahrradanzahl:", 
                              ["Aufrunden", "Abrunden", "Gleitkomma"])
    
    # Empfehlungstext
    st.markdown(f"""
    ### Empfehlung
    - Arbeitszeit pro m²: **{min_pro_m2} Minuten** 
    - Arbeitstage pro Person im Jahr: **{tage_pro_jahr}**
    - Aktive Arbeitszeit in Stunden/Tag: **{std_pro_tag}**
    - Fahrrad/Arbeiter (Anzahl Personen für ein Rad): **{arbeiter_pro_rad}** 
    
    ### Berechnung-Erklärung 
    
    #### Funktion berechne_arbeiter(area_ha):
    - Eingabe: Fläche in Hektar (area_ha)
    - Umrechnung in Quadratmeter: area_m2 = area_ha * 10.000
    - Zeitaufwand: Pro m² werden {min_pro_m2} Minuten benötigt
    - Umrechnung in Stunden und Tage
    - Ein Arbeiter arbeitet {tage_pro_jahr} Tage im Jahr
    - Ausgabe: Aufgerundete Anzahl an Arbeitern, mindestens 1
    """)

    st.markdown("""
    ### Erläuterung 
    - **Aufrunden**: Bei z.B. "0,5" Fahrrädern wird ein Fahrrad empfohlen
    - **Abrunden**: Bei z.B. "0,5" Fahrrädern wird kein Fahrrad empfohlen  
    - **Gleitkomma**: Bei 0,5 Fahrrädern bleibt die Empfehlung bei der Dezimalzahl
    """)  

    # WICHTIG: Daten bei Parameteränderung neu verarbeiten
    @st.cache_data
    def process_data_with_params(min_area, max_area, min_pro_m2_val, std_pro_tag_val, 
                                tage_pro_jahr_val, arbeiter_pro_rad_val, methode_val):
        """Verarbeitet Daten mit aktuellen Parametern"""
        
        # Kopie der ursprünglichen Daten erstellen
        parks_df = base_data["parks"]["df"].copy()
        cemetery_df = base_data["cemetery"]["df"].copy()
        camping_df = base_data["camping"]["df"].copy()
        
        # Berechnungen für alle Datensätze durchführen
        def calculate_for_dataset(df):
            if df.empty or 'area_ha' not in df.columns:
                return df
            
            df["Arbeiter"] = df["area_ha"].apply(
                lambda x: berechne_arbeiter(x, min_pro_m2_val, std_pro_tag_val, tage_pro_jahr_val)
            )
            df["Marktpotenzial"] = df["Arbeiter"].apply(
                lambda a: berechne_fahrradanzahl(a, arbeiter_pro_rad_val, methode_val)
            )
            return df
        
        # Berechnungen anwenden
        parks_df = calculate_for_dataset(parks_df)
        cemetery_df = calculate_for_dataset(cemetery_df)
        camping_df = calculate_for_dataset(camping_df)
        
        # Nach Flächengröße filtern
        def filter_by_area(df, min_a, max_a):
            if df.empty or 'area_ha' not in df.columns:
                return df
            return df[(df["area_ha"] >= min_a) & (df["area_ha"] <= max_a)].copy()
        
        parks_filtered = filter_by_area(parks_df, min_area, max_area)
        cemetery_filtered = filter_by_area(cemetery_df, min_area, max_area)
        camping_filtered = filter_by_area(camping_df, min_area, max_area)
        
        return {
            "parks_filtered": parks_filtered,
            "cemetery_filtered": cemetery_filtered,
            "camping_filtered": camping_filtered,
            "parks_all": parks_df,
            "cemetery_all": cemetery_df,
            "camping_all": camping_df
        }

    # Daten mit aktuellen Parametern verarbeiten
    processed_data = process_data_with_params(
        area_range[0], area_range[1], min_pro_m2, std_pro_tag,
        tage_pro_jahr, arbeiter_pro_rad, methode
    )

    # Ergebnisse anzeigen
    st.subheader("Ergebnisse")
    
    total_locations = (len(processed_data["parks_filtered"]) + 
                      len(processed_data["cemetery_filtered"]) + 
                      len(processed_data["camping_filtered"]))
    
    st.write(f"**Gefilterte Standorte:** {total_locations}")

    if total_locations > 0:
        # Gesamtstatistiken berechnen
        gesamt_arbeiter = (processed_data["parks_filtered"]["Arbeiter"].sum() + 
                          processed_data["cemetery_filtered"]["Arbeiter"].sum() + 
                          processed_data["camping_filtered"]["Arbeiter"].sum())
        
        gesamt_fahrrad = (processed_data["parks_filtered"]["Marktpotenzial"].sum() + 
                         processed_data["cemetery_filtered"]["Marktpotenzial"].sum() + 
                         processed_data["camping_filtered"]["Marktpotenzial"].sum())

        st.markdown(f"""
        - **Gesamtanzahl Arbeiter (DE):** {gesamt_arbeiter}
        - **Gesamtanzahl Fahrräder (DE):** {gesamt_fahrrad}
        - **Flächenbereich:** {area_range[0]} - {area_range[1]} ha
        """)

        # Gefilterte Daten anzeigen
        if not processed_data["parks_filtered"].empty:
            st.subheader("Gefilterte Parks")
            st.dataframe(processed_data["parks_filtered"][['name', 'area_ha', 'Arbeiter', 'Marktpotenzial']])

        if not processed_data["cemetery_filtered"].empty:
            st.subheader("Gefilterte Friedhöfe")
            st.dataframe(processed_data["cemetery_filtered"][['name', 'area_ha', 'Arbeiter', 'Marktpotenzial']])


        if not processed_data["camping_filtered"].empty:
            st.subheader("Gefilterte Campingplätze")
            st.dataframe(processed_data["camping_filtered"][['name', 'area_ha', 'Arbeiter', 'Marktpotenzial']])


        # Karten erstellen mit gefilterten Daten
        try:
            # Erstelle neue Datenstruktur für die Kartenvisualisierung
            filtered_map_data = {
                "parks": {
                    "df": processed_data["parks_filtered"],
                    "gdf": base_data["parks"]["gdf"][
                        base_data["parks"]["gdf"].index.isin(processed_data["parks_filtered"].index)
                    ] if base_data["parks"]["gdf"] is not None else None
                },
                "cemetery": {
                    "df": processed_data["cemetery_filtered"],
                    "gdf": base_data["cemetery"]["gdf"][
                        base_data["cemetery"]["gdf"].index.isin(processed_data["cemetery_filtered"].index)
                    ] if base_data["cemetery"]["gdf"] is not None else None
                },
                "camping": {
                    "df": processed_data["camping_filtered"],
                    "gdf": base_data["camping"]["gdf"][
                        base_data["camping"]["gdf"].index.isin(processed_data["camping_filtered"].index)
                    ] if base_data["camping"]["gdf"] is not None else None
                },
                "cities": base_data["cities"],
                "federal_states": base_data["federal_states"],
                "heatmap": base_data["heatmap"],
                "camping_heatmap": base_data["camping_heatmap"]
            }
            
            viz = ParksVisualization()
            
            # Hauptkarte mit gefilterten Daten erstellen
            main_map = viz.create_main_map(filtered_map_data, area_range[0])
            
            # Tabs für Kartenanzeige
            tab1, tab2, tab3 = st.tabs(["Gesamtkarte", "Bundesländer", "Datenübersicht"])

            with tab1:
                st.subheader("Gesamtkarte Deutschlands")
                st.write(f"Zeigt alle Standorte zwischen {area_range[0]} und {area_range[1]} ha")
                st_folium(main_map, width=1200, height=900)

            with tab2:
                st.subheader("Karten nach Bundesland")
                
                # Bundesländer mit gefilterten Daten erstellen
                try:
                    bundesland_maps = viz.create_bundesland_maps(filtered_map_data, area_range[0])
                    
                    if bundesland_maps and len(bundesland_maps) > 0:
                        # Dropdown für Bundesland-Auswahl
                        available_bundeslaender = list(bundesland_maps.keys())
                        selected_bundesland = st.selectbox(
                            "Wählen Sie ein Bundesland:", 
                            available_bundeslaender,
                            key="bundesland_selector"
                        )
                        
                        if selected_bundesland:
                            # Statistiken für das gewählte Bundesland
                            bl_stats = calculate_bundesland_stats(
                                processed_data, selected_bundesland
                            )
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Standorte", bl_stats["total_locations"])
                            with col2:
                                st.metric("Arbeiter", bl_stats["total_workers"])
                            with col3:
                                st.metric("Fahrräder", bl_stats["total_bikes"])
                            with col4:
                                st.metric("Gesamtfläche", f"{bl_stats['total_area']:.1f} ha")
                            
                            # Karte anzeigen
                            st_folium(bundesland_maps[selected_bundesland], width=1200, height=600)
                            
                            # Detaillierte Aufschlüsselung für das Bundesland
                            with st.expander(f"Detaillierte Daten für {selected_bundesland}"):
                                show_bundesland_details(processed_data, selected_bundesland)
                    else:
                        st.warning("Keine Bundeslandkarten verfügbar oder keine Daten im gewählten Bereich.")
                        
                except Exception as e:
                    st.error(f"Fehler beim Erstellen der Bundeslandkarten: {e}")
                    st.write("Debug Info für Bundesländer:")
                    if 'filtered_map_data' in locals():
                        st.write("Verfügbare Daten:", list(filtered_map_data.keys()))

            with tab3:
                st.subheader("Detaillierte Datenübersicht")
                
                # Zeige alle gefilterten Datensätze
                datasets = [
                    ("Parks", processed_data["parks_filtered"]),
                    ("Friedhöfe", processed_data["cemetery_filtered"]),
                    ("Campingplätze", processed_data["camping_filtered"])
                ]
                
                for name, df in datasets:
                    if not df.empty:
                        st.subheader(f"{name} ({len(df)} Standorte)")
                        st.dataframe(df[['name', 'area_ha', 'Arbeiter', 'Marktpotenzial']])
                        
                        # Statistiken pro Kategorie
                        st.write(f"**{name} Statistiken:**")
                        st.write(f"- Gesamtarbeiter: {df['Arbeiter'].sum()}")
                        st.write(f"- Gesamtfahrräder: {df['Marktpotenzial'].sum()}")
                        st.write(f"- Durchschnittliche Fläche: {df['area_ha'].mean():.2f} ha")
                        st.write("---")
                    
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Karten: {e}")
            st.write("Debug Info:")
            st.write(f"- Parks gefiltert: {len(processed_data['parks_filtered'])}")
            st.write(f"- Cemetery gefiltert: {len(processed_data['cemetery_filtered'])}")
            st.write(f"- Camping gefiltert: {len(processed_data['camping_filtered'])}")
    else:
        st.warning("Keine Standorte im gewählten Flächenbereich gefunden!")

if __name__ == "__main__":
    main()