import streamlit as st
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.event import Event
from models.event_registration import EventRegistration
from models.event_speaker import EventSpeaker
from models.participant import Participant
from models.payment import Payment
from datetime import date
import pandas as pd
import uuid
from components.downloads import export_buttons_df
from services.statistics_service import StatisticsService
from components.statistics import render_stats_cards

st.title("Gestión de Eventos")
# Gate de acceso: solo admin (tolerante si 'user' no es dict)
_u = st.session_state.get("user")
if isinstance(_u, dict):
    _role_val = _u.get("role") or _u.get("rol") or _u.get("perfil")
else:
    _role_val = _u  # puede ser string
_role = (st.session_state.get("role") or _role_val or "")
if str(_role).lower() not in ["admin", "administrador"]:
    st.warning("Solo el administrador puede acceder a Gestión de Eventos")
    st.stop()
# Estilos para botones de acciones (emoji) tono celeste suave
st.markdown("""
<style>
/* Estilo general de botones en esta página (tono celeste) */
.stButton > button {
    background: #ffffff !important;
    border: 1px solid #ffffff !important;
    color: #ffffff !important;
}
/* Botones compactos */
.stButton > button {
    padding: 6px 10px !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

with st.expander("Crear Evento"):
    with st.form("event_form"):
        name = st.text_input("Nombre del Evento")
        event_date = st.date_input("Fecha", value=date.today())
        location = st.text_input("Lugar")
        capacity = st.number_input("Capacidad", min_value=1, value=500, step=10)
        submitted = st.form_submit_button("Crear")
        if submitted:
            db = SessionLocal()
            e = Event(name=name, event_date=event_date, location=location, capacity=capacity, is_active=True)
            db.add(e)
            db.commit()
            db.close()
            st.success("Evento creado")
            st.rerun()

# -----------------------------------------------------------------------------
# ESTADÍSTICAS DEL MÓDULO
# -----------------------------------------------------------------------------

db = SessionLocal()
stats = StatisticsService.get_event_stats(db)
db.close()

if stats:
    st.markdown("### 📊 Estadísticas de Eventos")
    render_stats_cards([
        {"label": "Total Eventos", "value": stats["total"], "icon": "📅", "color": "#000080"},
        {"label": "Capacidad Total", "value": stats["total_capacity"], "icon": "👥", "color": "#1e90ff"},
        {"label": "Total Ocupados", "value": stats["total_occupied"], "icon": "✅", "color": "#28a745"},
        {"label": "Capacidad Promedio", "value": stats["avg_capacity"], "icon": "📊", "color": "#ffd700"},
    ])
    st.markdown(f"**Evento con mayor ocupación:** {stats['most_occupied']}")
    st.markdown(f"**Evento con menor ocupación:** {stats['least_occupied']}")

header_l, header_r = st.columns([4, 2])
with header_l:
    st.markdown("### Eventos Disponibles")
db = SessionLocal()
events = db.query(Event).filter(Event.is_active == True, Event.event_date >= date.today(), Event.current_count < Event.capacity).all()
db.close()

# Inicializar claves de estado para evitar AttributeError
for _k in ["edit_event_id", "speaker_event_id", "participant_event_id", "detail_event_id", "detail_event_target", "pending_route"]:
    if _k not in st.session_state:
        st.session_state[_k] = None

if events:
    with header_r:
        q = st.text_input("Buscar por nombre o lugar", placeholder="Buscar por nombre o lugar…")
    filtered_events = []
    for e in events:
        ok_q = True
        if q:
            s = q.lower().strip()
            ok_q = s in (e.name or "").lower() or s in (e.location or "").lower()
        if ok_q:
            filtered_events.append(e)
    events = filtered_events
    if "edit_event_id" not in st.session_state:
        st.session_state.edit_event_id = None
    # Cabecera de la tabla personalizada
    h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 2, 2, 1, 3])
    h1.markdown("**Nombre**")
    h2.markdown("**Fecha**")
    h3.markdown("**Lugar**")
    h4.markdown("**Capacidad**")
    h5.markdown("**Ocupados**")
    h6.markdown("**Acciones**")
    st.markdown("---")
    for e in events:
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 1, 3])
        c1.write(e.name)
        c2.write(e.event_date)
        c3.write(e.location)
        c4.write(int(e.capacity))
        c5.write(int(e.current_count or 0))
        with c6:
            a1, a2, a3 = st.columns([1, 1, 1])
            b_edit = a1.button("✏️", key=f"edit_{e.id}")
            b_speaker = a2.button("🤵‍♂️", key=f"add_speaker_{e.id}")
            b_detail = a3.button("📜", key=f"detail_{e.id}")
        if b_edit:
            st.session_state.edit_event_id = e.id
            st.session_state.pop("speaker_event_id", None)
            st.session_state.pop("participant_event_id", None)
            st.session_state.pop("detail_event_id", None)
            st.rerun()
        if b_speaker:
            
            st.session_state.speaker_event_id = e.id
            st.session_state.pop("edit_event_id", None)
            st.session_state.pop("participant_event_id", None)
            st.session_state.pop("detail_event_id", None)
        # if b_part:
        #     st.session_state.participant_event_id = e.id
        #     st.session_state.pop("edit_event_id", None)
        #     st.session_state.pop("speaker_event_id", None)
        #     st.session_state.pop("detail_event_id", None)
        #     st.rerun()
        if b_detail:
            st.session_state["detail_event_target"] = e.id
            try:
                from streamlit.commands import execution_control as _ec
                _ec.switch_page("pages/07_Evento_Detalle.py")
            except Exception:
                try:
                    st.switch_page("pages/07_Evento_Detalle.py")
                except Exception:
                    st.experimental_set_query_params(event_id=e.id)
                    st.info("Abre la pestaña 'Detalle de Evento' en el menú para continuar.")
        # Ventana de edición
        if st.session_state.get("edit_event_id") == e.id:
            st.markdown(
                "<div style='border:2px solid #ffd700; padding:12px; border-radius:8px; background:#fffce8;'>",
                unsafe_allow_html=True
            )
            with st.form(f"edit_event_form_{e.id}"):
                fc1, fc2 = st.columns(2)
                name_ed = fc1.text_input("Nombre del Evento", value=e.name)
                date_ed = fc2.date_input("Fecha", value=e.event_date)
                loc_ed = fc1.text_input("Lugar", value=e.location)
                cap_ed = fc2.number_input("Capacidad", min_value=1, value=int(e.capacity), step=10)
                b_cancel, b_save = st.columns([1, 2])
                save_clicked = b_save.form_submit_button("💾 Guardar")
                cancel_clicked = b_cancel.form_submit_button("✖️ Cancelar")
                if cancel_clicked:
                    st.session_state.edit_event_id = None
                    st.rerun()
                if save_clicked:
                    dbu = SessionLocal()
                    try:
                        evu = dbu.query(Event).get(e.id)
                        evu.name = name_ed
                        evu.event_date = date_ed
                        evu.location = loc_ed
                        # Ajustar ocupados si nueva capacidad < ocupados
                        evu.capacity = int(cap_ed)
                        if (evu.current_count or 0) > evu.capacity:
                            evu.current_count = evu.capacity
                        dbu.commit()
                        st.success("✅ Evento actualizado")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"❌ Error al actualizar: {ex}")
                    finally:
                        dbu.close()
            st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.get("speaker_event_id") == e.id:
            st.markdown("<div style='border:2px solid #1e90ff; padding:12px; border-radius:8px; background:#eef7ff;'>", unsafe_allow_html=True)
            dbs = SessionLocal()
            plist = dbs.query(Participant).filter(Participant.p_type == "Ponente").all()
            qsp = st.text_input("Buscar Ponente (DNI o Nombre)", key=f"search_speaker_{e.id}")
            def _m(p, s):
                s = (s or "").lower().strip()
                return s in (p.dni or "").lower() or s in (p.full_name or "").lower()
            fl = [p for p in plist if (_m(p, qsp) if qsp else True)]
            # Construir múltiples opciones por ponente (una por cada ponencia, truncada a 15 chars)
            try:
                from models.paper import Paper
                pid_list = [p.id for p in fl]
                papers = dbs.query(Paper).filter(Paper.participant_id.in_(pid_list)).all() if pid_list else []
                titles_by_author = {}
                for pap in papers:
                    titles_by_author.setdefault(pap.participant_id, []).append((pap.id, pap.title or ""))
            except Exception:
                titles_by_author = {}
            opts = []
            mapping = {}
            if fl:
                for p in fl:
                    titles = titles_by_author.get(p.id, [])
                    if not titles:
                        label = f"{p.dni} — {p.full_name} - sin ponencia"
                        opts.append(label)
                        mapping[label] = (p.id, None)
                    else:
                        for pap_id, t in titles:
                            t = (t or "").strip()
                            t_short = t[:100] + ("…" if len(t) > 100 else "")
                            label = f"{p.dni} — {p.full_name} - {t_short}"
                            opts.append(label)
                            mapping[label] = (p.id, pap_id)
            else:
                opts = ["Sin resultados"]
                mapping = {}
            dbs.close()
            sel_sp = st.selectbox("Seleccionar Ponente", opts, key=f"sel_speaker_{e.id}")
            c_cancel, c_save = st.columns([1, 2])
            if c_cancel.button("✖️ Cancelar", key=f"cancel_sp_{e.id}"):
                st.session_state.pop("speaker_event_id", None)
                st.rerun()
            if c_save.button("💾 Guardar", key=f"save_sp_{e.id}"):
                if sel_sp == "Sin resultados":
                    st.error("Seleccione un ponente válido")
                else:
                    dbs = SessionLocal()
                    try:
                        pid, pap_id = mapping.get(sel_sp, (None, None))
                        p = dbs.query(Participant).get(pid) if pid else None
                        if not p:
                            st.error("Participante no encontrado")
                        else:
                            # Evitar duplicar el mismo ponente en el evento (independiente de la ponencia)
                            exists = dbs.query(EventSpeaker).filter(
                                EventSpeaker.event_id == e.id,
                                EventSpeaker.participant_id == p.id
                            ).first()
                            if exists:
                                st.warning("El ponente ya está asignado a este evento")
                            else:
                                es = EventSpeaker(event_id=e.id, participant_id=p.id, paper_id=pap_id)
                                dbs.add(es)
                                dbs.commit()
                                st.success("✅ Ponente asignado correctamente")
                                st.session_state.pop("speaker_event_id", None)
                                st.rerun()
                    except Exception as ex:
                        st.error(f"Error: {ex}")
                    finally:
                        dbs.close()
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
        # if st.session_state.get("participant_event_id") == e.id:
        if False and st.session_state.get("participant_event_id") == e.id:
            st.markdown("<div style='border:2px solid #28a745; padding:12px; border-radius:8px; background:#effaf3;'>", unsafe_allow_html=True)
            dbp = SessionLocal()
            plist = dbp.query(Participant).all()
            dbp.close()
            r1, r2 = st.columns(2)
            qp = r1.text_input("Buscar Participante (DNI o Nombre)", key=f"search_part_{e.id}")
            def _mp(pp, s):
                s = (s or "").lower().strip()
                return s in (pp.dni or "").lower() or s in (pp.full_name or "").lower()
            pfl = [pp for pp in plist if (_mp(pp, qp) if qp else True)]
            popts = [f"{pp.dni} — {pp.full_name}" for pp in pfl] if pfl else ["Sin resultados"]
            pmapping = {f"{pp.dni} — {pp.full_name}": pp.id for pp in pfl}
            sel_pa = r1.selectbox("Seleccionar Participante", popts, key=f"sel_part_{e.id}")
            amount_pa = r2.number_input("Monto (S/.)", min_value=0.0, value=0.0, step=1.0, key=f"amount_part_{e.id}")
            method_pa = r2.selectbox("Método", ["Yape", "Plin", "Transferencia", "Efectivo"], key=f"method_part_{e.id}")
            c_cancel2, c_save2 = st.columns([1, 2])
            if c_cancel2.button("✖️ Cancelar", key=f"cancel_pa_{e.id}"):
                st.session_state.pop("participant_event_id", None)
                st.rerun()
            if c_save2.button("💾 Guardar", key=f"save_pa_{e.id}"):
                dbp = SessionLocal()
                try:
                    if sel_pa == "Sin resultados":
                        st.error("Seleccione un participante válido")
                    else:
                        pid = pmapping.get(sel_pa)
                        part = dbp.query(Participant).get(pid)
                        if not part:
                            st.error("Participante no encontrado")
                        else:
                            if (e.current_count or 0) >= e.capacity:
                                st.error("Capacidad del evento alcanzada")
                            else:
                                reg = EventRegistration(event_id=e.id, participant_id=part.id, status="Pendiente")
                                dbp.add(reg)
                                dbp.commit()
                                ref = f"EVT-{e.id}-{reg.id}-{uuid.uuid4().hex[:6].upper()}"
                                reg.payment_reference = ref
                                pay = Payment(participant_id=part.id, amount=st.session_state.get(f'amount_part_{e.id}', 0.0), method=st.session_state.get(f'method_part_{e.id}', 'Yape'), reference=ref, status="Pendiente")
                                dbp.add(pay)
                                dbp.commit()
                                st.success(f"Registro creado. Código de pago: {ref}")
                                st.session_state.pop("participant_event_id", None)
                                st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")
                finally:
                    dbp.close()
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
        if False and (b_detail or st.session_state.get("detail_event_id") == e.id):
            st.markdown("<div style='background:#ffffff; border:1px solid #e0e0e0; border-radius:10px; padding:12px 14px; box-shadow:0 6px 24px rgba(0,0,0,0.08);'>", unsafe_allow_html=True)
            st.markdown("**Detalle de Evento**")
            dbd = SessionLocal()
            regs = dbd.query(EventRegistration).filter(EventRegistration.event_id == e.id).all()
            approved = []
            for r in regs:
                if r.payment_reference:
                    pay = dbd.query(Payment).filter(Payment.reference == r.payment_reference, Payment.status == "Aprobado").first()
                    if pay:
                        p = dbd.query(Participant).get(r.participant_id)
                        if p:
                            approved.append(p)
            es_list = dbd.query(EventSpeaker).filter(EventSpeaker.event_id == e.id).all()
            speaker_rows = []
            for es in es_list:
                p = dbd.query(Participant).get(es.participant_id)
                if p:
                    pap = None
                    try:
                        from models.paper import Paper
                        if getattr(es, "paper_id", None):
                            pap = dbd.query(Paper).get(es.paper_id)
                        if not pap:
                            pap = dbd.query(Paper).filter(Paper.participant_id == p.id).order_by(Paper.id.desc()).first()
                    except Exception:
                        pap = None
                    t = (pap.title if pap and pap.title else "sin ponencia").strip()
                    t_short = t[:60] + ("…" if len(t) > 60 else "")
                    speaker_rows.append({"es_id": es.id, "dni": p.dni, "name": p.full_name, "title": t_short})
            dbd.close()
            speaker_dnis = {r["dni"] for r in speaker_rows}
            audience_rows = []
            for p in approved:
                if p.dni not in speaker_dnis:
                    audience_rows.append({"dni": p.dni, "name": p.full_name})
            # Encabezado
            st.write(f"Evento: {e.name}")
            st.write(f"Lugar: {e.location}    Fecha: {e.event_date}")
            # Buscadores
            cql, cqr = st.columns(2)
            qsp = cql.text_input("Buscar ponentes", "", key=f"ov_qsp_{e.id}")
            qau = cqr.text_input("Buscar público", "", key=f"ov_qau_{e.id}")
            # Columnas listas
            cl, cr = st.columns(2)
            with cl:
                st.markdown("Ponentes")
                sview = [r for r in speaker_rows if (qsp.lower() in r["dni"].lower() or qsp.lower() in r["name"].lower())] if qsp else speaker_rows
                st.markdown('<div class="ovcol">', unsafe_allow_html=True)
                for r in sview:
                    rl, rr = st.columns([4,1])
                    rl.write(f'{r["dni"]} — {r["name"]} — {r["title"]}')
                    if rr.button("Quitar", key=f'ov_rm_{r["es_id"]}'):
                        dbx = SessionLocal()
                        obj = dbx.query(EventSpeaker).get(r["es_id"])
                        if obj:
                            dbx.delete(obj)
                            dbx.commit()
                        dbx.close()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with cr:
                st.markdown("Público")
                aview = [r for r in audience_rows if (qau.lower() in r["dni"].lower() or qau.lower() in r["name"].lower())] if qau else audience_rows
                st.markdown('<div class="ovcol">', unsafe_allow_html=True)
                for r in aview:
                    st.write(f'{r["dni"]} — {r["name"]}')
                st.markdown('</div>', unsafe_allow_html=True)
            # PDF
            d1, d2 = st.columns([1, 2])
            if d1.button("✖️ Cerrar", key=f"close_detail_{e.id}"):
                st.session_state.pop("detail_event_id", None)
                st.rerun()
            from services.reports import ReportService
            pdf_speakers = [f'{r["dni"]} {r["name"]} - {r["title"]}' for r in speaker_rows]
            pdf_audience = [f'{r["dni"]} {r["name"]}' for r in audience_rows]
            pdf_bytes = ReportService.event_attendees_pdf_bytes(
                {"name": e.name, "location": e.location, "date": str(e.event_date)},
                pdf_speakers, pdf_audience
            )
            import base64 as _b64
            b64 = _b64.b64encode(pdf_bytes).decode("utf-8")
            d2.download_button("📄 Exportar PDF", data=pdf_bytes, file_name=f"evento_{e.id}_participantes.pdf", mime="application/pdf", use_container_width=True)
            st.markdown(f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='320px' style='border-radius:8px;'></iframe>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # Reportes (Excel / PDF) de eventos actuales
    def _audience_count(ev_id: int) -> int:
        dbn = SessionLocal()
        try:
            regs = dbn.query(EventRegistration).filter(EventRegistration.event_id == ev_id).all()
            # Ponentes a excluir del conteo de público
            sp_ids = {s.participant_id for s in dbn.query(EventSpeaker).filter(EventSpeaker.event_id == ev_id).all()}
            cnt = 0
            for r in regs:
                ok = False
                if (r.status or "").lower() == "confirmada":
                    ok = True
                elif r.payment_reference:
                    pay = dbn.query(Payment).filter(Payment.reference == r.payment_reference, Payment.status == "Aprobado").first()
                    ok = bool(pay)
                if ok and r.participant_id not in sp_ids:
                    cnt += 1
            return cnt
        finally:
            dbn.close()
    rows = [{
        "ID": e.id,
        "Nombre": e.name,
        "Fecha": e.event_date,
        "Lugar": e.location,
        "Capacidad": e.capacity,
        "Ocupados": _audience_count(e.id)
    } for e in events]
    df = pd.DataFrame(rows)
    export_buttons_df(df, "eventos_disponibles", "Eventos Disponibles", pdf_exclude_cols=["ID"])
    sel_id = st.session_state.get("detail_event_id")
    if False and sel_id:
        dbd2 = SessionLocal()
        ev = dbd2.query(Event).get(sel_id)
        regs = dbd2.query(EventRegistration).filter(EventRegistration.event_id == sel_id).all()
        approved = []
        for r in regs:
            if r.payment_reference:
                pay = dbd2.query(Payment).filter(Payment.reference == r.payment_reference, Payment.status == "Aprobado").first()
                if pay:
                    p = dbd2.query(Participant).get(r.participant_id)
                    if p:
                        approved.append(p)
        es_list = dbd2.query(EventSpeaker).filter(EventSpeaker.event_id == sel_id).all()
        speaker_rows = []
        for es in es_list:
            p = dbd2.query(Participant).get(es.participant_id)
            if p:
                pap = None
                try:
                    from models.paper import Paper
                    if getattr(es, "paper_id", None):
                        pap = dbd2.query(Paper).get(es.paper_id)
                    if not pap:
                        pap = dbd2.query(Paper).filter(Paper.participant_id == p.id).order_by(Paper.id.desc()).first()
                except Exception:
                    pap = None
                t = (pap.title if pap and pap.title else "sin ponencia").strip()
                t_short = t[:60] + ("…" if len(t) > 60 else "")
                speaker_rows.append({"es_id": es.id, "dni": p.dni, "name": p.full_name, "title": t_short})
        speaker_dnis = {r["dni"] for r in speaker_rows}
        audience_rows = []
        for p in approved:
            if p.dni not in speaker_dnis:
                audience_rows.append({"dni": p.dni, "name": p.full_name})
        dbd2.close()
        st.markdown("<div style='background:#ffffff; border:1px solid #e0e0e0; border-radius:10px; padding:12px 14px; box-shadow:0 6px 24px rgba(0,0,0,0.08);'>", unsafe_allow_html=True)
        st.markdown("**Detalle de Evento**")
        st.write(f"Evento: {getattr(ev,'name','-')}")
        st.write(f"Lugar: {getattr(ev,'location','-')}    Fecha: {getattr(ev,'event_date','-')}")
        cql2, cqr2 = st.columns(2)
        qsp2 = cql2.text_input("Buscar ponentes", "", key="ov2_qsp")
        qau2 = cqr2.text_input("Buscar público", "", key="ov2_qau")
        cl2, cr2 = st.columns(2)
        with cl2:
            st.markdown("Ponentes")
            sview2 = [r for r in speaker_rows if (qsp2.lower() in r["dni"].lower() or qsp2.lower() in r["name"].lower())] if qsp2 else speaker_rows
            st.markdown("<div style='max-height:360px; overflow:auto; padding-right:6px;'>", unsafe_allow_html=True)
            for r in sview2:
                rl2, rr2 = st.columns([4,1])
                rl2.write(f'{r["dni"]} — {r["name"]} — {r["title"]}')
                if rr2.button("Quitar", key=f'ov2_rm_{r["es_id"]}'):
                    dbx = SessionLocal()
                    obj = dbx.query(EventSpeaker).get(r["es_id"])
                    if obj:
                        dbx.delete(obj)
                        dbx.commit()
                    dbx.close()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with cr2:
            st.markdown("Público")
            aview2 = [r for r in audience_rows if (qau2.lower() in r["dni"].lower() or qau2.lower() in r["name"].lower())] if qau2 else audience_rows
            st.markdown("<div style='max-height:360px; overflow:auto; padding-right:6px;'>", unsafe_allow_html=True)
            for r in aview2:
                st.write(f'{r["dni"]} — {r["name"]}')
            st.markdown("</div>", unsafe_allow_html=True)
        from services.reports import ReportService
        pdf_speakers2 = [f'{r["dni"]} {r["name"]} - {r["title"]}' for r in speaker_rows]
        pdf_audience2 = [f'{r["dni"]} {r["name"]}' for r in audience_rows]
        pdf_bytes2 = ReportService.event_attendees_pdf_bytes(
            {"name": getattr(ev,"name","-"), "location": getattr(ev,"location","-"), "date": str(getattr(ev,"event_date","-"))},
            pdf_speakers2, pdf_audience2
        )
        import base64 as _b64
        b64_2 = _b64.b64encode(pdf_bytes2).decode("utf-8")
        dd1, dd2 = st.columns([1,2])
        with dd1:
            if st.button("✖️ Cerrar", key="ov2_close"):
                st.session_state["detail_event_id"] = None
                st.rerun()
            st.download_button("📄 Exportar PDF", data=pdf_bytes2, file_name=f"evento_{sel_id}_participantes.pdf", mime="application/pdf", use_container_width=True)
        with dd2:
            st.markdown(f"<iframe src='data:application/pdf;base64,{b64_2}' width='100%' height='320px' style='border-radius:8px;'></iframe>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No hay eventos disponibles")
