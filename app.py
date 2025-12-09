import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
import os

# Import du système de scoring
try:
    from scoring_logic import charger_matrice, consolider_poids_utilisateur, recommander_quartiers
    SCORING_DISPONIBLE = True
except Exception as e:
    print(f"⚠️ Système de scoring non disponible: {e}")
    SCORING_DISPONIBLE = False

st.set_page_config(
    page_title="Où s'installer à Lille ?",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------
# Données (template)
# -----------------------

PLACES = [
    {
        "name": "Q1 : Ambiance de quartier",
        "emoji": "🏘️",
        "vibe": "Quel type d'ambiance ?",
        "tags": ["ambiance", "environnement", "style de vie"],
        "description": "Quelle ambiance de quartier te correspond le mieux ?",
        "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Paisible & proche de la nature", "Calme mais avec un peu de vie", "Urbain & dynamique", "Très animé (bars, sorties, nightlife)"]
    },
    {
        "name": "Q2 : Mode de déplacement",
        "emoji": "🚴",
        "vibe": "Comment te déplaces-tu ?",
        "tags": ["transport", "mobilité", "déplacement"],
        "description": "Quel est ton principal mode de déplacement au quotidien ?",
        "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Transports en commun", "Vélo / V'Lille", "Voiture", "À pied"]
    },
    {
        "name": "Q3 : Sensibilité au bruit",
        "emoji": "🔇",
        "vibe": "Le bruit te dérange ?",
        "tags": ["bruit", "calme", "nuisances"],
        "description": "Quelle est ta sensibilité au bruit environnant ?",
        "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Très sensible", "Un peu sensible", "Ça m'est égal", "J'aime quand ça bouge"]
    },
    {
        "name": "Q4 : Importance des espaces verts",
        "emoji": "🌳",
        "vibe": "Nature à proximité ?",
        "tags": ["parcs", "nature", "espaces verts"],
        "description": "Quelle importance accordes-tu aux espaces verts et parcs ?",
        "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Pas important", "Un peu important", "Très important", "Essentiel dans mon quotidien"]
    },
    {
        "name": "Q5 : Budget logement",
        "emoji": "💰",
        "vibe": "Quel est ton budget ?",
        "tags": ["prix", "budget", "loyer"],
        "description": "Quel budget peux-tu consacrer à ton logement ?",
        "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Serré", "Modéré", "Confortable", "Flexible"]
    },
    {
        "name": "Q6 : Habitudes alimentaires",
        "emoji": "🍽️",
        "vibe": "Comment manges-tu ?",
        "tags": ["cuisine", "restaurants", "alimentation"],
        "description": "Quelles sont tes habitudes pour les repas ?",
        "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Je cuisine souvent", "Je cuisine de temps en temps", "Je cuisine rarement", "Je mange beaucoup dehors"]
    },
    {
        "name": "Q7 : Services de proximité",
        "emoji": "🏪",
        "vibe": "Services essentiels ?",
        "tags": ["commerces", "services", "proximité"],
        "description": "Quels services sont importants pour toi à proximité ?",
        "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Pharmacie", "Commerces / supermarchés", "Restaurants / cafés", "Pas particulièrement"]
    },
    {
        "name": "Q8 : Enfants",
        "emoji": "👶",
        "vibe": "As-tu des enfants ?",
        "tags": ["famille", "enfants", "écoles"],
        "description": "As-tu des enfants ou prévois-tu d'en avoir ?",
        "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Oui", "Pas encore mais bientôt", "Non", "Jamais"]
    },
    {
        "name": "Q9 : Sécurité et tranquillité",
        "emoji": "🔒",
        "vibe": "Sécurité importante ?",
        "tags": ["sécurité", "tranquillité", "calme"],
        "description": "Quelle importance pour la sécurité et la tranquillité ?",
        "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Très important", "Assez important", "Peu important", "Pas vraiment"]
    },
    {
        "name": "Q10 : Rythme de vie",
        "emoji": "⚡",
        "vibe": "Quel est ton rythme ?",
        "tags": ["rythme", "lifestyle", "activité"],
        "description": "Quel est ton rythme de vie au quotidien ?",
        "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
        "options": ["Plutôt tranquille", "Relax & chill", "Dynamique", "Très actif / je sors souvent"]
    },
]

TOTAL = len(PLACES)


# -----------------------
# Styles globaux - Tinder Design + iOS
# -----------------------

st.markdown(
    """
    <style>
        :root {
            --accent-primary: #ff5a5f;     /* Tinder rouge chaud */
            --accent-secondary: #ff7a7d;   /* Orange chaud */
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #121212;
            --text-secondary: #6c6c6c;
            --divider: #e8e8e8;
            --success: #66bb6a;            /* Vert accent pour like */
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 100%);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        }

        /* Masquer les éléments Streamlit non pertinents */
        #MainMenu, footer {
            display: none;
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            max-width: 440px !important;
            padding-top: 24px !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-bottom: 32px !important;
        }

        /* Header épuré iOS */
        .app-header {
            text-align: center;
            padding: 24px 20px 16px 20px;
            border-bottom: 1px solid var(--divider);
            margin-bottom: 24px;
        }

        .app-title {
            font-size: 42px;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .app-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
            font-weight: 400;
            line-height: 1.6;
        }

        /* Barre de progression - super épurée */
        .progress-section {
            padding: 16px 20px;
            margin-bottom: 12px;
        }

        .progress-label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: block;
        }

        .progress-bar {
            height: 3px;
            background: var(--divider);
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        /* Carte Tinder - le cœur du design */
        .swipe-card {
            background: var(--bg-primary);
            border-radius: 28px;
            overflow: hidden;
            margin: 0 12px 20px 12px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--divider);
            animation: cardAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
        }

        @keyframes cardAppear {
            from {
                opacity: 0;
                transform: translateY(32px) scale(0.94);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Pulse effect quand on hover */
        .swipe-card:hover {
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12);
        }

        .swipe-image-container {
            position: relative;
            width: 100%;
            height: 360px;
            overflow: hidden;
            background: var(--bg-secondary);
        }

        .swipe-image-bg {
            width: 100%;
            height: 100%;
            background-size: cover;
            background-position: center;
            filter: brightness(0.95);
            transition: transform 0.3s ease;
        }

        .swipe-card:hover .swipe-image-bg {
            transform: scale(1.02);
        }

        .swipe-image-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(
                to top,
                rgba(0, 0, 0, 0.28),
                rgba(0, 0, 0, 0.08) 30%,
                transparent 60%
            );
            z-index: 2;
        }

        .swipe-image-content {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 24px 20px;
            z-index: 3;
            display: flex;
            align-items: flex-end;
            gap: 14px;
        }

        .swipe-emoji-large {
            font-size: 48px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
        }

        .swipe-title-wrapper {
            flex: 1;
        }

        .swipe-name {
            font-size: 32px;
            font-weight: 700;
            color: white;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            margin-bottom: 4px;
        }

        .swipe-vibe {
            font-size: 16px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
        }

        /* Contenu de la carte */
        .swipe-body {
            padding: 20px;
        }

        .swipe-description {
            font-size: 17px;
            line-height: 1.7;
            color: var(--text-primary);
            margin-bottom: 16px;
        }

        .swipe-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 4px;
        }

        .swipe-tag {
            padding: 8px 14px;
            background: #ff5a5f10;
            border: 1px solid #ff5a5f30;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            color: var(--accent-primary);
            white-space: nowrap;
        }

        /* Actions (boutons) - Tinder Style */
        .swipe-actions {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            padding: 24px 20px 28px 20px;
            background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1));
        }

        /* Bouton DISLIKE */
        .action-btn-dislike {
            width: 60px;
            height: 60px;
            min-width: 60px;
            border-radius: 50%;
            background: white;
            border: 2px solid #d9d9d9;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            position: relative;
            overflow: hidden;
        }

        .action-btn-dislike::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle, rgba(0, 0, 0, 0.05), transparent);
            opacity: 0;
            transition: opacity 0.25s ease;
        }

        .action-btn-dislike:hover {
            border-color: #bbb;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
            transform: scale(1.05);
        }

        .action-btn-dislike:active {
            transform: scale(0.92);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .action-btn-dislike:active::before {
            opacity: 1;
        }

        /* Bouton LIKE */
        .action-btn-like {
            width: 68px;
            height: 68px;
            min-width: 68px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 8px 24px rgba(255, 90, 95, 0.4);
            position: relative;
            overflow: hidden;
        }

        .action-btn-like::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.3), transparent);
            opacity: 0;
            transition: opacity 0.25s ease;
        }

        .action-btn-like:hover {
            transform: scale(1.08);
            box-shadow: 0 12px 32px rgba(255, 90, 95, 0.5);
        }

        .action-btn-like:active {
            transform: scale(0.92);
            box-shadow: 0 4px 16px rgba(255, 90, 95, 0.3);
        }

        .action-btn-like:active::before {
            opacity: 1;
        }

        /* Bouton Recommencer - stylisé */
        [data-testid="stButton"] > :first-child > button {
            font-size: 18px !important;
            padding: 16px 24px !important;
            border-radius: 28px !important;
            font-weight: 600 !important;
        }

        /* Style des 4 boutons de rating */
        [data-testid="stButton"] button {
            border-radius: 16px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 18px 10px !important;
            border: none !important;
            transition: all 0.2s ease !important;
            height: 120px !important;
            width: 100% !important;
            white-space: pre-line !important;
            line-height: 1.4 !important;
        }

        /* Bouton 1: Pas intéressé (gris) */
        [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] button {
            background: #f3f4f6 !important;
            color: #6b7280 !important;
            border: 2px solid #d1d5db !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] button:hover {
            background: #e5e7eb !important;
            border-color: #9ca3af !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.15) !important;
        }

        /* Bouton 2: Moyen intéressé (orange clair) */
        [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] button {
            background: #fef3c7 !important;
            color: #d97706 !important;
            border: 2px solid #fcd34d !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] button:hover {
            background: #fde68a !important;
            border-color: #fbbf24 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(217, 119, 6, 0.2) !important;
        }

        /* Bouton 3: Intéressé (vert clair) */
        [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stButton"] button {
            background: #d1fae5 !important;
            color: #059669 !important;
            border: 2px solid #6ee7b7 !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stButton"] button:hover {
            background: #a7f3d0 !important;
            border-color: #34d399 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
        }

        /* Bouton 4: Très intéressé (vert foncé) */
        [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stButton"] button {
            background: linear-gradient(135deg, #10b981, #059669) !important;
            color: white !important;
            border: none !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stButton"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3) !important;
        }

        /* Fin de quiz */
        .results-container {
            padding: 20px;
            text-align: center;
        }

        .results-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            color: var(--accent-primary);
        }

        .results-subtitle {
            font-size: 15px;
            color: var(--text-secondary);
            margin-bottom: 32px;
        }

        .results-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }

        .results-card {
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 20px;
            text-align: left;
            border: 1px solid var(--divider);
        }

        .results-card-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .results-item {
            font-size: 14px;
            color: var(--text-primary);
            margin-bottom: 8px;
            font-weight: 500;
        }

        .results-empty {
            font-size: 13px;
            color: var(--text-secondary);
            font-style: italic;
        }

        /* Boutons principaux */
        .primary-btn {
            width: 100%;
            padding: 14px 20px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            border-radius: 26px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            margin-bottom: 12px;
            letter-spacing: 0.3px;
            box-shadow: 0 6px 16px rgba(255, 90, 95, 0.25);
        }

        .primary-btn:active {
            transform: scale(0.98);
        }

        .secondary-btn {
            width: 100%;
            padding: 14px 20px;
            background: white;
            color: var(--accent-primary);
            border: 2px solid var(--accent-primary);
            border-radius: 26px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            margin-bottom: 12px;
            letter-spacing: 0.3px;
        }

        .secondary-btn:active {
            background: #ff5a5f10;
            transform: scale(0.98);
        }

        /* Système 4 boutons Fruitz */
        .buttons-container-4 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 12px;
            padding: 20px 12px;
            background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1));
        }

        .rating-btn {
            padding: 14px 8px;
            border: none;
            border-radius: 14px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            letter-spacing: 0.2px;
        }

        .rating-btn .emoji {
            font-size: 24px;
        }

        /* Bouton 1: Je veux carrément pas (rouge sombre) */
        .rating-btn-1 {
            background: #fee4e3;
            color: #c1261f;
            border: 1.5px solid #f5a9a3;
        }

        .rating-btn-1:hover {
            background: #fdd2cd;
            border-color: #ff8a7c;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(193, 38, 31, 0.2);
        }

        .rating-btn-1:active {
            transform: scale(0.95);
        }

        /* Bouton 2: Je veux pas (orange) */
        .rating-btn-2 {
            background: #ffecd1;
            color: #d97706;
            border: 1.5px solid #ffd4a3;
        }

        .rating-btn-2:hover {
            background: #ffd9b3;
            border-color: #ffb347;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(217, 119, 6, 0.2);
        }

        .rating-btn-2:active {
            transform: scale(0.95);
        }

        /* Bouton 3: Je veux (vert clair) */
        .rating-btn-3 {
            background: #d4f8d4;
            color: #16a34a;
            border: 1.5px solid #a5e6a5;
        }

        .rating-btn-3:hover {
            background: #b8f0b8;
            border-color: #6ee876;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(22, 163, 74, 0.2);
        }

        .rating-btn-3:active {
            transform: scale(0.95);
        }

        /* Bouton 4: Je veux carrément (vert foncé) */
        .rating-btn-4 {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            border: none;
        }

        .rating-btn-4:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(16, 185, 129, 0.3);
        }

        .rating-btn-4:active {
            transform: scale(0.95);
        }

        /* Responsive iOS */
        @media (max-width: 600px) {
            .block-container {
                max-width: 100% !important;
            }

            .swipe-card {
                margin: 0 8px 20px 8px;
            }

            .swipe-image-container {
                height: 340px;
            }

            .app-title {
                font-size: 28px;
            }
        }

        /* Animation spinner pour reset */
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .spin-animation {
            display: inline-block;
            animation: spin 0.6s linear;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------
# État de l'application
# -----------------------

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "liked" not in st.session_state:
    st.session_state.liked = []

if "disliked" not in st.session_state:
    st.session_state.disliked = []

if "reponses" not in st.session_state:
    st.session_state.reponses = {}

if "matrice_data" not in st.session_state and SCORING_DISPONIBLE:
    st.session_state.matrice_data = charger_matrice()

if "top_quartiers" not in st.session_state:
    st.session_state.top_quartiers = None

if "tous_scores" not in st.session_state:
    st.session_state.tous_scores = None

if "selected_quartier" not in st.session_state:
    st.session_state.selected_quartier = None


def next_question():
    """Passe à la question suivante."""
    st.session_state.current_index = min(TOTAL, st.session_state.current_index + 1)
    
    # Si on a fini toutes les questions, calculer les recommandations
    if st.session_state.current_index == TOTAL and SCORING_DISPONIBLE:
        if st.session_state.matrice_data is not None:
            poids = consolider_poids_utilisateur(st.session_state.reponses)
            # Calculer le top 3
            st.session_state.top_quartiers = recommander_quartiers(
                poids, 
                st.session_state.matrice_data, 
                n_recommandations=3
            )
            # Calculer TOUS les scores pour la carte
            st.session_state.tous_scores = recommander_quartiers(
                poids, 
                st.session_state.matrice_data, 
                n_recommandations=999  # Tous les quartiers
            )


def enregistrer_reponse(option_texte):
    """Enregistre la réponse de l'utilisateur pour la question actuelle."""
    # Déterminer le poids selon la position du bouton (1-4)
    place = PLACES[st.session_state.current_index]
    if 'options' in place:
        position = place['options'].index(option_texte) if option_texte in place['options'] else 0
        # Position 0 = poids 1, Position 1 = poids 2, etc.
        poids = position + 1
    else:
        poids = 2  # Poids par défaut
    
    # Stocker l'option et le poids
    st.session_state.reponses[st.session_state.current_index] = {
        'option': option_texte,
        'poids': poids
    }
    
    next_question()
    st.rerun()  # Force le rechargement immédiat


@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def scraper_immosens(secteur="Vieux Lille", max_annonces=10):
    """Scrape les annonces immobilières depuis Immosens"""
    BASE_URL = "https://www.immosens.fr"
    SEARCH_URL = "https://www.immosens.fr/produits.php"
    
    params = {
        'valid': 'ok',
        'transac': 'L',
        'type[]': '*',
        'ville': 'Lille',
        'budget_min': '200',
        'budget_max': '',
        'rayon': '0',
        'ref': '',
        'secteur': secteur,
        'sous_type': '*',
        'nb_pieces': '*'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        main_listing = soup.find('div', class_='main-listing')
        
        if not main_listing:
            return []
        
        listings = main_listing.find_all('div', class_='col-lg-4')[:max_annonces]
        annonces = []
        
        for col in listings:
            try:
                product = col.find('div', class_='product-container')
                if not product:
                    continue
                
                annonce = {}
                
                # Type de bien
                type_elem = product.find('h2', class_='type')
                annonce['type'] = type_elem.get_text(strip=True) if type_elem else 'Appartement'
                
                # Prix
                prix_elem = product.find('span', class_='prix')
                annonce['prix'] = prix_elem.get_text(strip=True) if prix_elem else 'Prix sur demande'
                
                # Localisation
                loc_elem = product.find('span', class_='lieu')
                annonce['localisation'] = loc_elem.get_text(strip=True) if loc_elem else secteur
                
                # Description
                desc_elem = product.find('span', class_='description')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                annonce['description'] = description
                
                # Extraction surface et pièces
                surface_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', description)
                annonce['surface'] = surface_match.group(1).replace(',', '.') + ' m²' if surface_match else 'N/A'
                
                type_match = re.search(r'T(\d+)', description, re.IGNORECASE)
                if type_match:
                    annonce['pieces'] = f"T{type_match.group(1)}"
                else:
                    pieces_match = re.search(r'(\d+)\s*pièces?', description, re.IGNORECASE)
                    annonce['pieces'] = f"{pieces_match.group(1)} pièces" if pieces_match else 'N/A'
                
                # Image
                img_elem = product.find('img')
                if img_elem and img_elem.get('src'):
                    annonce['image'] = urljoin(BASE_URL, img_elem['src'])
                else:
                    annonce['image'] = 'https://via.placeholder.com/400x300?text=Pas+d\'image'
                
                # Lien
                link_elem = product.find('a', class_='link_product')
                if link_elem and link_elem.get('href'):
                    annonce['lien'] = urljoin(BASE_URL, link_elem['href'])
                else:
                    annonce['lien'] = '#'
                
                annonces.append(annonce)
                
            except Exception as e:
                continue
        
        return annonces
        
    except Exception as e:
        # En cas d'erreur, retourner des données par défaut
        return []


# -----------------------
# Layout principal iOS-style
# -----------------------

# Espace du haut
st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

# Barre de progression
progress_pct = (st.session_state.current_index) / TOTAL if TOTAL else 0
st.markdown(
    f"""
    <div class="progress-section">
        <span class="progress-label">Exploration · {min(st.session_state.current_index + 1, TOTAL)} / {TOTAL}</span>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_pct * 100}%"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.current_index < TOTAL:
    place = PLACES[st.session_state.current_index]

    # Carte Tinder
    st.markdown(
        f"""
        <div class="swipe-card">
            <div class="swipe-image-container" style="background-image: url('{place['image']}'); background-size: cover; background-position: center;">
                <div class="swipe-image-bg"></div>
                <div class="swipe-image-overlay"></div>
                <div class="swipe-image-content">
                    <div class="swipe-emoji-large">{place['emoji']}</div>
                    <div class="swipe-title-wrapper">
                        <div class="swipe-name">{place['name']}</div>
                        <div class="swipe-vibe">{place['vibe']}</div>
                    </div>
                </div>
            </div>
            <div class="swipe-body">
                <div class="swipe-description">{place['description']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Boutons avec les options de la question
    if 'options' in place and len(place['options']) >= 4:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(f"😐\n{place['options'][0]}", key=f"btn1_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse(place['options'][0])
        with col2:
            if st.button(f"🙂\n{place['options'][1]}", key=f"btn2_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse(place['options'][1])
        with col3:
            if st.button(f"😊\n{place['options'][2]}", key=f"btn3_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse(place['options'][2])
        with col4:
            if st.button(f"🤩\n{place['options'][3]}", key=f"btn4_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse(place['options'][3])
    else:
        # Fallback si pas d'options
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("😐\nPas intéressé", key=f"btn1_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse("😐 Pas intéressé")
        with col2:
            if st.button("🙂\nMoyen", key=f"btn2_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse("🙂 Moyen")
        with col3:
            if st.button("😊\nIntéressé", key=f"btn3_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse("😊 Intéressé")
        with col4:
            if st.button("🤩\nTrès intéressé", key=f"btn4_{st.session_state.current_index}", use_container_width=True):
                enregistrer_reponse("🤩 Très intéressé")

else:
    # Fin du quiz - Résultats
    st.markdown(
        """
        <div class="results-container">
            <div class="results-title">✨ C'est noté !</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Afficher un message si le scoring est disponible ou non
    if st.session_state.top_quartiers is not None and not st.session_state.top_quartiers.empty:
        st.success(f"🎯 **{len(st.session_state.top_quartiers)} quartiers** correspondent à vos préférences !")
        
        # Afficher le top 3 des quartiers avec leurs scores
        st.markdown("### 🏆 Vos meilleurs quartiers :")
        for idx, row in st.session_state.top_quartiers.iterrows():
            score_color = "#10b981" if row['Score_Max'] > 60 else "#ff5a5f" if row['Score_Max'] < 40 else "#fbbf24"
            st.markdown(
                f"""
                <div style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid {score_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; color: #121212; font-size: 18px;">🏘️ {row['NOM_IRIS']}</h3>
                            <p style="margin: 4px 0 0 0; color: #6c6c6c; font-size: 14px;">Score de compatibilité</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 32px; font-weight: bold; color: {score_color};">{row['Score_Max']:.0f}</div>
                            <div style="font-size: 12px; color: #6c6c6c;">/100</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
    elif not SCORING_DISPONIBLE or st.session_state.matrice_data is None:
        st.info("ℹ️ Mode exploration : Les scores affichés sont indicatifs. Pour des recommandations personnalisées, ajoutez le fichier `DATASET scores brut.xlsx`.")
    else:
        st.warning("⚠️ Aucune recommandation n'a pu être calculée.")

    # Quiz terminé - Afficher la carte IRIS de Lille

    # Charger le GeoJSON
    with open("iris_v2_Lille.geojson") as f:
        geojson_data = json.load(f)

    # Créer la carte Folium centrée sur la Place de la République
    m = folium.Map(
        location=[50.6300, 3.2600],  # Place de la République, Lille
        zoom_start=13,
        tiles="CartoDB positron",
    )

    # Fonction pour générer une couleur basée sur un score normalisé (0-100)
    def get_color_from_score(score, min_score, max_score):
        """Normalise le score entre min et max, puis génère la couleur"""
        # Normaliser le score entre 0 et 100
        if max_score > min_score:
            normalized = ((score - min_score) / (max_score - min_score)) * 100
        else:
            normalized = 50  # Si tous les scores sont identiques
        
        # Générer la couleur : rouge (0) -> jaune (50) -> vert (100)
        if normalized < 50:
            # Rouge à Jaune (0-50)
            ratio = normalized / 50
            r = 255
            g = int(255 * ratio)  # 0 à 255
            b = 0
        else:
            # Jaune à Vert (50-100)
            ratio = (normalized - 50) / 50
            r = int(255 * (1 - ratio))  # 255 à 0
            g = 255
            b = 0
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # Créer des dictionnaires de scores par CODE_IRIS et NOM_IRIS
    scores_par_code = {}
    scores_par_nom = {}
    
    if st.session_state.tous_scores is not None and not st.session_state.tous_scores.empty:
        # Utiliser TOUS les scores calculés
        for _, row in st.session_state.tous_scores.iterrows():
            scores_par_nom[row['NOM_IRIS']] = row['Score_Max']
            # Aussi stocker par CODE_IRIS si disponible
            if 'IRIS_Meilleur' in row:
                scores_par_code[str(row['IRIS_Meilleur'])] = row['Score_Max']
    elif st.session_state.top_quartiers is not None and not st.session_state.top_quartiers.empty:
        # Fallback sur le top 3
        for _, row in st.session_state.top_quartiers.iterrows():
            scores_par_nom[row['NOM_IRIS']] = row['Score_Max']
            if 'IRIS_Meilleur' in row:
                scores_par_code[str(row['IRIS_Meilleur'])] = row['Score_Max']
    
    # Si on a les scores mais pas de mapping CODE_IRIS, charger depuis matrice
    if scores_par_nom and not scores_par_code and st.session_state.matrice_data is not None:
        for _, row in st.session_state.matrice_data.iterrows():
            nom = row['NOM_IRIS']
            if nom in scores_par_nom:
                code = str(row['CODE_IRIS'])
                scores_par_code[code] = scores_par_nom[nom]
    
    # Calculer les scores min/max pour normaliser les couleurs
    all_scores = list(scores_par_code.values()) + list(scores_par_nom.values())
    if all_scores:
        min_score = min(all_scores)
        max_score = max(all_scores)
    else:
        min_score = 0
        max_score = 100

    # Ajouter les polygones IRIS avec scores calculés ou aléatoires
    for feature in geojson_data['features']:
        nom_iris = feature['properties'].get('nom_iris', 'N/A')
        code_iris_geo = feature['properties'].get('code_iris', 'N/A')
        
        # Essayer d'abord par code_iris, puis par nom_iris
        score = None
        if code_iris_geo in scores_par_code:
            score = scores_par_code[code_iris_geo]
        elif nom_iris in scores_par_nom:
            score = scores_par_nom[nom_iris]
        else:
            # Mode exploration : score aléatoire
            score = (hash(code_iris_geo) % 100) + 1
        
        # Obtenir la couleur basée sur le score normalisé
        color = get_color_from_score(score, min_score, max_score)
        
        folium.GeoJson(
            {
                "type": "Feature",
                "geometry": feature['geometry'],
                "properties": feature['properties']
            },
            style_function=lambda x, current_color=color: {
                "fillColor": current_color,
                "color": "#d63d42",
                "weight": 1.5,
                "opacity": 0.8,
                "fillOpacity": 0.6,
            },
            highlight_function=lambda x, current_color=color: {
                "fillColor": current_color,
                "color": "#ff5a5f",
                "weight": 3,
                "opacity": 1,
                "fillOpacity": 0.8,
            },
            tooltip=folium.Tooltip(
                f'<div style="background-color: {color}; color: white; font-weight: bold; border: none; padding: 4px 8px; border-radius: 4px;">Score: {score:.0f}</div>',
                sticky=False
            ),
        ).add_to(m)

    # Afficher la carte dans Streamlit
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    
    # Afficher la carte avec hauteur personnalisée et récupérer les interactions
    map_result = st_folium(m, width=2600, height=500)

    # --- Interactions: détecter clic et trouver le sous-quartier IRIS cliqué ---
    def _point_in_ring(x, y, ring):
        # Ray casting algorithm (ring is list of [lon, lat])
        inside = False
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
            )
            if intersect:
                inside = not inside
            j = i
        return inside

    def find_feature_by_point(lon, lat, features):
        for feature in features:
            geom = feature.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])
            if gtype == "Polygon":
                for ring in coords:
                    if _point_in_ring(lon, lat, ring):
                        return feature
            elif gtype == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        if _point_in_ring(lon, lat, ring):
                            return feature
        return None

    # Détection de clic sur la carte
    clicked = None
    if isinstance(map_result, dict):
        clicked = map_result.get("last_clicked") or map_result.get("lastClick") or map_result.get("last_object_clicked")

    if clicked and isinstance(clicked, dict):
        # extract lat/lng robustly
        lat = clicked.get("lat") or clicked.get("latitude") or clicked.get("y")
        lon = clicked.get("lng") or clicked.get("lon") or clicked.get("longitude") or clicked.get("x")
        try:
            lat = float(lat)
            lon = float(lon)
            selected_feature = find_feature_by_point(lon, lat, geojson_data.get("features", []))
            if selected_feature:
                props = selected_feature.get("properties", {})
                nom_iris = props.get("nom_iris", "Zone")
                # Mettre à jour le quartier sélectionné seulement si c'est un nouveau quartier
                if st.session_state.selected_quartier != nom_iris:
                    st.session_state.selected_quartier = nom_iris
                    st.rerun()
        except Exception:
            pass

    # Afficher les détails du quartier sélectionné
    if st.session_state.selected_quartier:
        nom_iris = st.session_state.selected_quartier

        st.markdown("---")
        st.markdown(f"### 📍 {nom_iris}")
        
        # Afficher l'explication du score si disponible
        if st.session_state.tous_scores is not None and not st.session_state.tous_scores.empty:
            quartier_data = st.session_state.tous_scores[st.session_state.tous_scores['NOM_IRIS'] == nom_iris]
            if not quartier_data.empty:
                score = quartier_data.iloc[0]['Score_Max']
                
                # Calculer les détails du scoring
                if st.session_state.matrice_data is not None and len(st.session_state.reponses) > 0:
                    poids = consolider_poids_utilisateur(st.session_state.reponses)
                    
                    # Trouver la ligne correspondante dans la matrice
                    quartier_row = st.session_state.matrice_data[st.session_state.matrice_data['NOM_IRIS'] == nom_iris]
                    if not quartier_row.empty:
                        # Calculer la contribution de chaque critère
                        contributions = {}
                        total_poids = sum(poids.values())
                        
                        # Traductions françaises des critères
                        traductions = {
                            'Norm_Bruit': '🔇 Calme (peu de bruit)',
                            'Norm_Prix': '💰 Prix abordable',
                            'Norm_Surface_Verte_m2': '🌳 Espaces verts',
                            'Norm_Nb_Pharmacies': '💊 Pharmacies',
                            'Norm_Nb_Commerces': '🏪 Commerces',
                            'Norm_Nb_Restaurants': '🍽️ Restaurants',
                            'Norm_Nb_Transports': '🚇 Transports en commun',
                            'Norm_Nb_VLille': '🚴 Stations V\'Lille',
                            'Norm_Nb_ParcsEnfants': '👶 Aires de jeux',
                            'Norm_Nb_ComplexesSportifs': '⚽ Complexes sportifs',
                            'Norm_Nb_Ecoles': '🏫 Écoles',
                            'Norm_Nb_Bars': '🍺 Bars & vie nocturne',
                            'Norm_Nb_Parkings': '🅿️ Parkings',
                        }
                        
                        for critere, poids_critere in poids.items():
                            if poids_critere > 0 and critere in quartier_row.columns:
                                valeur_normalisee = quartier_row.iloc[0][critere]
                                contribution = (valeur_normalisee * poids_critere / total_poids) * 100
                                # Utiliser la traduction française avec emoji
                                nom_francais = traductions.get(critere, critere.replace('Norm_', '').replace('_', ' '))
                                contributions[nom_francais] = contribution
                        
                        # Afficher l'explication du score
                        score_color = "#10b981" if score > 60 else "#ff5a5f" if score < 40 else "#fbbf24"
                        st.markdown(
                            f"""
                            <div style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid {score_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0; color: #121212;">💯 Score de compatibilité</h4>
                                    <div style="font-size: 24px; font-weight: bold; color: {score_color};">{score:.0f}/100</div>
                                </div>
                                <p style="color: #6c6c6c; font-size: 14px; margin: 0;">Ce score est calculé en fonction de vos préférences. Voici comment il se décompose :</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Afficher les top 5 critères les plus importants
                        if contributions:
                            top_contributions = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:5]
                            st.markdown("**🎯 Principaux facteurs influençant ce score :**")
                            st.caption(f"_Poids total appliqué : {sum(poids.values())} points répartis sur {len([p for p in poids.values() if p > 0])} critères_")
                            for nom_critere, contribution in top_contributions:
                                bar_width = min(contribution, 100)  # Cap à 100%
                                st.markdown(
                                    f"""
                                    <div style="margin-bottom: 8px;">
                                        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                                            <span style="color: #121212;">{nom_critere}</span>
                                            <span style="color: #6c6c6c;">{contribution:.1f} pts</span>
                                        </div>
                                        <div style="background: #f3f4f6; height: 6px; border-radius: 3px; overflow: hidden;">
                                            <div style="background: {score_color}; height: 100%; width: {bar_width}%; transition: width 0.3s ease;"></div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
        
        # Section annonces immobilières
        st.markdown("---")
        st.markdown(f"### 🏠 Offres disponibles")
        
        # Scraper les annonces réelles
        with st.spinner("Chargement des offres..."):
            annonces = scraper_immosens(secteur=nom_iris, max_annonces=10)
        
        if not annonces:
            st.info(f"Aucune offre trouvée pour {nom_iris}. Essayez un autre quartier.")
        else:
            # Carrousel horizontal avec plusieurs offres d'annonces
            st.markdown(
                """
                <style>
                    .carousel-container {
                        display: flex;
                        gap: 14px;
                        overflow-x: auto;
                        padding: 12px 0;
                        margin-bottom: 16px;
                        scroll-behavior: smooth;
                    }
                    .carousel-container::-webkit-scrollbar {
                        height: 4px;
                    }
                    .carousel-container::-webkit-scrollbar-track {
                        background: #f0f0f0;
                        border-radius: 2px;
                    }
                    .carousel-container::-webkit-scrollbar-thumb {
                        background: #ccc;
                        border-radius: 2px;
                    }
                    .carousel-container::-webkit-scrollbar-thumb:hover {
                        background: #999;
                    }
                    .listing-card {
                        flex: 0 0 320px;
                        border: 1px solid #e8e8e8;
                        padding: 12px;
                        border-radius: 10px;
                        background: white;
                        cursor: pointer;
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                    }
                    .listing-card:hover {
                        transform: translateY(-4px);
                        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                    }
                    .listing-image {
                        width: 100%;
                        height: 160px;
                        border-radius: 8px;
                        background-size: cover;
                        background-position: center;
                        margin-bottom: 10px;
                    }
                    .listing-title {
                        font-weight: 700;
                        margin-bottom: 6px;
                        color: #121212;
                    }
                    .listing-location {
                        color: #6c6c6c;
                        font-size: 13px;
                        margin-bottom: 8px;
                    }
                    .listing-price {
                        font-size: 16px;
                        font-weight: 800;
                        margin-bottom: 8px;
                    }
                    .listing-note {
                        margin-top: 8px;
                        font-size: 13px;
                        color: #6c6c6c;
                    }
                    .listing-link {
                        display: inline-block;
                        margin-top: 8px;
                        padding: 6px 12px;
                        background: #ff5a5f;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 600;
                    }
                    .listing-link:hover {
                        background: #ff7a7d;
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Générer le HTML du carrousel avec les vraies données
            cards_html = ""
            for annonce in annonces:
                details = f"{annonce['pieces']}" if annonce['pieces'] != 'N/A' else ""
                if annonce['surface'] != 'N/A':
                    details += f" • {annonce['surface']}"
                
                cards_html += f"""<div class="listing-card">
    <div class="listing-image" style="background-image: url('{annonce['image']}');"></div>
    <div class="listing-title">{annonce['type']}</div>
    <div class="listing-location">{annonce['localisation']} {details}</div>
    <div class="listing-price" style="color: #ff5a5f;">{annonce['prix']}</div>
    <a href="{annonce['lien']}" target="_blank" class="listing-link">Voir l'offre</a>
</div>"""
            
            listings_html = f'<div class="carousel-container">{cards_html}</div>'

            st.markdown(listings_html, unsafe_allow_html=True)
            st.markdown("\n---\n")

    st.markdown("---")

    # Bouton Recommencer
    def restart_game():
        st.session_state.current_index = 0
        st.session_state.liked = []
        st.session_state.disliked = []
        st.session_state.reponses = {}
        st.session_state.top_quartiers = None
    
    st.markdown(
        """
        <style>
        .restart-button-center {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 16px 0;
        }
        .restart-button-center [data-testid="stButton"] {
            width: auto !important;
        }
        </style>
        <div class="restart-button-center">
        """,
        unsafe_allow_html=True,
    )
    
    st.button("↻", use_container_width=False, on_click=restart_game)
    
    st.markdown("</div>", unsafe_allow_html=True)


# Fin de l'app
