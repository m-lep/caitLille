# 🧠 Comment fonctionne l'algorithme de recommandation

## Principe simple

L'algorithme **ne décide rien pour vous** - il compare vos priorités avec les données réelles de chaque quartier.

### 1️⃣ Vous exprimez vos priorités (6 questions)

Chaque réponse définit **ce qui compte le plus pour vous** :

- 🏠 **Budget** : Serré, modéré, confortable, ou illimité
- 🌆 **Ambiance** : Calme/vert, équilibré, animé, ou très animé
- 🏃 **Activité** : Peu sportif → très sportif
- 👶 **Statut** : Parent, étudiant, jeune actif, ou senior
- 🚗 **Transport** : Voiture, transports publics, ou vélo
- 🛒 **Priorité services** : Commerces, restaurants/bars, ou équilibre

### 2️⃣ Calcul des poids personnalisés

Chaque réponse ajuste l'**importance** (poids) des critères :

**Exemple : Budget serré**
- Prix du m² → **Poids 30** (ultra prioritaire !)
- Autres critères → poids standards (5-15)

**Exemple : Parent**
- Écoles → **+5 points** de poids
- Aires de jeux → **+5 points**

**Les poids s'additionnent** : si vous êtes parent + budget serré, Prix=30 ET Écoles=10

### 3️⃣ Normalisation des données (0 → 1)

Toutes les données sont normalisées entre 0 et 1 :

- **Prix** : 1 = pas cher, 0 = très cher (inversé car "bas prix = bon")
- **Transports** : 1 = beaucoup de stations, 0 = aucune
- **Bruit** : 1 = calme, 0 = bruyant

**Pourquoi ?** Pour comparer des choses différentes (m² verts vs nb de bars)

### 4️⃣ Score de compatibilité

Pour chaque quartier :

```
Score = Σ (Valeur_normalisée × Poids_critère)
```

**Exemple concret - Quartier X avec budget serré :**

```
Norm_Prix = 0.85 (pas cher)     → 0.85 × 30 = 25.5 points
Norm_Transports = 0.60          → 0.60 × 8  = 4.8 points
Norm_Écoles = 0.40              → 0.40 × 10 = 4.0 points
...
Total = 68/100
```

**Exemple - Quartier Y avec budget illimité :**

```
Norm_Prix = 0.10 (cher)         → 0.10 × 5  = 0.5 points (poids faible!)
Norm_Restaurants = 0.95         → 0.95 × 15 = 14.2 points
Norm_Bars = 0.90                → 0.90 × 15 = 13.5 points
...
Total = 82/100
```

### 5️⃣ Affichage visuel pur

Au lieu de vous dire "c'est bon" ou "c'est mauvais", l'app montre :

- **Couleur du quartier** : Rouge foncé (faible score) → Vert foncé (score élevé)
- **Barres bleues** : Votre niveau d'attente pour chaque critère
- **Barres violettes** : Ce que le quartier offre réellement

➡️ **Vous décidez** en comparant visuellement vos attentes vs la réalité

---

## Les 14 critères analysés

| Critère | Source | Impact |
|---------|--------|--------|
| 💰 Prix médian/m² | DVF (transactions réelles) | Inversé (bas = bien) |
| 🔇 Calme | Bruit ambiant dB | Inversé (bas = bien) |
| 🌳 Espaces verts | Surface m² | Direct |
| 🏪 Pharmacies | Points OSM | Direct |
| 🛒 Commerces | Points OSM | Direct |
| 🍽️ Restaurants | Points OSM | Direct |
| 🍺 Bars | Points OSM | Direct |
| 🚇 Transports | Stations métro/bus | Direct |
| 🚴 V'Lille | Stations vélo | Direct |
| 🏫 Écoles | Nombre total | Direct |
| 👶 Aires de jeux | Points OSM | Direct |
| ⚽ Complexes sportifs | Points OSM | Direct |
| 🅿️ Parkings | Points OSM | Direct |

---

## Points clés à retenir

✅ **L'algo ne juge pas** → il calcule la distance entre vos priorités et la réalité  
✅ **Budget serré = filtre radical** → poids x6 plus élevé que les autres critères  
✅ **Affichage neutre** → pas de "Excellent/Bon/Faible", juste des couleurs et barres  
✅ **Tous les critères affichés** → même ceux que vous n'avez pas priorisés (transparence totale)

---

## Formule complète

```python
Score_Final = Σ[i=1→14] (Norm_Critère_i × Poids_Critère_i)

où :
- Norm_Critère_i ∈ [0, 1] (normalisé min-max)
- Poids_Critère_i ∈ [5, 30] (selon vos réponses)
- Score_Final ∈ [0, 100] (normalisé relatif sur tous les quartiers)
```

**Normalisation relative** : Le score 100 = meilleur quartier selon VOS critères (pas un absolu)
