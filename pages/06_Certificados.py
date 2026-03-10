import streamlit as st
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.certificate import Certificate
from models.participant import Participant
from models.event import Event
from models.event_registration import EventRegistration
from models.payment import Payment
from fpdf import FPDF
from config import Config
import uuid
import base64
import os

st.title("Generación de Certificados")

role = st.session_state.get("role")
username = st.session_state.get("user")
my_participant = None
if role == "Participante" and username:
    db = SessionLocal()
    try:
        my_participant = db.query(Participant).filter(Participant.dni == username).first()
    finally:
        db.close()
    if my_participant:
        st.session_state['selected_participant'] = my_participant

col1, col2 = st.columns([1, 2])

with col1:
    if role in ("Admin", "Tesorero"):
        st.subheader("Buscar Participante")
        q = st.text_input("DNI o Nombre")
        if st.button("Buscar"):
            db = SessionLocal()
            parts = db.query(Participant).all()
            db.close()
            res = [p for p in parts if q.lower().strip() in (p.dni or "").lower() or q.lower().strip() in (p.full_name or "").lower()]
            if res:
                opts = {f"{p.dni} — {p.full_name}": p.id for p in res}
                st.session_state["cert_part_opts"] = opts
            else:
                st.session_state["cert_part_opts"] = {}
        if "cert_part_opts" in st.session_state and st.session_state["cert_part_opts"]:
            label = st.selectbox("Seleccionar", list(st.session_state["cert_part_opts"].keys()))
            if st.button("Seleccionar Participante"):
                db = SessionLocal()
                st.session_state['selected_participant'] = db.query(Participant).get(st.session_state["cert_part_opts"][label])
                db.close()
    else:
        st.subheader("Certificados Propios")
        if my_participant:
            st.write(f"Participante: {my_participant.full_name}")
        else:
            st.error("No se encontró tu registro como participante")

with col2:
    if 'selected_participant' in st.session_state and st.session_state['selected_participant']:
        part = st.session_state['selected_participant']
        st.subheader("Generar Certificado")
        db = SessionLocal()
        regs = db.query(EventRegistration).filter(EventRegistration.participant_id == part.id).all()
        approved = []
        for r in regs:
            pay = db.query(Payment).filter(Payment.reference == r.payment_reference, Payment.status == "Aprobado").first()
            if pay and r.status == "Confirmada":
                ev = db.query(Event).get(r.event_id)
                if ev:
                    approved.append((r, ev))
        db.close()
        if approved:
            ev_map = {f"{e.name} ({e.event_date})": (r, e) for r, e in approved}
            sel = st.selectbox("Evento", list(ev_map.keys()))
            if st.button("Previsualizar"):
                r, e = ev_map[sel]
                def build_certificate_bytes(person_name: str, event_name: str, place: str, date_text: str):
                    pdf = FPDF()
                    pdf.set_auto_page_break(auto=False)
                    pdf.add_page()
                    base_dir = Config.BASE_DIR
                    tmpl_dir = os.path.join(base_dir, "certificado")
                    tmpl_path = None
                    if os.path.isdir(tmpl_dir):
                        for fname in os.listdir(tmpl_dir):
                            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                                tmpl_path = os.path.join(tmpl_dir, fname)
                                break
                    if tmpl_path and os.path.isfile(tmpl_path):
                        pdf.image(tmpl_path, x=0, y=0, w=210)
                    pdf.set_text_color(255, 255, 255)
                    # Ajuste dinámico del tamaño de fuente para el nombre y permitir salto de línea
                    max_width = 190
                    fs = 28
                    pdf.set_font("Arial", 'B', fs)
                    while pdf.get_string_width(person_name) > max_width and fs > 16:
                        fs -= 1
                        pdf.set_font("Arial", 'B', fs)
                    pdf.set_xy(10, 56)
                    # Si aún excede, usar multi_cell para envolver
                    if pdf.get_string_width(person_name) > max_width:
                        pdf.multi_cell(max_width, 10, person_name, align='C')
                    else:
                        pdf.cell(max_width, 12, person_name, align='C', ln=1)
                    pdf.set_font("Arial", '', 14)
                    pdf.set_xy(10, 75)
                    # Formato deseado:
                    # "Por su participación en el evento [nombre evento],"
                    # "realizado en [lugar] el [fecha]"
                    pretty_date = date_text
                    try:
                        from datetime import datetime as _dt
                        d = _dt.strptime(str(date_text), "%Y-%m-%d").date()
                        meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                        pretty_date = f"{d.day} de {meses[d.month-1]} de {d.year}"
                    except Exception:
                        pass
                    line1 = f"Por su participación en el evento {event_name},"
                    line2 = f"realizado en {place} el {pretty_date}."
                    pdf.multi_cell(190, 8, f"{line1}\n{line2}", align='C')
                    # No escribir más contenido para evitar salto a segunda página
                    return bytes(pdf.output(dest='S'))
                def build_certificate_bytes_img(person_name: str, event_name: str, place: str, date_text: str):
                    base_dir = Config.BASE_DIR
                    tmpl_dir = os.path.join(base_dir, "certificado")
                    tmpl_path = None
                    if os.path.isdir(tmpl_dir):
                        for fname in os.listdir(tmpl_dir):
                            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                                tmpl_path = os.path.join(tmpl_dir, fname)
                                break
                    pretty_date = date_text
                    try:
                        from datetime import datetime as _dt
                        d = _dt.strptime(str(date_text), "%Y-%m-%d").date()
                        meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                        pretty_date = f"{d.day} de {meses[d.month-1]} de {d.year}"
                    except Exception:
                        pass
                    line1 = f"Por su participación en el evento {event_name},"
                    line2 = f"realizado en {place} el {pretty_date}."
                    try:
                        from PIL import Image, ImageDraw, ImageFont
                        if not tmpl_path or not os.path.isfile(tmpl_path):
                            raise RuntimeError("no_template")
                        img = Image.open(tmpl_path).convert("RGB")
                        draw = ImageDraw.Draw(img)
                        W, H = img.size
                        def mm_to_px(y_mm): return int(H * (y_mm / 297.0))
                        fill = (255, 255, 255)
                        try:
                            font_name = ImageFont.truetype("arial.ttf", 72)
                        except Exception:
                            font_name = ImageFont.load_default()
                        try:
                            font_desc = ImageFont.truetype("arial.ttf", 36)
                        except Exception:
                            font_desc = ImageFont.load_default()
                        y_name = mm_to_px(120)
                        bbox = draw.textbbox((0, 0), person_name, font=font_name)
                        tw = bbox[2] - bbox[0]
                        x_name = (W - tw) // 2
                        draw.text((x_name, y_name), person_name, font=font_name, fill=fill)
                        y_desc = mm_to_px(150)
                        desc = f"{line1}\n{line2}"
                        max_width_px = int(W * 0.85)
                        lines = []
                        for paragraph in desc.split("\n"):
                            words = paragraph.split(" ")
                            cur = ""
                            for w in words:
                                test = (cur + " " + w).strip()
                                twt = draw.textbbox((0, 0), test, font=font_desc)[2]
                                if twt <= max_width_px:
                                    cur = test
                                else:
                                    lines.append(cur)
                                    cur = w
                            if cur:
                                lines.append(cur)
                        lh = draw.textbbox((0, 0), "Ay", font=font_desc)[3]
                        for i, ln in enumerate(lines):
                            lw = draw.textbbox((0, 0), ln, font=font_desc)[2]
                            draw.text(((W - lw) // 2, y_desc + i * lh), ln, font=font_desc, fill=fill)
                        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
                        tmp_jpg = os.path.join(Config.REPORTS_DIR, f"cert_{uuid.uuid4().hex[:6]}.jpg")
                        img.save(tmp_jpg, "JPEG")
                        pdf = FPDF()
                        pdf.set_auto_page_break(auto=False)
                        pdf.add_page()
                        pdf.image(tmp_jpg, x=0, y=0, w=210, h=297)
                        return bytes(pdf.output(dest='S'))
                    except Exception:
                        return build_certificate_bytes(person_name, event_name, place, date_text)
                cert_bytes = build_certificate_bytes_img(
                    person_name=part.full_name,
                    event_name=e.name,
                    place=e.location,
                    date_text=str(e.event_date)
                )
                b64 = base64.b64encode(cert_bytes).decode("utf-8")
                st.session_state["cert_preview"] = {"bytes": cert_bytes, "b64": b64, "event_label": sel}
            if "cert_preview" in st.session_state:
                col_left, col_right = st.columns([1, 1])
                with col_left:
                    st.markdown(f"<iframe src='data:application/pdf;base64,{st.session_state['cert_preview']['b64']}' width='100%' height='400px'></iframe>", unsafe_allow_html=True)
                with col_right:
                    if st.button("Generar y Descargar PDF"):
                        db = SessionLocal()
                        code = str(uuid.uuid4())[:8].upper()
                        try:
                            pid = part.id if part else (my_participant.id if my_participant else None)
                            if not pid:
                                st.error("Participante no establecido")
                            else:
                                new_cert = Certificate(participant_id=pid, code=code, type="Asistencia")
                                db.add(new_cert)
                                db.commit()
                                p_dni = getattr(part, "dni", None) or getattr(my_participant, "dni", "certificado")
                                st.download_button("Descargar Certificado", data=st.session_state["cert_preview"]["bytes"], file_name=f"certificado_{p_dni}.pdf", mime="application/pdf")
                        finally:
                            db.close()
                    if st.button("Cerrar Previsualización"):
                        del st.session_state["cert_preview"]
        else:
            st.info("Sin eventos con pago aprobado y registro confirmado")

role = str(st.session_state.get("role") or "").lower()
if role in ("admin", "administrador"):
    st.subheader("Generar todos los certificados por evento")
    db = SessionLocal()
    all_events = db.query(Event).all()
    db.close()
    if all_events:
        UNIVERSIDADES = [
            "Todas",
            "UNT", "UPAO", "UPC", "UPN", "UCV", "USS", "ULADECH",
            "UNITRU", "UNS", "UNMSM", "UNI", "PUCP", "UNFV",
            "UNSA", "UNAP", "UNSAC", "PUC", "UNP", "Otra"
        ]
        ev_opt = {f"{e.name} ({e.event_date})": e.id for e in all_events}
        ev_label = st.selectbox("Evento a certificar", list(ev_opt.keys()))
        univ_cert_filter = st.selectbox("🏛️ Filtrar por Universidad", UNIVERSIDADES)

        if st.button("Generar PDF de todos"):
            sel_id = ev_opt[ev_label]
            db = SessionLocal()
            regs = db.query(EventRegistration).filter(EventRegistration.event_id == sel_id).all()
            persons = []
            for r in regs:
                pay = db.query(Payment).filter(Payment.reference == r.payment_reference, Payment.status == "Aprobado").first()
                if pay and r.status == "Confirmada":
                    p = db.query(Participant).get(r.participant_id)
                    e = db.query(Event).get(sel_id)
                    if p and e:
                        # FILTRO POR UNIVERSIDAD
                        if univ_cert_filter != "Todas":
                            if (p.university or "").strip().upper() != univ_cert_filter.strip().upper():
                                continue
                        persons.append((p, e))
            db.close()
            if not persons:
                st.info("No hay participantes con pago aprobado y registro confirmado para este evento")
            else:
                base_dir = Config.BASE_DIR
                tmpl_dir = os.path.join(base_dir, "certificado")
                tmpl_path = None
                if os.path.isdir(tmpl_dir):
                    for fname in os.listdir(tmpl_dir):
                        if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                            tmpl_path = os.path.join(tmpl_dir, fname)
                            break
                combined = FPDF()
                combined.set_auto_page_break(auto=False)
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    use_pil = tmpl_path and os.path.isfile(tmpl_path)
                except Exception:
                    use_pil = False
                for p, e in persons:
                    if use_pil:
                        try:
                            img = Image.open(tmpl_path).convert("RGBA")
                            draw = ImageDraw.Draw(img)
                            W, H = img.size
                            def mm_to_px(y_mm): return int(H * (y_mm / 297.0))
                            fill = (255,255,255,255)
                            try:
                                font_name = ImageFont.truetype("arial.ttf", 72)
                            except Exception:
                                font_name = ImageFont.load_default()
                            try:
                                font_desc = ImageFont.truetype("arial.ttf", 36)
                            except Exception:
                                font_desc = ImageFont.load_default()
                            # Usar mismas posiciones que el individual (usuario ajustó a 120mm / 150mm)
                            y_name = mm_to_px(120)
                            bbox = draw.textbbox((0,0), p.full_name, font=font_name)
                            tw = bbox[2]-bbox[0]
                            x_name = (W - tw)//2
                            draw.text((x_name, y_name), p.full_name, font=font_name, fill=fill)
                            y_desc = mm_to_px(150)
                            try:
                                from datetime import datetime as _dt
                                d = _dt.strptime(str(e.event_date), "%Y-%m-%d").date()
                                meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                                pretty_date = f"{d.day} de {meses[d.month-1]} de {d.year}"
                            except Exception:
                                pretty_date = str(e.event_date)
                            desc = f"Por su participación en el evento {e.name},\nrealizado en {e.location} el {pretty_date}."
                            max_width_px = int(W*0.85)
                            lines = []
                            for paragraph in desc.split("\n"):
                                words = paragraph.split(" ")
                                cur = ""
                                for w in words:
                                    test = (cur+" "+w).strip()
                                    tw = draw.textbbox((0,0), test, font=font_desc)[2]
                                    if tw <= max_width_px:
                                        cur = test
                                    else:
                                        lines.append(cur)
                                        cur = w
                                if cur:
                                    lines.append(cur)
                            lh = draw.textbbox((0,0), "Ay", font=font_desc)[3]
                            for i, ln in enumerate(lines):
                                lw = draw.textbbox((0,0), ln, font=font_desc)[2]
                                draw.text(((W-lw)//2, y_desc + i*lh), ln, font=font_desc, fill=fill)
                            out_dir = Config.REPORTS_DIR
                            os.makedirs(out_dir, exist_ok=True)
                            tmp_png = os.path.join(out_dir, f"cert_{uuid.uuid4().hex[:6]}.png")
                            img.save(tmp_png, "PNG")
                            combined.add_page()
                            combined.image(tmp_png, x=0, y=0, w=210, h=297)
                        except Exception:
                            combined.add_page()
                            if tmpl_path and os.path.isfile(tmpl_path):
                                combined.image(tmpl_path, x=0, y=0, w=210, h=297)
                            combined.set_text_color(255,255,255)
                            max_width = 190
                            fs = 28
                            combined.set_font("Arial", 'B', fs)
                            while combined.get_string_width(p.full_name) > max_width and fs > 16:
                                fs -= 1
                                combined.set_font("Arial", 'B', fs)
                            # Mismas posiciones que el individual
                            combined.set_xy(10,120)
                            if combined.get_string_width(p.full_name) > max_width:
                                combined.multi_cell(max_width,10,p.full_name,align='C')
                            else:
                                combined.cell(max_width,12,p.full_name,align='C',ln=1)
                            combined.set_font("Arial",'',14)
                            combined.set_xy(10,150)
                            combined.multi_cell(190,8,f"Por su participación en el evento {e.name},\nrealizado en {e.location} el {str(e.event_date)}.",align='C')
                    else:
                        combined.add_page()
                        if tmpl_path and os.path.isfile(tmpl_path):
                            combined.image(tmpl_path, x=0, y=0, w=210, h=297)
                        combined.set_text_color(255,255,255)
                        max_width = 190
                        fs = 28
                        combined.set_font("Arial", 'B', fs)
                        while combined.get_string_width(p.full_name) > max_width and fs > 16:
                            fs -= 1
                            combined.set_font("Arial", 'B', fs)
                        combined.set_xy(10,120)
                        if combined.get_string_width(p.full_name) > max_width:
                            combined.multi_cell(max_width,10,p.full_name,align='C')
                        else:
                            combined.cell(max_width,12,p.full_name,align='C',ln=1)
                        combined.set_font("Arial",'',14)
                        combined.set_xy(10,150)
                        try:
                            from datetime import datetime as _dt
                            d = _dt.strptime(str(e.event_date), "%Y-%m-%d").date()
                            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
                            pretty_date = f"{d.day} de {meses[d.month-1]} de {d.year}"
                        except Exception:
                            pretty_date = str(e.event_date)
                        combined.multi_cell(190,8,f"Por su participación en el evento {e.name},\nrealizado en {e.location} el {pretty_date}.",align='C')
                pdf_bytes = bytes(combined.output(dest='S'))
                suffix = f"_{univ_cert_filter}" if univ_cert_filter != "Todas" else "_todos"
                st.download_button(
                    f"⬇️ Descargar Certificados ({univ_cert_filter}) — {len(persons)} participantes",
                    data=pdf_bytes,
                    file_name=f"certificados_evento{suffix}.pdf",
                    mime="application/pdf"
                )
#else:
    #st.info("Solo el administrador puede generar certificados masivos por evento.")
