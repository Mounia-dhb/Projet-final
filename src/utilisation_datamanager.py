from data_manager import AgriculturalDataManager

# Initialisation du gestionnaire de données
data_manager = AgriculturalDataManager()

# Chargement des données
data_manager.load_and_clean_data()

# Préparation des caractéristiques
features = data_manager.prepare_features()

# Analyse des patterns temporels pour une parcelle spécifique
parcelle_id = 'P001'
history, trend = data_manager.get_temporal_patterns(parcelle_id=parcelle_id)

# Calcul des métriques de risque
if features is not None:
    risk_metrics = data_manager.calculate_risk_metrics(data_manager.final_data)

# Affichage des résultats
if trend:
    print(f"Tendance de rendement : {trend['pente']:.2f} tonnes/ha/an")
    print(f"Variation moyenne : {trend['variation_moyenne'] * 100:.1f}%")
else:
    print(f"Aucune tendance calculée pour la parcelle {parcelle_id}.")
