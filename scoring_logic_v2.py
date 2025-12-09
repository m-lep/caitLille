import pandas as pd
import numpy as np
import json
from shapely.geometry import shape
from math import radians, cos, sin, asin, sqrt

# --------------------------------------------------------------------------
# NOUVEAU SYSTÈME DE SCORING - REFONTE COMPLÈTE
# --------------------------------------------------------------------------

FICHIER_MATRICE = 'DATASET scores brut.xlsx'
NOM_FEUILLE = 'Matrice_Brute_Normalisee'

# --------------------------------------------------------------------------
# REGROUPEMENT DES CRITÈRES EN CATÉGORIES LOGIQUES
# --------------------------------------------------------------------------

# Critères regroupés de manière intelligente
CATEGORIES_CRITERES = {
    'PRIX': ['Norm_Prix'],  # PRIX DOIT PRIMER ABSOLUMENT
    'SERVICES_PROXIMITE': ['Norm_Nb_Pharmacies', 'Norm_Nb_Commerces'],
    'VIE_ANIMEE': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants'],
    'TRANSPORTS': ['Norm_Nb_Transports', 'Norm_Nb_VLille'],
    'CALME': ['Norm_Bruit', 'Norm_Surface_Verte_m2'],
    'FAMILLE': ['Norm_Nb_Ecoles', 'Norm_Nb_ParcsEnfants'],
    'SPORT': ['Norm_Nb_ComplexesSportifs'],
    'PARKING': ['Norm_Nb_Parkings']
}

# --------------------------------------------------------------------------
# NOUVELLES QUESTIONS PERTINENTES
# --------------------------------------------------------------------------

# Chaque question incrémente certains critères et en décrémente d'autres
# Format: {option: {critere: +poids ou -poids}}
LOGIQUE_QUESTIONS = {
    # Q1: Budget (ABSOLUMENT PRIORITAIRE)
    'budget': {
        'Serré (< 2000€/m²)': {
            'PRIX': 30,  # POIDS MASSIF pour le budget serré - PRIORITÉ ABSOLUE
            'SERVICES_PROXIMITE': 2,  # Un peu de services pratiques
            'TRANSPORTS': 2,  # Besoin de transports accessibles
        },
        'Modéré (2000-3000€/m²)': {
            'PRIX': 18,  # Important mais moins strict
            'SERVICES_PROXIMITE': 2,
            'VIE_ANIMEE': 1,
        },
        'Confortable (3000-4000€/m²)': {
            'PRIX': 10,  # Encore considéré
            'VIE_ANIMEE': 2,
            'SERVICES_PROXIMITE': 2,
        },
        'Aucune limite (> 4000€/m²)': {
            'VIE_ANIMEE': 3,
            'SERVICES_PROXIMITE': 2,
            'CALME': 1,
        }
    },
    
    # Q2: Ambiance recherchée
    'ambiance': {
        'Très calme, nature et verdure': {
            'CALME': 4,
            'VIE_ANIMEE': -3,  # DÉCRÉMENTE la vie animée
            'SERVICES_PROXIMITE': 1,
        },
        'Calme avec services de base': {
            'CALME': 3,
            'SERVICES_PROXIMITE': 3,
            'VIE_ANIMEE': -1,
        },
        'Dynamique et urbain': {
            'VIE_ANIMEE': 3,
            'TRANSPORTS': 2,
            'CALME': -2,  # DÉCRÉMENTE le calme
            'SERVICES_PROXIMITE': 2,
        },
        'Très animé (vie nocturne, bars)': {
            'VIE_ANIMEE': 5,
            'TRANSPORTS': 3,
            'CALME': -4,  # FORTEMENT décrémenté
        }
    },
    
    # Q3: Mode de vie
    'mode_vie': {
        'Je cuisine, j\'aime le calme': {
            'SERVICES_PROXIMITE': 3,
            'CALME': 3,
            'VIE_ANIMEE': -1,
        },
        'Équilibré (cuisine + sorties)': {
            'SERVICES_PROXIMITE': 2,
            'VIE_ANIMEE': 2,
            'TRANSPORTS': 2,
        },
        'Je sors souvent au resto/bars': {
            'VIE_ANIMEE': 4,
            'TRANSPORTS': 2,
            'SERVICES_PROXIMITE': 1,
        },
        'Vie nocturne intense': {
            'VIE_ANIMEE': 5,
            'TRANSPORTS': 3,
            'CALME': -3,
        }
    },
    
    # Q4: Statut
    'statut': {
        'Parent (avec enfants)': {
            'FAMILLE': 5,
            'CALME': 3,
            'SERVICES_PROXIMITE': 2,
            'VIE_ANIMEE': -2,
        },
        'Étudiant(e)': {
            'VIE_ANIMEE': 4,
            'TRANSPORTS': 3,
            'CALME': -2,
            'FAMILLE': -3,
        },
        'Jeune actif(ve)': {
            'VIE_ANIMEE': 3,
            'TRANSPORTS': 2,
            'SERVICES_PROXIMITE': 2,
        },
        'Senior / Retraité(e)': {
            'CALME': 4,
            'SERVICES_PROXIMITE': 3,
            'VIE_ANIMEE': -2,
            'TRANSPORTS': 1,
        }
    },
    
    # Q5: Transport
    'transport': {
        'Transports en commun uniquement': {
            'TRANSPORTS': 5,
            'SERVICES_PROXIMITE': 2,
            'PARKING': -3,  # Pas besoin de parking
        },
        'Vélo / V\'Lille': {
            'TRANSPORTS': 3,
            'SERVICES_PROXIMITE': 2,
            'CALME': 1,
            'PARKING': -2,
        },
        'Voiture personnelle': {
            'PARKING': 4,
            'SERVICES_PROXIMITE': 2,
            'TRANSPORTS': -1,
        },
        'Mix voiture + transports': {
            'PARKING': 2,
            'TRANSPORTS': 2,
            'SERVICES_PROXIMITE': 1,
        }
    },
    
    # Q6: Activité physique
    'activite': {
        'Très sportif (besoin d\'équipements)': {
            'SPORT': 4,
            'CALME': 2,
            'VIE_ANIMEE': 1,
        },
        'Sportif occasionnel': {
            'SPORT': 2,
            'CALME': 1,
        },
        'Peu sportif': {
            'SERVICES_PROXIMITE': 1,
            'VIE_ANIMEE': 1,
        },
        'Pas du tout': {
            'VIE_ANIMEE': 2,
            'SPORT': -2,
        }
    },
}

# --------------------------------------------------------------------------
# FONCTIONS DE SCORING
# --------------------------------------------------------------------------

def charger_matrice():
    """Charge la matrice de données depuis Excel"""
    try:
        df = pd.read_excel(FICHIER_MATRICE, sheet_name=NOM_FEUILLE)
        
        if 'NOM_IRIS' not in df.columns:
            print("❌ ERREUR : La colonne 'NOM_IRIS' est manquante.")
            return None
        
        if df.empty:
            print("❌ ERREUR : La feuille Excel est vide.")
            return None
        
        # Nettoyage
        cols_norm = [col for col in df.columns if col.startswith('Norm_')]
        df[cols_norm] = df[cols_norm].fillna(0.0)
        
        print(f"✅ Matrice chargée avec {df.shape[0]} lignes.")
        return df
        
    except Exception as e:
        print(f"❌ ERREUR lors du chargement : {e}")
        return None


def calculer_centroids_iris(geojson_path='iris_v2_Lille.geojson'):
    """
    Calcule les centroïdes de chaque IRIS depuis le GeoJSON
    Retourne: {CODE_IRIS: {'lon': x, 'lat': y}}
    """
    try:
        with open(geojson_path, 'r') as f:
            geojson = json.load(f)
        
        centroids = {}
        for feature in geojson['features']:
            code_iris = str(feature['properties']['code_iris'])
            geom = shape(feature['geometry'])
            centroid = geom.centroid
            centroids[code_iris] = {'lon': centroid.x, 'lat': centroid.y}
        
        return centroids
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des centroïdes: {e}")
        return {}


def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en mètres entre deux points GPS (formule haversine)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Rayon de la Terre en mètres
    return c * r


def appliquer_bonus_proximite(matrice_df, seuil_distance_m=500):
    """
    Applique des bonus de proximité aux IRIS voisins:
    - Si un IRIS a une grosse surface verte (>50000 m²), les voisins à <500m reçoivent +0.15 en Norm_Surface_Verte_m2
    - Si un IRIS a beaucoup de transports (>10), les voisins à <500m reçoivent +0.15 en Norm_Nb_Transports
    
    Args:
        matrice_df: DataFrame avec colonnes CODE_IRIS, Surface_Verte_m2, Nb_Transports, Norm_*
        seuil_distance_m: Distance en mètres pour considérer un IRIS comme voisin (défaut: 500m)
    
    Returns:
        DataFrame avec bonus de proximité appliqués
    """
    try:
        # Calculer les centroïdes
        centroids = calculer_centroids_iris()
        if not centroids:
            print("⚠️ Pas de centroïdes disponibles, bonus de proximité ignoré")
            return matrice_df
        
        # Créer une copie pour ne pas modifier l'original
        df = matrice_df.copy()
        
        # Identifier les IRIS avec grosses surfaces vertes (seuil: 50000 m²)
        iris_gros_espaces_verts = df[df['Surface_Verte_m2'] > 50000]['CODE_IRIS'].values
        
        # Identifier les IRIS avec beaucoup de transports (seuil: 10)
        iris_gros_transports = df[df['Nb_Transports'] > 10]['CODE_IRIS'].values
        
        print(f"🌳 {len(iris_gros_espaces_verts)} IRIS avec gros espaces verts détectés")
        print(f"🚇 {len(iris_gros_transports)} IRIS avec beaucoup de transports détectés")
        
        # Initialiser les colonnes de bonus
        df['Bonus_Vert_Proximite'] = 0.0
        df['Bonus_Transport_Proximite'] = 0.0
        
        # Pour chaque IRIS, vérifier la proximité avec les gros équipements
        for idx, row in df.iterrows():
            code_iris = str(row['CODE_IRIS'])
            
            if code_iris not in centroids:
                continue
            
            lon1, lat1 = centroids[code_iris]['lon'], centroids[code_iris]['lat']
            
            # Bonus espaces verts
            for code_iris_vert in iris_gros_espaces_verts:
                code_iris_vert_str = str(code_iris_vert)
                if code_iris_vert_str == code_iris:
                    continue  # Pas de bonus pour soi-même
                
                if code_iris_vert_str in centroids:
                    lon2, lat2 = centroids[code_iris_vert_str]['lon'], centroids[code_iris_vert_str]['lat']
                    distance = haversine_distance(lon1, lat1, lon2, lat2)
                    
                    if distance <= seuil_distance_m:
                        df.at[idx, 'Bonus_Vert_Proximite'] += 0.15
            
            # Bonus transports
            for code_iris_transport in iris_gros_transports:
                code_iris_transport_str = str(code_iris_transport)
                if code_iris_transport_str == code_iris:
                    continue
                
                if code_iris_transport_str in centroids:
                    lon2, lat2 = centroids[code_iris_transport_str]['lon'], centroids[code_iris_transport_str]['lat']
                    distance = haversine_distance(lon1, lat1, lon2, lat2)
                    
                    if distance <= seuil_distance_m:
                        df.at[idx, 'Bonus_Transport_Proximite'] += 0.15
        
        # Appliquer les bonus aux colonnes normalisées (plafonner à 1.0)
        df['Norm_Surface_Verte_m2'] = np.minimum(
            df['Norm_Surface_Verte_m2'] + df['Bonus_Vert_Proximite'], 
            1.0
        )
        df['Norm_Nb_Transports'] = np.minimum(
            df['Norm_Nb_Transports'] + df['Bonus_Transport_Proximite'], 
            1.0
        )
        
        nb_bonus_vert = (df['Bonus_Vert_Proximite'] > 0).sum()
        nb_bonus_transport = (df['Bonus_Transport_Proximite'] > 0).sum()
        
        print(f"✅ Bonus de proximité appliqués: {nb_bonus_vert} IRIS (espaces verts), {nb_bonus_transport} IRIS (transports)")
        
        return df
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'application des bonus de proximité: {e}")
        return matrice_df


def consolider_poids_utilisateur(reponses_dict):
    """
    Nouvelle logique: incrémente et décrémente les catégories selon les réponses.
    reponses_dict: {0: {'question_id': 'budget', 'option': 'Serré'}, ...}
    """
    # Initialiser les poids à 0 pour toutes les catégories
    poids_categories = {cat: 0 for cat in CATEGORIES_CRITERES.keys()}
    
    for question_idx, reponse_data in reponses_dict.items():
        if not isinstance(reponse_data, dict):
            continue
        
        question_id = reponse_data.get('question_id', '')
        option_choisie = reponse_data.get('option', '')
        
        if question_id not in LOGIQUE_QUESTIONS:
            continue
        
        if option_choisie not in LOGIQUE_QUESTIONS[question_id]:
            continue
        
        # Récupérer les modifications de poids pour cette option
        modifications = LOGIQUE_QUESTIONS[question_id][option_choisie]
        
        for categorie, delta_poids in modifications.items():
            if categorie in poids_categories:
                poids_categories[categorie] += delta_poids
    
    # Convertir les poids de catégories en poids de critères normalisés
    poids_criteres_finaux = {}
    
    for categorie, poids_cat in poids_categories.items():
        # Ne garder que les poids positifs (si négatif, c'est qu'on ne veut pas ce critère)
        if poids_cat > 0:
            criteres = CATEGORIES_CRITERES[categorie]
            # Distribuer le poids uniformément sur les critères de la catégorie
            poids_par_critere = poids_cat / len(criteres)
            for critere in criteres:
                poids_criteres_finaux[critere] = poids_criteres_finaux.get(critere, 0) + poids_par_critere
    
    return poids_criteres_finaux, poids_categories


def recommander_quartiers(poids_finaux_consolides, matrice_data, n_recommandations=10, avec_bonus_proximite=True):
    """
    Calcule les scores de correspondance avec FORTE PRIORITÉ AU PRIX.
    Applique les bonus de proximité pour espaces verts et transports.
    Retourne plus de recommandations pour avoir de la variété.
    
    Args:
        poids_finaux_consolides: Dictionnaire {critere: poids}
        matrice_data: DataFrame avec les données normalisées
        n_recommandations: Nombre de quartiers à recommander
        avec_bonus_proximite: Si True, applique les bonus de proximité (défaut: True)
    """
    if matrice_data is None or matrice_data.empty:
        return None
    
    if not poids_finaux_consolides:
        return None
    
    # Appliquer les bonus de proximité AVANT le scoring
    if avec_bonus_proximite:
        df_reco = appliquer_bonus_proximite(matrice_data)
    else:
        df_reco = matrice_data.copy()
    
    df_reco['Score_Correspondance_Total'] = 0.0
    
    total_poids_valides = sum(poids_finaux_consolides.values())
    
    if total_poids_valides == 0:
        return None
    
    # Calcul de la Somme Pondérée
    for col_norm, poids in poids_finaux_consolides.items():
        if col_norm in df_reco.columns and poids > 0:
            df_reco['Score_Correspondance_Total'] += df_reco[col_norm] * poids
    
    # Normalisation sur 100
    df_reco['Score_Final_100'] = (df_reco['Score_Correspondance_Total'] / total_poids_valides) * 100
    
    # AJOUT DE VARIÉTÉ : ajouter un petit facteur aléatoire (±2 points) pour diversifier
    np.random.seed(42)  # Pour reproductibilité
    df_reco['Score_Final_100'] += np.random.uniform(-2, 2, size=len(df_reco))
    
    # Regroupement et Classement
    recommendations = (
        df_reco.groupby('NOM_IRIS')
        .agg(
            Score_Max=('Score_Final_100', 'max'),
            Prix_Median_m2=('Prix_Median_m2', 'mean') if 'Prix_Median_m2' in df_reco.columns else ('Score_Final_100', 'count'),
            CODE_IRIS=('CODE_IRIS', 'first')
        )
        .sort_values(by='Score_Max', ascending=False)
        .head(n_recommandations)
        .reset_index()
    )
    
    return recommendations


def calculer_tous_scores(poids_finaux_consolides, matrice_data, avec_bonus_proximite=True):
    """
    Calcule les scores pour TOUS les quartiers (pour affichage sur la carte).
    Applique les bonus de proximité si activé.
    """
    if matrice_data is None or matrice_data.empty:
        return None
    
    if not poids_finaux_consolides:
        return None
    
    # Appliquer les bonus de proximité AVANT le scoring
    if avec_bonus_proximite:
        df_scores = appliquer_bonus_proximite(matrice_data)
    else:
        df_scores = matrice_data.copy()
    
    df_scores['Score_Correspondance_Total'] = 0.0
    
    total_poids_valides = sum(poids_finaux_consolides.values())
    
    if total_poids_valides == 0:
        return None
    
    # Calcul de la Somme Pondérée
    for col_norm, poids in poids_finaux_consolides.items():
        if col_norm in df_scores.columns and poids > 0:
            df_scores['Score_Correspondance_Total'] += df_scores[col_norm] * poids
    
    # Normalisation sur 100
    df_scores['Score_Final_100'] = (df_scores['Score_Correspondance_Total'] / total_poids_valides) * 100
    
    # Ajouter variété
    np.random.seed(42)
    df_scores['Score_Final_100'] += np.random.uniform(-2, 2, size=len(df_scores))
    
    return df_scores[['CODE_IRIS', 'NOM_IRIS', 'Score_Final_100', 'Prix_Median_m2'] + list(poids_finaux_consolides.keys())]
