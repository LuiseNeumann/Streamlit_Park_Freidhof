import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import math
import hashlib

# ---------------------Initialisierung Session-Werte-------------------
if "slider_min" not in st.session_state:
    st.session_state.slider_min = 1.0
    st.session_state.slider_max = 20.0

if "manual_min" not in st.session_state:
    st.session_state.manual_min = st.session_state.slider_min
    st.session_state.manual_max = st.session_state.slider_max

# Slider Änderung → Update Number Input
def update_manual_from_slider():
    st.session_state.manual_min = st.session_state.slider_min
    st.session_state.manual_max = st.session_state.slider_max

# Number Input Änderung → Update Slider
def update_slider_from_manual():
    st.session_state.slider_min = st.session_state.manual_min
    st.session_state.slider_max = st.session_state.manual_max

# ------------------------Berechnungsfunktionen----------------------
def berechne_arbeiter(area_ha, min_pro_m2, std_pro_tag, tage_pro_jahr):
    area_m2 = area_ha * 10000
    minuten = area_m2 * min_pro_m2
    stunden = minuten / 60
    tage = stunden / std_pro_tag
    arbeiter = tage / tage_pro_jahr
    return max(1, math.ceil(arbeiter)) if area_ha > 0 else 0

def berechne_fahrradanzahl(arbeiter, arbeiter_pro_rad, methode):
    if methode == "Aufrunden":
        return math.ceil(arbeiter / arbeiter_pro_rad)
    elif methode == "Abrunden":
        return math.floor(arbeiter / arbeiter_pro_rad)
    elif methode == "Gleitkomma":
        return round(arbeiter / arbeiter_pro_rad, 2)
    return 0

@st.cache_data
def erstelle_marktkarte_cached(df_hash, df_json, min_groesse, methode):
    df = pd.read_json(df_json)
    karte = folium.Map(location=[51.1657, 10.4515], zoom_start=6)

    for _, row in df.iterrows():
        popup_text = f"""
        {row['name']} ({row['city']})<br>
        Fläche: {row['area_ha']} ha<br>
        Arbeiter: {row['Arbeiter']}<br>
        Marktpotenzial: {row['Marktpotenzial']} Räder<br>
        """
        farbe = "green" if row["Marktpotenzial"] > 0 else "red"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup_text,
            icon=folium.Icon(color=farbe)
        ).add_to(karte)
    return karte

def create_data_hash(df, min_groesse, methode, min_pro_m2, std_pro_tag, tage_pro_jahr, arbeiter_pro_rad):
    """Erstellt einen Hash der relevanten Parameter für Cache-Invalidierung"""
    hash_string = f"{len(df)}_{min_groesse}_{methode}_{min_pro_m2}_{std_pro_tag}_{tage_pro_jahr}_{arbeiter_pro_rad}"
    return hashlib.md5(hash_string.encode()).hexdigest()

@st.cache_data
def lade_daten():
    daten_park = pd.read_csv("Parks_Deutschland_all.csv")     
    daten_friedh = pd.read_csv("Friedhöfe_Deutschland_all.csv")    #CStreamlit-UI\Friedhöfe_Deutschland_all.csv
   
    daten_park["Typ"] = "Park"
    daten_friedh["Typ"] = "Friedhof"
    return pd.concat([daten_park, daten_friedh], ignore_index=True)

#-----------------------UI---------------------------------------------

def main():
    st.set_page_config(page_title="Marktdurchdringungstool", layout="wide")
    st.title("Marktdurchdringungstool für Lastenräder")

    daten = lade_daten()

    # Seitenleiste: Parameter
    st.sidebar.header("Parameter für Marktanalyse")

    st.sidebar.markdown("### Minimale Flächengröße (ha)")

    st.sidebar.slider("Flächenbereich wählen (Slider)", min_value=0.0, max_value=1000.0, value=(st.session_state.slider_min, st.session_state.slider_max), step=0.1,key="slider_range",on_change=update_manual_from_slider)

    # Eingabefelder mit Callback
    st.sidebar.markdown("**Oder exakte Werte eingeben:**")
    st.sidebar.number_input("Minimale Fläche (ha)", min_value=0.0, max_value=1000.0, step=0.1,key="manual_min",on_change=update_slider_from_manual)
    st.sidebar.number_input("Maximale Fläche (ha)", min_value=0.0, max_value=1000.0, step=0.1,key="manual_max",on_change=update_slider_from_manual)

    min_groesse = (st.session_state.slider_min, st.session_state.slider_max)


    min_pro_m2 = st.sidebar.slider("Arbeistzeit in Minuten pro m²", 0.5, 5.0, 1.3, 0.1)
    std_pro_tag = st.sidebar.slider("aktive Arbeitsstunden pro Tag (abzüglich Pausen, Anfahrt etc.) ", 1, 10, 5)
    tage_pro_jahr = st.sidebar.slider("Arbeitstage pro Jahr pro Person (abzüglich Feiertage, Urlaub)", 100, 300, 220)
    arbeiter_pro_rad = st.sidebar.slider("Anzahl Arbeiter pro Fahrrad", 0.5, 5.0, 2.0, 0.1)

    # Empfehlungstext
    st.markdown(f"""
    ### Empfehlung
    - Arbeitszeit pro m²: **{min_pro_m2} Minuten** 
    - Arbeitstage pro Person im Jahr: **{tage_pro_jahr}**
    - Aktive Arbeitszeit in Stunden/Tag: **{std_pro_tag}**
    - Fahrrad/Arbeiter (Anzahl Personen für ein Rad): **{arbeiter_pro_rad}** 
    - Quellen: [VKU-Publikationen](https://www.vku.de/fileadmin/user_upload/Verbandsseite/Publikationen/2019/181204_VKU_Betriebsdaten_BBH_2018_gesamt_RZ-WEB_einzel.pdf), [VKU-Publikationen 21](https://cloud.ovgu.de/apps/files/files/72477936?dir=/Marktanalyse/M%C3%A4rkte/Stadtreinigung/Daten&openfile=true)

    ### Berechnung-Erklärung 
    
    #### Funktion berechne_arbeiter(area_ha):
    - Eingabe: Fläche in Hektar (area_ha)
    - Umrechnung in Quadratmeter: area_m2 = area_ha * 10.000
    - Zeitaufwand: Pro m² werden [1,3] Minuten benötigt → Minuten = area_m2 * [1.3]
    - Umrechnung in Stunden 
    - aktive Arbeitszeit pro Tag: [5 h] → Tage = Stunden / 5
    - ein Arbeiter arbeitet [220 Tage] im Jahr → Arbeiter = Tage / 220
    - Ausgabe: Aufgerundete Anzahl an Arbeitern, mindestens 1

    #### Funktion berechne_fahrradanzahl(Arbeiter):
    - Eingabe: Anzahl der benötigten Arbeiter
    - Annahme: Ein Fahrrad lohnt sich für je [2 Arbeiter]
    - Ausgabe: [Aufgerundete] Anzahl an Fahrrädern (Arbeiter / [2])
    """)

    # Auswahl Berechnungsmodus
    #methode = st.radio("Berechnungsmethode für Fahrradanzahl:", ["Aufrunden", "Abrunden", "Gleitkomma"])
    st.markdown("**Berechnungsmethode für Fahrradanzahl:**")
    methode = st.radio(
        label="",
        options=["Aufrunden", "Abrunden", "Gleitkomma"],
        key="methode_radio",
        label_visibility="collapsed"
    )

    st.markdown(f"""
                ### Erläuterung 
                - Aufrunden: bei z.B."0,5" Fahrrädern wird ein Fahrrad empfohlen (Risiko: zu hohes Vorhersagepotenzial)
                - Abrunden: bei z.B."0,5" Fahrrädern wird kein Fahrrad empfohlen (Risiko: mögliche Potenziale z.b bei ,8 gehen verloren)
                - Gleitkomma: bei 0,5 Fahrrädern bleibt die Empfehlung bei der konkreten Dezimalzahl 
              """)  

    # Berechnungen
    daten["Arbeiter"] = daten["area_ha"].apply(
        lambda x: berechne_arbeiter(x, min_pro_m2, std_pro_tag, tage_pro_jahr)
    )
    daten["Marktpotenzial"] = daten["Arbeiter"].apply(
        lambda a: berechne_fahrradanzahl(a, arbeiter_pro_rad, methode)
    )

    #gefiltert = daten[daten["area_ha"] >= min_groesse]
    gefiltert = daten[
    (daten["area_ha"] >= min_groesse[0]) & 
    (daten["area_ha"] <= min_groesse[1])
    ]


    # Anzeige: Tabelle und Summen
    st.subheader("Ergebnisse")
    st.write(f"**Gefilterte Standorte:** {len(gefiltert)}")

    gesamt_arbeiter = gefiltert["Arbeiter"].sum()
    gesamt_fahrrad = gefiltert["Marktpotenzial"].sum()

    st.markdown(f"""
    - **Gesamtanzahl Arbeiter (DE):** {gesamt_arbeiter}
    - **Gesamtanzahl Fahrräder (DE):** {gesamt_fahrrad}
    """)

    st.dataframe(gefiltert)

    # Karte

    data_hash = create_data_hash(gefiltert, min_groesse, methode, min_pro_m2, std_pro_tag, tage_pro_jahr, arbeiter_pro_rad)

    #karte = erstelle_marktkarte(gefiltert, min_groesse, methode)
    karte = erstelle_marktkarte_cached(
        data_hash, 
        gefiltert.to_json(), 
        min_groesse, 
        methode
    )

    # Speichere den Map State, um Zoom/Pan zu erhalten
    if 'map_data' not in st.session_state:
        st.session_state.map_data = None

    map_data = st_folium(karte, width=1200, height=800)
    # Speichere Map State für nächsten Reload
    st.session_state.map_data = map_data


    # Download
    st.subheader("Bericht herunterladen")
    csv_download = gefiltert.to_csv(index=False).encode("utf-8")
    st.download_button("Bericht herunterladen (CSV)", data=csv_download, file_name="marktpotenzial_bericht.csv")


# -------------------- Histogramm: Fahrräder nach Flächengrößenklasse -------------------------------------------
    st.subheader("Histogramm: Verteilung der Fahrräder nach Flächengröße (alle Rundungsmodi)")

# Neue Bin-Labels in 10er Schritten
    bins = list(range(0, int(daten["area_ha"].max()) + 10, 10))
    labels = [f"{b}-{b+10}" for b in bins[:-1]]

# Funktion zum Histogramm-Datensatz pro Methode
    def histo_daten(df, methode_label):
        tmp = df.copy()
        tmp["Arbeiter"] = tmp["area_ha"].apply(
            lambda x: berechne_arbeiter(x, min_pro_m2, std_pro_tag, tage_pro_jahr)
        )
        tmp["Marktpotenzial"] = tmp["Arbeiter"].apply(
            lambda a: berechne_fahrradanzahl(a, arbeiter_pro_rad, methode_label)
        )
        tmp["Flächenklasse"] = pd.cut(tmp["area_ha"], bins=bins, labels=labels, right=False)
        grouped = tmp.groupby("Flächenklasse")["Marktpotenzial"].sum().reset_index()
        grouped["Methode"] = methode_label
        return grouped

# Daten für alle Methoden erzeugen
    daten_auf = histo_daten(gefiltert, "Aufrunden")
    daten_ab = histo_daten(gefiltert, "Abrunden")
    daten_gl = histo_daten(gefiltert, "Gleitkomma")

# Zusammenführen
    hist_all = pd.concat([daten_auf, daten_ab, daten_gl], ignore_index=True)

# Plotten
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x="Flächenklasse", y="Marktpotenzial", hue="Methode", data=hist_all, ax=ax)

# Achsenticks ausdünnen: alle 50 ha beschriften
    xticks = ax.get_xticks()
    xticklabels = [label.get_text() for label in ax.get_xticklabels()]
    for i, label in enumerate(ax.get_xticklabels()):
        if i % 5 != 0:  # nur jeden 5. anzeigen (entspricht 50 ha)
            label.set_visible(False)

    ax.set_xlabel("Flächenklasse (ha)")
    ax.set_ylabel("Fahrräder")
    ax.set_title("Fahrradverteilung pro Flächenklasse nach Rundungsmethode")
    st.pyplot(fig)

    
if __name__ == "__main__":
    main()

