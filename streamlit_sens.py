import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import math

# Berechnungsfunktionen
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

def erstelle_marktkarte(df, min_groesse, methode):
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

def lade_daten():
    daten_park = pd.read_csv("C:/Users/luise/python, vorkurs/12.10. vorlesung/aura/Parks_in_Städten/Visual/all/Parks_Deutschland_all.csv")
    daten_friedh = pd.read_csv("C:/Users/luise/python, vorkurs/12.10. vorlesung/aura/Parks_in_Städten/Visual/all/Friedhöfe_Deutschland_all.csv")
   
    daten_park["Typ"] = "Park"
    daten_friedh["Typ"] = "Friedhof"
    return pd.concat([daten_park, daten_friedh], ignore_index=True)

def main():
    st.set_page_config(page_title="Marktdurchdringungstool", layout="wide")
    st.title("Marktdurchdringungstool für Lastenräder")

    daten = lade_daten()

    # Seitenleiste: Parameter
    st.sidebar.header("Parameter für Marktanalyse")
    min_groesse = st.sidebar.slider("Minimale Fläche (ha)", 0, 1000, (1, 3))
    min_pro_m2 = st.sidebar.slider("Minuten pro m²", 0.5, 5.0, 1.3, 0.1)
    std_pro_tag = st.sidebar.slider("Arbeitsstunden pro Tag", 1, 10, 5)
    tage_pro_jahr = st.sidebar.slider("Arbeitstage pro Jahr", 100, 300, 220)
    arbeiter_pro_rad = st.sidebar.slider("Arbeiter pro Fahrrad", 0.5, 5.0, 2.0, 0.1)

    # Empfehlungstext
    st.markdown(f"""
    ### Empfehlung
    - Zeit pro m²: **{min_pro_m2} Minuten**
    - Arbeitstage/Jahr: **{tage_pro_jahr}**
    - Aktive Stunden/Tag: **{std_pro_tag}**
    - Arbeiter/Fahrrad: **{arbeiter_pro_rad}**

    ### Berechnung 
    
    #### Funktion berechne_arbeiter(area_ha):
    - Eingabe: Fläche in Hektar (area_ha)
    - Umrechnung in Quadratmeter: area_m2 = area_ha * 10.000
    - Zeitaufwand:Pro m² werden [1,3] Minuten benötigt → minuten = area_m2 * [1.3]
    - Umrechnung in Stunden 
    - aktive Arbeitszeit pro Tag: [5 h] → tage = stunden / 5
    - Ein Arbeiter arbeitet [220 Tage] im Jahr → arbeiter = tage / 220
    - Ausgabe: Aufgerundete Anzahl an Arbeitern, mindestens 1

    #### Funktion berechne_fahrradanzahl(arbeiter):
    - Eingabe: Anzahl der benötigten Arbeiter
    - Annahme: Ein Fahrrad lohnt sich für je [2 Arbeiter]
    - Ausgabe: [Aufgerundete] Anzahl an Fahrrädern (arbeiter / [2])
    """)

    # Auswahl Berechnungsmodus
    methode = st.radio("Berechnungsmethode für Fahrradanzahl:", ["Aufrunden", "Abrunden", "Gleitkomma"])

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
    karte = erstelle_marktkarte(gefiltert, min_groesse, methode)
    st_folium(karte, width=1200, height=800)

    # Download
    st.subheader("Bericht herunterladen")
    csv_download = gefiltert.to_csv(index=False).encode("utf-8")
    st.download_button("Bericht herunterladen (CSV)", data=csv_download, file_name="marktpotenzial_bericht.csv")



    # --- Sensitivitätsanalyse ---
    st.subheader("Sensitivitätsanalyse")

# Erzeuge Beispielwerte für jeden Parameter (um Auswirkungen zu testen)
    sens_daten = []

    parameter_range = {
    "min_pro_m2": np.linspace(0.5, 5.0, 10),
    "std_pro_tag": np.linspace(1, 10, 10),
    "tage_pro_jahr": np.linspace(100, 300, 10),
    "arbeiter_pro_rad": np.linspace(0.5, 5.0, 10),
    }

    for param, values in parameter_range.items():
        base_values = {
            "min_pro_m2": min_pro_m2,
            "std_pro_tag": std_pro_tag,
            "tage_pro_jahr": tage_pro_jahr,
            "arbeiter_pro_rad": arbeiter_pro_rad,
        }

        results = []
        for v in values:
            base_values[param] = v
            tmp_df = daten.copy()
            tmp_df["Arbeiter"] = tmp_df["area_ha"].apply(
                lambda x: berechne_arbeiter(x, base_values["min_pro_m2"], base_values["std_pro_tag"], base_values["tage_pro_jahr"])
            )
            tmp_df["Marktpotenzial"] = tmp_df["Arbeiter"].apply(
                lambda a: berechne_fahrradanzahl(a, base_values["arbeiter_pro_rad"], methode)
            )
            results.append(tmp_df["Marktpotenzial"].sum())
    
        delta = np.ptp(results)  # peak-to-peak (max - min)
        sens_daten.append({"Parameter": param, "Einfluss (Δ Räder)": delta})

    sens_df = pd.DataFrame(sens_daten).sort_values("Einfluss (Δ Räder)", ascending=False)
    st.dataframe(sens_df)

# Balkendiagramm: Einfluss pro Parameter
    fig_sens, ax_sens = plt.subplots()
    sns.barplot(x="Einfluss (Δ Räder)", y="Parameter", data=sens_df, ax=ax_sens)
    st.pyplot(fig_sens)

# --- Histogramm: Fahrräder nach Flächengrößenklasse ---
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