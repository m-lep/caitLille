# Système de Scoring Intégré

## 📋 Configuration Requise

Pour activer le système de scoring personnalisé basé sur vos réponses, vous devez placer le fichier Excel suivant dans le même dossier que `app.py` :

**Fichier requis** : `DATASET scores brut.xlsx`
- **Feuille à utiliser** : `Matrice_Brute_Normalisee`

## 📁 Structure des Fichiers

```
caitlille-streamlit/
├── app.py                          # Application principale
├── scoring_logic.py                # Logique de scoring
├── DATASET scores brut.xlsx        # ⚠️ À AJOUTER - Matrice de scores normalisés
├── iris_v2_Lille.geojson          # Données géographiques IRIS
└── README_SCORING.md              # Ce fichier
```

## 🎯 Comment ça Marche

### 1. **Réponses aux Questions**
Chaque fois que vous cliquez sur un bouton (😤 😕 😊 🤩), votre réponse est enregistrée avec un poids :
- 😤 Carrément pas → Poids 1
- 😕 Pas pour moi → Poids 2  
- 😊 J'aime bien → Poids 3
- 🤩 J'adore! → Poids 4

### 2. **Calcul des Poids par Critère**
Chaque question renforce certains critères normalisés :
- **Q1 (Vie urbaine)** : Renforce `Norm_Nb_Bars`, `Norm_Nb_Restaurants`, etc.
- **Q2 (Nature)** : Renforce `Norm_Surface_Verte_m2`, `Norm_Bruit`
- **Q3 (Centre-ville)** : Renforce `Norm_Nb_Transports`, `Norm_Nb_VLille`
- Et ainsi de suite...

### 3. **Scoring Final**
À la fin des 10 questions :
1. Les poids sont consolidés pour chaque critère
2. Un score de correspondance est calculé pour chaque quartier IRIS
3. Les quartiers sont classés par score (0-100)
4. Les **TOP 10** sont affichés sur la carte avec leurs vraies couleurs

### 4. **Affichage sur la Carte**
- **Quartiers recommandés** : Couleur basée sur le score réel (vert = meilleur match)
- **Autres quartiers** : Score aléatoire pour comparaison
- Cliquez sur un quartier pour voir les offres immobilières

## 📊 Critères Normalisés Utilisés

Les 13 critères dans la matrice Excel :
- `Norm_Bruit` - Niveau de calme (inversé)
- `Norm_Prix` - Prix au m² (inversé)
- `Norm_Surface_Verte_m2` - Espaces verts
- `Norm_Nb_Pharmacies` - Pharmacies
- `Norm_Nb_Commerces` - Commerces
- `Norm_Nb_Restaurants` - Restaurants
- `Norm_Nb_Transports` - Transports en commun
- `Norm_Nb_VLille` - Stations V'Lille
- `Norm_Nb_ParcsEnfants` - Aires de jeux
- `Norm_Nb_ComplexesSportifs` - Complexes sportifs
- `Norm_Nb_Ecoles` - Écoles
- `Norm_Nb_Bars` - Bars
- `Norm_Nb_Parkings` - Parkings

## 🔧 Mode Dégradé

Si le fichier Excel n'est pas trouvé, l'application fonctionne quand même :
- ✅ Questions et navigation OK
- ✅ Carte IRIS avec scores aléatoires
- ✅ Offres immobilières scrapées
- ❌ Pas de scoring personnalisé

## ✅ Vérification

Lancez l'app et vérifiez dans la console :
```
✅ Matrice chargée avec XXX lignes.
```

Si vous voyez :
```
⚠️ Système de scoring non disponible: [Errno 2] No such file or directory: 'DATASET scores brut.xlsx'
```

→ Placez le fichier Excel dans `/Users/marinlepine/Downloads/caitlille-streamlit/`

## 🎨 Exemple de Mappage (Q1)

**Question 1 : Vie urbaine animée**

| Bouton | Poids | Critères Renforcés |
|--------|-------|-------------------|
| 😤 Carrément pas | 1 | Aucun |
| 😕 Pas pour moi | 2 | `Norm_Bruit` (préfère calme) |
| 😊 J'aime bien | 3 | `Norm_Nb_Commerces`, `Norm_Nb_Restaurants` |
| 🤩 J'adore! | 4 | `Norm_Nb_Bars`, `Norm_Nb_Restaurants`, `Norm_Nb_Transports` |

---

💡 **Conseil** : Répondez honnêtement à toutes les questions pour obtenir les meilleures recommandations !
