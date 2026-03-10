import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from services.database import SessionLocal
from models.participant import Participant
from models.payment import Payment
from models.event import Event
from models.event_registration import EventRegistration
import plotly.express as px
import plotly.graph_objects as go
from services.reports import ReportService
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard - CONITEK 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de colores UNT
COLORS = {
    "navy": "#000080",
    "dodgerblue": "#1e90ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "olive": "#808000",
    "white": "#ffffff",
    "light_gray": "#f8f9fa"
}

def load_dashboard_css():
    """Estilos aislados solo para el dashboard"""
    st.markdown(f"""
    <style>
        /* Aplicar solo en esta página del dashboard */
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(135deg, {COLORS["light_gray"]} 0%, {COLORS["white"]} 100%);
        }}
        
        /* Ocultar elementos */
        #MainMenu, footer {{visibility: hidden;}}
        
        /* Contenedor principal compacto */
        .block-container {{
            padding: 1.5rem 2rem !important;
            max-width: 1400px;
        }}
        
        /* Header compacto */
        .dashboard-header {{
            background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["dodgerblue"]} 100%);
            border-radius: 12px;
            padding: 20px 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .dashboard-header h1 {{
            color: {COLORS["white"]};
            font-size: 26px;
            font-weight: 800;
            margin: 0;
        }}
        
        .dashboard-header h1 span {{
            color: {COLORS["gold"]};
        }}
        
        .user-info {{
            color: {COLORS["gold"]};
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .role-badge {{
            display: inline-block;
            padding: 3px 10px;
            background-color: {COLORS["gold"]};
            color: {COLORS["navy"]};
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
            margin-left: 8px;
        }}
        
        /* Métricas compactas */
        [data-testid="stMetric"] {{
            background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["dodgerblue"]});
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid {COLORS["gold"]};
            box-shadow: 0 3px 10px rgba(0,0,128,0.12);
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {COLORS["gold"]} !important;
            font-weight: 600;
            font-size: 13px;
        }}
        
        [data-testid="stMetricValue"] {{
            color: {COLORS["white"]} !important;
            font-size: 28px;
            font-weight: 700;
        }}
        
        [data-testid="stMetricDelta"] {{
            color: {COLORS["white"]} !important;
            opacity: 0.85;
            font-size: 12px;
        }}
        
        /* Títulos de sección */
        .section-title {{
            color: {COLORS["navy"]};
            font-size: 20px;
            font-weight: 700;
            border-left: 4px solid {COLORS["gold"]};
            padding-left: 12px;
            margin: 20px 0 15px 0;
        }}
        
        /* Contenedores de gráficos */
        .chart-wrapper {{
            background: {COLORS["white"]};
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-top: 3px solid {COLORS["goldenrod"]};
        }}
        
        .chart-wrapper h3 {{
            color: {COLORS["navy"]};
            font-size: 16px;
            font-weight: 700;
            margin: 0 0 12px 0;
        }}
        
        /* Expander compacto */
        [data-testid="stExpander"] {{
            background: {COLORS["white"]};
            border-radius: 8px;
            border: 1px solid {COLORS["goldenrod"]};
            margin-top: 15px;
        }}
        
        /* Botón de descarga */
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["dodgerblue"]});
            color: {COLORS["white"]};
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.3s;
        }}
        
        .stDownloadButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,128,0.3);
        }}
        
        /* Footer compacto */
        .dashboard-footer {{
            text-align: center;
            padding: 15px;
            margin-top: 20px;
            background: {COLORS["white"]};
            border-radius: 10px;
            border-top: 3px solid {COLORS["gold"]};
            color: {COLORS["navy"]};
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .dashboard-footer strong {{
            color: {COLORS["gold"]};
        }}
        
        /* DataFrames */
        [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .block-container {{
                padding: 1rem !important;
            }}
            .dashboard-header {{
                padding: 15px;
            }}
            .dashboard-header h1 {{
                font-size: 22px;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

# Cargar estilos solo si estamos autenticados
if 'user' in st.session_state:
    load_dashboard_css()

# -----------------------------------------------------------------------------
# VERIFICACIÓN DE AUTENTICACIÓN
# -----------------------------------------------------------------------------

if 'user' not in st.session_state:
    st.warning("🔐 Por favor inicie sesión para acceder al dashboard.")
    st.stop()
    
u = st.session_state.get('user')
username = u if isinstance(u, str) else getattr(u, 'username', 'Usuario')
user_role = st.session_state.get('role', '-')

# -----------------------------------------------------------------------------
# CONSULTAS A LA BASE DE DATOS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=300)
def get_dashboard_data():
    db = SessionLocal()
    try:
        total_participants = db.query(Participant).count()
        total_payments = db.query(Payment).filter(Payment.status == "Aprobado").count()
        total_revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "Aprobado").scalar() or 0
        
        participants_by_uni = db.query(
            Participant.university,
            func.count(Participant.id).label('count')
        ).group_by(Participant.university).order_by(desc('count')).all()
        
        participants_by_type = db.query(
            Participant.p_type,
            func.count(Participant.id).label('count')
        ).group_by(Participant.p_type).all()
        
        participants_by_modality = db.query(
            Participant.modality,
            func.count(Participant.id).label('count')
        ).group_by(Participant.modality).all()
        
        payments_by_method = db.query(
            Payment.method,
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).filter(Payment.status == "Aprobado").group_by(Payment.method).all()
        
        registrations_by_event = db.query(
            Event.name,
            func.count(EventRegistration.id).label('count')
        ).join(EventRegistration, Event.id == EventRegistration.event_id).group_by(Event.name).all()
        
        payments_by_status = db.query(
            Payment.status,
            func.count(Payment.id).label('count')
        ).group_by(Payment.status).all()
        
        return {
            "total_participants": total_participants,
            "total_payments": total_payments,
            "total_revenue": total_revenue,
            "participants_by_uni": participants_by_uni,
            "participants_by_type": participants_by_type,
            "participants_by_modality": participants_by_modality,
            "payments_by_method": payments_by_method,
            "registrations_by_event": registrations_by_event,
            "payments_by_status": payments_by_status
        }
    finally:
        db.close()

data = get_dashboard_data()

# -----------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------

# Header compacto
st.markdown(f"""
<div class="dashboard-header">
    <h1>📊 Dashboard General - <span>Sistemas UNITRU</span></h1>
    <div class="user-info">
        👤 {username} <span class="role-badge">{user_role}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Métricas principales
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("👥 Total Participantes", data["total_participants"], "Registrados")
with c2:
    st.metric("✅ Pagos Aprobados", data["total_payments"], "Transacciones")
with c3:
    st.metric("💰 Recaudación Total", f"S/. {data['total_revenue']:.2f}", "Soles")

# Título de sección
st.markdown('<h2 class="section-title">📈 Estadísticas Detalladas</h2>', unsafe_allow_html=True)

# Lista para exportar gráficos y títulos
export_figs = []
export_titles = []

# Fila 1: Universidad y Tipo
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>🏛️ Participantes por Universidad</h3>', unsafe_allow_html=True)
    
    if data["participants_by_uni"]:
        df_uni = [{"Universidad": row[0] or "Sin registrar", "Cantidad": row[1]} for row in data["participants_by_uni"]]
        fig_uni = px.bar(
            df_uni, x="Universidad", y="Cantidad",
            color="Cantidad",
            color_continuous_scale=[COLORS["navy"], COLORS["dodgerblue"], COLORS["gold"]],
            text="Cantidad"
        )
        fig_uni.update_traces(textposition='outside', marker_line_width=1.5)
        fig_uni.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            coloraxis_showscale=False, height=320,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_uni, use_container_width=True)
        export_figs.append(fig_uni)
        export_titles.append("Participantes por Universidad")
    else:
        st.warning("⚠️ No hay datos")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>🎯 Participantes por Tipo</h3>', unsafe_allow_html=True)
    
    if data["participants_by_type"]:
        df_type = [{"Tipo": row[0] or "Sin clasificar", "Cantidad": row[1]} for row in data["participants_by_type"]]
        fig_type = px.pie(
            df_type, names="Tipo", values="Cantidad",
            color_discrete_map={
                "Estudiante": COLORS["dodgerblue"],
                "Profesional": COLORS["gold"],
                "Ponente": COLORS["olive"]
            }
        )
        fig_type.update_traces(textposition='inside', textinfo='percent+label')
        fig_type.update_layout(
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            height=320, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig_type, use_container_width=True)
        export_figs.append(fig_type)
        export_titles.append("Participantes por Tipo")
    else:
        st.warning("⚠️ No hay datos")
    st.markdown('</div>', unsafe_allow_html=True)

# Fila 2: Modalidad y Pagos
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>💻 Modalidad de Participación</h3>', unsafe_allow_html=True)
    
    if data["participants_by_modality"]:
        df_mod = [{"Modalidad": row[0] or "Sin definir", "Cantidad": row[1]} for row in data["participants_by_modality"]]
        fig_mod = px.bar(
            df_mod, x="Modalidad", y="Cantidad",
            color="Modalidad",
            color_discrete_map={
                "Presencial": COLORS["navy"],
                "Virtual": COLORS["dodgerblue"]
            }
        )
        fig_mod.update_traces(texttemplate='%{y}', textposition='outside')
        fig_mod.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            showlegend=False, height=320,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_mod, use_container_width=True)
        export_figs.append(fig_mod)
        export_titles.append("Modalidad de Participación")
    else:
        st.warning("⚠️ No hay datos")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>💳 Métodos de Pago</h3>', unsafe_allow_html=True)
    
    if data["payments_by_method"]:
        df_pay = [{"Método": row[0] or "Efectivo", "Monto": float(row[2] or 0)} for row in data["payments_by_method"]]
        fig_pay = px.bar(
            df_pay, x="Método", y="Monto",
            color="Método",
            color_discrete_map={
                "Yape": COLORS["goldenrod"],
                "Plin": COLORS["olive"],
                "Transferencia": COLORS["dodgerblue"],
                "Efectivo": COLORS["navy"]
            },
            text="Monto"
        )
        fig_pay.update_traces(texttemplate='S/. %{text:.0f}', textposition='outside')
        fig_pay.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            height=320, margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_pay, use_container_width=True)
        export_figs.append(fig_pay)
        export_titles.append("Métodos de Pago")
    else:
        st.info("ℹ️ No hay pagos")
    st.markdown('</div>', unsafe_allow_html=True)

# Fila 3: Eventos y Estado
col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>🎪 Registraciones por Evento</h3>', unsafe_allow_html=True)
    
    if data["registrations_by_event"]:
        df_evt = [{"Evento": row[0], "Registrados": row[1]} for row in data["registrations_by_event"]]
        fig_evt = px.bar(
            df_evt, x="Evento", y="Registrados",
            color="Registrados",
            color_continuous_scale=[COLORS["olive"], COLORS["gold"]]
        )
        fig_evt.update_traces(texttemplate='%{y}', textposition='outside')
        fig_evt.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            coloraxis_showscale=False, height=320,
            margin=dict(l=20, r=20, t=20, b=50)
        )
        fig_evt.update_xaxes(tickangle=45)
        st.plotly_chart(fig_evt, use_container_width=True)
        export_figs.append(fig_evt)
        export_titles.append("Registraciones por Evento")
    else:
        st.warning("⚠️ No hay datos")
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3>📋 Estado de Pagos</h3>', unsafe_allow_html=True)
    
    if data["payments_by_status"]:
        df_status = [{"Estado": row[0] or "Desconocido", "Cantidad": row[1]} for row in data["payments_by_status"]]
        fig_status = px.pie(
            df_status, names="Estado", values="Cantidad",
            color="Estado",
            color_discrete_map={
                "Aprobado": COLORS["gold"],
                "Pendiente": COLORS["olive"],
                "Rechazado": COLORS["goldenrod"]
            }
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        fig_status.update_layout(
            font=dict(family="Segoe UI", color=COLORS["navy"]),
            height=320, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig_status, use_container_width=True)
        export_figs.append(fig_status)
        export_titles.append("Estado de Pagos")
    st.markdown('</div>', unsafe_allow_html=True)

# Botones de exportación
col_spacer, col_btn = st.columns([5, 1])
with col_btn:
    kpis = {
        "Total Participantes": data["total_participants"],
        "Pagos Aprobados": data["total_payments"],
        "Recaudación (S/.)": f"{data['total_revenue']:.2f}"
    }
    
    @st.cache_data
    def generate_dashboard_pdf(figs, title, kpis):
        return ReportService.dashboard_pdf_bytes(figs, title=title, kpis=kpis)
    
    pdf_bytes = generate_dashboard_pdf(export_figs, "Dashboard CONITEK 2026", kpis)
    st.download_button(
        "📄 Exportar PDF",
        data=pdf_bytes,
        file_name="dashboard_conitek.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# Tabla de resumen
with st.expander("📋 Ver Datos Detallados", expanded=False):
    summary_data = {
        "Métrica": [
            "Total Participantes",
            "Pagos Aprobados", 
            "Recaudación Total",
            "Universidades",
            "Eventos Activos"
        ],
        "Valor": [
            data["total_participants"],
            data["total_payments"],
            f"S/. {data['total_revenue']:.2f}",
            len(data["participants_by_uni"]),
            len(data["registrations_by_event"]) if data["registrations_by_event"] else 0
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

# Footer
st.markdown(f"""
<div class="dashboard-footer">
    <strong>🎓 Universidad Nacional de Trujillo</strong> • CONITEK 2026<br>
    Sistema de Gestión Académica • By: Tato09_Productions
</div>
""", unsafe_allow_html=True)

# Restricción de acceso por rol
if 'role' not in st.session_state or st.session_state['role'] not in ("Admin","Tesorero","Evaluador"):
    st.warning("No tiene permisos para ver el Dashboard.")
    st.stop()
