import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# --- I. CONFIGURATION GLOBALE ---
# --------------------------------------------------------------------------

FICHIER_MATRICE = 'DATASET scores brut.xlsx'
NOM_FEUILLE = 'Matrice_Brute_Normalisee'

# 1. Tous les critères normalisés de votre matrice Excel
TOUS_LES_CRITERES_NORMALISES = [
    'Norm_Bruit', 'Norm_Prix', 'Norm_Surface_Verte_m2', 'Norm_Nb_Pharmacies',
    'Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports',
    'Norm_Nb_VLille', 'Norm_Nb_ParcsEnfants', 'Norm_Nb_ComplexesSportifs',
    'Norm_Nb_Ecoles', 'Norm_Nb_Bars', 'Norm_Nb_Parkings'
]

# 2. Les 4 boutons représentent le niveau d'intérêt (1 à 4)
# 😤 (bouton 1) = Pas intéressé (poids 1)
# 😕 (bouton 2) = Moyen intéressé (poids 2)
# 😊 (bouton 3) = Intéressé (poids 3)
# 🤩 (bouton 4) = Très intéressé (poids 4)
# Le poids est déterminé par la position du bouton cliqué, pas par le texte affiché

# 3. Logique de Scoring avec pondérations diversifiées pour plus de variété
LOGIQUE_SCORING = {
    # Q1 : Ambiance - Ajout de critères secondaires pour diversifier
    'Paisible & proche de la nature': ['Norm_Surface_Verte_m2', 'Norm_Bruit', 'Norm_Nb_ParcsEnfants', 'Norm_Nb_ComplexesSportifs'],
    'Calme mais avec un peu de vie': ['Norm_Bruit', 'Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Nb_Pharmacies'],
    'Urbain & dynamique': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Nb_Bars', 'Norm_Nb_Transports', 'Norm_Nb_VLille'],
    'Très animé (bars, sorties, nightlife)': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports', 'Norm_Nb_VLille'],

    # Q2 : Déplacement - Enrichissement des critères
    'Transports en commun': ['Norm_Nb_Transports', 'Norm_Nb_VLille', 'Norm_Nb_Commerces'],
    'Vélo / V\'Lille': ['Norm_Nb_VLille', 'Norm_Nb_Transports', 'Norm_Nb_ComplexesSportifs'],
    'Voiture': ['Norm_Nb_Parkings', 'Norm_Nb_Commerces'],
    'À pied': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Nb_Pharmacies'],

    # Q3 : Bruit - Diversification
    'Très sensible': ['Norm_Bruit', 'Norm_Surface_Verte_m2'],
    'Un peu sensible': ['Norm_Bruit', 'Norm_Nb_ParcsEnfants'],
    'Ça m\'est égal': ['Norm_Nb_Commerces'],
    'J\'aime quand ça bouge': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants'],

    # Q4 : Espaces Verts - Critères complémentaires
    'Pas important': ['Norm_Nb_Transports'],
    'Un peu important': ['Norm_Surface_Verte_m2', 'Norm_Nb_ParcsEnfants'],
    'Très important': ['Norm_Surface_Verte_m2', 'Norm_Nb_ParcsEnfants', 'Norm_Nb_ComplexesSportifs'],
    'Essentiel dans mon quotidien': ['Norm_Surface_Verte_m2', 'Norm_Bruit', 'Norm_Nb_ParcsEnfants', 'Norm_Nb_ComplexesSportifs'],

    # Q5 : Budget Logement - Ajout critères secondaires
    'Serré': ['Norm_Prix', 'Norm_Nb_Transports'],
    'Modéré': ['Norm_Prix', 'Norm_Nb_Commerces'],
    'Confortable': ['Norm_Prix', 'Norm_Nb_Restaurants'],
    'Flexible': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants'],

    # Q6 : Repas - Enrichissement
    'Je cuisine souvent': ['Norm_Nb_Commerces', 'Norm_Nb_Pharmacies'],
    'Je cuisine de temps en temps': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants'],
    'Je cuisine rarement': ['Norm_Nb_Restaurants', 'Norm_Nb_Commerces'],
    'Je mange beaucoup dehors': ['Norm_Nb_Restaurants', 'Norm_Nb_Bars', 'Norm_Nb_Transports'],

    # Q7 : Services - Plus de diversité
    'Pharmacie': ['Norm_Nb_Pharmacies', 'Norm_Nb_Commerces'],
    'Commerces / supermarchés': ['Norm_Nb_Commerces', 'Norm_Nb_Transports'],
    'Restaurants / cafés': ['Norm_Nb_Restaurants', 'Norm_Nb_Bars', 'Norm_Nb_Transports'],
    'Pas particulièrement': ['Norm_Nb_VLille'],

    # Q8 : Enfants - Critères étendus
    'Oui': ['Norm_Nb_Ecoles', 'Norm_Nb_ParcsEnfants', 'Norm_Surface_Verte_m2', 'Norm_Nb_ComplexesSportifs', 'Norm_Bruit'],
    'Pas encore mais bientôt': ['Norm_Nb_Ecoles', 'Norm_Nb_ParcsEnfants', 'Norm_Surface_Verte_m2'],
    'Non': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants'],
    'Jamais': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports'],

    # Q9 : Sécurité / Tranquillité - Plus de nuances
    'Très important': ['Norm_Bruit', 'Norm_Nb_ParcsEnfants', 'Norm_Surface_Verte_m2'],
    'Assez important': ['Norm_Bruit', 'Norm_Nb_ParcsEnfants'],
    'Peu important': ['Norm_Nb_Bars'],
    'Pas vraiment': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants'],

    # Q10 : Rythme de vie - Diversification accrue
    'Plutôt tranquille': ['Norm_Bruit', 'Norm_Surface_Verte_m2', 'Norm_Nb_ParcsEnfants'],
    'Relax & chill': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Surface_Verte_m2'],
    'Dynamique': ['Norm_Nb_Restaurants', 'Norm_Nb_Commerces', 'Norm_Nb_Transports', 'Norm_Nb_VLille'],
    'Très actif / je sors souvent': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports', 'Norm_Nb_VLille'],
}


# --------------------------------------------------------------------------
# --- II. CHARGEMENT SÉCURISÉ DES DONNÉES ---
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


# --------------------------------------------------------------------------
# --- III. FONCTIONS DE SCORING ---
# --------------------------------------------------------------------------

def consolider_poids_utilisateur(reponses_dict):
    """
    Traduit les réponses utilisateur en poids pour chaque critère.
    reponses_dict: {0: {'option': 'Paisible & proche de la nature', 'poids': 1}, ...}
    Le poids (1-4) représente le niveau d'intérêt de l'utilisateur.
    """
    poids_finaux = {col: 0 for col in TOUS_LES_CRITERES_NORMALISES}
    
    for question_idx, reponse_data in reponses_dict.items():
        # Extraire l'option et le niveau d'intérêt (poids du bouton)
        if isinstance(reponse_data, dict):
            option_choisie = reponse_data.get('option', '')
            niveau_interet = reponse_data.get('poids', 0)  # 1=😐, 2=🙂, 3=😊, 4=🤩
        else:
            continue
        
        if niveau_interet == 0:
            continue
        
        # Déterminer si c'est une question budget
        is_budget = 'Serré' in option_choisie or 'Modéré' in option_choisie or 'Confortable' in option_choisie
        
        # Récupérer les critères à renforcer pour cette option
        if option_choisie and option_choisie in LOGIQUE_SCORING:
            criteres_renforces = LOGIQUE_SCORING[option_choisie]
            
            for idx, critere in enumerate(criteres_renforces):
                if critere in poids_finaux:
                    # Pour le budget, SEUL le critère Norm_Prix reçoit le boost ×3
                    if is_budget and critere == 'Norm_Prix':
                        poids_finaux[critere] += niveau_interet * 3
                    # Les autres critères reçoivent le poids normal
                    else:
                        poids_finaux[critere] += niveau_interet
        
        # Cas spécial "Flexible" : pas de contrainte budget
        if 'Flexible' in option_choisie:
            # Remettre Norm_Prix à 0 s'il avait été ajouté
            if 'Norm_Prix' in poids_finaux:
                poids_finaux['Norm_Prix'] = 0
    
    return poids_finaux


def recommander_quartiers(poids_finaux_consolides, matrice_data, n_recommandations=5):
    """
    Calcule les scores de correspondance et retourne les meilleurs quartiers.
    """
    if matrice_data is None or matrice_data.empty:
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
    
    # Regroupement et Classement
    recommendations = (
        df_reco.groupby('NOM_IRIS')
        .agg(
            Score_Max=('Score_Final_100', 'max'),
            Prix_Median_m2=('Prix_Median_m2', 'mean') if 'Prix_Median_m2' in df_reco.columns else ('Score_Final_100', 'count'),
            IRIS_Meilleur=('CODE_IRIS', lambda x: df_reco.loc[df_reco.loc[x.index, 'Score_Final_100'].idxmax(), 'CODE_IRIS'] if 'CODE_IRIS' in df_reco.columns else x.iloc[0])
        )
        .sort_values(by='Score_Max', ascending=False)
        .head(n_recommandations)
        .reset_index()
    )
    
    return recommendations
