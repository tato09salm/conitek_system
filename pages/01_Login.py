import streamlit as st
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.user import User
import time
import os, json
from config import Config
from services.audit import log_event

# -------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------

st.set_page_config(
    page_title="ING DE SISTEMAS UNT - Acceso",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# COLORES UNT
# -------------------------------------------------------------

COLORS = {
    "navy": "#000080",
    "blue": "#1e90ff",
    "gold": "#ffd700",
    "white": "#ffffff",
    "gray_light": "#f8f9fa"
}

# -------------------------------------------------------------
# ESTILOS CSS COMPACTOS
# -------------------------------------------------------------

def load_css():
    st.markdown(f"""
    <style>
    
    /* Aplicar solo a la página de login */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, {COLORS["gray_light"]} 0%, {COLORS["white"]} 100%);
    }}
    
    #MainMenu, footer, header {{visibility: hidden;}}
    
    /* Contenedor principal compacto */
    .block-container {{
        padding: 1rem 1rem 0.5rem 1rem !important;
        max-width: 900px !important;
    }}
    
    /* Header compacto */
    .header-compact {{
        text-align: center;
        padding: 15px;
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    .header-compact h1 {{
        font-size: 28px;
        font-weight: 900;
        color: {COLORS["white"]};
        margin: 0;
        letter-spacing: 1px;
    }}
    
    .header-compact h1 span {{
        color: {COLORS["gold"]};
    }}
    
    .header-compact p {{
        font-size: 13px;
        color: {COLORS["gold"]};
        margin: 5px 0 0 0;
        font-weight: 600;
    }}
    
    /* Columnas */
    [data-testid="column"] {{
        padding: 0 10px !important;
    }}
    
    /* Imagen compacta */
    .image-wrapper {{
        background: white;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid {COLORS["gold"]};
        margin-bottom: 10px;
    }}
    
    .image-wrapper img {{
        border-radius: 8px;
    }}
    
    /* Info box compacta */
    .info-compact {{
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        border-radius: 10px;
        padding: 12px 15px;
        color: white;
        font-size: 12px;
        line-height: 1.6;
    }}
    
    .info-compact strong {{
        color: {COLORS["gold"]};
        display: block;
        margin-bottom: 8px;
        font-size: 14px;
    }}
    
    .info-compact ul {{
        margin: 0;
        padding-left: 20px;
    }}
    
    .info-compact li {{
        margin: 3px 0;
    }}
    
    /* Login card sin div extra */
    .stForm {{
        background: white;
        border-radius: 15px;
        padding: 25px 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        border-top: 4px solid {COLORS["gold"]};
    }}
    
    .login-title {{
        text-align: center;
        color: {COLORS["navy"]};
        font-size: 22px;
        font-weight: 800;
        margin: 0 0 5px 0;
    }}
    
    .login-subtitle {{
        text-align: center;
        color: #666;
        font-size: 13px;
        margin: 0 0 20px 0;
    }}
    
    /* Inputs compactos */
    .stTextInput > div > div {{
        margin-bottom: 8px !important;
    }}
    
    .stTextInput label {{
        font-weight: 600;
        color: {COLORS["navy"]};
        font-size: 13px;
        margin-bottom: 5px;
    }}
    
    .stTextInput input {{
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 10px 14px;
        font-size: 14px;
        transition: all 0.3s ease;
        outline: none !important;
    }}
    
    .stTextInput input:focus {{
        border-color: #e0e0e0 !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    
    /* Ocultar el texto 'Press Enter to submit form' */
    .stTextInput .stMarkdown {{
        display: none !important;
    }}
    
    /* Checkbox compacto */
    .stCheckbox {{
        margin: 10px 0 15px 0;
    }}
    
    .stCheckbox label {{
        font-size: 13px;
        color: {COLORS["navy"]};
    }}
    
    /* Botón compacto */
    .stButton > button {{
        width: 100%;
        padding: 12px;
        font-size: 15px;
        font-weight: 700;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 128, 0.25);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 128, 0.35);
    }}
    
    /* Alertas compactas */
    .stAlert {{
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 13px;
        margin: 10px 0;
    }}
    
    /* Footer compacto */
    .footer-compact {{
        text-align: center;
        padding: 15px;
        background: white;
        border-radius: 12px;
        margin-top: 15px;
        font-size: 11px;
        color: {COLORS["navy"]};
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    
    .footer-compact strong {{
        color: {COLORS["gold"]};
        font-size: 12px;
    }}
    
    /* Animación suave */
    .stForm {{
        animation: fadeIn 0.5s ease;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 0.5rem !important;
        }}
        .header-compact h1 {{
            font-size: 24px;
        }}
        .stForm {{
            padding: 20px 15px;
        }}
    }}
    
    </style>
    """, unsafe_allow_html=True)

# Solo cargar CSS si estamos en la página de login
if "authenticated" not in st.session_state or not st.session_state.get("authenticated"):
    load_css()

# -------------------------------------------------------------
# HEADER COMPACTO
# -------------------------------------------------------------

st.markdown("""
<div class="header-compact">
    <h1>🎓 INGENIERIA<span> DE </span> SISTEMAS UNT</h1>
    <p>Sistema de Gestión Académica</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# CONTENIDO EN DOS COLUMNAS
# -------------------------------------------------------------

col1, col2 = st.columns([1, 1.3])

# COLUMNA 1: IMAGEN + INFO
with col1:
    cfg_path = os.path.join(Config.ASSETS_DIR, "banner_config.json")
    defaults = {
        "image_path": "",
        "image_url": "https://image2url.com/r2/default/images/1772822996355-d97c481b-c863-4935-837e-ffd88abee4a3.jpg",
        "title": "📋 Información del Evento",
        "description": "📋 Información del Evento\n- Fecha: 15-17 Nov 2026\n- Presencial y Virtual\n- Sede: UNT\n- Certificación incluida",
        "grad_top": "#000080",
        "grad_bottom": "#1e90ff",
        "text_color": "#ffffff",
        "title_color": "#ffffff",
        "desc_color": "#ffffff",
        "max_height_px": 420
    }
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as rf:
                data = json.load(rf)
                if isinstance(data, dict):
                    defaults.update(data)
    except Exception:
        pass
    st.markdown(
        f"<style>"
        f".image-wrapper{{max-height:{int(defaults['max_height_px'])}px; overflow:hidden; border-radius:12px; border:2px solid {COLORS['gold']}; box-shadow:0 4px 12px rgba(0,0,0,0.08); margin-bottom:10px;}} "
        f".info-compact{{background: linear-gradient(135deg, {defaults['grad_top']} 0%, {defaults['grad_bottom']} 100%); border-radius:10px; padding:12px 15px; color:{defaults['text_color']}; font-size:12px; line-height:1.6;}} "
        f".info-compact .info-title{{color:{defaults['title_color']} !important; font-weight:700; margin-bottom:8px;}} "
        f".info-compact .info-desc{{color:{defaults['desc_color']} !important;}}"
        f"</style>",
        unsafe_allow_html=True
    )
    st.markdown('<div class="image-wrapper">', unsafe_allow_html=True)
    src = defaults.get("image_path") or defaults.get("image_url")
    if src and os.path.isfile(src):
        st.image(src, use_container_width=True)
    else:
        st.image(src, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="info-compact">
            <div class="info-title">{defaults.get('title') or 'Información'}</div>
            <div class="info-desc" style="white-space:pre-line;">{defaults.get('description') or ''}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# COLUMNA 2: LOGIN
with col2:
    st.markdown('<h2 class="login-title">Iniciar Sesión</h2>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Accede a tu cuenta del sistema</p>', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        
        username = st.text_input("👤 Usuario", placeholder="usuario UNT")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
        remember = st.checkbox("Recordar mi sesión")
        
        login_btn = st.form_submit_button("🚀 Ingresar")

        if login_btn:
            if username == "" or password == "":
                st.warning("⚠️ Complete todos los campos")
            else:
                with st.spinner("🔍 Verificando..."):
                    time.sleep(1)

                    db: Session = SessionLocal()
                    user = db.query(User).filter(
                        User.username == username,
                        User.password_hash == password
                    ).first()
                    db.close()

                    if user:
                        try:
                            log_event(usuario=user.username, accion="LOGIN", tabla="users", registro_id=user.id, detalle="Inicio de sesión")
                        except Exception:
                            pass
                        st.session_state["user"] = user.username
                        st.session_state["role"] = user.role
                        st.session_state["authenticated"] = True
                        st.success(f"✅ ¡Bienvenido {user.username}!")
                        st.rerun()
                    else:
                        try:
                            log_event(usuario=username, accion="LOGIN_FAIL", tabla="users", detalle="Intento de inicio fallido")
                        except Exception:
                            pass
                        st.error("❌ Credenciales incorrectas")

# -------------------------------------------------------------
# FOOTER COMPACTO
# -------------------------------------------------------------

st.markdown("""
<div class="footer-compact">
    <strong>Universidad Nacional de Trujillo</strong><br>
    ING DE SISTEMAS UNT| 📧 ingsistemas@unitru.edu.pe | 📞 (044) 474-852
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# CREAR USUARIOS DE PRUEBA
# -------------------------------------------------------------

def seed_users():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            users = [
                {"username":"admin", "email":"admin@unt.edu.pe", "password_hash":"123", "role":"Admin"},
                {"username":"tesorero", "email":"tesoreria@unt.edu.pe", "password_hash":"123", "role":"Tesorero"},
                {"username":"evaluador", "email":"evaluador@unt.edu.pe", "password_hash":"123", "role":"Evaluador"},
                {"username":"participante", "email":"user@unt.edu.pe", "password_hash":"123", "role":"Participante"}
            ]
            for u in users:
                db.add(User(**u))
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

if "seeded" not in st.session_state:
    seed_users()
    st.session_state["seeded"] = True
