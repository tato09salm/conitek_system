import streamlit as st
from config import Config
from services.database import init_db, SessionLocal
from models.participant import Participant
from models.event_speaker import EventSpeaker
from models.paper import Paper
from components.ui import header

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS (TEMA UNT TRUJILLO)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="CONITEK 2026", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definición de la paleta de colores
COLORS = {
    "navy": "#000080",
    "dodgerblue": "#1e90ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "olive": "#808000",
    "yellow": "#ffff00",
    "black": "#000000",
    "white": "#ffffff",
    "light_gray": "#f0f2f6"
}

# CSS Personalizado para inyectar el estilo
def load_css():
    st.markdown(f"""
    <style>
        /* --- Variables Globales --- */
        :root {{
            --primary-color: {COLORS["navy"]};
            --secondary-color: {COLORS["gold"]};
            --accent-color: {COLORS["dodgerblue"]};
            --text-color: {COLORS["black"]};
            --bg-color: {COLORS["white"]};
        }}

        /* --- Fondo General y Texto --- */
        .stApp {{
            background-color: var(--bg-color);
            color: var(--text-color);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: var(--primary-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 10px;
        }}

        /* --- Barra Lateral (Sidebar) --- */
        section[data-testid="stSidebar"] {{
            background-color: var(--primary-color);
            color: var(--white);
        }}
        
        /* Texto dentro del sidebar */
        section[data-testid="stSidebar"] * {{
            color: {COLORS["white"]} !important;
        }}

        /* Enlaces del menú de navegación en el sidebar */
        .stSidebar .stNav a {{
            color: {COLORS["white"]} !important;
            font-weight: 500;
        }}
        
        .stSidebar .stNav a:hover {{
            color: var(--secondary-color) !important;
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        /* Elemento activo en el sidebar */
        .stSidebar .stNav li[class*="active"] a {{
            color: var(--secondary-color) !important;
            border-left: 4px solid var(--secondary-color);
        }}

        /* --- Botones --- */
        .stButton > button {{
            background-color: var(--primary-color);
            color: var(--secondary-color);
            border: 1px solid var(--primary-color);
            font-weight: bold;
            border-radius: 5px;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            background-color: var(--accent-color);
            color: var(--white);
            border-color: var(--accent-color);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        /* --- Inputs y Campos de Texto --- */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {{
            border: 1px solid var(--primary-color);
            color: var(--text-color);
        }}
        
        .stTextInput > div > div > input:focus, 
        .stSelectbox > div > div > select:focus {{
            border-color: var(--accent-color);
            box-shadow: 0 0 5px rgba(30, 144, 255, 0.5);
        }}

        /* --- Tablas y Dataframes --- */
        .stDataFrame {{
            border: 1px solid var(--goldenrod);
        }}
        div[data-testid="stDataFrame"] thead tr th {{
            background-color: var(--primary-color);
            color: var(--secondary-color);
        }}

        /* --- Alertas y Cajas de Información --- */
        .stInfo {{
            border-left: 5px solid var(--olive);
            background-color: #fafaf0;
        }}
        .stWarning {{
            border-left: 5px solid var(--goldenrod);
        }}
        .stError {{
            border-left: 5px solid #d9534f;
        }}
        .stSuccess {{
            border-left: 5px solid #5cb85c;
        }}

        /* --- Header Personalizado (Ajuste fino) --- */
        .header-container {{
            background: linear-gradient(90deg, {COLORS["navy"]} 0%, {COLORS["dodgerblue"]} 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
            border-bottom: 5px solid {COLORS["gold"]};
        }}
        
        /* Ocultar el footer default de streamlit para limpieza */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Decoración UNT */
        .unt-badge {{
            color: {COLORS["gold"]};
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    </style>
    """, unsafe_allow_html=True)

# Cargar estilos al iniciar
load_css()

# -----------------------------------------------------------------------------
# LÓGICA DE LA APLICACIÓN
# -----------------------------------------------------------------------------

init_db()

# Navegación según sesión y rol
if 'user' in st.session_state:
    # Resolver rol del usuario de forma robusta
    role = None
    user = st.session_state.get('user')
    if isinstance(user, dict):
        role = user.get('role') or user.get('rol') or user.get('perfil')
    if role is None:
        role = st.session_state.get('role')
    role_l = str(role).lower() if role else ""

    pages = []
    # Panel Principal solo para administrador y tesorero
    if role_l in ["admin", "administrador", "tesorero", "tesoreria", "tesorería"]:
        pages.append(st.Page("pages/02_Dashboard.py", title="Panel Principal", icon=":material/dashboard:"))

    # Ponencias visible para Admin/Evaluador o participante ponente
    show_ponencias = False
    if role_l in ["admin", "administrador", "evaluador"]:
        show_ponencias = True
    else:
        user_val = st.session_state.get("user")
        if user_val:
            dbx = SessionLocal()
            try:
                me = dbx.query(Participant).filter(Participant.dni == str(user_val)).first()
                if me:
                    has_paper = dbx.query(Paper).filter(Paper.participant_id == me.id).first() is not None
                    is_speaker = dbx.query(EventSpeaker).filter(EventSpeaker.participant_id == me.id).first() is not None
                    show_ponencias = has_paper or is_speaker
            finally:
                dbx.close()
    if show_ponencias:
        pages.append(st.Page("pages/04_Gestion_Ponencias.py", title="Ponencias", icon=":material/article:"))
    pages.append(st.Page("pages/05_Gestion_Pagos.py", title="Tesorería", icon=":material/payments:"))
    # Participantes solo para administrador
    if role_l in ["admin", "administrador"]:
        pages.insert(1, st.Page("pages/03_Gestion_Participantes.py", title="Participantes", icon=":material/people:"))
    if role_l in ["admin", "administrador", "tesorero", "tesoreria", "tesorería"]:
        pages.append(st.Page("pages/banner.py", title="Banner", icon=":material/image:"))

    # Eventos y Detalle de Evento solo para administrador y tesorero (visibles)
    if role_l in ["admin", "administrador", "tesorero", "tesoreria", "tesorería"]:
        pages.append(st.Page("pages/07_Eventos.py", title="Eventos", icon=":material/event:"))
        pages.append(st.Page("pages/07_Evento_Detalle.py", title="Detalle de Evento", icon=":material/description:"))
        pages.append(st.Page("pages/10_audit.py", title="Auditoría", icon=":material/manage_search:"))

    # Resto
    pages.extend([
        st.Page("pages/09_Inscripciones.py", title="Inscripciones", icon=":material/assignment_add:"),
        st.Page("pages/08_Usuarios.py", title="Usuarios", icon=":material/manage_accounts:"),
        st.Page("pages/06_Certificados.py", title="Certificados", icon=":material/verified:"),
        st.Page("pages/00_Logout.py", title="Cerrar Sesión", icon=":material/logout:"),
    ])
else:
    pages = [
        st.Page("pages/01_Login.py", title="Ingreso", icon=":material/login:"),
    ]

pg = st.navigation(pages)
pg.run()
