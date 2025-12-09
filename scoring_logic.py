import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# --- I. CONFIGURATION GLOBALE ---
# --------------------------------------------------------------------------

FICHIER_MATRICE = 'DATASET scores brut.xlsx'
NOM_FEUILLE = 'Matrice_Brute_Normalisee_V2'

# Nouveaux critères de proximité (normalisés)
NOUVELLES_PROXIMITES_NORM = [
    'Norm_Prox_Densite_Ecoles',
    'Norm_Prox_Densite_Commerces',
    'Norm_Prox_Densite_Transports',
    'Norm_Prox_Ratio_EspacesVerts'
]

# CRITÈRE D'ÉGALISATION
CRITERE_EGALISATION = 'Norm_Equilibre_Global'

# 1. Tous les critères normalisés (INCLUANT PROXIMITÉ ET ÉGALISATION)
TOUS_LES_CRITERES_NORMALISES = [
    'Norm_Bruit', 'Norm_Prix', 'Norm_Surface_Verte_m2', 'Norm_Nb_Pharmacies',
    'Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports',
    'Norm_Nb_VLille', 'Norm_Nb_ParcsEnfants', 'Norm_Nb_ComplexesSportifs',
    'Norm_Nb_Ecoles', 'Norm_Nb_Bars', 'Norm_Nb_Parkings'
] + NOUVELLES_PROXIMITES_NORM + [CRITERE_EGALISATION] # <-- AJOUT DU CRITÈRE

# 2. Les 4 boutons représentent le niveau d'intérêt (1 à 4)
# ...

# 3. Logique de Scoring avec Facteur d'Égalisation
# --- LOGIQUE SCORING (10 QUESTIONS) ---

LOGIQUE_SCORING = {
    
    # =================================================================
    # Q1 : MON AMBIANCE DE QUARTIER IDÉALE
    # =================================================================
    'Très animé (nightlife)': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports'],
    'Urbain & dynamique': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Prox_Densite_Commerces', 'Norm_Nb_VLille'],
    'Calme avec commerces': ['Norm_Bruit', 'Norm_Nb_Commerces', 'Norm_Nb_Pharmacies', 'Norm_Equilibre_Global'],
    'Paisible & résidentiel': ['Norm_Bruit', 'Norm_Surface_Verte_m2', 'Norm_Nb_ParcsEnfants', 'Norm_Prox_Ratio_EspacesVerts'],

    # =================================================================
    # Q2 : MON NIVEAU DE FLEXIBILITÉ BUDGÉTAIRE
    # =================================================================
    'Très serré': ['Norm_Prix', 'Norm_Nb_Transports'],
    'Modéré': ['Norm_Prix', 'Norm_Nb_Commerces', 'Norm_Equilibre_Global'],
    'Confortable': ['Norm_Prix', 'Norm_Nb_Restaurants', 'Norm_Nb_Parkings'],
    'Flexible': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_ComplexesSportifs'], # Norm_Prix est ignoré

    # =================================================================
    # Q3 : MON EXIGENCE EN PROXIMITÉ DES SERVICES
    # =================================================================
    'Services médicaux (Pharmacie/Santé)': ['Norm_Nb_Pharmacies', 'Norm_Nb_Commerces', 'Norm_Bruit'],
    'Hypermarchés': ['Norm_Nb_Commerces', 'Norm_Nb_Parkings', 'Norm_Prox_Densite_Commerces'],
    'Restauration': ['Norm_Nb_Restaurants', 'Norm_Nb_Bars', 'Norm_Prox_Densite_Commerces'],
    'Hyper-proximité totale (tout à pied)': ['Norm_Prox_Densite_Commerces', 'Norm_Prox_Densite_Transports', 'Norm_Nb_Pharmacies', 'Norm_Equilibre_Global'],

    # =================================================================
    # Q4 : MON MODE DE DÉPLACEMENT PRINCIPAL
    # =================================================================
    'Transports en commun': ['Norm_Nb_Transports', 'Norm_Nb_VLille', 'Norm_Prox_Densite_Transports'],
    'Vélo': ['Norm_Nb_VLille', 'Norm_Surface_Verte_m2', 'Norm_Nb_ComplexesSportifs'],
    'Voiture': ['Norm_Nb_Parkings', 'Norm_Nb_Commerces', 'Norm_Bruit'],
    'Uniquement à pied': ['Norm_Prox_Densite_Commerces', 'Norm_Prox_Densite_Transports', 'Norm_Equilibre_Global'],

    # =================================================================
    # Q5 : MON BESOIN EN ESPACES VERTS ET NATURE
    # =================================================================
    'Essentiel (Nature/Détente)': ['Norm_Prox_Ratio_EspacesVerts', 'Norm_Surface_Verte_m2', 'Norm_Bruit', 'Norm_Nb_ParcsEnfants'],
    'Juste quelques parcs': ['Norm_Surface_Verte_m2', 'Norm_Nb_ParcsEnfants', 'Norm_Equilibre_Global'],
    'Pratique pour le sport': ['Norm_Nb_ComplexesSportifs', 'Norm_Prox_Ratio_EspacesVerts', 'Norm_Nb_Transports'],
    'Peu important': ['Norm_Nb_Transports', 'Norm_Nb_Commerces'],

    # =================================================================
    # Q6 : MON BESOIN EN INFRASTRUCTURES POUR ENFANTS/FAMILLE
    # =================================================================
    'Écoles': ['Norm_Prox_Densite_Ecoles', 'Norm_Nb_Ecoles', 'Norm_Bruit'],
    'Parcs d\'enfants': ['Norm_Nb_ParcsEnfants', 'Norm_Surface_Verte_m2', 'Norm_Bruit'],
    'Écoles + Sport': ['Norm_Prox_Densite_Ecoles', 'Norm_Nb_ComplexesSportifs', 'Norm_Prox_Ratio_EspacesVerts'],
    'Pas pertinent': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Nb_Transports'], # Inverse le poids vers non-famille

    # =================================================================
    # Q7 : MA SENSIBILITÉ AU BRUIT
    # =================================================================
    'Extrêmement sensible': ['Norm_Bruit', 'Norm_Surface_Verte_m2', 'Norm_Equilibre_Global'],
    'Un peu sensible': ['Norm_Bruit', 'Norm_Nb_ParcsEnfants'],
    'Ça m\'est égal': ['Norm_Nb_Commerces', 'Norm_Nb_Transports'],
    'J\'aime quand ça bouge': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Prox_Densite_Transports'],

    # =================================================================
    # Q8 : MON PROFIL DE VIE ACTUEL (Statut)
    # =================================================================
    'Étudiant': ['Norm_Nb_Transports', 'Norm_Nb_Bars', 'Norm_Prix', 'Norm_Prox_Densite_Transports'],
    'Actif (Salarié/Indépendant)': ['Norm_Nb_Transports', 'Norm_Nb_Commerces', 'Norm_Nb_Parkings', 'Norm_Equilibre_Global'],
    'Retraité': ['Norm_Bruit', 'Norm_Nb_Pharmacies', 'Norm_Surface_Verte_m2', 'Norm_Equilibre_Global'],
    'Famille avec enfants': ['Norm_Prox_Densite_Ecoles', 'Norm_Nb_ParcsEnfants', 'Norm_Bruit', 'Norm_Prox_Ratio_EspacesVerts'],

    # =================================================================
    # Q9 : MON RYTHME DE VIE ET MES HABITUDES
    # =================================================================
    'Très tranquille (à la maison)': ['Norm_Bruit', 'Norm_Surface_Verte_m2', 'Norm_Equilibre_Global'],
    'Sorties fréquentes': ['Norm_Nb_Bars', 'Norm_Nb_Restaurants', 'Norm_Prox_Densite_Transports'],
    'Fait du sport': ['Norm_Nb_ComplexesSportifs', 'Norm_Nb_VLille', 'Norm_Prox_Ratio_EspacesVerts'],
    'Cuisiner vs. Manger dehors': ['Norm_Nb_Commerces', 'Norm_Nb_Restaurants', 'Norm_Equilibre_Global'],

    # =================================================================
    # Q10 : MON CRITÈRE DE QUALITÉ DE VIE ABSOLU
    # =================================================================
    'Uniquement la performance globale (Équilibre)': ['Norm_Equilibre_Global', 'Norm_Prix', 'Norm_Bruit'],
    'Le meilleur prix': ['Norm_Prix', 'Norm_Nb_Transports', 'Norm_Nb_Commerces'],
    'Le moins de bruit': ['Norm_Bruit', 'Norm_Surface_Verte_m2', 'Norm_Equilibre_Global'],
    'L\'hyper-proximité': ['Norm_Prox_Densite_Commerces', 'Norm_Prox_Densite_Transports', 'Norm_Nb_Pharmacies'],
}

# --------------------------------------------------------------------------
# --- II. CHARGEMENT SÉCURISÉ DES DONNÉES (MISE À JOUR) ---
# --------------------------------------------------------------------------

def charger_matrice():
    """Charge la matrice de données et calcule le Facteur d'Égalisation."""
    try:
        df = pd.read_excel(FICHIER_MATRICE, sheet_name=NOM_FEUILLE)
        
        if 'NOM_IRIS' not in df.columns:
            print("❌ ERREUR : La colonne 'NOM_IRIS' est manquante.")
            return None
        
        # 1. Identifier toutes les colonnes normalisées (Norm_) et de proximité (Prox_)
        colonnes_a_inclure = [
            col for col in df.columns 
            if col.startswith('Norm_') or col.startswith('Prox_')
        ]
        
        # S'assurer que les colonnes de prix normalisé et bruit sont incluses (car elles peuvent avoir un préfixe différent si non 'Norm_')
        # Nous allons nous baser sur TOUS_LES_CRITERES_NORMALISES pour la robustesse
        
        # 2. Calcul du Facteur d'Égalisation (Moyenne des scores normalisés)
        # On ne prend que les colonnes qui existent dans le DF
        colonnes_existantes = [col for col in TOUS_LES_CRITERES_NORMALISES if col in df.columns and col != CRITERE_EGALISATION]
        
        if colonnes_existantes:
             # Calcule la moyenne des scores normalisés pour chaque ligne (IRIS)
             df[CRITERE_EGALISATION] = df[colonnes_existantes].mean(axis=1)
             print(f"✅ Ajout du critère d'égalisation '{CRITERE_EGALISATION}'.")
        else:
             print("⚠️ Avertissement : Impossible de calculer le Facteur d'Égalisation (colonnes normalisées manquantes).")
             df[CRITERE_EGALISATION] = 0.5


        # 3. Nettoyage final
        # Inclure le nouveau critère d'égalisation dans le nettoyage
        cols_for_cleanup = colonnes_a_inclure + [CRITERE_EGALISATION]
        df[cols_for_cleanup] = df[cols_for_cleanup].fillna(0.0)
        
        print(f"✅ Matrice chargée avec {df.shape[0]} lignes depuis la feuille '{NOM_FEUILLE}'.")
        return df
        
    except Exception as e:
        print(f"❌ ERREUR lors du chargement : {e}")
        return None


# --------------------------------------------------------------------------
# --- III. FONCTIONS DE SCORING (Inchangé) ---
# --------------------------------------------------------------------------
# Les fonctions consolider_poids_utilisateur et recommander_quartiers ne nécessitent 
# pas de modification car elles gèrent la liste TOUS_LES_CRITERES_NORMALISES mise à jour.

# --- NOUVELLE CONFIGURATION GLOBALE ---
# Facteur d'amplification pour l'équilibre (pour le tester plus fortement)
FACTEUR_AMPLIFICATION_EQUILIBRE = 3
CRITERE_EGALISATION = 'Norm_Equilibre_Global'
# -------------------------------------

def consolider_poids_utilisateur(reponses_dict):
    """
    Traduit les réponses utilisateur en poids pour chaque critère,
    en appliquant une amplification uniquement au Facteur d'Égalisation.
    """
    poids_finaux = {col: 0 for col in TOUS_LES_CRITERES_NORMALISES}
    
    for reponse_data in reponses_dict.values():
        if not isinstance(reponse_data, dict):
            continue
            
        option_choisie = reponse_data.get('option', '')
        niveau_interet = reponse_data.get('poids', 0) 
        poids_a_ajouter = niveau_interet
        
        if niveau_interet == 0:
            continue
            
        if 'Flexible' in option_choisie:
            pass 

        if option_choisie in LOGIQUE_SCORING:
            criteres_renforces = LOGIQUE_SCORING[option_choisie]
            
            for critere in criteres_renforces:
                if critere in poids_finaux:
                    poids = poids_a_ajouter
                    
                    # AMPLIFICATION CIBLÉE SUR LE FACTEUR D'ÉGALISATION
                    if critere == CRITERE_EGALISATION:
                        poids *= FACTEUR_AMPLIFICATION_EQUILIBRE
                    
                    poids_finaux[critere] += poids
    
    return poids_finaux


def recommander_quartiers(poids_finaux_consolides, matrice_data, n_recommandations=5):
    # ... (inchangé)
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
