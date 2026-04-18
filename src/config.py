# src/config.py
import os
import sys

# --- MANAGER DATABASE (2025/26 Season) ---
MANAGERS = {
    "Arsenal": "Mikel Arteta",
    "Chelsea": "Liam Rosenior",
    "Liverpool": "Arne Slot",
    "Manchester City": "Pep Guardiola",
    "Manchester United": "Michael Carrick",
    "Tottenham": "Roberto de Zerbi",
}

# --- Big Six Team Names ---
BIG_SIX = [
    "Arsenal",
    "Chelsea",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Tottenham",
]

# --- Team Logo URLs (Wikimedia SVG) ---
TEAM_LOGOS = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Tottenham": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
}

# --- Team Primary Colors ---
TEAM_COLORS = {
    "Arsenal": "#EF0107",
    "Chelsea": "#034694",
    "Liverpool": "#C8102E",
    "Manchester City": "#6CABDD",
    "Manchester United": "#DA020E",
    "Tottenham": "#132257",
}

# --- Extended Club Data (FIFA-style panel) ---
TEAM_EXTRA = {
    "Arsenal": {
        "founded": 1886,
        "stadium": "Emirates Stadium",
        "capacity": "60,704",
        "league_titles": 13,
        "stars": 4.5,
        "kit_home": "/assets/arsenal_h.png",
        "kit_away": "/assets/arsenal_a.png",
        "nickname": "The Gunners",
    },
    "Chelsea": {
        "founded": 1905,
        "stadium": "Stamford Bridge",
        "capacity": "40,173",
        "league_titles": 6,
        "stars": 4.0,
        "kit_home": "/assets/chelsea_h.png",
        "kit_away": "/assets/chelsea_a.png",
        "nickname": "The Blues",
    },
    "Liverpool": {
        "founded": 1892,
        "stadium": "Anfield",
        "capacity": "61,276",
        "league_titles": 20,
        "stars": 5.0,
        "kit_home": "/assets/liverpool_h.png",
        "kit_away": "/assets/liverpool_a.png",
        "nickname": "The Reds",
    },
    "Manchester City": {
        "founded": 1880,
        "stadium": "Etihad Stadium",
        "capacity": "52,900",
        "league_titles": 10,
        "stars": 4.5,
        "kit_home": "/assets/mancity_h.png",
        "kit_away": "/assets/mancity_a.png",
        "nickname": "The Citizens",
    },
    "Manchester United": {
        "founded": 1878,
        "stadium": "Old Trafford",
        "capacity": "74,310",
        "league_titles": 20,
        "stars": 4.0,
        "kit_home": "/assets/manutd_h.png",
        "kit_away": "/assets/manutd_a.png",
        "nickname": "The Red Devils",
    },
    "Tottenham": {
        "founded": 1882,
        "stadium": "Tottenham Hotspur Stadium",
        "capacity": "62,850",
        "league_titles": 2,
        "stars": 3.5,
        "kit_home": "/assets/tottenham_h.png",
        "kit_away": "/assets/tottenham_a.png",
        "nickname": "Spurs",
    },
}

# --- 2025/26 Premier League Standings (Big Six) ---
# Updated with latest image data (March 2026)
PL_STANDINGS = {
    "Arsenal": {
        "pos": 1, "played": 31, "won": 21, "drawn": 7, "lost": 3,
        "gf": 61, "ga": 22, "gd": 39, "points": 70, "form": "WWWWD",
    },
    "Manchester City": {
        "pos": 2, "played": 30, "won": 18, "drawn": 7, "lost": 5,
        "gf": 60, "ga": 28, "gd": 32, "points": 61, "form": "DDWWW",
    },
    "Manchester United": {
        "pos": 3, "played": 30, "won": 15, "drawn": 9, "lost": 6,
        "gf": 54, "ga": 41, "gd": 13, "points": 54, "form": "WLWWD",
    },
    "Liverpool": {
        "pos": 5, "played": 30, "won": 14, "drawn": 7, "lost": 9,
        "gf": 49, "ga": 40, "gd": 9, "points": 49, "form": "DLWWW",
    },
    "Chelsea": {
        "pos": 6, "played": 30, "won": 13, "drawn": 9, "lost": 8,
        "gf": 53, "ga": 35, "gd": 18, "points": 48, "form": "LWLDD",
    },
    "Tottenham": {
        "pos": 16, "played": 30, "won": 7, "drawn": 9, "lost": 14,
        "gf": 40, "ga": 47, "gd": -7, "points": 30, "form": "DLLLL",
    },
}


# --- API CONFIGURATION ---
API_KEY = "YOUR_API_KEY_HERE"  # Replaced for open sourcing
BASE_URL = "YOUR_BASE_URL_HERE" # Replaced for open sourcing
NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"
NEWS_API_URL = "https://newsapi.org/v2/everything"

TEAM_IDS = {
    "Arsenal": 42, "Chelsea": 49, "Liverpool": 40,
    "Manchester City": 50, "Manchester United": 33, "Tottenham": 47,
}

# --- FILE PATHS ---
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
HISTORICAL_FILE = os.path.join(DATA_DIR, "final_matches.csv")
FIXTURE_FILE = os.path.join(DATA_DIR, "2025_26_real_fixtures.csv")
MODEL_FILE = os.path.join(MODEL_DIR, "predarby_model.pkl")
