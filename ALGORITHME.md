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

Chaque réponse ajuste l'**importance** (poids) des critères. Voici **exactement** ce qui se passe :

#### 📋 **Q1 : Budget**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Serré (< 2000€/m²)** | Prix: **+30** (ultra prioritaire !), Services proximité: +2, Transports: +2 |
| **Modéré (2000-3000€/m²)** | Prix: **+18**, Services proximité: +2, Vie animée: +1 |
| **Confortable (3000-4000€/m²)** | Prix: **+10**, Vie animée: +2, Services proximité: +2 |
| **Aucune limite (> 4000€/m²)** | Vie animée: +3, Services proximité: +2, Calme: +1 |

#### 🌆 **Q2 : Ambiance**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Très calme, nature et verdure** | Calme: **+4**, Vie animée: **-3**, Services proximité: +1 |
| **Calme avec services de base** | Calme: **+3**, Services proximité: +3, Vie animée: -1 |
| **Dynamique et urbain** | Vie animée: **+3**, Transports: +2, Calme: **-2**, Services proximité: +2 |
| **Très animé (vie nocturne, bars)** | Vie animée: **+5**, Transports: +3, Calme: **-4** |

#### 🏠 **Q3 : Mode de vie**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Je cuisine, j'aime le calme** | Services proximité: +3, Calme: +3, Vie animée: -1 |
| **Équilibré (cuisine + sorties)** | Services proximité: +2, Vie animée: +2, Transports: +2 |
| **Je sors souvent au resto/bars** | Vie animée: **+4**, Transports: +2, Services proximité: +1 |
| **Vie nocturne intense** | Vie animée: **+5**, Transports: +3, Calme: **-3** |

#### 👤 **Q4 : Statut**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Parent (avec enfants)** | Famille (écoles/aires): **+5**, Calme: +3, Services proximité: +2, Vie animée: **-2** |
| **Étudiant(e)** | Vie animée: **+4**, Transports: +3, Calme: **-2**, Famille: **-3** |
| **Jeune actif(ve)** | Vie animée: +3, Transports: +2, Services proximité: +2 |
| **Senior / Retraité(e)** | Calme: **+4**, Services proximité: +3, Vie animée: **-2**, Transports: +1 |

#### 🚗 **Q5 : Transport**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Transports en commun uniquement** | Transports: **+5**, Services proximité: +2, Parking: **-3** |
| **Vélo / V'Lille** | Transports: +3, Services proximité: +2, Calme: +1, Parking: -2 |
| **Voiture personnelle** | Parking: **+4**, Services proximité: +2, Transports: -1 |
| **Mix voiture + transports** | Parking: +2, Transports: +2, Services proximité: +1 |

#### ⚽ **Q6 : Activité physique**

| Réponse | Impact sur les poids |
|---------|---------------------|
| **Très sportif (besoin d'équipements)** | Sport: **+4**, Calme: +2, Vie animée: +1 |
| **Sportif occasionnel** | Sport: +2, Calme: +1 |
| **Peu sportif** | Services proximité: +1, Vie animée: +1 |
| **Pas du tout** | Vie animée: +2, Sport: **-2** |

#### 💡 **Les poids s'additionnent !**

**Exemple : Parent + Budget serré + Calme**
- Prix: **30** (budget serré)
- Famille: **5** (parent)
- Calme: **3** (parent) + **4** (ambiance calme) = **7**
- Services proximité: **2** (budget) + **2** (parent) = **4**
- Vie animée: **-2** (parent) + **-3** (ambiance calme) = **-5** (ignoré, devient 0)

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
