import folium
from folium import plugins
from branca.colormap import LinearColormap

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
        """
        Crée la carte de base avec les couches appropriées.
        """
        try:
            # Utilisation des colonnes correctes pour les coordonnées
            center_lat = self.data_manager.final_data['latitude_x'].mean()
            center_lon = self.data_manager.final_data['longitude_x'].mean()
            print("Colonnes disponibles dans final_data :", self.data_manager.final_data.columns)
            print(self.data_manager.final_data.head())

            # Initialiser la carte centrée sur les parcelles
            self.map = folium.Map(location=[center_lat, center_lon], zoom_start=12)

            print("Carte de base créée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création de la carte de base : {e}")


    def add_yield_history_layer(self):
        """
        Ajoute une couche visualisant l’historique des rendements.
        """
        for _, row in self.data_manager.final_data.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                color=self.yield_colormap(row['rendement_final']),
                fill=True,
                fill_opacity=0.6,
                popup=f"Parcelle: {row['parcelle_id']}<br>Rendement: {row['rendement_final']} tonnes/ha"
            ).add_to(self.map)
            
        print("Couche de l'historique des rendements ajoutée avec succès.")
        
    def add_current_ndvi_layer(self):
        """
        Ajoute une couche de la situation NDVI actuelle avec des pop-ups contenant plus d'informations.
        """
        for _, row in self.data_manager.final_data.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color='green',
                fill=True,
                fill_color='orange',
                fill_opacity=0.7,
                popup=(
                    f"<b>Parcelle:</b> {row['parcelle_id']}<br>"
                    f"<b>NDVI:</b> {row['ndvi']:.2f}<br>"
                    f"<b>Culture:</b> {row['culture_x']}<br>"
                    f"<b>Stress hydrique:</b> {row['stress_hydrique']:.2f}<br>"
                    f"<b>Précipitations:</b> {row['precipitation']:.2f}<br>"
                    f"<b>Rendement estimé:</b> {row['rendement_estime']:.2f} tonnes/ha"
                )
            ).add_to(self.map)
        print("Couche NDVI actuelle ajoutée avec succès.")


    def calculate_risk_metrics(self, data):
        """
        Calcule les métriques de risque en fonction des conditions actuelles et historiques.
        """
        try:
            # Exemple simple : multiplier le stress hydrique et la précipitation
            data['risk_metric'] = data['stress_hydrique'] * data['precipitation']
            print("Les métriques de risque ont été calculées avec succès.")
        except Exception as e:
            print(f"Erreur lors du calcul des métriques de risque : {e}")
        data_manager.calculate_risk_metrics(data_manager.final_data)
        print(data_manager.final_data[['latitude', 'longitude', 'risk_metric']].head())  # Vérification


    def add_risk_heatmap(self):
        """
        Ajoute une carte de chaleur des zones à risque.
        """
        risk_data = self.data_manager.final_data[['latitude', 'longitude', 'risk_metric']].dropna()
        heat_data = [[row['latitude'], row['longitude'], row['risk_metric']] for _, row in risk_data.iterrows()]
        plugins.HeatMap(heat_data).add_to(self.map)
        print("Carte de chaleur des risques ajoutée avec succès.")

    def _calculate_yield_trend(self, history):
        """
        Calcule la tendance des rendements pour une parcelle.
        """
        trend = history['rendement_final'].mean() if not history.empty else 0
        print(f"Tendance des rendements calculée: {trend}")
        return trend

    def _create_yield_popup(self, history, mean_yield, trend):
        """
        Crée le contenu HTML du popup pour l’historique des rendements.
        """
        html_content = f"""
        <b>Historique des rendements:</b><br>
        Moyenne: {mean_yield:.2f} tonnes/ha<br>
        Tendance: {trend:.2f} tonnes/ha/an
        """
        print("Popup HTML pour les rendements créé avec succès.")
        return html_content

    def _format_recent_crops(self, history):
        """
        Formate la liste des cultures récentes pour le popup.
        """
        recent_crops = history['crop_name'].unique()
        formatted_crops = ', '.join(recent_crops)
        print(f"Liste des cultures récentes: {formatted_crops}")
        return formatted_crops

    def _create_ndvi_popup(self, row):
        """
        Crée le contenu HTML du popup pour les données NDVI actuelles.
        """
        html_content = f"""
        <b>NDVI Actuel:</b><br>
        NDVI: {row['ndvi']:.2f}<br>
        Culture: {row['crop_name']}
        """
        print("Popup NDVI créé avec succès.")
        return html_content

    def save_map(self, output_path):
        """
        Sauvegarde la carte dans un fichier HTML.
        """
        self.map.save(output_path)
        print(f"Carte sauvegardée avec succès dans {output_path}.")


# Exemple d'utilisation
if __name__ == "__main__":
    from data_manager import AgriculturalDataManager

    # Initialisation du gestionnaire de données
    data_manager = AgriculturalDataManager()
    data_manager.load_and_clean_data()
    data_manager.prepare_features()
    data_manager.merge_data()

    # Calcul des métriques de risque
    data_manager.calculate_risk_metrics(data_manager.final_data)

    # Vérification de la colonne 'risk_metric'
    print("Vérification des données après ajout de 'risk_metric' :")
    print(data_manager.final_data[['latitude', 'longitude', 'risk_metric']].head())


    # Initialisation de la carte agricole
    from map_visualization import AgriculturalMap
    
    agricultural_map = AgriculturalMap(data_manager)
    agricultural_map.create_base_map()
    agricultural_map.add_yield_history_layer()
    agricultural_map.add_current_ndvi_layer()
    agricultural_map.add_risk_heatmap()

    # Sauvegarder la carte
    output_path = "map_parcelles.html"
    agricultural_map.save_map(output_path)
