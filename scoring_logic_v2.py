import pandas as pd
import numpy as np

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
        df = pd.read_excel(FICHIER_MATRICE, sheet_name=NOM_FEUILLE, engine='openpyxl')
        
        if 'NOM_IRIS' not in df.columns:
            print("❌ ERREUR : La colonne 'NOM_IRIS' est manquante.")
            return None
        
        if df.empty:
            print("❌ ERREUR : La feuille Excel est vide.")
            return None
        
        # Fix encoding si nécessaire (double-encodage UTF-8)
        def fix_encoding(text):
            if not isinstance(text, str):
                return text
            try:
                # Si le texte contient des caractères mal encodés, corriger
                if 'Ã' in text:
                    return text.encode('latin1').decode('utf-8')
                return text
            except:
                return text
        
        df['NOM_IRIS'] = df['NOM_IRIS'].apply(fix_encoding)
        
        # Nettoyage
        cols_norm = [col for col in df.columns if col.startswith('Norm_')]
        df[cols_norm] = df[cols_norm].fillna(0.0)
        
        print(f"✅ Matrice chargée avec {df.shape[0]} lignes.")
        return df
        
    except Exception as e:
        print(f"❌ ERREUR lors du chargement : {e}")
        return None


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


def recommander_quartiers(poids_finaux_consolides, matrice_data, n_recommandations=10):
    """
    Calcule les scores de correspondance avec FORTE PRIORITÉ AU PRIX.
    Retourne plus de recommandations pour avoir de la variété.
    """
    if matrice_data is None or matrice_data.empty:
        return None
    
    if not poids_finaux_consolides:
        return None
    
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


def calculer_tous_scores(poids_finaux_consolides, matrice_data):
    """
    Calcule les scores pour TOUS les quartiers (pour affichage sur la carte).
    """
    if matrice_data is None or matrice_data.empty:
        return None
    
    if not poids_finaux_consolides:
        return None
    
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
