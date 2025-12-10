"""
🧪 TESTEUR ALGORITHME CAITLILLE - GOOGLE COLAB
===============================================

Ce notebook permet de tester l'algorithme de recommandation de quartiers 
avec une carte Folium interactive, SANS toucher au projet Streamlit principal.

INSTRUCTIONS :
1. Upload le fichier "DATASET scores brut.xlsx" dans Colab
2. Upload le fichier "iris_v2_Lille.geojson" dans Colab
3. Exécutez toutes les cellules
4. Modifiez les réponses dans la section "TESTEZ ICI" et re-exécutez

"""

# ============================================================================
# INSTALLATION & IMPORTS
# ============================================================================

!pip install pandas openpyxl folium -q

import pandas as pd
import numpy as np
import folium
from folium import GeoJson
import json

# ============================================================================
# MOTEUR DE SCORING (copie simplifiée de scoring_logic_v2.py)
# ============================================================================

def charger_matrice():
    """Charge les données depuis le fichier Excel"""
    return pd.read_excel('DATASET scores brut.xlsx')

def consolider_poids_utilisateur(reponses):
    """
    Convertit les réponses utilisateur en poids pour chaque critère
    
    Returns:
        tuple: (poids_criteres, poids_categories) - dictionnaires de poids
    """
    # Poids par défaut
    poids = {
        'Norm_Bruit': 8,
        'Norm_Prix': 8,
        'Norm_Surface_Verte_m2': 8,
        'Norm_Nb_Pharmacies': 5,
        'Norm_Nb_Commerces': 5,
        'Norm_Nb_Restaurants': 5,
        'Norm_Nb_Transports': 8,
        'Norm_Nb_VLille': 5,
        'Norm_Nb_ParcsEnfants': 5,
        'Norm_Nb_ComplexesSportifs': 5,
        'Norm_Nb_Ecoles': 5,
        'Norm_Nb_Bars': 5,
        'Norm_Nb_Parkings': 5,
    }
    
    poids_categories = {
        'Prix': 8,
        'Ambiance': 8,
        'Sport': 5,
        'Services': 5,
        'Transport': 8
    }
    
    # Parcourir les réponses et ajuster les poids
    for idx, reponse in reponses.items():
        question_id = reponse['question_id']
        option = reponse['option']
        
        # Q1: BUDGET (impact MAJEUR sur prix)
        if question_id == 'budget':
            if 'Serré' in option or '< 2000' in option or '< 2500' in option:
                poids['Norm_Prix'] = 30  # ULTRA PRIORITAIRE
                poids_categories['Prix'] = 30
            elif 'Modéré' in option or '2500-3500' in option:
                poids['Norm_Prix'] = 18
                poids_categories['Prix'] = 18
            elif 'Confortable' in option or '3500-4000' in option:
                poids['Norm_Prix'] = 10
                poids_categories['Prix'] = 10
            else:  # Aucune limite
                poids['Norm_Prix'] = 5
                poids_categories['Prix'] = 5
        
        # Q2: AMBIANCE
        elif question_id == 'ambiance':
            if 'Calme' in option:
                poids['Norm_Bruit'] = 15
                poids['Norm_Surface_Verte_m2'] = 12
                poids['Norm_Nb_Bars'] = 3
                poids['Norm_Nb_Restaurants'] = 5
            elif 'Équilibré' in option:
                poids['Norm_Bruit'] = 8
                poids['Norm_Surface_Verte_m2'] = 8
                poids['Norm_Nb_Restaurants'] = 8
                poids['Norm_Nb_Bars'] = 5
            elif 'Animé' in option:
                poids['Norm_Bruit'] = 3
                poids['Norm_Nb_Restaurants'] = 12
                poids['Norm_Nb_Bars'] = 10
                poids['Norm_Surface_Verte_m2'] = 3
            else:  # Très animé
                poids['Norm_Bruit'] = 2
                poids['Norm_Nb_Restaurants'] = 15
                poids['Norm_Nb_Bars'] = 15
                poids['Norm_Surface_Verte_m2'] = 2
        
        # Q3: ACTIVITÉ SPORTIVE
        elif question_id == 'activite':
            if 'Peu sportif' in option:
                poids['Norm_Nb_ComplexesSportifs'] = 2
            elif 'Occasionnellement' in option:
                poids['Norm_Nb_ComplexesSportifs'] = 5
            elif 'Régulièrement' in option:
                poids['Norm_Nb_ComplexesSportifs'] = 10
            else:  # Très sportif
                poids['Norm_Nb_ComplexesSportifs'] = 15
        
        # Q4: STATUT
        elif question_id == 'statut':
            if 'Parent' in option:
                poids['Norm_Nb_Ecoles'] = 10
                poids['Norm_Nb_ParcsEnfants'] = 10
            elif 'Étudiant' in option:
                poids['Norm_Nb_Bars'] = 12
                poids['Norm_Nb_Restaurants'] = 10
                poids['Norm_Prix'] = max(poids['Norm_Prix'], 20)
            elif 'Jeune actif' in option:
                poids['Norm_Nb_Transports'] = 12
                poids['Norm_Nb_Restaurants'] = 10
            else:  # Senior
                poids['Norm_Bruit'] = 15
                poids['Norm_Nb_Pharmacies'] = 10
                poids['Norm_Surface_Verte_m2'] = 10
        
        # Q5: TRANSPORT
        elif question_id == 'transport':
            if 'Voiture' in option:
                poids['Norm_Nb_Parkings'] = 15
                poids['Norm_Nb_Transports'] = 3
            elif 'Transports publics' in option:
                poids['Norm_Nb_Transports'] = 15
                poids['Norm_Nb_Parkings'] = 3
            else:  # Vélo
                poids['Norm_Nb_VLille'] = 15
                poids['Norm_Nb_Parkings'] = 5
        
        # Q6: SERVICES
        elif question_id == 'services':
            if 'Commerces' in option:
                poids['Norm_Nb_Commerces'] = 15
                poids['Norm_Nb_Pharmacies'] = 12
            elif 'Restaurants' in option:
                poids['Norm_Nb_Restaurants'] = 15
                poids['Norm_Nb_Bars'] = 12
            # Sinon équilibre (poids par défaut)
    
    return poids, poids_categories

def calculer_score_quartier(quartier_row, poids):
    """Calcule le score d'un quartier selon les poids définis"""
    score = 0
    for critere, poids_critere in poids.items():
        if critere in quartier_row.index:
            valeur_norm = quartier_row[critere]
            if pd.notna(valeur_norm):
                score += valeur_norm * poids_critere
    return score

def recommander_quartiers(poids, matrice, n_recommandations=110):
    """Calcule les scores de tous les quartiers"""
    scores = []
    
    for idx, row in matrice.iterrows():
        score = calculer_score_quartier(row, poids)
        scores.append({
            'CODE_IRIS': row['CODE_IRIS'],
            'NOM_IRIS': row['NOM_IRIS'],
            'Score_Max': score,
            'Prix_Median_m2': row.get('Prix_Median_m2', np.nan)
        })
    
    df_scores = pd.DataFrame(scores)
    df_scores = df_scores.sort_values('Score_Max', ascending=False)
    df_scores['Rang'] = range(1, len(df_scores) + 1)
    
    return df_scores.head(n_recommandations)

# ============================================================================
# FONCTIONS VISUALISATION
# ============================================================================

def get_color_from_score(score, min_score, max_score):
    """Génère une couleur de gradient selon le score"""
    if max_score > min_score:
        normalized = ((score - min_score) / (max_score - min_score)) * 100
    else:
        normalized = 50
    
    # Gradient : Rouge foncé → Orange → Jaune → Vert → Vert foncé
    if normalized < 20:
        ratio = normalized / 20
        r = int(139 + (255 - 139) * ratio)
        g = 0
        b = 0
    elif normalized < 40:
        ratio = (normalized - 20) / 20
        r = 255
        g = int(140 * ratio)
        b = 0
    elif normalized < 60:
        ratio = (normalized - 40) / 20
        r = 255
        g = int(140 + (255 - 140) * ratio)
        b = 0
    elif normalized < 75:
        ratio = (normalized - 60) / 15
        r = int(255 * (1 - ratio))
        g = 255
        b = int(50 * ratio)
    elif normalized < 90:
        ratio = (normalized - 75) / 15
        r = 0
        g = 255
        b = int(50 + (100 * ratio))
    else:
        ratio = (normalized - 90) / 10
        r = 0
        g = int(255 - (100 * ratio))
        b = int(150 - (50 * ratio))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def creer_carte(df_scores, geojson_path, matrice):
    """Crée une carte Folium avec les scores"""
    # Charger GeoJSON
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    # Créer mapping CODE_IRIS -> NOM_IRIS
    code_to_nom = dict(zip(matrice['CODE_IRIS'], matrice['NOM_IRIS']))
    
    # Créer mapping scores
    scores_par_code = dict(zip(df_scores['CODE_IRIS'], df_scores['Score_Max']))
    
    # Trouver min/max pour normalisation
    min_score = df_scores['Score_Max'].min()
    max_score = df_scores['Score_Max'].max()
    
    # Créer carte centrée sur Lille
    m = folium.Map(
        location=[50.6292, 3.0573],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Ajouter les polygones IRIS
    for feature in geojson_data['features']:
        code_iris = feature['properties'].get('code_iris')
        nom_iris = code_to_nom.get(int(code_iris), 'Inconnu') if code_iris else 'Inconnu'
        
        score = scores_par_code.get(int(code_iris), 0) if code_iris else 0
        color = get_color_from_score(score, min_score, max_score)
        
        folium.GeoJson(
            feature,
            style_function=lambda x, c=color: {
                'fillColor': c,
                'color': '#2d2d2d',
                'weight': 1.2,
                'fillOpacity': 0.5
            },
            highlight_function=lambda x, c=color: {
                'fillColor': c,
                'color': '#ff5a5f',
                'weight': 2.5,
                'fillOpacity': 0.75
            },
            tooltip=folium.Tooltip(
                f'<div style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px;"><b>{nom_iris}</b><br>Score: {score:.1f}</div>',
                sticky=False
            )
        ).add_to(m)
    
    return m

# ============================================================================
# 🧪 TESTEZ ICI VOS QUESTIONS/RÉPONSES
# ============================================================================

# Exemple 1: Budget serré, calme, parent
reponses_test = {
    0: {'question_id': 'budget', 'option': 'Serré (< 600€/mois)'},
    1: {'question_id': 'ambiance', 'option': 'Calme avec espaces verts'},
    2: {'question_id': 'activite', 'option': 'Occasionnellement sportif'},
    3: {'question_id': 'statut', 'option': 'Parent avec enfants'},
    4: {'question_id': 'transport', 'option': 'Transports publics'},
    5: {'question_id': 'services', 'option': 'Commerces de proximité'},
}

# ============================================================================
# EXÉCUTION
# ============================================================================

print("📊 Chargement des données...")
matrice = charger_matrice()
print(f"✅ {len(matrice)} quartiers chargés\n")

print("🧮 Calcul des poids selon vos réponses...")
poids, poids_cat = consolider_poids_utilisateur(reponses_test)
print("\n🎯 Poids des critères :")
for critere, val in sorted(poids.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  • {critere}: {val}")

print("\n🏆 Calcul des scores...")
df_resultats = recommander_quartiers(poids, matrice)

print("\n📍 Top 10 quartiers recommandés :")
print(df_resultats[['Rang', 'NOM_IRIS', 'Score_Max', 'Prix_Median_m2']].head(10).to_string(index=False))

print("\n🗺️ Génération de la carte interactive...")
carte = creer_carte(df_resultats, 'iris_v2_Lille.geojson', matrice)

print("\n✅ Carte prête ! Affichage ci-dessous :")
carte

# ============================================================================
# EXEMPLES DE TESTS SUPPLÉMENTAIRES
# ============================================================================

print("\n\n" + "="*80)
print("💡 AUTRES EXEMPLES À TESTER")
print("="*80)

print("""
# Exemple 2: Étudiant budget serré, vie animée
reponses_etudiant = {
    0: {'question_id': 'budget', 'option': 'Serré (< 600€/mois)'},
    1: {'question_id': 'ambiance', 'option': 'Très animé (vie nocturne, bars)'},
    2: {'question_id': 'activite', 'option': 'Peu sportif'},
    3: {'question_id': 'statut', 'option': 'Étudiant'},
    4: {'question_id': 'transport', 'option': 'Vélo (V\'Lille)'},
    5: {'question_id': 'services', 'option': 'Restaurants et bars'},
}

# Exemple 3: Senior aisé, calme absolu
reponses_senior = {
    0: {'question_id': 'budget', 'option': 'Aucune limite (> 1300€/mois)'},
    1: {'question_id': 'ambiance', 'option': 'Calme avec espaces verts'},
    2: {'question_id': 'activite', 'option': 'Occasionnellement sportif'},
    3: {'question_id': 'statut', 'option': 'Senior'},
    4: {'question_id': 'transport', 'option': 'Voiture personnelle'},
    5: {'question_id': 'services', 'option': 'Équilibre commerces/restaurants'},
}

# Pour tester, remplacez "reponses_test" ci-dessus et re-exécutez les cellules
""")
