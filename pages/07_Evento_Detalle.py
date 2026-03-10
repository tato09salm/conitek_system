import streamlit as st
from services.database import SessionLocal
from models.event import Event
from models.event_registration import EventRegistration
from models.event_speaker import EventSpeaker
from models.participant import Participant
from models.payment import Payment
from models.paper import Paper
import base64
from services.reports import ReportService

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)

hdr_l, hdr_r = st.columns([3, 2])
with hdr_l:
    st.markdown("")

st.set_page_config(
    page_title="Detalle de Evento - CONITEK 2026",
    page_icon="📜",
    layout="centered"
)
######################################
COLORS = {
    "navy": "#000080",
    "blue": "#1e90ff",
    "gold": "#ffd700",
    "white": "#ffffff",
    "light_gray": "#f8f9fa",
    "gray": "#e0e0e0",
    "red": "#dc3545"
}

# -----------------------------------------------------------------------------
# ESTILOS COMPACTOS
# -----------------------------------------------------------------------------

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background: {COLORS["light_gray"]};
    }}
    
    #MainMenu, footer {{visibility: hidden;}}
    
    .block-container {{
        padding: 0 !important;
        max-width: 900px !important;
    }}
    
    /* Header compacto */
    .event-top-bar {{
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        padding: 10px 25px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }}
    
    .back-button {{
        color: {COLORS["white"]};
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    
    /* Contenedor principal compacto */
    .event-container {{
        padding: 20px 25px;
    }}
    
    /* Título compacto */
    .event-title {{
        text-align: center;
        color: {COLORS["navy"]};
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 20px;
        
    }}
    
    /* Tarjeta de info compacta */
    .event-info-card {{
        background: {COLORS["white"]};
        border-radius: 10px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid {COLORS["gold"]};
    }}
    
    .event-info-header {{
        color: {COLORS["navy"]};
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    
    .event-info-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        color: #333;
        font-size: 13px;
    }}
    
    .event-info-icon {{
        color: {COLORS["blue"]};
        font-size: 16px;
        width: 20px;
    }}
    
    /* Secciones compactas */
    .section-title {{
        color: {COLORS["navy"]};
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    
    /* Input de búsqueda compacto */
    .stTextInput input {{
        border-radius: 6px;
        border: 1px solid {COLORS["gray"]};
        padding: 6px 12px;
        font-size: 13px;
    }}
    
    .stTextInput input:focus {{
        border-color: {COLORS["blue"]};
        box-shadow: 0 0 0 1px rgba(30,144,255,0.2);
    }}
    
    /* Tarjeta de participante compacta */
    .participant-card {{
        background: {COLORS["white"]};
        border: 1px solid {COLORS["gray"]};
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.2s;
    }}
    
    .participant-card:hover {{
        border-color: {COLORS["blue"]};
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    .participant-avatar {{
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: {COLORS["white"]};
        font-size: 14px;
        font-weight: 700;
        flex-shrink: 0;
    }}
    
    .participant-info {{
        flex: 1;
        min-width: 0;
    }}
    
    .participant-dni {{
        color: {COLORS["blue"]};
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 2px;
    }}
    
    .participant-name {{
        color: {COLORS["navy"]};
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .participant-talk {{
        color: #666;
        font-size: 11px;
        font-style: italic;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    /* Estado vacío compacto */
    .empty-state {{
        text-align: center;
        padding: 25px 15px;
        background: {COLORS["white"]};
        border-radius: 8px;
        border: 2px dashed {COLORS["gray"]};
        color: #999;
    }}
    
    .empty-state-text {{
        font-size: 13px;
    }}
    
    /* Botones compactos */
    .stButton > button {{
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 6px 12px;
    }}
    
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 13px;
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0,0,128,0.25);
    }}
    
    /* Expander compacto */
    [data-testid="stExpander"] {{
        background: {COLORS["white"]};
        border-radius: 8px;
        border: 1px solid {COLORS["gray"]};
        margin-top: 15px;
    }}
    
    [data-testid="stExpander"] summary {{
        font-size: 13px;
        font-weight: 600;
        padding: 8px;
    }}
    
    /* PDF iframe */
    iframe {{
        border-radius: 8px;
        border: 1px solid {COLORS["gray"]};
    }}
    
    /* Columnas */
    [data-testid="column"] {{
        padding: 0 8px;
    }}
    
    /* Scroll compacto */
    .participants-scroll {{
        max-height: 350px;
        overflow-y: auto;
        padding-right: 8px;
    }}
    
    .participants-scroll::-webkit-scrollbar {{
        width: 6px;
    }}
    
    .participants-scroll::-webkit-scrollbar-track {{
        background: {COLORS["light_gray"]};
        border-radius: 3px;
    }}
    
    .participants-scroll::-webkit-scrollbar-thumb {{
        background: {COLORS["gold"]};
        border-radius: 3px;
    }}
    
    .participants-scroll::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["navy"]};
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VALIDAR ACCESO Y EVENTO
# -----------------------------------------------------------------------------

# Gate de acceso: solo admin (tolerante si 'user' no es dict)
_u = st.session_state.get("user")
if isinstance(_u, dict):
    _role_val = _u.get("role") or _u.get("rol") or _u.get("perfil")
else:
    _role_val = _u
_role = (st.session_state.get("role") or _role_val or "")
if str(_role).lower() not in ["admin", "administrador"]:
    st.warning("Solo el administrador puede acceder al Detalle de Evento")
    st.stop()

if "detail_event_target" not in st.session_state:
    st.info("ℹ️ No se seleccionó evento")
    st.stop()

event_id = st.session_state["detail_event_target"]

db = SessionLocal()
e = db.query(Event).get(event_id)
if not e:
    db.close()
    st.info("ℹ️ Evento no encontrado")
    st.stop()

# Obtener participantes aprobados
regs = db.query(EventRegistration).filter(EventRegistration.event_id == e.id).all()
approved = []
for r in regs:
    if r.payment_reference:
        pay = db.query(Payment).filter(
            Payment.reference == r.payment_reference,
            Payment.status == "Aprobado"
        ).first()
        if pay:
            p = db.query(Participant).get(r.participant_id)
            if p:
                approved.append(p)

# Obtener ponentes
speakers = db.query(EventSpeaker).filter(EventSpeaker.event_id == e.id).all()
speaker_rows = []
for sp in speakers:
    p = db.query(Participant).get(sp.participant_id)
    if p:
        pap = db.query(Paper).get(sp.paper_id) if getattr(sp, "paper_id", None) else None
        if not pap:
            pap = db.query(Paper).filter(
                Paper.participant_id == p.id
            ).order_by(Paper.id.desc()).first()
        t = (pap.title if pap and pap.title else "sin ponencia").strip()
        t_short = t[:40] + ("…" if len(t) > 40 else "")
        speaker_rows.append({
            "dni": p.dni,
            "name": p.full_name,
            "title": t_short,
            "paper_id": getattr(sp, "paper_id", None)
        })

db.close()

# Separar público
audience_rows = []
speaker_names = set([r["name"] for r in speaker_rows])
for p in approved:
    if p.full_name not in speaker_names:
        audience_rows.append({"dni": p.dni, "name": p.full_name})

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

hdr_l, hdr_r = st.columns([3, 2])
with hdr_l:
    st.markdown("### Detalle de Evento")
with hdr_r:
    pdf_top = ReportService.event_attendees_pdf_bytes(
        {"name": e.name, "location": e.location, "date": str(e.event_date)},
        [f"{r['dni']} {r['name']} - {r['title']}" for r in speaker_rows],
        [f"{r['dni']} {r['name']}" for r in audience_rows]
    )
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "📄 Descargar PDF",
            data=pdf_top,
            file_name=f"evento_{e.id}_participantes.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf_hdr"
        )
    with c2:
        if st.button("⬅️ Regresar", use_container_width=True, key="back_events_hdr"):
            st.switch_page("pages/07_Eventos.py")

# -----------------------------------------------------------------------------
# CONTENIDO
# -----------------------------------------------------------------------------

st.markdown('<div class="event-container">', unsafe_allow_html=True)

#

# Info del evento
st.markdown(f"""
<div class="event-info-card">
    <div class="event-info-header">Información del Evento</div>
    <div class="event-info-row">
        <span class="event-info-icon">🎓</span>
        <span>{e.name}</span>
    </div>
    <div class="event-info-row">
        <span class="event-info-icon">📍</span>
        <span>{e.location}</span>
    </div>
    <div class="event-info-row">
        <span class="event-info-icon">📅</span>
        <span>{e.event_date}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Botón exportar
pdf_speakers = [f"{r['dni']} {r['name']} - {r['title']}" for r in speaker_rows]
pdf_audience = [f"{r['dni']} {r['name']}" for r in audience_rows]
pdf_bytes = ReportService.event_attendees_pdf_bytes(
    {"name": e.name, "location": e.location, "date": str(e.event_date)},
    pdf_speakers,
    pdf_audience
)

st.download_button(
    "📄 Exportar Lista (PDF)",
    data=pdf_bytes,
    file_name=f"evento_{e.id}_participantes.pdf",
    mime="application/pdf"
)

# Dos columnas
col_speakers, col_audience = st.columns(2)

def matches(item, q):
    if not q:
        return True
    s = q.lower().strip()
    return s in item["dni"].lower() or s in item["name"].lower()

# PONENTES
with col_speakers:
    st.markdown('<div class="section-title">Ponentes</div>', unsafe_allow_html=True)
    qsp = st.text_input("", placeholder="🔍 DNI o nombre", key="search_sp", label_visibility="collapsed")
    
    speaker_view = [r for r in speaker_rows if matches(r, qsp)]
    
    st.markdown('<div class="participants-scroll">', unsafe_allow_html=True)
    if speaker_view:
        for r in speaker_view:
            initial = r["name"][0].upper() if r["name"] else "?"
            
            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                <div class="participant-card">
                    <div class="participant-avatar">{initial}</div>
                    <div class="participant-info">
                        <div class="participant-dni">DNI: {r['dni']}</div>
                        <div class="participant-name">{r['name']}</div>
                        <div class="participant-talk">{r['title']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("🗑️", key=f"rm_{r['dni']}_{r.get('paper_id', 'none')}", help="Quitar"):
                    dbx = SessionLocal()
                    p = dbx.query(Participant).filter(Participant.dni == r["dni"]).first()
                    if p:
                        q = dbx.query(EventSpeaker).filter(
                            EventSpeaker.event_id == e.id,
                            EventSpeaker.participant_id == p.id
                        )
                        if r.get("paper_id") is not None:
                            q = q.filter(EventSpeaker.paper_id == r["paper_id"])
                        es = q.first()
                        if es:
                            dbx.delete(es)
                            dbx.commit()
                    dbx.close()
                    st.rerun()
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-text">No hay ponentes registrados</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# PÚBLICO
with col_audience:
    st.markdown('<div class="section-title">Público</div>', unsafe_allow_html=True)
    qau = st.text_input("", placeholder="🔍 DNI o nombre", key="search_au", label_visibility="collapsed")
    
    audience_view = [r for r in audience_rows if matches(r, qau)]
    
    st.markdown('<div class="participants-scroll">', unsafe_allow_html=True)
    if audience_view:
        for r in audience_view:
            initial = r["name"][0].upper() if r["name"] else "?"
            st.markdown(f"""
            <div class="participant-card">
                <div class="participant-avatar">{initial}</div>
                <div class="participant-info">
                    <div class="participant-dni">DNI: {r['dni']}</div>
                    <div class="participant-name">{r['name']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-text">Aún no hay público inscrito</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Vista previa PDF
with st.expander("📄 Vista Previa del PDF", expanded=False):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='400px'></iframe>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
