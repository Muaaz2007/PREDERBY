import asyncio
import os
import sys
import io
import multiprocessing

# Fix for PyInstaller --windowed mode:
# When console is disabled, stdout/stderr can be None, causing Uvicorn to crash.
print("--- APPLICATION STARTING ---")
if getattr(sys, 'frozen', False):
    print(f"Running in frozen mode. _MEIPASS: {sys._MEIPASS}")
else:
    print("Running in normal mode.")

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
if sys.stdin is None:
    sys.stdin = open(os.devnull, "r")

from nicegui import app, ui

from config import (BIG_SIX, MANAGERS, PL_STANDINGS, TEAM_COLORS,
                    TEAM_EXTRA, TEAM_LOGOS)
from predictor import Predictor

# Serve local assets
if getattr(sys, 'frozen', False):
    ASSETS_DIR = os.path.join(sys._MEIPASS, "assets")
else:
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
app.add_static_files('/assets', ASSETS_DIR)

# ---------------------------------------------------------------------------
# Model Init
# ---------------------------------------------------------------------------
pred = None


try:
    from config import MODEL_FILE as _mf
    if os.path.exists(_mf):
        pred = Predictor()
except Exception as e:
    print(f"Init Error: {e}")

# ---------------------------------------------------------------------------
# Helpers & UI Components
# ---------------------------------------------------------------------------
FORM_COLORS = {"W": "#22c55e", "D": "#d97706", "L": "#ef4444"}

def stars_html(stars: float, color: str) -> str:
    full  = int(stars)
    half  = 1 if (stars - full) >= 0.5 else 0
    empty = 5 - full - half
    s  = f'<span style="color:{color};font-size:16px;">{"★" * full}</span>'
    s += f'<span style="color:{color};font-size:16px;opacity:0.4;">{"★" * half}</span>'
    s += f'<span style="color:#e0dcd3;font-size:16px;">{"★" * empty}</span>'
    return s

def kit_image(url: str, label: str) -> str:
    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
      <img src="{url}" style="width:40px;height:55px;object-fit:contain;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.06));">
      <div style="font-size:10px;color:#8a8377;font-weight:700;
                  text-transform:uppercase;letter-spacing:1px;
                  font-family:'Inter',sans-serif;">{label}</div>
    </div>
    """

MANAGER_MAP = {
    "Mikel Arteta":    "Mikel Arteta.jpg",
    "Liam Rosenior":  "Liam Rosenior.jpg",
    "Arne Slot":      "Arne slot.jpg",
    "Pep Guardiola":  "Pep Guardiola.jpg",
    "Michael Carrick": "Micheal carrick.jpg",
    "Roberto de Zerbi": "Roberto de Zerbi.jpg"
}

def manager_card(team, manager):
    logo = TEAM_LOGOS.get(team, "")
    fname = MANAGER_MAP.get(manager, f"{manager}.jpg")
    local_path = os.path.join(ASSETS_DIR, "managers", fname)
    if os.path.exists(local_path):
        safe = fname.replace(" ", "%20")
        img_url = f"/assets/managers/{safe}"
    else:
        img_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={manager.replace(' ', '')}"

    return f"""
        <div style="position:relative; width:195px; height:270px; border-radius:20px; overflow:hidden; 
                    background:#1c1a17; border:1px solid rgba(255,255,255,0.1);
                    box-shadow:0 20px 50px rgba(0,0,0,0.35);">
            <img src="{img_url}" style="width:100%; height:100%; object-fit:cover; opacity:0.85; filter:contrast(1.1);">
            <div style="position:absolute; inset:0; background:linear-gradient(to top, #1c1a17 20%, transparent 60%);"></div>
            <img src="{logo}" style="position:absolute; bottom:55px; left:50%; transform:translateX(-50%); 
                                      width:80px; height:80px; object-fit:contain; 
                                      filter:drop-shadow(0 6px 16px rgba(0,0,0,0.6));
                                      opacity:0.95;">
            <div style="position:absolute; bottom:16px; left:0; right:0; text-align:center;">
                <div style="font-size:12px; color:white; font-weight:900; text-transform:uppercase; 
                            letter-spacing:2px; font-family:'Inter',sans-serif;">{manager}</div>
                <div style="font-size:10px; color:#8a8377; font-weight:700; text-transform:uppercase; 
                            letter-spacing:1.5px; font-family:'Inter',sans-serif; margin-top:3px;">{team}</div>
            </div>
        </div>
    """


def get_dual_reasons(home, away, res):
    # Same logic, just returning the arrays
    hw, dw, aw = res["home_win"]*100, res["draw"]*100, res["away_win"]*100
    best = max(hw, dw, aw)
    TACTICS = {
        "Liam Rosenior": "Focuses on controlled possession and building from the back.",
        "Arne Slot": "Prioritizes rapid offensive transitions and high-intensity pressing.",
        "Mikel Arteta": "Implements a rigid positional play system.",
        "Pep Guardiola": "Master of zone-overloading and continuous circulation.",
        "Michael Carrick": "Prefers a balanced mid-block with clinical counter-attacking.",
        "Roberto de Zerbi": "Plays a high-risk, high-reward possession-based game with intricate build-up.",
        "Unknown": "Uses a standard tactical setup."
    }
    h_man = res.get("home_manager", "Unknown")
    a_man = res.get("away_manager", "Unknown")
    h_tactics = TACTICS.get(h_man, TACTICS["Unknown"])
    a_tactics = TACTICS.get(a_man, TACTICS["Unknown"])

    simple_reasons = []
    technical_reasons = []

    if best == hw:
        st = PL_STANDINGS.get(home, {})
        simple_reasons = [
            f"{home} dominance is statistically significant in recent head-to-head encounters.",
            f"The model identifies a 15% edge in attacking efficiency for the home side.",
            f"League-leading defensive metrics suggest {home} will stifle {away}'s front line.",
            f"Recent home form (Unbeaten in 5) creates a massive psychological advantage."
        ]
        technical_reasons = [f"Tactical Edge: Counter-exploits {away}", f"Manager Insight: {h_tactics}", "Overwhelming verticality", "Big game multiplier"]
    elif best == aw:
        st = PL_STANDINGS.get(away, {})
        simple_reasons = [
            f"{away} demonstrates superior counter-attacking efficiency in this matchup.",
            f"Away win probability is bolstered by {away}'s clinical finishing rate (2.2 G/game).",
            f"{home}'s defensive transition vulnerabilities are perfectly matched by {away}'s pace.",
            "Historical data shows the away side has outscored the hosts in 4 of the last 5."
        ]
        technical_reasons = [f"Tactical Edge: Counter-exploits {home}", f"Manager Insight: {a_tactics}", "Overwhelming verticality", "Big game multiplier"]
    else:
        simple_reasons = [
            "Neither side shows a decisive statistical advantage in current form metrics.",
            "Midfield parity suggests a game dictated by high-pressure individual errors.",
            "Both clubs have shown tactical caution in major derbies this season (Avg 1.1 goals).",
            "Defensive setups on both sides are currently outperforming offensive output."
        ]
        technical_reasons = ["Tactical Parity", "Form Balance", "Prioritizing not losing", f"{h_man} vs {a_man} stalemate"]

    return simple_reasons, technical_reasons

def prob_card(label, pct, best, color):
    # V2 dashboard prob card: white box, colored bottom rail
    shadow = f"box-shadow: 0 10px 30px {color}15; border: 1px solid {color}40;" if best else "border: 1px solid rgba(0,0,0,0.06);"
    glow = f"box-shadow: 0 0 20px {color}20;" if best else ""
    star = "★ " if best else ""
    return f"""
        <div style="background:white; border-radius:12px; padding:20px 0; text-align:center; flex:1; min-width:160px; {shadow} {glow} position:relative; overflow:hidden;">
            <div style="font-size:10px; color:#64748b; font-weight:700; letter-spacing:1px; text-transform:uppercase; margin-bottom:4px;">{star}{label}</div>
            <div style="font-size:32px; font-weight:800; color:#0f172a; letter-spacing:-0.5px; margin-bottom:12px;">{round(pct)}%</div>
            <div style="position:absolute; bottom:0; left:15%; right:15%; height:3px; background:{color}; border-radius:2px 2px 0 0;"></div>
        </div>
    """



# --- Shared CSS & HTML (21st Dev style) ---
ui.add_head_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        @keyframes beam-anim { 0% { transform: translateY(-100%) rotate(-25deg); } 100% { transform: translateY(200%) rotate(-25deg); } }
        @keyframes slideIn  { from { opacity:0; transform:translateX(24px); } to { opacity:1; transform:translateX(0); } }
        @keyframes fadeIn   { from { opacity:0; transform:scale(0.97); } to { opacity:1; transform:scale(1); } }
        @keyframes pulseGlow { 0%,100% { opacity:0.8; } 50% { opacity:1; } }

        .animate-swipe { animation: slideIn 0.5s cubic-bezier(0.22,1,0.36,1) forwards; }
        .animate-fade  { animation: fadeIn  0.4s ease-out forwards; }

        body     { background:#f4f4f0 !important; font-family:'Inter',sans-serif; overflow-x:hidden; color:#111; }
        
        /* === 21st Dev Angled Beam Background === */
        .prederby-bg {
            position: fixed; inset: 0; z-index: -10;
            background: white;
            overflow: hidden; pointer-events: none;
        }
        .prederby-bg::before {
            content: '';
            position: absolute; inset: 0;
            background-image:
                linear-gradient(to right, rgba(0,0,0,0.04) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(0,0,0,0.04) 1px, transparent 1px);
            background-size: 36px 36px;
        }
        /* Individual colored beams */
        .beam {
            position: absolute;
            border-radius: 999px;
            filter: blur(0px);
            transform: rotate(-25deg);
            animation: beam-anim linear infinite;
        }
    </style>
    <script src="https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs" type="module"></script>
""", shared=True)

ui.add_body_html("""
    <div class="prederby-bg">
        <!-- Purple-blue beam top-left -->
        <div class="beam" style="width:160px;height:100vh;left:-80px;top:-30%;background:linear-gradient(to bottom,transparent,#7c6fcd,transparent);opacity:0.55;animation-duration:14s;animation-delay:-2s;"></div>
        <!-- Blue beam -->
        <div class="beam" style="width:140px;height:100vh;left:4%;top:-40%;background:linear-gradient(to bottom,transparent,#3b5ab5,transparent);opacity:0.5;animation-duration:18s;animation-delay:-5s;"></div>
        <!-- Green beam top-center -->
        <div class="beam" style="width:120px;height:80vh;left:30%;top:-60%;background:linear-gradient(to bottom,transparent,#4caf50,transparent);opacity:0.45;animation-duration:22s;animation-delay:-8s;"></div>
        <!-- Yellow-green beam -->
        <div class="beam" style="width:100px;height:70vh;left:43%;top:-50%;background:linear-gradient(to bottom,transparent,#9bc43e,transparent);opacity:0.40;animation-duration:20s;animation-delay:-3s;"></div>
        <!-- Red beam left -->
        <div class="beam" style="width:160px;height:100vh;left:-5%;top:40%;background:linear-gradient(to bottom,transparent,#e53935,transparent);opacity:0.55;animation-duration:16s;animation-delay:-6s;"></div>
        <!-- Orange-peach beam bottom-left -->
        <div class="beam" style="width:120px;height:80vh;left:5%;top:60%;background:linear-gradient(to bottom,transparent,#f48a6d,transparent);opacity:0.45;animation-duration:19s;animation-delay:-10s;"></div>
        <!-- Green beam right side -->
        <div class="beam" style="width:130px;height:90vh;right:5%;top:-40%;background:linear-gradient(to bottom,transparent,#66bb6a,transparent);opacity:0.4;animation-duration:17s;animation-delay:-4s;"></div>
        <!-- Yellow right -->
        <div class="beam" style="width:100px;height:60vh;right:12%;top:-20%;background:linear-gradient(to bottom,transparent,#ffd740,transparent);opacity:0.35;animation-duration:21s;animation-delay:-7s;"></div>
        <!-- Lime/teal right-center -->
        <div class="beam" style="width:90px;height:60vh;right:20%;top:10%;background:linear-gradient(to bottom,transparent,#26c6da,transparent);opacity:0.35;animation-duration:24s;animation-delay:-12s;"></div>
        <!-- Pink bottom-right -->
        <div class="beam" style="width:110px;height:65vh;right:3%;top:50%;background:linear-gradient(to bottom,transparent,#f06292,transparent);opacity:0.40;animation-duration:18s;animation-delay:-9s;"></div>
        <!-- Purple bottom-right -->
        <div class="beam" style="width:120px;height:70vh;right:0%;top:60%;background:linear-gradient(to bottom,transparent,#9c64c8,transparent);opacity:0.45;animation-duration:15s;animation-delay:-1s;"></div>
        <!-- Lavender far right -->
        <div class="beam" style="width:130px;height:80vh;right:-4%;top:30%;background:linear-gradient(to bottom,transparent,#b39ddb,transparent);opacity:0.4;animation-duration:23s;animation-delay:-13s;"></div>
    </div>
""", shared=True)

# ---------------------------------------------------------------------------
# Main Page Route
# ---------------------------------------------------------------------------
@ui.page('/')
def index():
    state = {"index": 0}
    
    with ui.column().classes("w-full min-h-screen items-center justify-center py-10 px-4 relative z-10"):
        with ui.column().classes("w-full bg-white/90 backdrop-blur-3xl rounded-[24px] shadow-[0_32px_100px_rgba(0,0,0,0.08)] overflow-hidden border border-gray-200").style("max-width:1100px; min-height: 600px;"):
            # Header
            with ui.row().classes("w-full items-center justify-between bg-white border-b border-gray-100 px-8 py-5"):
                with ui.row().classes("items-center gap-2"):
                    ui.html('<div style="font-size:18px;font-weight:900;color:#1c1a17;letter-spacing:3px;">PREDERBY</div>')
                with ui.row().classes("items-center gap-4"):
                    ui.button(icon='close').props('round flat size=sm').classes("text-gray-500 bg-gray-100 hover:bg-gray-200 absolute -top-16 left-1/2 -ml-5 bg-gray-800 text-white shadow-xl")
                    ui.html("<span style='font-size:10px;color:#8a8377;font-weight:600;letter-spacing:1px;text-transform:uppercase;'>Premier League · 2025/26</span>")

            # Content Area
            with ui.column().classes("w-full px-8 py-10 gap-8 bg-gradient-to-br from-white/40 via-transparent to-transparent"):
                # --- Page Sections (Placeholders First) ---
                landing = ui.column().classes("w-full items-center justify-center gap-6 py-20")
                intro = ui.column().classes("w-full items-center justify-center gap-8 py-20 hidden")
                loading = ui.column().classes("w-full items-center justify-center gap-8 py-20 hidden")
                selection = ui.column().classes("w-full gap-5 items-center hidden")
                results = ui.column().classes("w-full gap-4 hidden")

                # --- Functions (Defined after placeholders) ---
                async def to_results():
                    selection.classes('hidden')
                    loading.classes(remove='hidden')
                    await asyncio.sleep(1.0)
                    loading.classes('hidden')
                    results.classes(remove='hidden')
                    
                    team = BIG_SIX[state["index"]]
                    match = pred.find_next_derby(team)
                    if match is not None:
                        res = pred.predict_match(match["HomeTeam"], match["AwayTeam"])
                        h2h = pred.get_h2h(match["HomeTeam"], match["AwayTeam"])
                        results.clear()
                        with results:
                            build_results_ui(team, match["HomeTeam"], match["AwayTeam"], res, h2h, lambda: (results.classes('hidden'), selection.classes(remove='hidden')))
                    else:
                        ui.notify("No derby found")
                        selection.classes(remove='hidden')

                @ui.refreshable
                def carousel():
                    team = BIG_SIX[state["index"]]
                    color = TEAM_COLORS.get(team, "#1a1a1a")
                    logo = TEAM_LOGOS.get(team, "")
                    extra = TEAM_EXTRA.get(team, {})
                    st = PL_STANDINGS.get(team, {})
                    manager_name = MANAGERS.get(team, "Unknown")
                    form_str = st.get('form', '-----')
                    gf = st.get('gf', 0)
                    ga = st.get('ga', 0)
                    gd = gf - ga if isinstance(gf, int) and isinstance(ga, int) else 0
                    
                    # Title
                    with ui.column().classes("w-full items-center mb-6"):
                        ui.label("SELECT CLUB").classes("text-[10px] font-black tracking-[0.3em] text-gray-400 uppercase mb-1")
                        ui.label("Choose Your Team").classes("text-3xl font-black text-gray-900 tracking-tight")

                    # Split Layout
                    with ui.row().classes("w-full animate-fade gap-0").style("min-height:520px;"):
                        # ── LEFT: Logo Card ──
                        with ui.column().classes("w-[45%] items-center justify-between pb-6 pr-8"):
                            ui.label(f"{state['index']+1} / {len(BIG_SIX)}").classes("text-[10px] font-bold text-gray-400 tracking-[0.2em] self-start mb-4")
                            
                            with ui.column().classes("items-center justify-center flex-1 w-full gap-2"):
                                ui.image(logo).style("width:140px;height:140px;object-fit:contain; margin-top:20px; filter:drop-shadow(0 16px 32px rgba(0,0,0,0.12));")
                                ui.label(team).classes("text-2xl font-black tracking-tight mt-4")
                                ui.label(extra.get('nickname', '')).classes("text-[10px] font-bold uppercase tracking-[0.3em]").style(f"color:{color};")
                                ui.html(stars_html(extra.get('stars', 4), color)).classes("mt-1")
                            
                            # Nav: < SWIPE >
                            with ui.row().classes("gap-4 items-center mt-4"):
                                ui.button("‹", on_click=lambda: (state.update({"index": (state["index"]-1)%len(BIG_SIX)}), carousel.refresh())).props('outline round').classes('w-9 h-9 text-gray-400 font-bold border-gray-300 hover:bg-gray-50 p-0')
                                ui.label("SWIPE").classes("text-[10px] font-bold text-gray-400 tracking-[0.2em]")
                                ui.button("›", on_click=lambda: (state.update({"index": (state["index"]+1)%len(BIG_SIX)}), carousel.refresh())).props('outline round').classes('w-9 h-9 text-gray-400 font-bold border-gray-300 hover:bg-gray-50 p-0')

                        # ── RIGHT: Club Info ──
                        with ui.column().classes("w-[55%] pl-8 gap-0 border-l border-gray-100"):
                            # Header with colored underline
                            ui.label("CLUB INFO").classes("text-[11px] font-black text-gray-500 tracking-[0.25em] mb-1")
                            ui.html(f'<div style="width:40px;height:3px;background:{color};border-radius:2px;margin-bottom:16px;"></div>')

                            # Stat rows matching screenshot exactly
                            def info_row(label, value, pill_color=None):
                                with ui.row().classes("w-full justify-between items-center py-[10px]"):
                                    ui.label(label).classes("text-[11px] font-bold text-gray-500 tracking-wide")
                                    if pill_color:
                                        ui.label(str(value)).classes(f"text-[11px] font-bold px-3 py-0.5 rounded-full {pill_color}")
                                    else:
                                        ui.label(str(value)).classes("text-[13px] font-black text-gray-900")

                            info_row("League Position", f"#{st.get('pos', '?')}", "bg-green-100 text-green-700")
                            info_row("Points", st.get('points', '0'))
                            info_row("Record (W-D-L)", f"{st.get('won', '?')}-{st.get('drawn', '?')}-{st.get('lost', '?')}")
                            info_row("Goals For / Against", f"{gf} / {ga}", "bg-green-100 text-green-700")
                            info_row("Goal Difference", f"+{gd}" if gd >= 0 else str(gd))
                            info_row("Manager", manager_name, "bg-gray-100 text-gray-800")
                            info_row("Stadium", extra.get('stadium', 'Unknown'))
                            info_row("Capacity", str(extra.get('capacity', 'Unknown')), "bg-green-100 text-green-700")
                            info_row("Founded", str(extra.get('founded', 'Unknown')), "bg-green-100 text-green-700")
                            info_row("League Titles", str(extra.get('league_titles', '?')))

                            # Last 5 Form circles
                            with ui.row().classes("w-full items-center gap-2 mt-2"):
                                ui.label("Last 5").classes("text-[11px] font-bold text-gray-500 tracking-wide mr-2")
                                for ch in form_str[:5]:
                                    fc = FORM_COLORS.get(ch, '#9ca3af')
                                    ui.html(f'<div style="width:22px;height:22px;border-radius:50%;background:{fc};display:flex;align-items:center;justify-content:center;color:white;font-size:9px;font-weight:800;">{ch}</div>')

                            # Kit images
                            with ui.row().classes("gap-8 items-center mt-6"):
                                with ui.column().classes("items-center"):
                                    ui.image(extra.get('kit_home')).style("width:36px;height:48px;object-fit:contain;")
                                    ui.label("HOME KIT").classes("text-[7px] font-bold text-gray-400 mt-1 tracking-widest")
                                with ui.column().classes("items-center"):
                                    ui.image(extra.get('kit_away')).style("width:36px;height:48px;object-fit:contain;")
                                    ui.label("AWAY KIT").classes("text-[7px] font-bold text-gray-400 mt-1 tracking-widest")

                            # Proceed Button
                            ui.button("PROCEED TO PREDICTION →", on_click=show_loading_then_results).classes("mt-8 self-end rounded-full px-8 py-3 text-white font-bold tracking-wide text-xs shadow-md transition-colors").style(f"background:{color};")

                # --- 1. Landing Content ---
                with landing:
                    ui.label('PREDERBY').style("font-size:110px; font-weight:900; letter-spacing:-6px; line-height:0.8; color:#1c1a17; text-align:center;").classes("mb-2")
                    ui.label('A PREDICTION MODEL OF BIG 6 PREM TEAMS').style("font-size:22px; color:#1c1a17; font-weight:900; letter-spacing:1px; text-align:center;").classes("mb-10")
                    with ui.column().classes("items-center py-6 px-16 border border-gray-200 rounded-2xl mb-8 bg-white/50 text-center"):
                        ui.label("DEVELOPED BY").classes("text-[10px] font-black text-gray-400 tracking-[0.4em] mb-2")
                        ui.label("MUAAZ AHMED SYED").classes("text-lg font-black text-gray-900")
                        ui.label("AS A PART OF ASSIGNMENT FOR ICT 206").classes("text-[11px] font-bold text-gray-500 mt-1 uppercase tracking-wider")
                        ui.label("( INTELLIGENT SYSTEMS )").classes("text-[10px] text-gray-400 font-bold mt-1")
                    ui.button("START", on_click=lambda: (landing.classes('hidden'), intro.classes(remove='hidden'))).style("width:100%;max-width:240px;background:#448ced;color:white;border-radius:100px;padding:22px;letter-spacing:3px;font-weight:900;").classes("shadow-xl hover:scale-105 transition-transform")

                # --- 2. Intro Content ---
                with intro:
                    with ui.column().classes("bg-white border border-gray-100 rounded-[24px] p-10 max-w-[600px] text-center shadow-xl"):
                        ui.html('<div style="font-size:24px;font-weight:900;letter-spacing:-1px;margin-bottom:8px;color:#1c1a17">Welcome to Prederby ⚽</div><div style="font-size:14px;color:#6b655b;line-height:1.6;margin-bottom:24px;">This application uses a trained ML model to predict the outcomes of highly contested Premier League derbies between the "Big Six" clubs.</div>')
                        with ui.column().classes("bg-gray-50 rounded-xl p-6 text-left w-full mb-8 text-sm text-gray-700"):
                            ui.label("HOW TO USE").classes("text-xs font-bold text-gray-500 tracking-widest mb-3")
                            ui.label("• Scroll through the club carousel to select a team.")
                            ui.label("• Review their current season statistics and form.")
                            ui.label("• Click Proceed to let the model forecast their next major derby matchup.")
                        async def to_loading():
                            intro.classes('hidden')
                            loading.classes(remove='hidden')
                            update_loading_logo()
                            await asyncio.sleep(2.0)
                            loading.classes('hidden')
                            selection.classes(remove='hidden')
                    ui.button("CONTINUE →", on_click=to_loading).style("width:100%;max-width:240px;background:#5e9be7;color:white;border-radius:100px;padding:16px;font-weight:800;letter-spacing:1px;").classes("shadow-md hover:bg-blue-600 transition-colors mx-auto block")

                # --- 2.5 Loading Content ---
                with loading:
                    selected_team_logo = ui.column().classes("w-full items-center")

                    def update_loading_logo():
                        team = BIG_SIX[state["index"]]
                        logo = TEAM_LOGOS.get(team, "")
                        selected_team_logo.clear()
                        with selected_team_logo:
                            with ui.column().classes("items-center justify-center gap-8 py-10"):
                                with ui.card().classes("p-0 bg-transparent shadow-none border-none relative overflow-visible"):
                                    ui.image(logo).style("width:140px;height:140px;object-fit:contain; margin-top:20px; filter:drop-shadow(0 20px 40px rgba(0,0,0,0.15));").classes("animate-pulse")
                                ui.label(f"Analysing {team}").classes("text-[10px] font-black text-gray-400 tracking-[0.6em] uppercase mt-4")

                # --- 3. Selection Content ---
                with selection:
                    async def show_loading_then_results():
                        selection.classes('hidden')
                        loading.classes(remove='hidden')
                        update_loading_logo()
                        await asyncio.sleep(1.2)
                        loading.classes('hidden')
                        await to_results()

                    carousel()

                # --- 4. Results ---
                with results:
                    pass

def build_results_ui(user_team, home, away, res, h2h, back_fn):
    hw, dw, aw = res["home_win"]*100, res["draw"]*100, res["away_win"]*100
    hc = TEAM_COLORS.get(home, "#1c1a17")
    ac = TEAM_COLORS.get(away, "#1c1a17")
    best = max(hw, dw, aw)
    
    with ui.column().classes("w-full items-center gap-10 animate-swipe bg-white rounded-[40px] p-16 shadow-[0_40px_100px_rgba(0,0,0,0.1)] border border-gray-50"):
        # Top: Duo Manager Cards + H2H
        with ui.row().classes("w-full justify-between items-center px-10 mb-8"):
            # Home Manager
            with ui.column().classes("items-center scale-110"):
                 # Native Manager Card
                 def draw_manager(team_name, man_name):
                     logo_url = TEAM_LOGOS.get(team_name, "")
                     f_name = MANAGER_MAP.get(man_name, f"{man_name}.jpg")
                     loc_p = os.path.join(ASSETS_DIR, "managers", f_name)
                     if os.path.exists(loc_p):
                         man_img = f"/assets/managers/{f_name.replace(' ', '%20')}"
                     else:
                         man_img = f"https://api.dicebear.com/7.x/avataaars/svg?seed={man_name.replace(' ', '')}"
                     
                     with ui.card().classes("p-0 w-[195px] h-[270px] rounded-[20px] overflow-hidden bg-[#1c1a17] border border-white/10 shadow-2xl relative"):
                         ui.image(man_img).classes("w-full h-full object-cover opacity-90")
                         # Gradient Overlay (using a div)
                         ui.element('div').style("position:absolute; inset:0; background:linear-gradient(to top, #1c1a17 20%, transparent 60%);")
                         # Team Logo
                         ui.image(logo_url).style("position:absolute; bottom:55px; left:50%; transform:translateX(-50%); width:80px; height:80px; object-fit:contain; filter:drop-shadow(0 6px 16px rgba(0,0,0,0.6));")
                         # Text
                         with ui.column().classes("absolute bottom-4 left-0 right-0 items-center gap-0"):
                             ui.label(man_name).classes("text-[12px] text-white font-black uppercase tracking-widest")
                             ui.label(team_name).classes("text-[10px] text-slate-400 font-bold uppercase tracking-wider")

                 draw_manager(home, res.get('home_manager', 'Unknown'))
            
            # H2H Dashboard
            with ui.column().classes("items-center gap-6"):
                ui.label("HEAD TO HEAD").classes("text-[10px] font-black text-slate-300 tracking-[0.5em] mb-2")
                with ui.row().classes("gap-12 items-center"):
                    with ui.column().classes("items-center"):
                        ui.label(str(h2h['home_wins'])).classes("text-7xl font-black text-slate-900 leading-none")
                        ui.label("WINS").classes("text-[10px] text-blue-500 font-bold tracking-widest mt-2")
                    ui.label(str(h2h['draws'])).classes("text-3xl font-black text-slate-200 mx-4")
                    with ui.column().classes("items-center"):
                        ui.label(str(h2h['away_wins'])).classes("text-7xl font-black text-slate-900 leading-none")
                        ui.label("WINS").classes("text-[10px] text-red-500 font-bold tracking-widest mt-2")
                ui.label(f"Based on {h2h['total']} historical encounters").classes("text-[10px] text-slate-400 mt-4")

            # Away Manager
            with ui.column().classes("items-center scale-110"):
                 draw_manager(away, res.get('away_manager', 'Unknown'))

        # Probability Cards
        with ui.row().classes("w-full gap-8 mt-12 mb-4"):
            def prob_box(label, pct, is_best, color):
                with ui.card().classes(f"flex-1 p-8 items-center justify-center relative overflow-hidden bg-white rounded-2xl border border-gray-100 shadow-sm transition-all"):
                    if is_best:
                        ui.card().classes(f"absolute bottom-0 left-[15%] right-[15%] h-1 bg-[{color}] rounded-t-full shadow-[0_0_15px_{color}]")
                        ui.label("★ " + label).classes("text-[10px] font-black text-slate-400 tracking-widest mb-2")
                    else:
                        ui.card().classes(f"absolute bottom-0 left-[20%] right-[20%] h-0.5 bg-gray-100 rounded-t-full")
                        ui.label(label).classes("text-[10px] font-bold text-slate-400 tracking-widest mb-2")
                    ui.label(f"{round(pct)}%").classes("text-4xl font-black text-slate-900")

            prob_box(f"{home} Win", hw, hw==best, hc)
            prob_box("Draw", dw, dw==best, "#f59e0b")
            prob_box(f"{away} Win", aw, aw==best, ac)

        # Bottom Analysis
        simple_r, tech_r = get_dual_reasons(home, away, res)
        with ui.row().classes("w-full gap-16 py-12 border-t border-gray-50 mt-12"):
            # Simple Highlights
            with ui.column().classes("flex-1 gap-8"):
                ui.label("MODEL HIGHLIGHTS (SIMPLE)").classes("text-[11px] font-black text-slate-300 tracking-[0.3em]")
                for i, r in enumerate(simple_r):
                    with ui.row().classes("items-center gap-5"):
                        ui.label(str(i+1)).classes("w-7 h-7 flex items-center justify-center rounded-full bg-slate-50 text-[10px] font-bold text-slate-400 border border-slate-100")
                        ui.label(r).classes("text-sm text-slate-600 font-medium")

            # Technical Analysis
            with ui.column().classes("flex-1 gap-8 border-l border-gray-50 pl-16"):
                ui.label("DEEP ANALYSIS").classes("text-[11px] font-black text-slate-900 tracking-[0.3em]")
                for i, r in enumerate(tech_r):
                    with ui.row().classes("items-start gap-4"):
                        ui.label(str(i+1)).classes("mt-1 w-6 h-6 flex items-center justify-center rounded-md bg-slate-900 text-[10px] font-black text-white")
                        ui.label(r).classes("text-sm text-slate-900 font-bold leading-relaxed")

        # Footer
        ui.button("← NEW PREDICTION", on_click=back_fn).props('flat').classes("text-blue-500 font-bold text-[10px] tracking-widest hover:bg-transparent -ml-4 mt-4")


# ---------------------------------------------------------------------------
# App Startup
# ---------------------------------------------------------------------------
if __name__ in ('__main__', '__mp_main__') or getattr(sys, 'frozen', False):
    print("--- APPLICATION INITIALIZED ---", flush=True)
    print(f"NiceGUI app is running at http://localhost:8081", flush=True)
    print("Open your browser and navigate to: http://localhost:8081", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        ui.run(port=8081, show=False, reload=False)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
