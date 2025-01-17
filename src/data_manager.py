import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import numpy as np
from datetime import datetime
from statsmodels.tsa.seasonal import seasonal_decompose

os.environ['TCL_LIBRARY'] = r"C:\Users\dahbi\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
os.environ['TK_LIBRARY'] = r"C:\Users\dahbi\AppData\Local\Programs\Python\Python313\tcl\tk8.6"

class AgriculturalDataManager:
    def __init__(self):
        """
        Initialise le gestionnaire de données agricoles.
        """
        self.monitoring_data = None
        self.weather_data = None
        self.soil_data = None
        self.yield_history = None
        self.final_data = None

    def load_and_clean_data(self):
        """
        Charge et nettoie les fichiers de données fournis.
        """
        try:
            # Chemins absolus des fichiers
            monitoring_path = "C:/Master DSEF/Projet final/projet_agricole/data/monitoring_cultures.csv"
            weather_path = "C:/Master DSEF/Projet final/projet_agricole/data/meteo_detaillee.csv"
            soil_path = "C:/Master DSEF/Projet final/projet_agricole/data/sols.csv"
            yield_path = "C:/Master DSEF/Projet final/projet_agricole/data/historique_rendements.csv"

            # Chargement des données
            self.monitoring_data = pd.read_csv(monitoring_path, parse_dates=['date'])
            self.weather_data = pd.read_csv(weather_path, parse_dates=['date'])
            self.soil_data = pd.read_csv(soil_path)
            self.yield_history = pd.read_csv(yield_path, parse_dates=['date'])

            # Suppression des doublons
            self.monitoring_data.drop_duplicates(subset=['parcelle_id', 'date'], inplace=True)
            self.weather_data.drop_duplicates(subset=['date'], inplace=True)
            self.soil_data.drop_duplicates(subset=['parcelle_id'], inplace=True)
            self.yield_history.drop_duplicates(subset=['parcelle_id', 'date'], inplace=True)

            # Gestion des valeurs manquantes
            self.monitoring_data.ffill(inplace=True)
            self.weather_data.ffill(inplace=True)
            numeric_cols = self.soil_data.select_dtypes(include=[np.number]).columns
            self.soil_data[numeric_cols] = self.soil_data[numeric_cols].fillna(self.soil_data[numeric_cols].mean())
            
            # Ajout d'une colonne "imputed" pour marquer les valeurs imputées dans `rendement_final`
            self.yield_history['imputed'] = 0
            missing_before = self.yield_history['rendement_final'].isna().sum()

            # Imputation des valeurs manquantes
            # Étape 1 : Interpolation linéaire
            self.yield_history['rendement_final'] = self.yield_history['rendement_final'].interpolate(method='linear')

            # Étape 2 : Remplissage par la moyenne si des valeurs sont encore manquantes
            self.yield_history['rendement_final'] = self.yield_history['rendement_final'].fillna(
                self.yield_history['rendement_final'].mean()
            )

            # Assurer que la colonne 'imputed' est correcte
            self.yield_history['imputed'] = np.where(
                self.yield_history['rendement_final'].notna(), self.yield_history['imputed'], 1
            )
            self.yield_history['imputed'].fillna(0, inplace=True)  # Remplace les NaN par 0

            # Marquer les données imputées
            missing_after = self.yield_history['rendement_final'].isna().sum()

            print(f"Valeurs manquantes dans rendement_final avant imputation : {missing_before}")
            print(f"Valeurs manquantes dans rendement_final après imputation : {missing_after}")

            print("Toutes les données ont été chargées et nettoyées avec succès.")
            print("Yield History après ajustement :")
            print(self.yield_history[['parcelle_id', 'date', 'rendement_final', 'imputed']].head(10))
        except Exception as e:
            print(f"Erreur lors du chargement et du nettoyage des données : {e}")



    def _setup_temporal_indices(self):
        """
        Configure les indices temporels pour les séries de données.
        """
        try:
            self.monitoring_data.set_index('date', inplace=True)
            self.weather_data.set_index('date', inplace=True)
            self.yield_history.set_index('date', inplace=True)
            print("Les indices temporels ont été configurés avec succès.")
        except Exception as e:
            print(f"Erreur lors de la configuration des indices temporels : {e}")

    def prepare_features(self):
        """
        Prépare les caractéristiques dérivées nécessaires pour l'analyse ou la modélisation.
        """
        try:
            self.monitoring_data['ndvi_lai_ratio'] = self.monitoring_data['ndvi'] / (self.monitoring_data['lai'] + 1e-6)
            print("Les caractéristiques ont été préparées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la préparation des caractéristiques : {e}")

    def merge_data(self):
        """
        Fusionne toutes les sources de données en une seule table finale.
        """
        try:
            # Ajout des données imputées dans la fusion
            merged_data = self.monitoring_data.reset_index().merge(
                self.weather_data.reset_index(), on='date', how='inner'
            )
            merged_data = merged_data.merge(
                self.soil_data, on='parcelle_id', how='inner'
            )
            self.final_data = self._enrich_with_yield_history(merged_data)

            # Fusion des colonnes latitude et longitude
            self.final_data['latitude'] = self.final_data['latitude_x'].fillna(self.final_data['latitude_y'])
            self.final_data['longitude'] = self.final_data['longitude_x'].fillna(self.final_data['longitude_y'])

            print("Colonnes après ajout des coordonnées fusionnées :", self.final_data.columns)
            print(self.final_data[['latitude', 'longitude']].head())
            
            # Vérification des données imputées
            if 'imputed' in self.final_data.columns:
                self.final_data['imputed'].fillna(0, inplace=True)  # Remplir les valeurs manquantes par 0
                print(f"Données imputées intégrées :\n{self.final_data[self.final_data['imputed'] == 1].head()}")

            print("Toutes les données ont été fusionnées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la fusion des données : {e}")


    def _enrich_with_yield_history(self, data):
        """
        Enrichit les données avec les informations historiques des rendements.
        """
        try:
            enriched_data = data.merge(
                self.yield_history.reset_index(), on=['parcelle_id', 'date'], how='left'
            )
            enriched_data['rendement_estime'] = enriched_data['rendement_estime'].fillna(0)
            enriched_data['rendement_final'] = enriched_data['rendement_final'].fillna(0)
            enriched_data['progression'] = enriched_data['progression'].fillna(0)
            print("Les données ont été enrichies avec les rendements historiques.")
            return enriched_data
        except Exception as e:
            print(f"Erreur lors de l'enrichissement des données : {e}")

    def get_temporal_patterns(self, parcelle_id):
        """
        Analyse les tendances temporelles pour une parcelle donnée.
        """
        try:
            parcelle_data = self.yield_history[self.yield_history['parcelle_id'] == parcelle_id]
            if parcelle_data.empty:
                print(f"Aucune donnée disponible pour la parcelle {parcelle_id}.")
                return None, None

            numeric_cols = parcelle_data.select_dtypes(include=[np.number])
            if numeric_cols.empty:
                print(f"Données insuffisantes pour analyser les tendances pour la parcelle {parcelle_id}.")
                return None, None

            temporal_patterns = numeric_cols.groupby(parcelle_data.index.year).mean()
            if len(temporal_patterns) < 2:
                print(f"Données insuffisantes pour calculer des tendances pour la parcelle {parcelle_id}.")
                return None, None

            trends = {
                'pente': (temporal_patterns['rendement_final'].iloc[-1] - temporal_patterns['rendement_final'].iloc[0]) /
                        max((temporal_patterns.index[-1] - temporal_patterns.index[0]), 1),
                'variation_moyenne': temporal_patterns['rendement_final'].pct_change().replace([np.inf, -np.inf], np.nan).mean()
            }

            # Remplacement des NaN ou inf par 0
            trends = {key: (0 if np.isnan(value) else value) for key, value in trends.items()}

            print(f"Tendances temporelles pour la parcelle {parcelle_id} analysées avec succès.")
            return temporal_patterns, trends
        except Exception as e:
            print(f"Erreur lors de l'analyse des tendances temporelles : {e}")
            return None, None

    def analyze_yield_patterns(self, parcelle_id):
        """
        Réalise une analyse approfondie des patterns de rendement pour une parcelle donnée.
        """
        try:
            history = self.yield_history[self.yield_history['parcelle_id'] == parcelle_id].copy()
            if history.empty:
                print(f"Aucune donnée disponible pour la parcelle {parcelle_id}.")
                return None

            history.sort_values(by='date', inplace=True)
            yield_series = history['rendement_final']

            if len(yield_series.dropna()) < 2:
                print(f"Données insuffisantes pour analyser les patterns temporels pour la parcelle {parcelle_id}.")
                return None

            decomposition = seasonal_decompose(yield_series, model='additive', period=12, extrapolate_trend='freq')
            print(f"Analyse temporelle avancée pour la parcelle {parcelle_id} réalisée avec succès.")
            return decomposition
        except Exception as e:
            print(f"Erreur lors de l'analyse temporelle avancée : {e}")
            return None

    def calculate_risk_metrics(self, data):
        """
        Calcule les métriques de risque en fonction des conditions actuelles et historiques.
        """
        try:
            data['risk_metric'] = data['stress_hydrique'] * data['precipitation']
            print("Les métriques de risque ont été calculées avec succès.")
        except Exception as e:
            print(f"Erreur lors du calcul des métriques de risque : {e}")

    def plot_yield_analysis(self, decomposition, parcelle_id):
        """
        Génère des graphiques pour les composantes temporelles : tendance, saisonnalité et résidus.

        :param decomposition: Objet de décomposition des séries temporelles.
        :param parcelle_id: Identifiant de la parcelle.
        """
        try:
            if decomposition is None:
                print(f"Aucune donnée disponible pour tracer les composantes temporelles pour la parcelle {parcelle_id}.")
                return

            plt.figure(figsize=(12, 8))

            # Tendance
            plt.subplot(3, 1, 1)
            plt.plot(decomposition.trend, label='Tendance', color='blue')
            plt.title(f"Tendance de Rendement pour la parcelle {parcelle_id}")
            plt.legend()

            # Saisonnalité
            plt.subplot(3, 1, 2)
            plt.plot(decomposition.seasonal, label='Saisonnalité', color='green')
            plt.title(f"Saisonnalité de Rendement pour la parcelle {parcelle_id}")
            plt.legend()

            # Résidus
            plt.subplot(3, 1, 3)
            plt.plot(decomposition.resid, label='Résidus', color='red')
            plt.title(f"Résidus pour la parcelle {parcelle_id}")
            plt.legend()

            plt.tight_layout()
            plt.show()

            print(f"Graphiques générés avec succès pour la parcelle {parcelle_id}.")
        except Exception as e:
            print(f"Erreur lors de la génération des graphiques : {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    data_manager = AgriculturalDataManager()
    data_manager.load_and_clean_data()
    data_manager._setup_temporal_indices()
    data_manager.prepare_features()
    data_manager.merge_data()
    data_manager.calculate_risk_metrics(data_manager.final_data)

    parcelle_id = 'P001'
    temporal_patterns, trends = data_manager.get_temporal_patterns(parcelle_id)
    if trends:
        print(f"Tendance de rendement : {trends['pente']:.2f} tonnes/ha/an")
        print(f"Variation moyenne : {trends['variation_moyenne'] * 100:.1f}%")

    decomposition = data_manager.analyze_yield_patterns(parcelle_id)
    if decomposition:
        print("Analyse avancée des composantes temporelles réussie.")
        print(decomposition.trend.head())
        # Génération des graphiques
        data_manager.plot_yield_analysis(decomposition, parcelle_id)