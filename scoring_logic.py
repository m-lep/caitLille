"""
Algorithme de Recommandation d'IRIS - Métropole de Lille (VERSION CORRIGÉE v2)
===============================================================================

Utilise UNIQUEMENT les vraies données du fichier Excel, sans invention.
Système de scoring multi-critères avec anti-monopole pour garantir équité.
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# --- CONFIGURATION GLOBALE ---
# --------------------------------------------------------------------------

FICHIER_MATRICE = 'DATASET scores brut.xlsx'


class CriterePonderation:
    """Définit l'importance relative des différents critères"""
    PRIX = 1.0
    TRANSPORTS = 2.0
    ESPACES_VERTS = 1.5
    SECURITE = 2.0
    COMMERCES = 1.5
    CULTURE = 1.5
    SPORT = 1.0


@dataclass
class ProfilUtilisateur:
    """Profil créé à partir des réponses du questionnaire (9 questions)"""
    budget_multiplier: float  # 1.0 à 4.0
    mobilite_multiplier: float  # 0.5 à 4.0
    nature_importance: float  # 0.3 à 3.0
    tranquillite_importance: float  # 0.5 à 3.0
    vie_nocturne: float  # 0.0 à 2.0
    famille_boost: float  # 0.0 à 2.5
    culture_sport: float  # 0.3 à 2.5
    calme_vs_anime: float  # -2.0 à +2.0
    communaute: float  # 0.0 à 2.0
    reponses_texte: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# --- CHARGEMENT DES DONNÉES ---
# --------------------------------------------------------------------------

def charger_matrice():
    """Charge la matrice de données depuis Excel"""
    try:
        df = pd.read_excel(FICHIER_MATRICE)
        
        print(f"✅ Matrice chargée avec {len(df)} lignes")
        return df
        
    except Exception as e:
        print(f"❌ ERREUR lors du chargement : {e}")
        return None


# --------------------------------------------------------------------------
# --- FONCTIONS DE NORMALISATION ---
# --------------------------------------------------------------------------

def _normaliser_score(valeurs: pd.Series, inverse: bool = False) -> pd.Series:
    """Normalise un score entre 0 et 100 avec distribution non-linéaire"""
    if valeurs.std() == 0:
        return pd.Series([50] * len(valeurs), index=valeurs.index)
    
    # Normalisation robuste
    q1 = valeurs.quantile(0.25)
    q3 = valeurs.quantile(0.75)
    iqr = q3 - q1
    
    if iqr == 0:
        normalized = (valeurs - valeurs.min()) / (valeurs.max() - valeurs.min() + 1e-10)
    else:
        normalized = (valeurs - q1) / (iqr * 1.5)
        normalized = normalized.clip(0, 1)
    
    if inverse:
        normalized = 1 - normalized
    
    # Application fonction sigmoïde
    sigmoid_normalized = 100 / (1 + np.exp(-6 * (normalized - 0.5)))
    
    return sigmoid_normalized


# --------------------------------------------------------------------------
# --- CALCUL DES SCORES PAR CRITÈRE ---
# --------------------------------------------------------------------------

def _calculer_score_prix(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score basé sur le prix RÉEL adapté au budget de l'utilisateur"""
    prix_m2 = iris_data['Prix_Median_m2']
    
    # Si budget limité (1.0-2.0) : on préfère les quartiers bon marché (inverse=True)
    # Si budget élevé (2.5-4.0) : on accepte/préfère les quartiers plus chers (inverse=False)
    if profil.budget_multiplier < 2.0:
        # Budget limité : score élevé pour prix bas
        score_base = _normaliser_score(prix_m2, inverse=True)
        
        # Bonus pour quartiers très abordables
        bonus_abordable = pd.Series(0.0, index=score_base.index)
        quartiers_abordables = prix_m2 < 2500
        bonus_valeur = (2500 - prix_m2[quartiers_abordables]) / 2500 * 40
        bonus_abordable[quartiers_abordables] = bonus_valeur
        
        return (score_base + bonus_abordable).clip(upper=100)
    else:
        # Budget confortable/élevé : score neutre ou favorable aux prix élevés
        # On normalise sans inverser (prix élevés = score élevé)
        score_base = _normaliser_score(prix_m2, inverse=False)
        return (score_base * (profil.budget_multiplier / 2.0)).clip(upper=100)


def _calculer_score_espaces_verts(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score espaces verts"""
    surface_verts = iris_data['Surface_Verte_m2']
    scores = _normaliser_score(surface_verts)
    return (scores * profil.nature_importance).clip(upper=100)


def _calculer_score_transports(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score transports basé sur Nb_Transports"""
    nb_transports = iris_data['Nb_Transports']
    score = _normaliser_score(nb_transports)
    return (score * profil.mobilite_multiplier).clip(upper=100)


def _calculer_score_tranquillite(iris_data: pd.DataFrame, iris_data_raw: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score tranquillité basé sur NORM_BRUIT"""
    # Moins de bruit = plus tranquille
    if 'Norm_Bruit' in iris_data_raw.columns:
        score_base = 100 - (iris_data_raw['Norm_Bruit'] * 100)
    else:
        # Fallback si colonne manquante
        score_base = pd.Series(50.0, index=iris_data.index)
    
    # Bonus quartiers très calmes
    bonus_calme = pd.Series(0.0, index=score_base.index)
    if profil.tranquillite_importance >= 2.0 and 'Bruit_Leq_dB' in iris_data_raw.columns:
        bruit_db = iris_data_raw['Bruit_Leq_dB']
        quartiers_calmes = bruit_db < 60
        bonus_valeur = (60 - bruit_db[quartiers_calmes]) / 60 * 30
        bonus_calme[quartiers_calmes] = bonus_valeur
    
    return ((score_base + bonus_calme) * profil.tranquillite_importance).clip(upper=100)


def _calculer_score_commerces(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score commerces/commodités"""
    score = (
        iris_data['Nb_Commerces'] * 3 +
        iris_data['Nb_Pharmacies'] * 5 +
        iris_data['Nb_Restaurants'] * 2
    )
    normalized = _normaliser_score(score)
    
    score_final = normalized
    if profil.vie_nocturne > 1.0:
        score_final *= 1.2
    
    return score_final.clip(upper=100)


def _calculer_score_culture(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score culture basé sur Nb_Bars"""
    score = iris_data['Nb_Bars']
    normalized = _normaliser_score(score)
    return normalized.clip(upper=100)


def _calculer_score_sport(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Score sport basé sur Nb_ComplexesSportifs"""
    score = iris_data['Nb_ComplexesSportifs']
    normalized = _normaliser_score(score)
    return (normalized * profil.culture_sport).clip(upper=100)


# --------------------------------------------------------------------------
# --- BONUS ---
# --------------------------------------------------------------------------

def _calculer_bonus_familial(iris_data: pd.DataFrame, profil: ProfilUtilisateur) -> pd.Series:
    """Bonus quartier familial"""
    bonus = pd.Series(0.0, index=iris_data.index)
    
    if profil.famille_boost >= 1.5:
        nb_ecoles = iris_data['Nb_Ecoles']
        iris_educatifs = nb_ecoles >= 3
        bonus[iris_educatifs] = (nb_ecoles[iris_educatifs] - 2) * 15
    
    return bonus


def _calculer_bonus_equilibre(iris_data: pd.DataFrame, iris_data_raw: pd.DataFrame) -> pd.Series:
    """Bonus équilibre pour quartiers corrects sur plusieurs critères"""
    bonus = pd.Series(0.0, index=iris_data.index)
    
    nb_criteres_ok = pd.Series(0, index=iris_data.index)
    
    if 'Prix_Median_m2' in iris_data.columns:
        nb_criteres_ok += (iris_data['Prix_Median_m2'] < 2800).astype(int)
    if 'Surface_Verte_m2' in iris_data.columns:
        nb_criteres_ok += (iris_data['Surface_Verte_m2'] > 5000).astype(int)
    if 'Nb_Transports' in iris_data.columns:
        nb_criteres_ok += (iris_data['Nb_Transports'] > 2).astype(int)
    if 'Nb_Commerces' in iris_data.columns:
        nb_criteres_ok += (iris_data['Nb_Commerces'] > 5).astype(int)
    if 'Bruit_Leq_dB' in iris_data_raw.columns:
        nb_criteres_ok += (iris_data_raw['Bruit_Leq_dB'] < 70).astype(int)
    
    bonus[nb_criteres_ok == 2] = 10
    bonus[nb_criteres_ok == 3] = 20
    bonus[nb_criteres_ok >= 4] = 35
    
    return bonus


def _appliquer_antimonopole(scores: pd.Series) -> pd.Series:
    """Système anti-monopole : pénalisation progressive des superstars"""
    moyenne = scores.mean()
    ecart_type = scores.std()
    seuil = moyenne + 0.85 * ecart_type
    
    scores_penalises = scores.copy()
    
    for idx in scores.index:
        if scores[idx] > seuil:
            exces = scores[idx] - seuil
            penalite = exces * 0.35 + math.log(1 + exces) * 12
            scores_penalises[idx] = scores[idx] - penalite
    
    return scores_penalises


# --------------------------------------------------------------------------
# --- FONCTION PRINCIPALE DE CALCUL ---
# --------------------------------------------------------------------------

def calculer_scores_complets(profil: ProfilUtilisateur, iris_data: pd.DataFrame, iris_data_raw: pd.DataFrame) -> pd.DataFrame:
    """Calcule les scores complets pour tous les IRIS"""
    
    resultats = pd.DataFrame()
    
    # Gérer CODE_IRIS ou code_iris
    if 'CODE_IRIS' in iris_data.columns:
        resultats['code_iris'] = iris_data['CODE_IRIS'].astype(str)
    elif 'code_iris' in iris_data.columns:
        resultats['code_iris'] = iris_data['code_iris'].astype(str)
    else:
        # Fallback: créer des codes factices
        resultats['code_iris'] = [f'IRIS_{i}' for i in range(len(iris_data))]
    
    # Calculer chaque critère
    resultats['score_prix'] = _calculer_score_prix(iris_data, profil)
    resultats['score_espaces_verts'] = _calculer_score_espaces_verts(iris_data, profil)
    resultats['score_transports'] = _calculer_score_transports(iris_data, profil)
    resultats['score_tranquillite'] = _calculer_score_tranquillite(iris_data, iris_data_raw, profil)
    resultats['score_commerces'] = _calculer_score_commerces(iris_data, profil)
    resultats['score_culture'] = _calculer_score_culture(iris_data, profil)
    resultats['score_sport'] = _calculer_score_sport(iris_data, profil)
    
    # Score total pondéré
    poids = CriterePonderation
    resultats['score_total'] = (
        resultats['score_prix'] * poids.PRIX +
        resultats['score_transports'] * poids.TRANSPORTS +
        resultats['score_espaces_verts'] * poids.ESPACES_VERTS +
        resultats['score_tranquillite'] * poids.SECURITE +
        resultats['score_commerces'] * poids.COMMERCES +
        resultats['score_culture'] * poids.CULTURE +
        resultats['score_sport'] * poids.SPORT
    ) / (poids.PRIX + poids.TRANSPORTS + poids.ESPACES_VERTS + 
         poids.SECURITE + poids.COMMERCES + poids.CULTURE + poids.SPORT)
    
    # Bonus ciblés
    bonus_familial = _calculer_bonus_familial(iris_data, profil)
    bonus_equilibre = _calculer_bonus_equilibre(iris_data, iris_data_raw)
    
    resultats['score_total'] = resultats['score_total'] + bonus_familial + bonus_equilibre
    
    # Anti-monopole
    resultats['score_total'] = _appliquer_antimonopole(resultats['score_total'])
    
    # Classer
    resultats = resultats.sort_values('score_total', ascending=False).reset_index(drop=True)
    resultats['rang'] = range(1, len(resultats) + 1)
    
    return resultats


# --------------------------------------------------------------------------
# --- FONCTION DE CONVERSION DEPUIS RÉPONSES ---
# --------------------------------------------------------------------------

def creer_profil_depuis_reponses(reponses_dict: Dict) -> ProfilUtilisateur:
    """
    Crée un ProfilUtilisateur à partir des réponses du questionnaire.
    
    reponses_dict structure:
    {
        0: {'option': 'Très limité', 'poids': 4},  # Q1: Budget
        1: {'option': 'Transports publics', 'poids': 4},  # Q2: Mobilité
        ...
    }
    """
    
    # Mappings des réponses vers les valeurs du profil
    budget_map = {
        'Très limité': 1.0,
        'Modéré': 1.5,
        'Confortable': 2.5,
        'Élevé': 4.0
    }
    
    mobilite_map = {
        'Voiture': 0.5,
        'Transports publics': 4.0,
        'Vélo': 2.0,
        'À pied': 1.5
    }
    
    nature_map = {
        'Essentiel': 3.0,
        'Important': 2.0,
        'Secondaire': 1.0,
        'Indifférent': 0.3
    }
    
    tranquillite_map = {
        'Primordial': 3.0,
        'Important': 2.0,
        'Normal': 1.0,
        'Peu important': 0.5
    }
    
    vie_map = {
        'Très important': 2.0,
        'Occasionnellement': 1.0,
        'Rarement': 0.3,
        'Jamais': 0.0
    }
    
    famille_map = {
        'Célibataire': 0.0,
        'Couple sans enfant': 0.5,
        'Jeune famille': 2.0,
        'Famille nombreuse': 2.5
    }
    
    sport_map = {
        'Très actif': 2.5,
        'Occasionnellement': 1.5,
        'Rarement': 0.8,
        'Jamais': 0.3
    }
    
    ambiance_map = {
        'Très calme': -2.0,
        'Calme mais vivant': -0.5,
        'Animé': 1.0,
        'Très animé': 2.0
    }
    
    # Extraire les valeurs (avec defaults)
    r1 = reponses_dict.get(0, {}).get('option', 'Modéré')
    r2 = reponses_dict.get(1, {}).get('option', 'Vélo')
    r3 = reponses_dict.get(2, {}).get('option', 'Important')
    r4 = reponses_dict.get(3, {}).get('option', 'Important')
    r6 = reponses_dict.get(5, {}).get('option', 'Occasionnellement')
    r7 = reponses_dict.get(6, {}).get('option', 'Couple sans enfant')
    r8 = reponses_dict.get(7, {}).get('option', 'Occasionnellement')
    r9 = reponses_dict.get(8, {}).get('option', 'Calme mais vivant')
    
    budget_val = budget_map.get(r1, 2.5)
    mobilite_val = mobilite_map.get(r2, 2.0)
    nature_val = nature_map.get(r3, 2.0)
    tranquillite_val = tranquillite_map.get(r4, 2.0)
    vie_val = vie_map.get(r6, 1.0)
    famille_val = famille_map.get(r7, 0.5)
    sport_val = sport_map.get(r8, 1.5)
    calme_val = ambiance_map.get(r9, 0.0)
    
    profil = ProfilUtilisateur(
        budget_multiplier=budget_val,
        mobilite_multiplier=mobilite_val,
        nature_importance=nature_val,
        tranquillite_importance=tranquillite_val,
        vie_nocturne=vie_val,
        famille_boost=famille_val,
        culture_sport=sport_val,
        calme_vs_anime=calme_val,
        communaute=famille_val * 0.5,
        reponses_texte={
            'Q1_Budget': r1,
            'Q2_Mobilité': r2,
            'Q3_Espaces_verts': r3,
            'Q4_Tranquillité': r4,
            'Q6_Vie_nocturne': r6,
            'Q7_Famille': r7,
            'Q8_Sport': r8,
            'Q9_Ambiance': r9
        }
    )
    
    return profil


# --------------------------------------------------------------------------
# --- FONCTION COMPATIBLE AVEC APP.PY ---
# --------------------------------------------------------------------------

def recommander_quartiers(reponses_dict: Dict, matrice_data: pd.DataFrame, n_recommandations: int = 110):
    """
    Fonction compatible avec l'interface Streamlit existante.
    Retourne les résultats sous forme de DataFrame.
    """
    if matrice_data is None or matrice_data.empty:
        return None
    
    # Créer le profil
    profil = creer_profil_depuis_reponses(reponses_dict)
    
    # Calculer les scores
    resultats = calculer_scores_complets(profil, matrice_data, matrice_data)
    
    # Ajouter le nom IRIS pour compatibilité
    if 'NOM_IRIS' in matrice_data.columns:
        code_to_nom = dict(zip(matrice_data['CODE_IRIS'].astype(str), matrice_data['NOM_IRIS']))
        resultats['NOM_IRIS'] = resultats['code_iris'].map(code_to_nom)
    
    # Renommer pour compatibilité
    resultats = resultats.rename(columns={'score_total': 'Score_Max'})
    
    return resultats.head(n_recommandations)


def consolider_poids_utilisateur(reponses_dict: Dict) -> Dict:
    """Fonction de compatibilité (non utilisée dans le nouveau système)"""
    return {}
