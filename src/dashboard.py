from bokeh.layouts import column, row, gridplot
from bokeh.models import ColumnDataSource, Select, DataRange1d, Slider, HoverTool, ColorBar, LinearColorMapper
from bokeh.plotting import figure, curdoc
import pandas as pd
import numpy as np
from tornado.web import RequestHandler
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import Server
from bokeh.palettes import Viridis256

# Étendre les permissions pour autoriser les directives WebSocket
class CustomHandler(RequestHandler):
    def set_default_headers(self):
        super().set_default_headers()
        self.set_header("Content-Security-Policy", "default-src * 'unsafe-inline' 'unsafe-eval' ws:;")


class AgriculturalDashboard:
    def __init__(self, data_manager):
        """
        Initialise le tableau de bord avec le gestionnaire de données.
        """
        self.data_manager = data_manager
        self.source = ColumnDataSource(data=dict())
        self.ndvi_source = ColumnDataSource(data=dict())
        self.stress_source = ColumnDataSource(data=dict())
        self.prediction_source = ColumnDataSource(data=dict())
        self.selected_parcelle = None

        # Widgets
        self.parcelle_select = Select(title="Sélectionnez une parcelle :", options=[], value=None)

        # Initialisation des graphiques
        self.history_plot = self.create_yield_history_plot()
        self.ndvi_plot = self.create_ndvi_temporal_plot()
        self.stress_plot = self.create_stress_matrix()
        self.prediction_plot = self.create_yield_prediction_plot()

        # Initialisation des données
        self.create_data_sources()

    def create_data_sources(self):
        """
        Prépare les sources de données pour les graphiques.
        """
        # Inclure les données imputées
        self.source.data = self.data_manager.final_data[['date', 'rendement_final', 'imputed']].to_dict('list')
        self.ndvi_source.data = self.data_manager.monitoring_data.to_dict('list')
        self.stress_source.data = self.data_manager.final_data[['stress_hydrique', 'precipitation']].to_dict('list')
        self.prediction_source.data = self.data_manager.final_data[['date', 'rendement_final']].assign(
            predicted_yield=lambda df: df['rendement_final'] * 1.05  # Exemple
        ).to_dict('list')

    def create_yield_history_plot(self):
        """
        Crée un graphique pour l'historique des rendements.
        """
        p = figure(title="Historique des Rendements par Parcelle", x_axis_type="datetime", height=300)
        p.line(x='date', y='rendement_final', source=self.source, color="blue", legend_label="Rendement")
        p.scatter(x='date', y='rendement_final', source=self.source, color="red", legend_label="Points de rendement")
        p.yaxis.axis_label = "Rendement (tonnes/ha)"
        p.xaxis.axis_label = "Date"
        return p

    def create_ndvi_temporal_plot(self):
        """
        Crée un graphique pour l'évolution temporelle du NDVI.
        """
        p = figure(title="Évolution du NDVI", x_axis_type="datetime", height=300)
        p.line(x='date', y='ndvi', source=self.ndvi_source, color="green", legend_label="NDVI")
        p.yaxis.axis_label = "NDVI"
        p.xaxis.axis_label = "Date"
        return p

    def create_stress_matrix(self):
        """
        Crée une matrice de stress combinant stress hydrique et conditions météorologiques.
        """
        # Mapper de couleur pour les valeurs normalisées
        mapper = LinearColorMapper(palette=Viridis256, low=0, high=1)

        # Configuration du graphique
        p = figure(title="Matrice de Stress", x_axis_label="Stress Hydrique", y_axis_label="Précipitation", 
                x_range=(0, 1), y_range=(0, 1), height=300)

        # Ajout des rectangles pour représenter la matrice
        p.rect(x='stress_hydrique', y='precipitation', width=0.1, height=0.1, source=self.stress_source,
            fill_color={'field': 'stress_normalized', 'transform': mapper}, line_color=None)

        # Ajouter une barre de couleur pour indiquer l'échelle
        color_bar = ColorBar(color_mapper=mapper, location=(0, 0))
        p.add_layout(color_bar, 'right')

        return p


    def create_yield_prediction_plot(self):
        """
        Crée un graphique pour la prédiction des rendements.
        """
        # Configuration du graphique
        p = figure(title="Prédiction des Rendements", x_axis_type="datetime", height=300, 
                x_axis_label="Date", y_axis_label="Rendement (tonnes/ha)")

        # Ligne pour le rendement actuel
        p.line(x='date', y='rendement_final', source=self.prediction_source, color="blue", legend_label="Rendement Actuel")
        p.scatter(x='date', y='rendement_final', source=self.prediction_source, color="blue", size=5)

        # Ligne pour le rendement prédit
        p.line(x='date', y='predicted_yield', source=self.prediction_source, color="orange", legend_label="Rendement Prédit")

        # Configuration de la légende
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        return p

    def create_layout(self):
        """
        Organise tous les graphiques dans une mise en page cohérente.
        """
        self.parcelle_select.options = self.get_parcelle_options()
        self.parcelle_select.on_change('value', self.update_plots)
        controls = column(self.parcelle_select)
        layout = column(controls, gridplot([[self.history_plot, self.ndvi_plot], [self.stress_plot, self.prediction_plot]]))
        return layout

    def get_parcelle_options(self):
        """
        Retourne la liste des parcelles disponibles.
        """
        return sorted(self.data_manager.final_data['parcelle_id'].unique())

    def prepare_stress_data(self):
        """
        Prépare les données pour la matrice de stress.
        """
        try:
            stress_data = self.data_manager.final_data[['stress_hydrique', 'precipitation']].copy()
            stress_data['stress_normalized'] = stress_data['stress_hydrique'] / (stress_data['precipitation'] + 1e-6)
            stress_data['stress_normalized'] = stress_data['stress_normalized'].clip(lower=0, upper=1)  # Limite les valeurs à [0,1]

            # Conversion en dictionnaire
            self.stress_source.data = {
                'stress_hydrique': stress_data['stress_hydrique'].tolist(),
                'precipitation': stress_data['precipitation'].tolist(),
                'stress_normalized': stress_data['stress_normalized'].tolist(),
            }

            # Ajout de la ligne pour afficher les données
            print(self.stress_source.data)  # Vérifie les données préparées

            print("Les données pour la matrice de stress ont été préparées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la préparation des données de stress : {e}")



    def update_plots(self, attr, old, new):
        """
        Met à jour tous les graphiques quand une nouvelle parcelle est sélectionnée.
        """
        parcelle_id = self.parcelle_select.value
        if parcelle_id:
            parcelle_data = self.data_manager.final_data[self.data_manager.final_data['parcelle_id'] == parcelle_id]
            self.source.data = parcelle_data[['date', 'rendement_final']].to_dict('list')

            # NDVI data
            ndvi_data = self.data_manager.monitoring_data[self.data_manager.monitoring_data['parcelle_id'] == parcelle_id]
            self.ndvi_source.data = ndvi_data[['date', 'ndvi']].to_dict('list')

            # Stress matrix data
            self.prepare_stress_data()

            # Predicted yield data
            self.prediction_source.data = parcelle_data[['date', 'rendement_final']].copy().assign(
                predicted_yield=lambda df: df['rendement_final'] * 1.05  # Exemple de prédiction
            ).to_dict('list')

            print("Les graphiques ont été mis à jour pour la parcelle :", parcelle_id)



# Exemple d'utilisation
# Fonction principale pour charger le tableau de bord
def load_dashboard(doc):
    dashboard = AgriculturalDashboard(data_manager)
    layout = dashboard.create_layout()
    doc.add_root(layout)
    
# Initialisation du gestionnaire de données
from data_manager import AgriculturalDataManager

data_manager = AgriculturalDataManager()
data_manager.load_and_clean_data()
data_manager.prepare_features()
data_manager.merge_data()

# Fonction principale pour charger le tableau de bord
def load_dashboard(doc):
    """
    Charge le tableau de bord dans le document Bokeh.
    """
    dashboard = AgriculturalDashboard(data_manager)
    layout = dashboard.create_layout()

    # Important : Ajoutez l'instruction pour initialiser les sources et lier les données
    dashboard.create_data_sources()
    doc.add_root(layout)

# Création de l'application Bokeh
apps = {'/dashboard': Application(FunctionHandler(load_dashboard))}

# Lancer le serveur Bokeh
server = Server(apps, port=5007, allow_websocket_origin=["localhost:5007"])
server.start()
print("Serveur Bokeh lancé à l'adresse : http://localhost:5007/dashboard")

# Boucle pour maintenir le serveur actif
server.io_loop.add_callback(server.show, "/dashboard")
server.io_loop.start()
