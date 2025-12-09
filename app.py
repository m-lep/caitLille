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
    from scoring_logic_v2 import charger_matrice, consolider_poids_utilisateur, recommander_quartiers, calculer_tous_scores
    SCORING_DISPONIBLE = True
    print("✅ Nouveau système de scoring V2 chargé")
except Exception as e:
    try:
        from scoring_logic import charger_matrice, consolider_poids_utilisateur, recommander_quartiers
        SCORING_DISPONIBLE = True
        calculer_tous_scores = None
        print("⚠️ Ancien système de scoring chargé (fallback)")
    except Exception as e2:
        print(f"⚠️ Système de scoring non disponible: {e2}")
        SCORING_DISPONIBLE = False

# Import des nouvelles questions
try:
    from nouvelles_questions import NOUVELLES_QUESTIONS
    print("✅ Nouvelles questions (6 questions optimisées) chargées")
except:
    NOUVELLES_QUESTIONS = None
    print("⚠️ Utilisation des questions par défaut (10 questions)")

st.set_page_config(
    page_title="Où s'installer à Lille ?",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------
# Données (template)
# -----------------------

# Utiliser les nouvelles questions si disponibles, sinon garder les 10 questions
if NOUVELLES_QUESTIONS is not None:
    PLACES = NOUVELLES_QUESTIONS
else:
    # Questions par défaut (10 questions)
    PLACES = [
        {
            "name": "Q1 : Ambiance de Quartier Idéale",
            "emoji": "🏘️",
            "vibe": "Urbain, Nature, Calme, Fête ?",
            "tags": ["ambiance", "bruit", "nature"],
            "description": "Quelle ambiance de quartier te correspond le mieux ?",
            "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Très animé (nightlife)", "Urbain & dynamique", "Calme avec commerces", "Paisible & résidentiel"]
        },
        {
            "name": "Q2 : Flexibilité Budgétaire",
            "emoji": "💰",
            "vibe": "Quel est ton budget logement ?",
            "tags": ["prix", "budget", "loyer"],
            "description": "Quel budget peux-tu consacrer à ton logement ?",
            "image": "https://uploads.lebonbonfr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Très serré", "Modéré", "Confortable", "Flexible"]
        },
        {
            "name": "Q3 : Exigence en Proximité des Services",
            "emoji": "🏪",
            "vibe": "Tout doit être accessible à pied ?",
            "tags": ["commerces", "services", "santé", "proximité"],
            "description": "Quels services sont importants pour toi à proximité immédiate ?",
            "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Services médicaux (Pharmacie/Santé)", "Hypermarchés", "Restauration", "Hyper-proximité totale (tout à pied)"]
        },
        {
            "name": "Q4 : Mode de Déplacement Principal",
            "emoji": "🚲",
            "vibe": "Comment te déplaces-tu au quotidien ?",
            "tags": ["transport", "mobilité", "voiture", "vélo"],
            "description": "Quel est ton principal mode de déplacement au quotidien ?",
            "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Transports en commun", "Vélo / V'Lille", "Voiture", "Uniquement à pied"]
        },
        {
            "name": "Q5 : Besoin en Espaces Verts et Nature",
            "emoji": "🌳",
            "vibe": "Importance de la nature ?",
            "tags": ["parcs", "nature", "sport"],
            "description": "Quelle est l'importance des espaces verts et de la nature à proximité ?",
            "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Essentiel (Nature/Détente)", "Juste quelques parcs", "Pratique pour le sport", "Peu important"]
        },
        {
            "name": "Q6 : Infrastructures pour Enfants/Famille",
            "emoji": "👶",
            "vibe": "Écoles, parcs, sport ?",
            "tags": ["famille", "enfants", "écoles"],
            "description": "Quel est ton besoin en infrastructures pour enfants/famille ?",
            "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Écoles", "Parcs d'enfants", "Écoles + Sport", "Pas pertinent"]
        },
        {
            "name": "Q7 : Sensibilité au Bruit",
            "emoji": "🔇",
            "vibe": "Quelle est ta tolérance au bruit ?",
            "tags": ["bruit", "calme", "nuisances"],
            "description": "Quelle est ta sensibilité au bruit environnant ?",
            "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Extrêmement sensible", "Un peu sensible", "Ça m'est égal", "J'aime quand ça bouge"]
        },
        {
            "name": "Q8 : Profil de Vie Actuel (Statut)",
            "emoji": "👤",
            "vibe": "Ton statut personnel ?",
            "tags": ["étudiant", "actif", "retraité", "famille"],
            "description": "Quel est ton profil de vie actuel ?",
            "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Étudiant", "Actif (Salarié/Indépendant)", "Retraité", "Famille avec enfants"]
        },
        {
            "name": "Q9 : Rythme de Vie et Habitudes",
            "emoji": "⚡",
            "vibe": "Activité et sorties ?",
            "tags": ["lifestyle", "sport", "sorties"],
            "description": "Quel est ton rythme de vie et tes habitudes (sorties, sport) ?",
            "image": "https://asset-prod.france.fr/en_tete_article_Mathieu_Lassalle_Hello_Lille_d989f67e94.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Très tranquille (à la maison)", "Sorties fréquentes", "Fait du sport", "Cuisiner vs. Manger dehors"]
        },
        {
            "name": "Q10 : Critère de Qualité de Vie Absolu",
            "emoji": "🥇",
            "vibe": "Ton critère non négociable ?",
            "tags": ["non-négociable", "qualité", "équilibre"],
            "description": "Quel est le critère qui prime sur tous les autres ?",
            "image": "https://uploads.lebonbon.fr/source/2023/march/2043048/ville-lille_1_2000.jpg?auto=format&fit=crop&w=1200&q=80",
            "options": ["Uniquement la performance globale (Équilibre)", "Le meilleur prix", "Le moins de bruit", "L'hyper-proximité"]
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

        /* Bouton 1: Gris neutre */
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

        /* Bouton 2: Gris neutre (identique) */
        [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] button {
            background: #f3f4f6 !important;
            color: #6b7280 !important;
            border: 2px solid #d1d5db !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] button:hover {
            background: #e5e7eb !important;
            border-color: #9ca3af !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.15) !important;
        }

        /* Bouton 3: Gris neutre (identique) */
        [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stButton"] button {
            background: #f3f4f6 !important;
            color: #6b7280 !important;
            border: 2px solid #d1d5db !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stButton"] button:hover {
            background: #e5e7eb !important;
            border-color: #9ca3af !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.15) !important;
        }

        /* Bouton 4: Gris neutre (identique) */
        [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stButton"] button {
            background: #f3f4f6 !important;
            color: #6b7280 !important;
            border: 2px solid #d1d5db !important;
        }

        [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stButton"] button:hover {
            background: #e5e7eb !important;
            border-color: #9ca3af !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.15) !important;
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

        /* Bouton 1: Gris neutre */
        .rating-btn-1 {
            background: #f3f4f6;
            color: #6b7280;
            border: 1.5px solid #d1d5db;
        }

        .rating-btn-1:hover {
            background: #e5e7eb;
            border-color: #9ca3af;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(107, 114, 128, 0.15);
        }

        .rating-btn-1:active {
            transform: scale(0.95);
        }

        /* Bouton 2: Même gris */
        .rating-btn-2 {
            background: #f3f4f6;
            color: #6b7280;
            border: 1.5px solid #d1d5db;
        }

        .rating-btn-2:hover {
            background: #e5e7eb;
            border-color: #9ca3af;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(107, 114, 128, 0.15);
        }

        .rating-btn-2:active {
            transform: scale(0.95);
        }

        /* Bouton 3: Même gris */
        .rating-btn-3 {
            background: #f3f4f6;
            color: #6b7280;
            border: 1.5px solid #d1d5db;
        }

        .rating-btn-3:hover {
            background: #e5e7eb;
            border-color: #9ca3af;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(107, 114, 128, 0.15);
        }

        .rating-btn-3:active {
            transform: scale(0.95);
        }

        /* Bouton 4: Même gris */
        .rating-btn-4 {
            background: #f3f4f6;
            color: #6b7280;
            border: 1.5px solid #d1d5db;
        }

        .rating-btn-4:hover {
            background: #e5e7eb;
            border-color: #9ca3af;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(107, 114, 128, 0.15);
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

if "selected_quartier_nom" not in st.session_state:
    st.session_state.selected_quartier_nom = None


def next_question():
    """Passe à la question suivante."""
    st.session_state.current_index = min(TOTAL, st.session_state.current_index + 1)
    
    # Si on a fini toutes les questions, calculer les recommandations
    if st.session_state.current_index == TOTAL and SCORING_DISPONIBLE:
        if st.session_state.matrice_data is not None:
            # Système V2 retourne (poids_criteres, poids_categories)
            try:
                poids_result = consolider_poids_utilisateur(st.session_state.reponses)
                if isinstance(poids_result, tuple):
                    poids, poids_categories = poids_result
                else:
                    poids = poids_result
            except:
                poids = consolider_poids_utilisateur(st.session_state.reponses)
            
            # Calculer le top 3
            st.session_state.top_quartiers = recommander_quartiers(
                poids, 
                st.session_state.matrice_data, 
                n_recommandations=3
            )
            
            # Calculer TOUS les scores pour la carte (V2 a une fonction dédiée)
            if calculer_tous_scores is not None:
                try:
                    st.session_state.tous_scores = calculer_tous_scores(
                        poids,
                        st.session_state.matrice_data
                    )
                except:
                    st.session_state.tous_scores = recommander_quartiers(
                        poids, 
                        st.session_state.matrice_data, 
                        n_recommandations=999
                    )
            else:
                st.session_state.tous_scores = recommander_quartiers(
                    poids, 
                    st.session_state.matrice_data, 
                    n_recommandations=999
                )


def enregistrer_reponse(option_texte):
    """Enregistre la réponse de l'utilisateur pour la question actuelle."""
    place = PLACES[st.session_state.current_index]
    
    # Nouveau système V2 : stocker avec question_id
    if 'question_id' in place:
        st.session_state.reponses[st.session_state.current_index] = {
            'question_id': place['question_id'],
            'option': option_texte
        }
    else:
        # Ancien système : déterminer le poids selon la position du bouton (1-4)
        if 'options' in place:
            position = place['options'].index(option_texte) if option_texte in place['options'] else 0
            poids = position + 1
        else:
            poids = 2
        
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
        
        # Gérer le format dict {text, value} ou simple string
        for idx, (col, option) in enumerate(zip([col1, col2, col3, col4], place['options'])):
            with col:
                if isinstance(option, dict):
                    # Nouveau format avec emoji intégré
                    button_text = option['text']
                    option_value = option['value']
                else:
                    # Ancien format (string simple) - garder compatibilité
                    emojis = ["😐", "🙂", "😊", "🤩"]
                    button_text = f"{emojis[idx]}\n{option}"
                    option_value = option
                
                if st.button(button_text, key=f"btn{idx+1}_{st.session_state.current_index}", use_container_width=True):
                    enregistrer_reponse(option_value)
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

    # Fonction pour générer une couleur basée sur un score normalisé (0-100) avec plus de nuances
    def get_color_from_score(score, min_score, max_score):
        """Normalise le score entre min et max, puis génère la couleur avec gradient riche"""
        # Normaliser le score entre 0 et 100
        if max_score > min_score:
            normalized = ((score - min_score) / (max_score - min_score)) * 100
        else:
            normalized = 50  # Si tous les scores sont identiques
        
        # Gradient avec plus de nuances : Rouge -> Orange -> Jaune -> Jaune-vert -> Vert -> Vert foncé
        if normalized < 20:
            # Rouge foncé à Rouge (0-20)
            ratio = normalized / 20
            r = int(139 + (255 - 139) * ratio)  # 139 à 255
            g = 0
            b = 0
        elif normalized < 40:
            # Rouge à Orange (20-40)
            ratio = (normalized - 20) / 20
            r = 255
            g = int(140 * ratio)  # 0 à 140
            b = 0
        elif normalized < 60:
            # Orange à Jaune (40-60)
            ratio = (normalized - 40) / 20
            r = 255
            g = int(140 + (255 - 140) * ratio)  # 140 à 255
            b = 0
        elif normalized < 75:
            # Jaune à Jaune-vert (60-75)
            ratio = (normalized - 60) / 15
            r = int(255 * (1 - ratio))  # 255 à 0
            g = 255
            b = int(50 * ratio)  # 0 à 50
        elif normalized < 90:
            # Jaune-vert à Vert (75-90)
            ratio = (normalized - 75) / 15
            r = 0
            g = 255
            b = int(50 + (100 * ratio))  # 50 à 150
        else:
            # Vert à Vert foncé (90-100)
            ratio = (normalized - 90) / 10
            r = 0
            g = int(255 - (100 * ratio))  # 255 à 155
            b = int(150 - (50 * ratio))  # 150 à 100
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # Créer des dictionnaires de scores par CODE_IRIS et NOM_IRIS
    scores_par_code = {}
    scores_par_nom = {}
    
    if st.session_state.tous_scores is not None and not st.session_state.tous_scores.empty:
        # Utiliser TOUS les scores calculés
        # Gérer les deux formats de colonnes : Score_Max (recommander_quartiers) ou Score_Final_100 (calculer_tous_scores)
        score_col = 'Score_Max' if 'Score_Max' in st.session_state.tous_scores.columns else 'Score_Final_100'
        
        for _, row in st.session_state.tous_scores.iterrows():
            scores_par_nom[row['NOM_IRIS']] = row[score_col]
            # Aussi stocker par CODE_IRIS si disponible
            if 'CODE_IRIS' in row:
                scores_par_code[str(row['CODE_IRIS'])] = row[score_col]
            elif 'IRIS_Meilleur' in row:
                scores_par_code[str(row['IRIS_Meilleur'])] = row[score_col]
    elif st.session_state.top_quartiers is not None and not st.session_state.top_quartiers.empty:
        # Fallback sur le top 3
        for _, row in st.session_state.top_quartiers.iterrows():
            scores_par_nom[row['NOM_IRIS']] = row['Score_Max']
            if 'CODE_IRIS' in row:
                scores_par_code[str(row['CODE_IRIS'])] = row['Score_Max']
            elif 'IRIS_Meilleur' in row:
                scores_par_code[str(row['IRIS_Meilleur'])] = row['Score_Max']
    
    # Si on a les scores mais pas de mapping CODE_IRIS, charger depuis matrice
    if scores_par_nom and not scores_par_code and st.session_state.matrice_data is not None:
        for _, row in st.session_state.matrice_data.iterrows():
            nom = row['NOM_IRIS']
            if nom in scores_par_nom:
                code = str(row['CODE_IRIS'])
                scores_par_code[code] = scores_par_nom[nom]
    
    # Calculer les scores min/max pour normaliser les couleurs
    # Le meilleur score devient 100, le pire devient 0 (normalisation relative)
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
                "color": "#2d2d2d",  # Bordure noire/gris foncé
                "weight": 1.2,
                "opacity": 0.8,
                "fillOpacity": 0.45,  # Opacité réduite pour plus de beauté
            },
            highlight_function=lambda x, current_color=color: {
                "fillColor": current_color,
                "color": "#ff5a5f",  # Bordure rouge au survol
                "weight": 2.5,
                "opacity": 1,
                "fillOpacity": 0.75,  # Plus opaque au survol
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
                code_iris = props.get("code_iris", "")
                nom_iris_geo = props.get("nom_iris", "Zone")
                # Mettre à jour le quartier sélectionné seulement si c'est un nouveau quartier
                if st.session_state.selected_quartier != code_iris:
                    st.session_state.selected_quartier = code_iris
                    st.session_state.selected_quartier_nom = nom_iris_geo  # Stocker aussi le nom générique
                    st.rerun()
        except Exception:
            pass

    # Afficher les détails du quartier sélectionné
    if st.session_state.selected_quartier:
        code_iris_selected = st.session_state.selected_quartier
        nom_iris_geo = st.session_state.selected_quartier_nom or "Zone"

        st.markdown("---")
        
        # Récupérer les données de l'IRIS depuis la matrice en utilisant CODE_IRIS
        if st.session_state.matrice_data is not None:
            # Convertir code_iris en int si nécessaire
            try:
                code_iris_int = int(code_iris_selected)
            except:
                code_iris_int = code_iris_selected
            
            quartier_row = st.session_state.matrice_data[st.session_state.matrice_data['CODE_IRIS'] == code_iris_int]
            
            if not quartier_row.empty:
                # Récupérer le vrai nom de l'IRIS depuis la matrice
                nom_iris = quartier_row.iloc[0]['NOM_IRIS']
                st.markdown(f"### 📍 {nom_iris}")
                # Afficher le score de compatibilité si le quiz est terminé
                if st.session_state.tous_scores is not None and not st.session_state.tous_scores.empty:
                    quartier_data = st.session_state.tous_scores[st.session_state.tous_scores['NOM_IRIS'] == nom_iris]
                    if not quartier_data.empty:
                        # Gérer les deux formats de colonnes
                        score_col = 'Score_Max' if 'Score_Max' in quartier_data.columns else 'Score_Final_100'
                        score = quartier_data.iloc[0][score_col]
                        score_color = "#10b981" if score > 60 else "#ff5a5f" if score < 40 else "#fbbf24"
                        st.markdown(
                            f"""
                            <div style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid {score_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0; color: #121212;">💯 Score de compatibilité</h4>
                                    <div style="font-size: 24px; font-weight: bold; color: {score_color};">{score:.0f}/100</div>
                                </div>
                                <p style="color: #6c6c6c; font-size: 14px; margin: 0;">Ce score est calculé en fonction de vos préférences.</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                # Afficher les performances avec comparaison attentes vs réalité
                st.markdown("**📊 Compatibilité : Vos attentes vs Cette zone**")
                
                # Traductions françaises des critères avec regroupements
                traductions = {
                    'Norm_Bruit': '🔇 Calme',
                    'Norm_Prix': '💰 Prix abordable',
                    'Norm_Surface_Verte_m2': '🌳 Espaces verts',
                    'Norm_Nb_Pharmacies': '🏪 Services de proximité',  # Regroupé
                    'Norm_Nb_Commerces': '🏪 Services de proximité',   # Regroupé
                    'Norm_Nb_Restaurants': '🍽️ Vie animée',             # Regroupé
                    'Norm_Nb_Bars': '🍽️ Vie animée',                    # Regroupé
                    'Norm_Nb_Transports': '🚇 Transports',
                    'Norm_Nb_VLille': '🚴 V\'Lille',
                    'Norm_Nb_ParcsEnfants': '👶 Enfants (écoles & aires de jeux)',  # Regroupé
                    'Norm_Nb_ComplexesSportifs': '⚽ Complexes sportifs',
                    'Norm_Nb_Ecoles': '👶 Enfants (écoles & aires de jeux)',        # Regroupé
                    'Norm_Nb_Parkings': '🅿️ Parkings',
                }
                
                # Définir les regroupements
                regroupements = {
                    '🏪 Services de proximité': ['Norm_Nb_Pharmacies', 'Norm_Nb_Commerces'],
                    '🍽️ Vie animée': ['Norm_Nb_Restaurants', 'Norm_Nb_Bars'],
                    '👶 Enfants (écoles & aires de jeux)': ['Norm_Nb_Ecoles', 'Norm_Nb_ParcsEnfants'],
                }
                
                # Si le quiz est complété, afficher comparaison attentes vs zone
                if st.session_state.tous_scores is not None and not st.session_state.tous_scores.empty and len(st.session_state.reponses) > 0:
                    # Gérer les deux systèmes de scoring
                    try:
                        poids_result = consolider_poids_utilisateur(st.session_state.reponses)
                        if isinstance(poids_result, tuple):
                            poids, poids_categories = poids_result
                        else:
                            poids = poids_result
                    except:
                        poids = consolider_poids_utilisateur(st.session_state.reponses)
                    
                    total_poids = sum(poids.values())
                    
                    if total_poids > 0:
                        # Créer un dictionnaire pour les critères regroupés
                        criteres_groupes = {}
                        poids_max = max(poids.values()) if poids.values() else 1
                        
                        for critere, poids_critere in poids.items():
                            if poids_critere > 0 and critere in quartier_row.columns:
                                nom_francais = traductions.get(critere, critere.replace('Norm_', '').replace('_', ' '))
                                valeur_zone = quartier_row.iloc[0][critere] * 100
                                
                                # Si ce critère fait partie d'un regroupement
                                if nom_francais in criteres_groupes:
                                    # Ajouter au groupe existant (moyenne des valeurs)
                                    criteres_groupes[nom_francais]['poids_brut'] += poids_critere
                                    criteres_groupes[nom_francais]['valeur_zone'] = (
                                        criteres_groupes[nom_francais]['valeur_zone'] + valeur_zone
                                    ) / 2
                                    criteres_groupes[nom_francais]['count'] += 1
                                else:
                                    # Nouveau critère
                                    criteres_groupes[nom_francais] = {
                                        'nom': nom_francais,
                                        'poids_brut': poids_critere,
                                        'valeur_zone': valeur_zone,
                                        'count': 1
                                    }
                        
                        # Convertir en liste et calculer les métriques finales
                        criteres_importants = []
                        # Recalculer poids_max après regroupement
                        poids_max = max(c['poids_brut'] for c in criteres_groupes.values())
                        
                        for nom, data in criteres_groupes.items():
                            importance = (data['poids_brut'] / poids_max) * 100
                            criteres_importants.append({
                                'nom': nom,
                                'attente': importance,
                                'zone': data['valeur_zone'],
                                'ecart': data['valeur_zone'] - importance,
                                'poids_brut': data['poids_brut']
                            })
                        
                        # Trier par priorité utilisateur (attente) décroissante
                        criteres_importants.sort(key=lambda x: x['attente'], reverse=True)
                        
                        # Afficher détails budget si c'est un critère important
                        if any(c['nom'] == '💰 Prix abordable' for c in criteres_importants):
                            prix_median = quartier_row.iloc[0].get('Prix_Median_m2', None)
                            if prix_median and prix_median > 0:
                                st.info(f"💰 **Prix médian** : {prix_median:.0f}€/m² dans ce quartier")
                        
                        # Afficher le graphique de comparaison pour TOUS les critères importants
                        for critere in criteres_importants:
                            st.markdown(
                                f"""
                                <div style="margin-bottom: 16px; padding: 14px; background: white; border-radius: 10px; border: 1px solid #e5e7eb;">
                                    <div style="margin-bottom: 10px;">
                                        <span style="color: #121212; font-weight: 600; font-size: 14px;">{critere['nom']}</span>
                                    </div>
                                    <div style="margin-bottom: 6px;">
                                        <div style="font-size: 11px; margin-bottom: 3px; color: #6b7280;">
                                            <span>Ce que vous cherchez</span>
                                        </div>
                                        <div style="background: #f3f4f6; height: 10px; border-radius: 5px; overflow: hidden;">
                                            <div style="background: #3b82f6; height: 100%; width: {critere['attente']:.0f}%;"></div>
                                        </div>
                                    </div>
                                    <div>
                                        <div style="font-size: 11px; margin-bottom: 3px; color: #6b7280;">
                                            <span>Ce que le quartier offre</span>
                                        </div>
                                        <div style="background: #f3f4f6; height: 10px; border-radius: 5px; overflow: hidden;">
                                            <div style="background: #8b5cf6; height: 100%; width: {critere['zone']:.0f}%;"></div>
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                else:
                    # Si pas de quiz, afficher juste les performances brutes
                    st.caption("_Complétez le quiz pour voir la comparaison avec vos attentes_")
                    performances = {}
                    for critere, label in traductions.items():
                        if critere in quartier_row.columns:
                            valeur = quartier_row.iloc[0][critere]
                            performances[label] = valeur * 100
                    performances_triees = sorted(performances.items(), key=lambda x: x[1], reverse=True)
                    for nom_critere, performance in performances_triees:
                        perf_color = "#10b981" if performance > 60 else "#ff5a5f" if performance < 40 else "#fbbf24"
                        st.markdown(
                            f"""
                            <div style="margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                                    <span style="color: #121212;">{nom_critere}</span>
                                    <span style="color: #6c6c6c;">{performance:.0f}/100</span>
                                </div>
                                <div style="background: #f3f4f6; height: 6px; border-radius: 3px; overflow: hidden;">
                                    <div style="background: {perf_color}; height: 100%; width: {performance:.0f}%;"></div>
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
