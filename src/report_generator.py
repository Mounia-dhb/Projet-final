import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

class AgriculturalAnalyzer:
    def __init__(self, data_manager):
        """
        Initialise l’analyseur avec le gestionnaire de données.
        """
        self.data_manager = data_manager
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

    def analyze_yield_factors(self, parcelle_id):
        """
        Analyse les facteurs influençant les rendements.
        """
        parcelle_data = self.data_manager.final_data[self.data_manager.final_data['parcelle_id'] == parcelle_id]
        yield_data = parcelle_data[['date', 'rendement_final']].dropna()
        weather_data = parcelle_data[['temperature', 'humidite', 'precipitation']].dropna()
        soil_data = parcelle_data[['ph', 'azote', 'phosphore', 'potassium']].dropna()

        correlations = self._calculate_yield_correlations(yield_data, weather_data, soil_data)
        limiting_factors = self._identify_limiting_factors(parcelle_data, correlations)
        performance_trend = self._analyze_performance_trend(parcelle_data)

        print("Analyse des facteurs influençant les rendements complétée.")
        return {
            "correlations": correlations,
            "limiting_factors": limiting_factors,
            "performance_trend": performance_trend
        }

    def _calculate_yield_correlations(self, yield_data, weather_data, soil_data):
        """
        Calcule les corrélations entre les rendements et les différents facteurs environnementaux.
        """
        combined_data = pd.concat([yield_data['rendement_final'], weather_data, soil_data], axis=1)
        correlations = combined_data.corr()
        print("Corrélations calculées avec succès.")
        return correlations

    def _identify_limiting_factors(self, parcelle_data, correlations):
        """
        Identifie les facteurs limitant le rendement.
        """
        limiting_factors = correlations['rendement_final'].sort_values(ascending=True).head(3)
        print("Facteurs limitants identifiés avec succès.")
        return limiting_factors

    def _analyze_performance_trend(self, parcelle_data):
        """
        Analyse la tendance de performance de la parcelle.
        """
        rendement_series = parcelle_data[['date', 'rendement_final']].set_index('date')['rendement_final']
        trend = np.polyfit(range(len(rendement_series)), rendement_series, 1)
        print("Tendance de performance analysée avec succès.")
        return trend

    def _detect_yield_breakpoints(self, yield_series):
        """
        Détecte les changements significatifs dans la série temporelle des rendements.
        """
        breakpoints = np.diff(yield_series).argmax()  # Simple méthode pour détecter les plus grands changements
        print("Points de rupture détectés avec succès.")
        return breakpoints

    def _analyze_yield_stability(self, yield_series):
        """
        Analyse la stabilité des rendements au fil du temps.
        """
        stability_metrics = {
            "mean_yield": np.mean(yield_series),
            "yield_variance": np.var(yield_series),
            "coefficient_of_variation": stats.variation(yield_series)
        }
        print("Analyse de stabilité complétée avec succès.")
        return stability_metrics

    def _calculate_stability_index(self, yield_series):
        """
        Calcule un index de stabilité personnalisé.
        """
        stability_index = np.mean(yield_series) / (np.std(yield_series) + 1e-6)
        print("Index de stabilité calculé avec succès.")
        return stability_index

    def generate_report(self, parcelle_id):
        """
        Génère un rapport détaillé à partir de toutes les analyses.
        """
        analysis_results = self.analyze_yield_factors(parcelle_id)
        report = f"""
        Rapport d'Analyse pour la Parcelle {parcelle_id}:

        Corrélations avec les Rendements:
        {analysis_results['correlations']}

        Facteurs Limitants:
        {analysis_results['limiting_factors']}

        Tendance de Performance:
        {analysis_results['performance_trend']}
        """
        print("Rapport généré avec succès.")
        return report


# Exemple d'utilisation
if __name__ == "__main__":
    from data_manager import AgriculturalDataManager

    # Initialisation du gestionnaire de données
    data_manager = AgriculturalDataManager()
    data_manager.load_and_clean_data()
    data_manager.prepare_features()
    data_manager.merge_data()

    # Analyse d'une parcelle spécifique
    analyzer = AgriculturalAnalyzer(data_manager)
    report = analyzer.generate_report("P001")
    print(report)
