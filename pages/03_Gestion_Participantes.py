import streamlit as st
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.participant import Participant, ParticipantType, Modality
from services.reports import download_button_excel, ReportService
import pandas as pd
from components.downloads import export_buttons_df
import re
from services.audit import log_event

# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y ESTILOS
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Gestión de Participantes - CONITEK 2026",
    page_icon="👥",
    layout="wide"
)

# Gate de acceso: solo administrador (tolerante si 'user' no es dict)
_u = st.session_state.get("user")
if isinstance(_u, dict):
    _role_val = _u.get("role") or _u.get("rol") or _u.get("perfil")
else:
    _role_val = _u
_role = (st.session_state.get("role") or _role_val or "")
if str(_role).lower() not in ["admin", "administrador"]:
    st.warning("Solo el administrador puede acceder a Gestión de Participantes")
    st.stop()

COLORS = {
    "navy": "#000080",
    "blue": "#1e90ff",
    "gold": "#ffd700",
    "white": "#ffffff",
    "light_gray": "#f8f9fa",
    "green": "#28a745",
    "red": "#dc3545"
}

def load_participants_css():
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
        .page-header {{
            background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
            border-radius: 12px;
            padding: 15px 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .page-header h1 {{
            color: {COLORS["white"]};
            font-size: 24px;
            font-weight: 800;
            margin: 0;
        }}
        
        .page-header h1 span {{
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
        }}
        
        /* Formularios compactos */
        .stForm {{
            background: {COLORS["white"]};
            border-radius: 10px;
            padding: 15px;
        }}
        
        .stTextInput label, .stSelectbox label {{
            font-weight: 600;
            color: {COLORS["navy"]};
            font-size: 13px;
        }}
        
        .stTextInput input, .stSelectbox select {{
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            padding: 8px 12px;
            font-size: 14px;
        }}
        
        .stTextInput input:focus, .stSelectbox select:focus {{
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
            transition: all 0.3s;
        }}
        
        .stFormSubmitButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,128,0.3);
        }}
        
        /* Tabla personalizada */
        .custom-table-container {{
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
            display: flex;
            gap: 20px;
        }}
        
        .stat-badge {{
            background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
            color: {COLORS["white"]};
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        /* Área de tabla scrollable */
        .table-scroll {{
            max-height: 500px;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        
        .table-scroll::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        .table-scroll::-webkit-scrollbar-track {{
            background: {COLORS["light_gray"]};
            border-radius: 4px;
        }}
        
        .table-scroll::-webkit-scrollbar-thumb {{
            background: {COLORS["gold"]};
            border-radius: 4px;
        }}
        
        .table-scroll::-webkit-scrollbar-thumb:hover {{
            background: {COLORS["navy"]};
        }}
        
        /* DataEditor mejorado */
        [data-testid="stDataEditor"] {{
            border-radius: 8px;
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
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COLORS["green"]}, #20c997);
            color: white;
        }}
        
        /* Botón eliminar */
        .stButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, {COLORS["red"]}, #e74c3c);
            color: white;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        /* Filtros compactos */
        .filter-section {{
            background: {COLORS["light_gray"]};
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 15px;
        }}
        
        /* Alertas compactas */
        .stAlert {{
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 13px;
        }}
        
        /* Tabla vacía */
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
        
        .empty-state-text {{
            color: {COLORS["navy"]};
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .empty-state-subtext {{
            color: #666;
            font-size: 14px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .block-container {{
                padding: 1rem !important;
            }}
            .table-scroll {{
                max-height: 400px;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

load_participants_css()

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

st.markdown("""
<div class="page-header">
    <h1>👥 Gestión de <span>Participantes</span></h1>
</div>
""", unsafe_allow_html=True)

# Restricción de acceso
if 'role' not in st.session_state or st.session_state['role'] != "Admin":
    st.warning("No tiene permisos para gestionar participantes.")
    st.stop()

# -----------------------------------------------------------------------------
# NUEVO REGISTRO
# -----------------------------------------------------------------------------

with st.expander("➕ Nuevo Registro", expanded=False):
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        dni = col1.text_input("DNI *", max_chars=8)
        nombre = col2.text_input("Nombre Completo *")
        email = col1.text_input("Correo Electrónico *")
        universidad = col2.text_input("Universidad / Institución")
        telefono = col1.text_input("Teléfono", max_chars=15)
        tipo = col1.selectbox("Tipo", [t.value for t in ParticipantType])
        modalidad = col2.selectbox("Modalidad", [m.value for m in Modality])
        
        submit = st.form_submit_button("✅ Registrar Participante")
        
        if submit:
            db = SessionLocal()
            if not dni or not nombre or not email:
                st.error("⚠️ Campos obligatorios faltantes")
            elif db.query(Participant).filter((Participant.dni == dni) | (Participant.email == email)).first():
                st.error("❌ El DNI o Correo ya están registrados")
            else:
                new_p = Participant(
                    dni=dni, full_name=nombre, email=email, 
                    university=universidad, phone=telefono, 
                    p_type=tipo, modality=modalidad
                )
                db.add(new_p)
                db.commit()
                
                from models.user import User
                existing_user = db.query(User).filter(User.username == dni).first()
                if not existing_user:
                    u = User(username=dni, email=email, password_hash=dni, role="Participante", is_active=True)
                    db.add(u)
                    db.commit()
                    st.success("✅ Participante y usuario creados correctamente (usuario/contraseña: DNI).")
                else:
                    st.success("✅ Participante registrado. El usuario ya existía.")
                st.rerun()
            db.close()

# -----------------------------------------------------------------------------
# REGISTRO MASIVO
# -----------------------------------------------------------------------------

with st.expander("📤 Registro Masivo (CSV)", expanded=False):
    st.info("📋 Columnas requeridas: DNI, Nombre, Email, Universidad, Tipo, Modalidad. Opcional: Teléfono")
    
    sample = pd.DataFrame([
        {"DNI":"12345678","Nombre":"Juan Pérez","Email":"juan@unt.edu.pe","Universidad":"UNT","Tipo":"Estudiante","Modalidad":"Presencial","Telefono":"999111222"},
        {"DNI":"87654321","Nombre":"María López","Email":"maria@unt.edu.pe","Universidad":"UNT","Tipo":"Profesional","Modalidad":"Virtual","Telefono":"988777666"},
    ])
    
    st.download_button(
        "📥 Descargar Plantilla CSV", 
        sample.to_csv(index=False).encode("utf-8"), 
        "plantilla_participantes.csv", 
        "text/csv",
        use_container_width=True
    )
    
    up = st.file_uploader("Subir archivo CSV", type=["csv"])
    
    if up is not None and st.button("🚀 Procesar Registro Masivo", use_container_width=True):
        try:
            content = up.read()
            try:
                text = content.decode("utf-8")
            except:
                text = content.decode("latin-1")
            
            from io import StringIO
            df_csv = pd.read_csv(StringIO(text), sep=None, engine="python")
            cols = {c.strip().lower(): c for c in df_csv.columns}
            required = ["dni","nombre","email","universidad","tipo","modalidad"]
            
            if not all(k in cols for k in required):
                st.error("❌ Columnas requeridas faltantes")
            else:
                inserted = 0
                users_created = 0
                skipped = []
                failed = []
                db = SessionLocal()
                
                for idx, row in df_csv.iterrows():
                    try:
                        def clean_cell(v):
                            if pd.isna(v):
                                return ""
                            s = str(v).strip()
                            if s.lower() in ("nan","none","null"):
                                return ""
                            return s
                        
                        def clean_phone(v):
                            s = clean_cell(v)
                            if not s:
                                return ""
                            s = s.split(";")[0]
                            if s.endswith(".0"):
                                s = s[:-2]
                            s = re.sub(r"[^0-9 ]+", "", s)
                            s = re.sub(r"\s+", " ", s).strip()
                            return s
                        
                        dni_v = clean_cell(row[cols["dni"]])
                        nombre_v = clean_cell(row[cols["nombre"]])
                        email_v = clean_cell(row[cols["email"]])
                        univ_v = clean_cell(row.get(cols.get("universidad", "universidad"), ""))
                        
                        phone_key = None
                        for alias in ["teléfono","telefono","phone","celular","telf","movil","móvil","whatsapp"]:
                            if alias in cols:
                                phone_key = cols[alias]
                                break
                        
                        tel_v = clean_phone(row.get(phone_key, "")) if phone_key else ""
                        tipo_v = clean_cell(row[cols["tipo"]]).title()
                        mod_v = clean_cell(row[cols["modalidad"]]).title()
                        
                        if not dni_v or not dni_v.isdigit() or len(dni_v) < 8:
                            failed.append({"fila": idx+2, "dni": dni_v, "motivo": "DNI inválido"})
                            continue
                        
                        if not nombre_v or not email_v:
                            failed.append({"fila": idx+2, "dni": dni_v, "motivo": "Campos vacíos"})
                            continue
                        
                        if tipo_v not in ["Estudiante","Profesional","Ponente"]:
                            tipo_v = "Estudiante"
                        if mod_v not in ["Presencial","Virtual"]:
                            mod_v = "Presencial"
                        
                        exists = db.query(Participant).filter(Participant.dni == dni_v).first()
                        if exists:
                            skipped.append(dni_v)
                            continue
                        
                        obj = Participant(
                            dni=dni_v, full_name=nombre_v, email=email_v, 
                            university=univ_v, phone=tel_v, 
                            p_type=tipo_v, modality=mod_v
                        )
                        db.add(obj)
                        db.commit()
                        try:
                            actor = st.session_state.get("user")
                            log_event(usuario=str(actor) if actor else None, accion="INSERT", tabla="participants", registro_id=obj.id, detalle=f"Importación participante {dni_v}")
                        except Exception:
                            pass
                        inserted += 1
                        # Crear usuario si no existe
                        from models.user import User
                        if not db.query(User).filter(User.username == dni_v).first():
                            usr = User(username=dni_v, email=email_v, password_hash=dni_v, role="Participante", is_active=True)
                            db.add(usr)
                            db.commit()
                            try:
                                actor = st.session_state.get("user")
                                log_event(usuario=str(actor) if actor else None, accion="INSERT", tabla="users", registro_id=usr.id, detalle=f"Auto-usuario para participante {dni_v}")
                            except Exception:
                                pass
                            users_created += 1
                        
                    except Exception as ex:
                        failed.append({"fila": idx+2, "dni": row.get(cols.get("dni","dni"), ""), "motivo": str(ex)})
                
                db.close()
                
                st.success(f"✅ Participantes insertados: {inserted} | Usuarios creados: {users_created}")
                if skipped:
                    st.warning(f"⚠️ Omitidos (DNI existente): {len(skipped)}")
                if failed:
                    st.error(f"❌ Filas con error: {len(failed)}")
                    st.dataframe(pd.DataFrame(failed), use_container_width=True)
                
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error al procesar archivo: {str(e)}")

# -----------------------------------------------------------------------------
# LISTADO DE PARTICIPANTES
# -----------------------------------------------------------------------------

#with st.expander("🔐 Crear usuarios faltantes (usuario/contraseña = DNI)", expanded=False):
    #st.info("Ejecuta esta acción para crear usuarios por defecto a participantes existentes que aún no tienen cuenta.")
    #col_a, col_b = st.columns([1, 2])
    #if col_a.button("⚙️ Ejecutar creación de usuarios faltantes", use_container_width=True):
        #db = SessionLocal()
        #from models.user import User
        #parts = db.query(Participant).all()
        #created = 0
        #created_list = []
        #for p in parts:
            #if not p.dni:
                #continue
            #exists = db.query(User).filter(User.username == p.dni).first()
            #if not exists:
                #u = User(username=p.dni, email=p.email or "", password_hash=p.dni, role="Participante", is_active=True)
                #db.add(u)
                #db.commit()
                #created += 1
                #created_list.append(p.dni)
        #db.close()
        #st.success(f"✅ Usuarios creados: {created}")
        #if created_list:
            #st.write(", ".join(created_list[:30]) + ("..." if len(created_list) > 30 else ""))


db = SessionLocal()
participants = db.query(Participant).all()
db.close()

if participants:
    # Preparar datos
    data = [{
        "Seleccionar": False, 
        "ID": p.id, 
        "DNI": p.dni, 
        "Nombre": p.full_name, 
        "Email": p.email, 
        "Universidad": p.university or "", 
        "Teléfono": p.phone or "", 
        "Tipo": p.p_type, 
        "Modalidad": p.modality
    } for p in participants]
    df = pd.DataFrame(data)
    
    # Tabla personalizada
    st.markdown('<div class="custom-table-container">', unsafe_allow_html=True)
    
    # Header de tabla
    st.markdown(f"""
    <div class="table-header">
        <h3>📋 Listado de Participantes</h3>
        <div class="table-stats">
            <span class="stat-badge">Total: {len(participants)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col_search, col_tipo, col_mod = st.columns([2, 1, 1])
    
    filtro = col_search.text_input("🔍 Buscar", placeholder="DNI, Nombre, Email")
    tipo_filter = col_tipo.multiselect("Tipo", options=[t.value for t in ParticipantType])
    mod_filter = col_mod.multiselect("Modalidad", options=[m.value for m in Modality])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    df_view = df.copy()
    if filtro:
        f = filtro.lower()
        df_view = df_view[df_view.apply(
            lambda r: f in str(r["DNI"]).lower() or 
                     f in str(r["Nombre"]).lower() or 
                     f in str(r["Email"]).lower(), 
            axis=1
        )]
    if tipo_filter:
        df_view = df_view[df_view["Tipo"].isin(tipo_filter)]
    if mod_filter:
        df_view = df_view[df_view["Modalidad"].isin(mod_filter)]
    
    # Área de tabla scrollable
    st.markdown('<div class="table-scroll">', unsafe_allow_html=True)
    edited = st.data_editor(
        df_view,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("✓", default=False),
            "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "DNI": st.column_config.TextColumn("DNI", width="small"),
            "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
            "Email": st.column_config.TextColumn("Email", width="medium"),
            "Universidad": st.column_config.TextColumn("Universidad", width="medium"),
            "Teléfono": st.column_config.TextColumn("Teléfono", width="small"),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=[t.value for t in ParticipantType], width="small"),
            "Modalidad": st.column_config.SelectboxColumn("Modalidad", options=[m.value for m in Modality], width="small"),
        },
        use_container_width=True,
        num_rows="fixed",
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botones de acción
    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])
    
    if col1.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
        try:
            updates = []
            for _, row in edited.iterrows():
                orig = df[df["ID"] == row["ID"]].iloc[0]
                if any([
                    row["Nombre"] != orig["Nombre"],
                    row["Email"] != orig["Email"],
                    row["Universidad"] != orig["Universidad"],
                    row["Teléfono"] != orig["Teléfono"],
                    row["Tipo"] != orig["Tipo"],
                    row["Modalidad"] != orig["Modalidad"],
                ]):
                    updates.append(row)
            
            if updates:
                db = SessionLocal()
                for row in updates:
                    obj = db.query(Participant).get(int(row["ID"]))
                    obj.full_name = row["Nombre"]
                    obj.email = row["Email"]
                    obj.university = row["Universidad"]
                    obj.phone = row["Teléfono"]
                    obj.p_type = row["Tipo"]
                    obj.modality = row["Modalidad"]
                db.commit()
                try:
                    actor = st.session_state.get("user")
                    for row in updates:
                        log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="participants", registro_id=int(row["ID"]), detalle=f"Edición de participante {row['DNI']}")
                except Exception:
                    pass
                db.close()
                st.success("✅ Cambios guardados")
                st.rerun()
            else:
                st.info("ℹ️ No hay cambios")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    if col2.button("🗑️ Eliminar Seleccionados", use_container_width=True, type="secondary"):
        sel_ids = edited[edited["Seleccionar"] == True]["ID"].tolist()
        if sel_ids:
            db = SessionLocal()
            for pid in sel_ids:
                obj = db.query(Participant).get(int(pid))
                if obj:
                    dni_del = obj.dni
                    db.delete(obj)
                    try:
                        from models.user import User
                        usr = db.query(User).filter(User.username == dni_del, User.role == "Participante").first()
                        if usr:
                            db.delete(usr)
                    except:
                        pass
            db.commit()
            try:
                actor = st.session_state.get("user")
                for pid in sel_ids:
                    log_event(usuario=str(actor) if actor else None, accion="DELETE", tabla="participants", registro_id=int(pid), detalle="Eliminación de participante")
            except Exception:
                pass
            db.close()
            st.warning(f"🗑️ Eliminados: {len(sel_ids)}")
            st.rerun()
        else:
            st.info("ℹ️ Seleccione filas")
    
    if col3.button("🔄 Recargar", use_container_width=True):
        st.rerun()
    
    if col4.button("📊 Exportar", use_container_width=True):
        export_buttons_df(
            edited.drop(columns=["Seleccionar"], errors="ignore"), 
            "reporte_participantes", 
            "Listado de Participantes del Sistema",
            pdf_exclude_cols=["ID"]
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
else:
    # Estado vacío
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        <div class="empty-state-text">No hay participantes registrados</div>
        <div class="empty-state-subtext">Comience agregando un nuevo participante usando el formulario superior</div>
    </div>
    """, unsafe_allow_html=True)
