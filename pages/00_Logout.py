import streamlit as st
from services.audit import log_event

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Cerrar Sesión - CONITEK 2026",
    page_icon="🚪",
    layout="centered"
)

COLORS = {
    "navy": "#000080",
    "blue": "#1e90ff",
    "gold": "#ffd700",
    "white": "#ffffff",
    "light_gray": "#f8f9fa",
    "red": "#dc3545"
}

# -----------------------------------------------------------------------------
# ESTILOS AISLADOS SOLO PARA LOGOUT
# -----------------------------------------------------------------------------

# Solo aplicar si no hay navegación activa o estamos en logout
if "page" not in st.session_state or st.session_state.get("page") == "logout":
    st.markdown(f"""
    <style>
        /* Selector específico para esta página */
        [data-testid="stAppViewContainer"] > div:first-child {{
            background: linear-gradient(135deg, {COLORS["light_gray"]} 0%, {COLORS["white"]} 100%);
        }}
        
        /* Solo ocultar en esta página */
        .logout-page #MainMenu, 
        .logout-page footer {{
            visibility: hidden;
        }}
        
        .logout-page .block-container {{
            padding: 1rem !important;
            max-width: 450px !important;
        }}
        
        /* Tarjeta compacta */
        .logout-card {{
            background: {COLORS["white"]};
            border-radius: 12px;
            padding: 25px 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-top: 4px solid {COLORS["gold"]};
            text-align: center;
            animation: fadeIn 0.5s ease;
        }}
        
        /* Oso más pequeño */
        .bear-container {{
            width: 100px;
            height: 100px;
            margin: 0 auto 15px;
            position: relative;
        }}
        
        .bear {{
            width: 100%;
            height: 100%;
            position: relative;
        }}
        
        /* Cabeza reducida */
        .bear-head {{
            width: 55px;
            height: 55px;
            background: linear-gradient(135deg, #8B4513, #A0522D);
            border-radius: 50%;
            position: absolute;
            top: 28px;
            left: 22px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }}
        
        /* Orejas pequeñas */
        .bear-ear {{
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #8B4513, #A0522D);
            border-radius: 50%;
            position: absolute;
            top: 20px;
        }}
        
        .bear-ear.left {{
            left: 17px;
            animation: earWiggle 2s ease-in-out infinite;
        }}
        
        .bear-ear.right {{
            right: 17px;
            animation: earWiggle 2s ease-in-out infinite 0.1s;
        }}
        
        /* Ojos */
        .bear-eye {{
            width: 8px;
            height: 8px;
            background: #000;
            border-radius: 50%;
            position: absolute;
            top: 38px;
            animation: blink 3s ease-in-out infinite;
        }}
        
        .bear-eye.left {{ left: 30px; }}
        .bear-eye.right {{ right: 30px; }}
        
        /* Hocico */
        .bear-snout {{
            width: 28px;
            height: 22px;
            background: #D2691E;
            border-radius: 50%;
            position: absolute;
            bottom: 32px;
            left: 36px;
        }}
        
        .bear-nose {{
            width: 8px;
            height: 7px;
            background: #000;
            border-radius: 50%;
            position: absolute;
            top: 3px;
            left: 10px;
        }}
        
        .bear-mouth {{
            width: 14px;
            height: 7px;
            border: 1.5px solid #000;
            border-top: none;
            border-radius: 0 0 14px 14px;
            position: absolute;
            bottom: 3px;
            left: 7px;
        }}
        
        /* Birrete compacto */
        .graduation-cap {{
            position: absolute;
            top: 14px;
            left: 20px;
            z-index: 10;
        }}
        
        .cap-top {{
            width: 50px;
            height: 4px;
            background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
            border-radius: 2px;
            position: relative;
            transform: rotate(-5deg);
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}
        
        .cap-base {{
            width: 28px;
            height: 14px;
            background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
            border-radius: 4px 4px 0 0;
            position: absolute;
            top: 4px;
            left: 11px;
        }}
        
        .cap-tassel {{
            width: 1.5px;
            height: 18px;
            background: {COLORS["gold"]};
            position: absolute;
            top: 0;
            right: 7px;
            animation: tasselSwing 2s ease-in-out infinite;
        }}
        
        .cap-tassel::after {{
            content: '';
            width: 6px;
            height: 6px;
            background: {COLORS["gold"]};
            border-radius: 50%;
            position: absolute;
            bottom: -3px;
            left: -2.5px;
        }}
        
        /* Brazo compacto */
        .bear-arm {{
            width: 18px;
            height: 35px;
            background: linear-gradient(135deg, #8B4513, #A0522D);
            border-radius: 12px;
            position: absolute;
            top: 55px;
            right: 14px;
            transform-origin: top center;
            animation: wave 1s ease-in-out infinite;
        }}
        
        .bear-hand {{
            width: 14px;
            height: 14px;
            background: #D2691E;
            border-radius: 50%;
            position: absolute;
            bottom: -3px;
            left: 2px;
        }}
        
        /* Texto Bye compacto */
        .bye-text {{
            position: absolute;
            top: 15px;
            right: -35px;
            font-size: 18px;
            font-weight: 800;
            color: {COLORS["gold"]};
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            animation: byeFade 2s ease-in-out infinite;
        }}
        
        /* Animaciones */
        @keyframes wave {{
            0%, 100% {{ transform: rotate(-20deg); }}
            50% {{ transform: rotate(20deg); }}
        }}
        
        @keyframes tasselSwing {{
            0%, 100% {{ transform: rotate(-5deg); }}
            50% {{ transform: rotate(5deg); }}
        }}
        
        @keyframes blink {{
            0%, 90%, 100% {{ transform: scaleY(1); }}
            95% {{ transform: scaleY(0.1); }}
        }}
        
        @keyframes earWiggle {{
            0%, 100% {{ transform: rotate(-5deg); }}
            50% {{ transform: rotate(5deg); }}
        }}
        
        @keyframes byeFade {{
            0%, 100% {{ opacity: 0.6; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.1); }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(15px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Títulos compactos */
        .logout-title {{
            color: {COLORS["navy"]};
            font-size: 24px;
            font-weight: 800;
            margin: 0 0 8px 0;
        }}
        
        .logout-title span {{
            color: {COLORS["gold"]};
        }}
        
        .logout-subtitle {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        
        /* Botón compacto */
        .logout-page .stButton > button {{
            width: 100%;
            background: linear-gradient(135deg, {COLORS["red"]}, #e74c3c);
            color: {COLORS["white"]};
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-weight: 700;
            font-size: 14px;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
        }}
        
        .logout-page .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(220, 53, 69, 0.4);
        }}
        
        /* Alertas compactas */
        .logout-page .stAlert {{
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 12px;
            text-align: center;
            margin-top: 15px;
            border: none;
        }}
        
        /* Footer compacto */
        .logout-footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 11px;
        }}
        
        .logout-footer strong {{
            color: {COLORS["gold"]};
        }}
    </style>
    """, unsafe_allow_html=True)

# Marcar el body con clase para aislar estilos
st.markdown('<div class="logout-page">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONTENIDO CON OSO ANIMADO COMPACTO
# -----------------------------------------------------------------------------

st.markdown("""
<div class="logout-card">
    <div class="bear-container">
        <div class="bear">
            <div class="graduation-cap">
                <div class="cap-top">
                    <div class="cap-tassel"></div>
                </div>
                <div class="cap-base"></div>
            </div>
            <div class="bear-head">
                <div class="bear-ear left"></div>
                <div class="bear-ear right"></div>
                <div class="bear-eye left"></div>
                <div class="bear-eye right"></div>
                <div class="bear-snout">
                    <div class="bear-nose"></div>
                    <div class="bear-mouth"></div>
                </div>
            </div>
            <div class="bear-arm">
                <div class="bear-hand"></div>
            </div>
            <div class="bye-text">Bye!</div>
        </div>
    </div>
    <h1 class="logout-title">Cerrar <span>Sesión</span></h1>
    <p class="logout-subtitle">¿Estás seguro que deseas salir del sistema?</p>
</div>
""", unsafe_allow_html=True)

# Botón de confirmación
if st.button("🔒 Confirmar Cierre de Sesión"):
    try:
        usr = st.session_state.get("user")
        log_event(usuario=str(usr) if usr else None, accion="LOGOUT", tabla="users", detalle="Cierre de sesión")
    except Exception:
        pass
    keys = list(st.session_state.keys())
    for k in keys:
        del st.session_state[k]
    
    st.success("✅ Sesión finalizada exitosamente")
    #st.balloons()
    st.snow()
    import time
    time.sleep(1)
    st.rerun()

# Información adicional
st.info("ℹ️ mao mao, el oso académico, te despide con cariño. ¡Hasta la próxima! 🎓🐻")

# Footer
st.markdown("""
<div class="logout-footer">
    <strong>🎓 Universidad Nacional de Trujillo</strong><br>
    CONITEK 2026 • Sistema de Gestión Académica
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Cerrar logout-page
