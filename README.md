# 🏙️ Caitlille - Trouvez votre quartier idéal à Lille

Application Streamlit interactive pour découvrir le quartier parfait à Lille selon vos préférences.

## ✨ Fonctionnalités

- 🎯 **Quiz personnalisé** : 10 questions sur vos préférences de vie
- 🗺️ **Carte interactive** : Visualisation des 110 quartiers IRIS avec scores de compatibilité
- 📊 **Algorithme de scoring** : Recommandations basées sur 13 critères normalisés
- 🏠 **Offres immobilières** : Scraping en temps réel depuis Immosens
- 🎨 **Design moderne** : Interface Tinder-style responsive

## 🚀 Installation

```bash
# Cloner le repository
git clone https://github.com/VOTRE-USERNAME/caitlille-streamlit.git
cd caitlille-streamlit

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 📦 Dépendances

- streamlit
- pandas
- openpyxl
- folium
- streamlit-folium
- requests
- beautifulsoup4

## 📁 Structure du projet

```
caitlille-streamlit/
├── app.py                          # Application principale
├── scoring_logic.py                # Algorithme de scoring
├── iris_v2_Lille.geojson          # Données géographiques
├── DATASET scores brut.xlsx        # Matrice de scoring
└── README.md
```

## 🎮 Utilisation

1. Répondez aux 10 questions en sélectionnant votre niveau d'intérêt (😐🙂😊🤩)
2. Découvrez vos 3 meilleurs quartiers recommandés
3. Explorez la carte colorée selon vos scores
4. Cliquez sur les quartiers pour voir les offres immobilières

## 🔧 Configuration

L'application nécessite le fichier `DATASET scores brut.xlsx` avec :
- Colonne `NOM_IRIS` : Nom des quartiers
- Colonne `CODE_IRIS` : Code IRIS
- Colonnes `Norm_*` : 13 critères normalisés (Bruit, Prix, Espaces verts, etc.)

## 📊 Critères de scoring

- Calme (Norm_Bruit)
- Prix abordable (Norm_Prix)
- Espaces verts (Norm_Surface_Verte_m2)
- Transports (Norm_Nb_Transports)
- Commerces (Norm_Nb_Commerces)
- Restaurants (Norm_Nb_Restaurants)
- Et 7 autres critères...

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📝 Licence

Ce projet est sous licence MIT.

## 👤 Auteur

Marin Lepine

## 🙏 Remerciements

- Données IRIS de Lille
- API Immosens pour les offres immobilières
- Streamlit pour le framework
