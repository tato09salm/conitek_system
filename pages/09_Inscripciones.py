import streamlit as st
from services.database import SessionLocal
from models.event import Event
from models.event_registration import EventRegistration
from models.participant import Participant
from models.payment import Payment
from components.downloads import export_buttons_df
from services.reports import ReportService
from datetime import date
import pandas as pd
import uuid
from services.statistics_service import StatisticsService
from components.statistics import render_stats_cards

st.title("Inscripciones")

# -----------------------------------------------------------------------------
# ESTADÍSTICAS DEL MÓDULO (Solo para roles administrativos)
# -----------------------------------------------------------------------------
role = str(st.session_state.get("role") or "").lower()
if role in ("admin", "administrador", "tesorero", "tesoreria", "tesorería"):
    db = SessionLocal()
    stats = StatisticsService.get_registration_stats(db)
    db.close()
    
    if stats:
        st.markdown("### 📊 Resumen de Inscripciones")
        render_stats_cards([
            {"label": "Total Inscripciones", "value": stats["total_registrations"], "icon": "📝", "color": "#000080"},
            {"label": "Recaudación Total", "value": f"S/. {stats['total_collected']:,.2f}", "icon": "💰", "color": "#28a745"},
            {"label": "Monto Promedio", "value": f"S/. {stats['avg_payment']:,.2f}", "icon": "📈", "color": "#1e90ff"},
            {"label": "Monto Máximo", "value": f"S/. {stats['max_payment']:,.2f}", "icon": "🏆", "color": "#ffd700"},
            {"label": "Confirmadas", "value": stats["by_status"].get("Confirmada", 0), "icon": "✅", "color": "#28a745"},
            {"label": "Pendientes", "value": stats["by_status"].get("Pendiente", 0), "icon": "⏳", "color": "#fd7e14"},
        ])

user_val = st.session_state.get("user")

if role in ("admin", "administrador", "tesorero", "tesoreria", "tesorería"):
    db = SessionLocal()
    events = db.query(Event).filter(Event.is_active == True, Event.event_date >= date.today()).all()
    db.close()
    if not events:
        st.info("No hay eventos disponibles")
    else:
        ev_options = {f"{e.name} ({e.event_date}) [{e.current_count}/{e.capacity}]": e.id for e in events}
        ev_label = st.selectbox("Evento", list(ev_options.keys()))
        sel_event_id = ev_options[ev_label]
        db = SessionLocal()
        plist = db.query(Participant).all()
        db.close()
        q = st.text_input("Buscar participante (DNI o Nombre)")
        def matches(p, s):
            s = s.lower().strip()
            return s in (p.dni or "").lower() or s in (p.full_name or "").lower()
        filtered = [p for p in plist if (matches(p, q) if q else True)]
        pmap = {f"{p.dni} — {p.full_name}": p.id for p in filtered}
        p_label = st.selectbox("Participante", list(pmap.keys()) if pmap else ["Sin resultados"])
        amount = st.number_input("Monto a pagar (S/.)", min_value=0.0, value=0.0, step=1.0)
        if st.button("Reservar Inscripción y Generar Orden de Pago"):
            if not pmap or p_label == "Sin resultados":
                st.error("Seleccione un participante válido")
            else:
                db = SessionLocal()
                exists = db.query(EventRegistration).filter(EventRegistration.event_id == sel_event_id, EventRegistration.participant_id == pmap[p_label]).first()
                ev = db.query(Event).get(sel_event_id)
                if ev and ev.current_count >= ev.capacity:
                    st.error("El evento alcanzó el límite de capacidad. No es posible registrar más inscripciones.")
                    db.close()
                    st.stop()
                if exists:
                    st.warning("El participante ya tiene una inscripción para este evento")
                else:
                    reg = EventRegistration(event_id=sel_event_id, participant_id=pmap[p_label], status="Pendiente")
                    db.add(reg)
                    db.commit()
                    ref = f"EVT-{sel_event_id}-{reg.id}-{uuid.uuid4().hex[:6].upper()}"
                    reg.payment_reference = ref
                    pay = Payment(participant_id=pmap[p_label], amount=amount, method="Pendiente", reference=ref, status="Pendiente")
                    db.add(pay)
                    db.commit()
                    st.success(f"Inscripción creada. Orden de pago: {ref}")
                db.close()
                st.rerun()

    st.subheader("Registrados por Evento")
    db = SessionLocal()
    events_all = db.query(Event).all()
    db.close()
    if events_all:
        sel = st.selectbox("Seleccionar Evento para exportar", {f"{e.name} ({e.event_date})": e.id for e in events_all})
        sel_id = list({f"{e.name} ({e.event_date})": e.id for e in events_all}.values())[list({f"{e.name} ({e.event_date})": e.id for e in events_all}.keys()).index(sel)]
        db = SessionLocal()
        regs = db.query(EventRegistration).filter(EventRegistration.event_id == sel_id).all()
        parts = {r.participant_id: db.query(Participant).get(r.participant_id) for r in regs}
        db.close()
        rows = []
        for r in regs:
            p = parts.get(r.participant_id)
            rows.append({
                "DNI": p.dni if p else "",
                "Nombre": p.full_name if p else "",
                "Email": p.email if p else "",
                "Universidad": p.university if p else "",
                "Teléfono": p.phone if p else "",
                "Estado": r.status,
                "Referencia": r.payment_reference
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            export_buttons_df(df[["DNI","Nombre"]], "registrados_evento_pdf", "Registrados por Evento")
            st.download_button("Exportar CSV (Todos los datos)", df.to_csv(index=False).encode("utf-8"), "registrados_evento.csv", "text/csv")
else:
    db = SessionLocal()
    me = None
    if user_val:
        me = db.query(Participant).filter(Participant.dni == str(user_val)).first()
    events = db.query(Event).filter(Event.is_active == True, Event.event_date >= date.today()).all()
    if me and events:
        ev_opts_me = {f"{e.name} ({e.event_date}) [{e.current_count}/{e.capacity}]": e.id for e in events}
        ev_label_me = st.selectbox("Evento", list(ev_opts_me.keys()))
        sel_event_id_me = ev_opts_me[ev_label_me]
        amount_me = st.number_input("Monto a pagar (S/.)", min_value=0.0, value=0.0, step=1.0, key="amount_me")
        if st.button("Inscribirme y generar orden de pago"):
            exists = db.query(EventRegistration).filter(EventRegistration.event_id == sel_event_id_me, EventRegistration.participant_id == me.id).first()
            ev = db.query(Event).get(sel_event_id_me)
            if ev and ev.current_count >= ev.capacity:
                st.error("El evento alcanzó el límite de capacidad. No es posible registrar más inscripciones.")
            elif exists:
                st.warning("Ya tienes una inscripción para este evento")
            else:
                reg = EventRegistration(event_id=sel_event_id_me, participant_id=me.id, status="Pendiente")
                db.add(reg)
                db.commit()
                ref = f"EVT-{sel_event_id_me}-{reg.id}-{uuid.uuid4().hex[:6].upper()}"
                reg.payment_reference = ref
                pay = Payment(participant_id=me.id, amount=amount_me, method="Pendiente", reference=ref, status="Pendiente")
                db.add(pay)
                db.commit()
                st.success(f"Inscripción creada. Orden de pago: {ref}")
                st.rerun()
    regs = []
    if me:
        regs = db.query(EventRegistration).filter(EventRegistration.participant_id == me.id).all()
    evs = {r.event_id: db.query(Event).get(r.event_id) for r in regs} if regs else {}
    db.close()
    rows = []
    for r in regs:
        e = evs.get(r.event_id)
        rows.append({
            "Evento": e.name if e else "",
            "Fecha": e.event_date if e else "",
            "Estado": r.status,
            "Referencia": r.payment_reference
        })
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Aún no tienes inscripciones registradas")
    else:
        st.dataframe(df, use_container_width=True)
