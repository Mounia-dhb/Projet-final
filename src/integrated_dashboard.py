import streamlit as st
import folium
from folium import plugins
from branca.colormap import LinearColormap
from streamlit_folium import st_folium


class AgriculturalMap:
    def __init__(self, data_manager):
        """
        Initialise la carte avec le gestionnaire de données.
        """
        self.data_manager = data_manager
        self.map = None
        self.yield_colormap = LinearColormap(
            colors=['red', 'yellow', 'green'],
            vmin=0,
            vmax=12  # Rendement maximum en tonnes/ha
        )

    def create_base_map(self):
        try:
            # Vérifiez si les colonnes de coordonnées existent et ne sont pas vides
            if 'latitude_x' not in self.data_manager.final_data.columns or \
            'longitude_x' not in self.data_manager.final_data.columns or \
            self.data_manager.final_data.empty:
                print("Erreur : Les colonnes nécessaires (latitude_x, longitude_x) sont manquantes ou les données sont vides.")
                return

            center_lat = self.data_manager.final_data['latitude_x'].mean()
            center_lon = self.data_manager.final_data['longitude_x'].mean()

            # Initialiser la carte
            self.map = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            print("Carte de base créée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création de la carte : {e}")



    def add_yield_history_layer(self):
        """
        Ajoute une couche visualisant l’historique des rendements.
        """
        try:
            if self.data_manager.final_data.empty:
                print("Erreur : final_data est vide, impossible d'ajouter la couche historique.")
                return

            for _, row in self.data_manager.final_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude_x'], row['longitude_x']],
                    radius=8,
                    color=self.yield_colormap(row['rendement_final']),
                    fill=True,
                    fill_opacity=0.6,
                    popup=f"Parcelle: {row['parcelle_id']}<br>Rendement: {row['rendement_final']} tonnes/ha"
                ).add_to(self.map)
            print("Couche historique des rendements ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de la couche historique : {e}")

    def add_current_ndvi_layer(self):
        """
        Ajoute une couche de la situation NDVI actuelle avec des pop-ups contenant plus d'informations.
        """
        try:
            for _, row in self.data_manager.final_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude_x'], row['longitude_x']],
                    radius=6,
                    color='green',
                    fill=True,
                    fill_color='orange',
                    fill_opacity=0.7,
                    popup=(f"<b>Parcelle:</b> {row['parcelle_id']}<br>"
                           f"<b>NDVI:</b> {row['ndvi']:.2f}<br>"
                           f"<b>Culture:</b> {row['culture_x']}<br>"
                           f"<b>Stress hydrique:</b> {row['stress_hydrique']:.2f}<br>"
                           f"<b>Précipitations:</b> {row['precipitation']:.2f}<br>"
                           f"<b>Rendement estimé:</b> {row['rendement_estime']:.2f} tonnes/ha")
                ).add_to(self.map)
            print("Couche NDVI actuelle ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de la couche NDVI : {e}")

    def add_risk_heatmap(self):
        """
        Ajoute une carte de chaleur des zones à risque.
        """
        try:
            risk_data = self.data_manager.final_data[['latitude_x', 'longitude_x', 'risk_metric']].dropna()
            heat_data = [[row['latitude_x'], row['longitude_x'], row['risk_metric']] for _, row in risk_data.iterrows()]
            plugins.HeatMap(heat_data).add_to(self.map)
            print("Carte de chaleur des risques ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de la carte de chaleur : {e}")

    def save_map(self, output_path):
        """
        Sauvegarde la carte dans un fichier HTML.
        """
        try:
            self.map.save(output_path)
            print(f"Carte sauvegardée avec succès dans {output_path}.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la carte : {e}")

    def get_map(self):
        """
        Retourne la carte Folium.
        """
        return self.map


def create_streamlit_dashboard(data_manager):
    """
    Crée une interface Streamlit intégrant toutes les visualisations.
    """
    st.set_page_config(layout="wide")
    st.title("Tableau de Bord Agricole Intégré")

    # Initialiser la carte agricole
    agricultural_map = AgriculturalMap(data_manager)
    agricultural_map.create_base_map()
    agricultural_map.add_yield_history_layer()
    agricultural_map.add_current_ndvi_layer()
    agricultural_map.add_risk_heatmap()

    # Afficher la carte Folium dans Streamlit
    st.write("### Carte Interactive (Folium)")
    if agricultural_map.get_map() is not None:
        st_folium(agricultural_map.get_map(), width=700, height=500)
    else:
        st.error("La carte n'a pas pu être générée en raison d'un problème de données.")


if __name__ == "__main__":
    from data_manager import AgriculturalDataManager

    # Charger les données
    data_manager = AgriculturalDataManager()
    data_manager.load_and_clean_data()

    # Créer le tableau de bord Streamlit
    create_streamlit_dashboard(data_manager)
