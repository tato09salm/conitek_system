import streamlit as st
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.paper import Paper, Evaluation
from models.paper_file import PaperFile
from models.participant import Participant
from models.user import User
import pandas as pd
from components.downloads import export_buttons_df
import os
from config import Config
from services.audit import log_event

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Gestión de Ponencias - CONITEK 2026",
    page_icon="📄",
    layout="wide"
)

COLORS = {
    "navy": "#000080",
    "blue": "#1e90ff",
    "gold": "#ffd700",
    "white": "#ffffff",
    "light_gray": "#f8f9fa",
    "green": "#28a745",
    "red": "#dc3545",
    "orange": "#fd7e14"
}

# -----------------------------------------------------------------------------
# ESTILOS AISLADOS PARA PONENCIAS
# -----------------------------------------------------------------------------

st.markdown(f"""
<style>
    /* Aplicar solo en esta página */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, {COLORS["light_gray"]} 0%, {COLORS["white"]} 100%);
    }}
    
    #MainMenu, footer {{visibility: hidden;}}
    
    .block-container {{
        padding: 1.5rem 2rem !important;
        max-width: 1400px;
    }}
    
    /* Header de página */
    .papers-header {{
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        border-radius: 12px;
        padding: 15px 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    .papers-header h1 {{
        color: {COLORS["white"]};
        font-size: 24px;
        font-weight: 800;
        margin: 0;
    }}
    
    .papers-header h1 span {{
        color: {COLORS["gold"]};
    }}
    
    /* Expanders compactos */
    [data-testid="stExpander"] {{
        background: {COLORS["white"]};
        border-radius: 10px;
        border: 2px solid {COLORS["gold"]};
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    
    [data-testid="stExpander"] summary {{
        font-weight: 700;
        color: {COLORS["navy"]};
        font-size: 15px;
        padding: 12px;
    }}
    
    /* Formularios */
    .stForm {{
        background: {COLORS["light_gray"]};
        border-radius: 10px;
        padding: 15px;
    }}
    
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {{
        font-weight: 600;
        color: {COLORS["navy"]};
        font-size: 13px;
    }}
    
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {{
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        font-size: 14px;
    }}
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {{
        border-color: {COLORS["gold"]};
        box-shadow: 0 0 0 2px rgba(255,215,0,0.2);
    }}
    
    /* Botones de formulario */
    .stFormSubmitButton > button {{
        width: 100%;
        background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
        color: {COLORS["white"]};
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-weight: 700;
        font-size: 14px;
    }}
    
    /* Tabla CRUD personalizada */
    .crud-table {{
        background: {COLORS["white"]};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        border-top: 4px solid {COLORS["gold"]};
        margin: 20px 0;
    }}
    
    .table-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 12px;
        border-bottom: 2px solid {COLORS["gold"]};
    }}
    
    .table-header h3 {{
        color: {COLORS["navy"]};
        font-size: 18px;
        font-weight: 700;
        margin: 0;
    }}
    
    .table-stats {{
        background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
        color: {COLORS["white"]};
        padding: 5px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }}
    
    /* Lista interactiva de items */
    .paper-item {{
        background: {COLORS["white"]};
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        transition: all 0.3s;
        cursor: pointer;
    }}
    
    .paper-item:hover {{
        border-color: {COLORS["gold"]};
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    
    .paper-item.selected {{
        border-color: {COLORS["navy"]};
        background: linear-gradient(135deg, rgba(0,0,128,0.05), rgba(30,144,255,0.05));
        box-shadow: 0 4px 12px rgba(0,0,128,0.2);
    }}
    
    .paper-title {{
        color: {COLORS["navy"]};
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    
    .paper-meta {{
        display: flex;
        gap: 15px;
        font-size: 13px;
        color: #666;
    }}
    
    .paper-meta-item {{
        display: flex;
        align-items: center;
        gap: 5px;
    }}
    
    .status-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    
    .status-enviado {{
        background: {COLORS["orange"]};
        color: white;
    }}
    
    .status-evaluado {{
        background: {COLORS["blue"]};
        color: white;
    }}
    
    .status-aceptado {{
        background: {COLORS["green"]};
        color: white;
    }}
    
    .status-rechazado {{
        background: {COLORS["red"]};
        color: white;
    }}
    
    /* Panel de detalles */
    .detail-panel {{
        background: {COLORS["light_gray"]};
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
    }}
    
    .detail-section {{
        background: {COLORS["white"]};
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid {COLORS["gold"]};
    }}
    
    .detail-section h4 {{
        color: {COLORS["navy"]};
        font-size: 16px;
        font-weight: 700;
        margin: 0 0 12px 0;
    }}
    
    /* Botones de acción */
    .action-buttons {{
        display: flex;
        gap: 10px;
        margin-top: 15px;
        flex-wrap: wrap;
    }}
    
    .stButton > button {{
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.3s;
        border: none;
    }}
    
    /* Botón guardar */
    div[data-testid="column"]:nth-child(1) .stButton > button {{
        background: linear-gradient(135deg, {COLORS["green"]}, #20c997);
        color: white;
    }}
    
    /* Botón eliminar */
    div[data-testid="column"]:nth-child(2) .stButton > button {{
        background: linear-gradient(135deg, {COLORS["red"]}, #e74c3c);
        color: white;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    
    /* Archivos adjuntos */
    .file-item {{
        background: {COLORS["white"]};
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    
    .file-name {{
        color: {COLORS["navy"]};
        font-size: 13px;
        font-weight: 600;
    }}
    
    /* Área de búsqueda */
    .search-box {{
        background: {COLORS["white"]};
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    
    /* Scroll personalizado */
    .papers-scroll {{
        max-height: 500px;
        overflow-y: auto;
        padding-right: 10px;
    }}
    
    .papers-scroll::-webkit-scrollbar {{
        width: 8px;
    }}
    
    .papers-scroll::-webkit-scrollbar-track {{
        background: {COLORS["light_gray"]};
        border-radius: 4px;
    }}
    
    .papers-scroll::-webkit-scrollbar-thumb {{
        background: {COLORS["gold"]};
        border-radius: 4px;
    }}
    
    .papers-scroll::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["navy"]};
    }}
    
    /* Estado vacío */
    .empty-state {{
        text-align: center;
        padding: 60px 20px;
        background: {COLORS["white"]};
        border-radius: 12px;
        border: 2px dashed {COLORS["gold"]};
    }}
    
    .empty-state-icon {{
        font-size: 64px;
        margin-bottom: 15px;
        opacity: 0.5;
    }}
    
    /* Alertas */
    .stAlert {{
        border-radius: 8px;
        padding: 10px 15px;
        font-size: 13px;
    }}
    
    /* DataFrames */
    [data-testid="stDataFrame"] {{
        border-radius: 8px;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem !important;
        }}
        .papers-scroll {{
            max-height: 400px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

# Control de acceso por rol/capacidad
role = st.session_state.get("role")
username = st.session_state.get("user")
if role not in ("Admin", "Evaluador", "Participante"):
    st.warning("No tiene permisos para acceder a Ponencias.")
    st.stop()

# Detectar si el usuario participante es Ponente por su DNI
is_ponente_user = False
ponente_participant_id = None
if role == "Participante" and username:
    db_chk = SessionLocal()
    p_me = db_chk.query(Participant).filter(Participant.dni == username).first()
    if p_me and (str(p_me.p_type).lower() == "ponente" or getattr(p_me, "p_type", "") == "Ponente"):
        is_ponente_user = True
        ponente_participant_id = p_me.id
    db_chk.close()
if role == "Participante" and not is_ponente_user:
    st.warning("No tiene permisos para acceder a Ponencias.")
    st.stop()

st.markdown("""
<div class="papers-header">
    <h1>📄 Gestión de <span>Ponencias</span></h1>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# NUEVA PONENCIA
# -----------------------------------------------------------------------------

if role in ("Admin", "Evaluador"):
    with st.expander("➕ Nueva Ponencia", expanded=False):
        db = SessionLocal()
        # Mostrar solo autores con rol de Ponente
        plist = db.query(Participant).filter(Participant.p_type == "Ponente").all()
        db.close()
        
        search = st.text_input("🔍 Buscar autor por DNI o Nombre", placeholder="Escriba para filtrar (solo Ponentes)…")
        
        def matches(p, s):
            s = s.lower().strip()
            return s in (p.dni or "").lower() or s in (p.full_name or "").lower()
        
        filtered = [p for p in plist if (matches(p, search) if search else True)]
        options = [f"{p.dni} — {p.full_name}" for p in filtered] if filtered else []
        mapping = {f"{p.dni} — {p.full_name}": p.id for p in filtered}
        
        with st.form("paper_form"):
            author = st.selectbox("👤 Autor (DNI — Nombre)", options if options else ["Sin resultados"])
            title = st.text_input("📋 Título de la Ponencia")
            abstract = st.text_area("📝 Resumen", height=120)
            
            submitted = st.form_submit_button("✅ Registrar Ponencia")
            
            if submitted:
                if not options or author == "Sin resultados":
                    st.error("❌ Seleccione un autor válido")
                elif not title or not abstract:
                    st.error("❌ Título y Resumen son obligatorios")
                else:
                    db = SessionLocal()
                    p = Paper(
                        participant_id=mapping[author], 
                        title=title, 
                        abstract=abstract, 
                        status="Enviado"
                    )
                    db.add(p)
                    db.commit()
                    try:
                        actor = st.session_state.get("user")
                        log_event(usuario=str(actor) if actor else None, accion="INSERT", tabla="papers", registro_id=p.id, detalle=f"Ponencia '{title[:50]}'")
                    except Exception:
                        pass
                    db.close()
                    st.success("✅ Ponencia registrada exitosamente")
                    st.rerun()

# -----------------------------------------------------------------------------
# LISTADO CON TABLA CRUD PERSONALIZADA
# -----------------------------------------------------------------------------

db = SessionLocal()
if role in ("Admin", "Evaluador"):
    papers = db.query(Paper).all()
else:
    # Ponente: solo sus ponencias
    papers = db.query(Paper).filter(Paper.participant_id == ponente_participant_id).all()
authors = {p.id: db.query(Participant).get(p.participant_id) for p in papers}
db.close()

if papers:
    # Header de tabla
    st.markdown('<div class="crud-table">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="table-header">
        <h3>📋 Listado de Ponencias</h3>
        <span class="table-stats">Total: {len(papers)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscador
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    q = st.text_input("🔍 Buscar", placeholder="DNI, Nombre del autor o Título de ponencia", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Preparar datos
    rows = []
    for p in papers:
        a = authors.get(p.id)
        rows.append({
            "ID": p.id,
            "DNI": a.dni if a else "",
            "Autor": a.full_name if a else "",
            "Título": p.title,
            "Estado": p.status
        })
    
    df = pd.DataFrame(rows)
    
    # Filtrar
    view = df.copy()
    if q:
        s = q.lower()
        view = view[view.apply(
            lambda r: s in str(r["DNI"]).lower() or 
                     s in str(r["Autor"]).lower() or 
                     s in str(r["Título"]).lower(), 
            axis=1
        )]
    
    # Layout de dos columnas: Lista | Detalles
    col_list, col_detail = st.columns([1, 1.5])
    
    # COLUMNA IZQUIERDA: LISTA INTERACTIVA
    with col_list:
        st.markdown("**Seleccione una ponencia:**")
        st.markdown('<div class="papers-scroll">', unsafe_allow_html=True)
        
        # Variable de sesión para tracking
        if "selected_paper_id" not in st.session_state:
            st.session_state.selected_paper_id = None
        
        for idx, row in view.iterrows():
            paper_id = row["ID"]
            is_selected = st.session_state.selected_paper_id == paper_id
            
            status_class = f"status-{row['Estado'].lower()}"
            
            # Botón de item
            if st.button(
                f"📄 {row['Título'][:40]}...",
                key=f"paper_{paper_id}",
                use_container_width=True
            ):
                st.session_state.selected_paper_id = paper_id
                st.rerun()
            
            # Mostrar metadata
            st.markdown(f"""
            <div class="paper-meta">
                <span class="paper-meta-item">👤 {row['Autor']}</span>
                <span class="status-badge {status_class}">{row['Estado']}</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # COLUMNA DERECHA: PANEL DE DETALLES
    with col_detail:
        if st.session_state.selected_paper_id:
            selected_id = st.session_state.selected_paper_id
            sel_row = df[df["ID"] == selected_id].iloc[0]
            
            st.markdown(f"""
            <div class="detail-panel">
                <h3 style="color: {COLORS["navy"]}; margin-top: 0;">
                    📄 {sel_row['Título']}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            db = SessionLocal()
            sel_obj = db.query(Paper).get(int(selected_id))
            
            # SECCIÓN 1: EDITAR PONENCIA (solo Admin/Evaluador)
            if role in ("Admin", "Evaluador"):
                st.markdown('<div class="detail-section">', unsafe_allow_html=True)
                st.markdown("#### ✏️ Editar Información")
                
                new_title = st.text_input("Título", value=sel_row["Título"], key="edit_title")
                new_abstract = st.text_area(
                    "Resumen", 
                    value=sel_obj.abstract if sel_obj else "", 
                    height=100,
                    key="edit_abstract"
                )
                new_status = st.selectbox(
                    "Estado", 
                    ["Enviado", "Evaluado", "Aceptado", "Rechazado"],
                    index=["Enviado","Evaluado","Aceptado","Rechazado"].index(sel_obj.status if sel_obj else "Enviado"),
                    key="edit_status"
                )
                
                col_save, col_del = st.columns(2)
                if col_save.button("💾 Guardar Cambios", use_container_width=True):
                    obj = db.query(Paper).get(int(selected_id))
                    obj.title = new_title
                    obj.abstract = new_abstract
                    obj.status = new_status
                    db.commit()
                    try:
                        actor = st.session_state.get("user")
                        log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="papers", registro_id=obj.id, detalle="Edición de ponencia")
                    except Exception:
                        pass
                    st.success("✅ Cambios guardados")
                    st.rerun()
                
                if col_del.button("🗑️ Eliminar Ponencia", use_container_width=True):
                    # Eliminar archivos
                    for fobj in db.query(PaperFile).filter(PaperFile.paper_id == int(selected_id)).all():
                        try:
                            if os.path.exists(fobj.path):
                                os.remove(fobj.path)
                        except:
                            pass
                        db.delete(fobj)
                    
                    obj = db.query(Paper).get(int(selected_id))
                    db.delete(obj)
                    db.commit()
                    try:
                        actor = st.session_state.get("user")
                        log_event(usuario=str(actor) if actor else None, accion="DELETE", tabla="papers", registro_id=int(selected_id), detalle="Eliminación de ponencia")
                    except Exception:
                        pass
                    st.session_state.selected_paper_id = None
                    st.warning("🗑️ Ponencia eliminada")
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # SECCIÓN 2: ARCHIVOS ADJUNTOS
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown("#### 📎 Archivos Adjuntos")
            
            upload_dir = os.path.join(Config.BASE_DIR, "uploads_papers")
            os.makedirs(upload_dir, exist_ok=True)
            
            up_files = st.file_uploader(
                "Agregar archivos",
                type=None,
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            if st.button("📤 Subir Archivos", use_container_width=True) and up_files:
                for f in up_files:
                    safe_name = f.name
                    dest = os.path.join(upload_dir, safe_name)
                    with open(dest, "wb") as out:
                        out.write(f.getbuffer())
                    pf = PaperFile(
                        paper_id=int(selected_id),
                        filename=safe_name,
                        path=dest,
                        mime_type=f.type or ""
                    )
                    db.add(pf)
                db.commit()
                try:
                    actor = st.session_state.get("user")
                    log_event(usuario=str(actor) if actor else None, accion="INSERT", tabla="paper_files", registro_id=pf.id, detalle=f"Archivo {fobj.name}")
                except Exception:
                    pass
                st.success("✅ Archivos cargados")
                st.rerun()
            
            # Lista de archivos
            files = db.query(PaperFile).filter(PaperFile.paper_id == int(selected_id)).all()
            if files:
                for fobj in files:
                    col_file, col_view, col_dl, col_del = st.columns([6, 1, 1, 1])
                    with col_file:
                        st.markdown(f"📄 {fobj.filename}")
                    with col_view:
                        if st.button("👁", key=f"view_file_{fobj.id}"):
                            st.session_state["preview_file_id"] = fobj.id
                    with col_dl:
                        try:
                            if os.path.exists(fobj.path):
                                with open(fobj.path, "rb") as rf:
                                    data_bytes = rf.read()
                                st.download_button("⬇️", data=data_bytes, file_name=fobj.filename, mime=fobj.mime_type or "application/octet-stream", key=f"dl_{fobj.id}")
                            else:
                                st.write("⬇️")
                        except:
                            st.write("⬇️")
                    with col_del:
                        if st.button("❌", key=f"del_file_{fobj.id}"):
                            try:
                                if os.path.exists(fobj.path):
                                    os.remove(fobj.path)
                            except:
                                pass
                            db.delete(fobj)
                            db.commit()
                            try:
                                actor = st.session_state.get("user")
                                log_event(usuario=str(actor) if actor else None, accion="DELETE", tabla="paper_files", registro_id=fobj.id, detalle=f"Archivo {fobj.filename}")
                            except Exception:
                                pass
                            st.warning("Archivo eliminado")
                            st.rerun()
                if st.session_state.get("preview_file_id"):
                    pfid = st.session_state["preview_file_id"]
                    target = next((x for x in files if x.id == pfid), None)
                    if target and os.path.exists(target.path):
                        try:
                            import base64
                            with open(target.path, "rb") as rf:
                                b64 = base64.b64encode(rf.read()).decode("utf-8")
                            if (target.mime_type or "").lower().find("pdf") != -1:
                                st.markdown(f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='600px'></iframe>", unsafe_allow_html=True)
                            elif (target.mime_type or "").lower().find("image") != -1:
                                st.image(target.path, use_container_width=True)
                            else:
                                st.info("Formato no soportado para vista previa. Use la descarga.")
                            if st.button("Cerrar previsualización", key=f"close_preview_{pfid}"):
                                del st.session_state["preview_file_id"]
                                st.rerun()
                        except:
                            st.info("No se pudo previsualizar el archivo.")
            else:
                st.info("No hay archivos adjuntos")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # SECCIÓN 3: EVALUACIÓN (solo Admin/Evaluador)
            if role in ("Admin", "Evaluador"):
                st.markdown('<div class="detail-section">', unsafe_allow_html=True)
                st.markdown("#### ⭐ Registrar Evaluación")
                
                evaluators = db.query(User).filter(User.role == "Evaluador").all()
                ev_search = st.text_input("🔎 Buscar evaluador (usuario o email)", placeholder="Escriba para filtrar evaluadores…")
                def ev_match(u, s):
                    s = (s or "").lower().strip()
                    return s in (u.username or "").lower() or s in (u.email or "").lower()
                ev_filtered = [u for u in evaluators if (ev_match(u, ev_search) if ev_search else True)]
                ev_options = [f"{u.username} — {u.email}" for u in ev_filtered] if ev_filtered else ["Sin resultados"]
                ev_map = {f"{u.username} — {u.email}": u.id for u in ev_filtered}

                with st.form(f"eval_form_{selected_id}"):
                    evaluator_choice = st.selectbox("👤 Seleccionar Evaluador", ev_options)
                    score = st.number_input("📊 Puntaje", min_value=0, max_value=100, value=80)
                    comments = st.text_area("💬 Comentarios", height=80)
                    if st.form_submit_button("✅ Registrar Evaluación"):
                        if evaluator_choice == "Sin resultados":
                            st.error("❌ Seleccione un evaluador válido")
                        else:
                            ev_user_id = ev_map[evaluator_choice]
                            ev_user = db.query(User).get(ev_user_id)
                            if ev_user and ev_user.role == "Evaluador":
                                ev = Evaluation(
                                    paper_id=int(selected_id),
                                    evaluator_id=ev_user.id,
                                    score=score,
                                    comments=comments
                                )
                                db.add(ev)
                                # Cambiar estado automáticamente a Evaluado
                                sel_obj.status = "Evaluado"
                                db.commit()
                                try:
                                    actor = st.session_state.get("user")
                                    log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="papers", registro_id=sel_obj.id, detalle="Evaluación registrada (status Evaluado)")
                                except Exception:
                                    pass
                                st.success("✅ Evaluación registrada y ponencia marcada como Evaluada")
                            else:
                                st.error("❌ El usuario seleccionado no tiene rol de Evaluador")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            db.close()
        else:
            st.info("👈 Seleccione una ponencia de la lista para ver los detalles")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de exportación
    st.markdown("---")
    export_buttons_df(df, "reporte_ponencias", "Listado de Ponencias CONITEK", pdf_exclude_cols=["ID"])
    
else:
    # Estado vacío
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📄</div>
        <div style="color: #000080; font-size: 18px; font-weight: 600; margin-bottom: 10px;">
            No hay ponencias registradas
        </div>
        <div style="color: #666; font-size: 14px;">
            Comience agregando una nueva ponencia usando el formulario superior
        </div>
    </div>
    """, unsafe_allow_html=True)
