import streamlit as st
from sqlalchemy.orm import Session, selectinload
from services.database import SessionLocal
from models.payment import Payment
from models.participant import Participant
from models.event_registration import EventRegistration
from models.event import Event
from components.downloads import export_buttons_df
from services.reports import ReportService
import base64
import pandas as pd
import os
from models.payment_file import PaymentFile
from config import Config
from services.audit import log_event

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Gestión de Pagos - CONITEK 2026",
    page_icon="💰",
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
    "orange": "#fd7e14",
    "purple": "#6f42c1"
}

# -----------------------------------------------------------------------------
# ESTILOS AISLADOS PARA PAGOS
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
    .payments-header {{
        background: linear-gradient(135deg, {COLORS["navy"]} 0%, {COLORS["blue"]} 100%);
        border-radius: 12px;
        padding: 15px 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    .payments-header h1 {{
        color: {COLORS["white"]};
        font-size: 24px;
        font-weight: 800;
        margin: 0;
    }}
    
    .payments-header h1 span {{
        color: {COLORS["gold"]};
    }}
    
    /* Formulario de validación destacado */
    .validation-form {{
        background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(30,144,255,0.05));
        border: 2px solid {COLORS["gold"]};
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    
    .validation-form h3 {{
        color: {COLORS["navy"]};
        font-size: 18px;
        font-weight: 700;
        margin: 0 0 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    /* Formularios */
    .stForm {{
        background: transparent;
    }}
    
    .stTextInput label, .stNumberInput label, .stSelectbox label {{
        font-weight: 600;
        color: {COLORS["navy"]};
        font-size: 13px;
    }}
    
    .stTextInput input, .stNumberInput input, .stSelectbox select {{
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        font-size: 14px;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {{
        border-color: {COLORS["gold"]};
        box-shadow: 0 0 0 2px rgba(255,215,0,0.2);
    }}
    
    /* Botón de validación destacado */
    .stFormSubmitButton > button {{
        width: 100%;
        background: linear-gradient(135deg, {COLORS["green"]}, #20c997);
        color: {COLORS["white"]};
        border: none;
        border-radius: 10px;
        padding: 12px;
        font-weight: 700;
        font-size: 15px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }}
    
    .stFormSubmitButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
    }}
    
    /* Comprobante destacado */
    .receipt-section {{
        background: linear-gradient(135deg, {COLORS["white"]}, {COLORS["light_gray"]});
        border: 3px solid {COLORS["gold"]};
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }}
    
    .receipt-header {{
        text-align: center;
        color: {COLORS["navy"]};
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 2px solid {COLORS["gold"]};
    }}
    
    /* Tabla de historial */
    .history-table {{
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
    
    /* Lista de pagos */
    .payment-item {{
        background: {COLORS["white"]};
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        transition: all 0.3s;
    }}
    
    .payment-item:hover {{
        border-color: {COLORS["gold"]};
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    
    .payment-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    
    .payment-ref {{
        color: {COLORS["navy"]};
        font-size: 16px;
        font-weight: 700;
    }}
    
    .payment-amount {{
        color: {COLORS["green"]};
        font-size: 18px;
        font-weight: 800;
    }}
    
    .payment-meta {{
        display: flex;
        gap: 15px;
        font-size: 13px;
        color: #666;
        flex-wrap: wrap;
    }}
    
    .status-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    
    .status-aprobado {{
        background: {COLORS["green"]};
        color: white;
    }}
    
    .status-pendiente {{
        background: {COLORS["orange"]};
        color: white;
    }}
    
    .status-cancelado {{
        background: {COLORS["red"]};
        color: white;
    }}
    
    .method-badge {{
        background: {COLORS["purple"]};
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    
    /* Panel de edición */
    .edit-panel {{
        background: {COLORS["light_gray"]};
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
    }}
    
    .edit-section {{
        background: {COLORS["white"]};
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid {COLORS["gold"]};
    }}
    
    /* Botones de acción */
    .stButton > button {{
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.3s;
        border: none;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    
    /* Expanders */
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
    
    /* DataFrames */
    [data-testid="stDataFrame"] {{
        border-radius: 8px;
    }}
    
    /* Download button */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLORS["navy"]}, {COLORS["blue"]});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 700;
        font-size: 14px;
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,128,0.3);
    }}
    
    /* Iframe para PDF */
    iframe {{
        border-radius: 8px;
        border: 2px solid {COLORS["gold"]};
    }}
    
    /* Alertas */
    .stAlert {{
        border-radius: 8px;
        padding: 10px 15px;
        font-size: 13px;
    }}
    
    /* Scroll personalizado */
    .payments-scroll {{
        max-height: 600px;
        overflow-y: auto;
        padding-right: 10px;
    }}
    
    .payments-scroll::-webkit-scrollbar {{
        width: 8px;
    }}
    
    .payments-scroll::-webkit-scrollbar-track {{
        background: {COLORS["light_gray"]};
        border-radius: 4px;
    }}
    
    .payments-scroll::-webkit-scrollbar-thumb {{
        background: {COLORS["gold"]};
        border-radius: 4px;
    }}
    
    .payments-scroll::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["navy"]};
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem !important;
        }}
        .payment-meta {{
            flex-direction: column;
            gap: 8px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Contexto de sesión y participante actual
role = st.session_state.get("role")
username = st.session_state.get("user")
my_participant = None
if role == "Participante" and username:
    db_ctx = SessionLocal()
    try:
        my_participant = db_ctx.query(Participant).filter(Participant.dni == username).first()
    finally:
        db_ctx.close()

# Obtener pagos y df para exportar
dbs = SessionLocal()
try:
    if role == "Participante" and my_participant:
        payments = dbs.query(Payment).filter(Payment.participant_id == my_participant.id).all()
    else:
        payments = dbs.query(Payment).all()
    data = []
    for p in payments:
        data.append({
            "Ref": p.reference,
            "Participante": (p.participant.full_name if p.participant else ""),
            "Monto": p.amount,
            "Método": p.method,
            "Estado": p.status,
            "Fecha": p.created_at
        })
    df = pd.DataFrame(data)
    # Asegurar columnas mínimas aunque no existan pagos
    base_cols = ["Ref","Participante","Monto","Método","Estado","Fecha"]
    for c in base_cols:
        if c not in df.columns:
            df[c] = pd.Series(dtype=object)
    # Resolver evento por referencia (si existe) para filtros
    ref_to_event = {}
    ref_to_event_id = {}
    try:
        if not df.empty and "Ref" in df.columns:
            refs = [str(r) for r in df["Ref"].dropna().tolist()]
            regs = []
            if refs:
                regs = dbs.query(EventRegistration).filter(EventRegistration.payment_reference.in_(refs)).all()
            if regs:
                ev_ids = {r.event_id for r in regs if r.event_id}
                ev_map = {e.id: e for e in dbs.query(Event).filter(Event.id.in_(list(ev_ids))).all()} if ev_ids else {}
                for r in regs:
                    ev = ev_map.get(r.event_id)
                    if ev:
                        ref_to_event[r.payment_reference] = f"{ev.name} ({ev.event_date})"
                        ref_to_event_id[r.payment_reference] = ev.id
    except Exception:
        ref_to_event = {}
        ref_to_event_id = {}
    df["Evento"] = df["Ref"].apply(lambda x: ref_to_event.get(x, "-")) if "Ref" in df.columns else "-"
finally:
    dbs.close()

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

col_title, col_buttons = st.columns([4, 1])
with col_title:
    st.markdown("""
<div class="payments-header">
    <h1>💰 Gestión de <span>Pagos</span> (Tesorería)</h1>
</div>
""", unsafe_allow_html=True)
with col_buttons:
    if role in ("Admin", "Tesorero"):
        export_buttons_df(df, "reporte_pagos", "Historial de Pagos")

# -----------------------------------------------------------------------------
# FORMULARIO DE VALIDACIÓN
# -----------------------------------------------------------------------------

if role in ("Admin","Tesorero"):
    st.markdown("""
    <div class="validation-form">
        <h3>✅ Validar Nuevo Pago</h3>
    </div>
    """, unsafe_allow_html=True)
    # Callback para autocompletar DNI al ingresar la referencia
    def _autofill_dni():
        refv = (st.session_state.get("ref_val") or "").strip()
        if not refv:
            return
        dbx = SessionLocal()
        try:
            payx = dbx.query(Payment).filter(Payment.reference == refv).first()
            if payx:
                px = dbx.query(Participant).get(payx.participant_id)
                if px and px.dni:
                    st.session_state["dni_val"] = px.dni
                    return
            # Si no hay Payment, intentar por EventRegistration
            regx = dbx.query(EventRegistration).filter(EventRegistration.payment_reference == refv).first()
            if regx:
                px = dbx.query(Participant).get(regx.participant_id)
                if px and px.dni:
                    st.session_state["dni_val"] = px.dni
        finally:
            dbx.close()
    # Uploader fuera del form para previsualizar de inmediato
    up_admin_preview = st.file_uploader("Adjuntar comprobante (imagen o PDF)", type=["png","jpg","jpeg","pdf"], key="up_admin_temp")
    if up_admin_preview is not None:
        st.caption("Previsualización del comprobante")
        try:
            if (up_admin_preview.type or "").lower().startswith("image"):
                st.image(up_admin_preview, width=240)
                _data = up_admin_preview.getvalue()
                _b64prev = base64.b64encode(_data).decode("utf-8")
                img_mime = up_admin_preview.type or "image/png"
                #st.markdown(f"<a href='data:{img_mime};base64,{_b64prev}' target='_blank'>: </a>", unsafe_allow_html=True)
            elif "pdf" in (up_admin_preview.type or "").lower():
                _data = up_admin_preview.getvalue()
                _b64prev = base64.b64encode(_data).decode("utf-8")
                st.markdown(f"<iframe src='data:application/pdf;base64,{_b64prev}' width='100%' height='300px'></iframe>", unsafe_allow_html=True)
                #st.markdown(f"<a href='data:application/pdf;base64,{_b64prev}' target='_blank'>👁 Abrir PDF en pestaña nueva</a>", unsafe_allow_html=True)
            else:
                st.info("Formato no soportado para vista previa")
        except Exception:
            st.info("No se pudo previsualizar el archivo")
    with st.form("payment_validation"):
        r1c1, r1c2 = st.columns(2)
        ref_inp = r1c1.text_input("🔖 Código de Referencia / Operación", value=st.session_state.get("ref_val",""))
        dni_inp = r1c2.text_input("🆔 DNI del Participante", value=st.session_state.get("dni_autofill",""))
        r2c1, r2c2 = st.columns(2)
        amount_default = float(st.session_state.get("amount_autofill") or 0.0)
        method_default = st.session_state.get("method_autofill") or "Yape"
        options_methods = ["Yape", "Plin", "Transferencia", "Efectivo"]
        idx_method = options_methods.index(method_default) if method_default in options_methods else 0
        monto_inp = r2c1.number_input("💵 Monto (S/.)", min_value=0.0, step=0.01, value=amount_default)
        metodo_inp = r2c2.selectbox("💳 Método de Pago", options_methods, index=idx_method)
        b1, b2 = st.columns([1, 2])
        find_clicked = b1.form_submit_button("🔎 Buscar por referencia")
        approve_clicked = b2.form_submit_button("✅ Validar y Aprobar Pago")
        
        if find_clicked:
            # Guardar referencia actual y autocompletar DNI/importe/método
            st.session_state["ref_val"] = ref_inp.strip()
            # Autocompletar DNI
            refv = st.session_state["ref_val"]
            dbs = SessionLocal()
            try:
                payp = dbs.query(Payment).filter(Payment.reference == refv).first()
                if payp:
                    px = dbs.query(Participant).get(payp.participant_id)
                    if px and px.dni:
                        st.session_state["dni_autofill"] = px.dni
                    st.session_state["amount_autofill"] = payp.amount or 0.0
                    st.session_state["method_autofill"] = payp.method if payp.method in options_methods else "Yape"
                else:
                    regx = dbs.query(EventRegistration).filter(EventRegistration.payment_reference == refv).first()
                    if regx:
                        px = dbs.query(Participant).get(regx.participant_id)
                        if px and px.dni:
                            st.session_state["dni_autofill"] = px.dni
            finally:
                dbs.close()
            st.rerun()
        
        if approve_clicked:
            if st.session_state.get("role") not in ("Admin","Tesorero"):
                st.error("❌ No tiene permisos para validar pagos")
                st.stop()
            db = None
            try:
                db = SessionLocal()
                ref = (ref_inp or "").strip()
                dni_participante = (dni_inp or "").strip()
                pay = db.query(Payment).filter(Payment.reference == ref).first()
                
                if pay:
                    reg = db.query(EventRegistration).filter(EventRegistration.payment_reference == ref).first()
                    ev_name = None
                    ev = None
                    if reg:
                        ev = db.query(Event).get(reg.event_id)
                        ev_name = ev.name if ev else None
                    
                    if reg and reg.status != "Confirmada" and ev and ev.current_count >= ev.capacity:
                        st.error("❌ Capacidad del evento alcanzada. No es posible aprobar este pago.")
                        st.stop()
                    
                    pay.amount = float(monto_inp or 0.0)
                    pay.method = metodo_inp or "Yape"
                    pay.status = "Aprobado"
                    db.commit()
                    
                    part = db.query(Participant).get(pay.participant_id)
                    st.success(f"✅ Pago aprobado para {part.full_name}")
                    upf = st.session_state.get("up_admin_temp")
                    if upf is not None:
                        upload_dir = os.path.join(Config.BASE_DIR, "uploads_payments")
                        os.makedirs(upload_dir, exist_ok=True)
                        safe_name = f"pay_{pay.id}_{upf.name}"
                        dest = os.path.join(upload_dir, safe_name)
                        with open(dest, "wb") as out:
                            out.write(upf.getbuffer())
                        pf = PaymentFile(payment_id=pay.id, filename=safe_name, path=dest, mime_type=upf.type or "")
                        db.add(pf)
                        db.commit()
                    
                    info = {
                        "receipt_no": f"{pay.id}",
                        "reference": pay.reference,
                        "participant_name": part.full_name,
                        "dni": part.dni,
                        "event_name": ev_name or "-",
                        "amount": pay.amount,
                        "method": pay.method,
                        "status": pay.status,
                        "created_at": pay.created_at.strftime("%Y-%m-%d %H:%M") if pay.created_at else "-"
                    }
                    pdf_bytes = ReportService.payment_voucher_pdf_bytes(info)
                    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
                    st.session_state["last_receipt"] = {
                        "pdf_bytes": pdf_bytes,
                        "filename": f"comprobante_{pay.id}.pdf",
                        "b64": b64
                    }
                else:
                    part = db.query(Participant).filter(Participant.dni == dni_participante).first()
                    if part:
                        reg = db.query(EventRegistration).filter(EventRegistration.payment_reference == ref).first()
                        ev_name = None
                        ev = None
                        if reg:
                            ev = db.query(Event).get(reg.event_id)
                            ev_name = ev.name if ev else None
                        
                        if reg and ev and ev.current_count >= ev.capacity:
                            st.error("❌ Capacidad del evento alcanzada. No es posible aprobar este pago.")
                            st.stop()
                        
                        if db.query(Payment).filter(Payment.reference == ref).first():
                            st.error("❌ Este código de referencia ya fue registrado en otro pago.")
                            st.stop()
                        
                        new_pay = Payment(
                            participant_id=part.id,
                            amount=float(monto_inp or 0.0),
                            method=metodo_inp or "Yape",
                            reference=ref,
                            status="Aprobado"
                        )
                        db.add(new_pay)
                        db.commit()
                        upf = st.session_state.get("up_admin_temp")
                        if upf is not None:
                            upload_dir = os.path.join(Config.BASE_DIR, "uploads_payments")
                            os.makedirs(upload_dir, exist_ok=True)
                            safe_name = f"pay_{new_pay.id}_{upf.name}"
                            dest = os.path.join(upload_dir, safe_name)
                            with open(dest, "wb") as out:
                                out.write(upf.getbuffer())
                            pf = PaymentFile(payment_id=new_pay.id, filename=safe_name, path=dest, mime_type=upf.type or "")
                            db.add(pf)
                            db.commit()
                        
                        st.success(f"✅ Pago de S/. {float(monto_inp or 0.0):.2f} aprobado para {part.full_name}")
                        
                        info = {
                            "receipt_no": f"{new_pay.id}",
                            "reference": new_pay.reference,
                            "participant_name": part.full_name,
                            "dni": part.dni,
                            "event_name": ev_name or "-",
                            "amount": new_pay.amount,
                            "method": new_pay.method,
                            "status": new_pay.status,
                            "created_at": new_pay.created_at.strftime("%Y-%m-%d %H:%M") if new_pay.created_at else "-"
                        }
                        pdf_bytes = ReportService.payment_voucher_pdf_bytes(info)
                        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
                        st.session_state["last_receipt"] = {
                            "pdf_bytes": pdf_bytes,
                            "filename": f"comprobante_{new_pay.id}.pdf",
                            "b64": b64
                        }
                    else:
                        st.error("❌ Participante no encontrado con ese DNI")
                
                reg = db.query(EventRegistration).filter(EventRegistration.payment_reference == ref).first()
                if reg and reg.status != "Confirmada":
                    reg.status = "Confirmada"
                    ev = db.query(Event).get(reg.event_id)
                    if ev.current_count < ev.capacity:
                        ev.current_count = ev.current_count + 1
                    db.commit()
                    st.info("ℹ️ Registro al evento confirmado")
                
                db.close()
                st.rerun()
            except Exception as ex:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
                st.error(f"❌ Error al validar pago: {ex}")
elif role == "Participante" and my_participant:
    st.markdown("""
    <div class="validation-form">
        <h3>🧾 Registrar/Actualizar mi pago</h3>
    </div>
    """, unsafe_allow_html=True)
    # Uploader fuera del form para previsualizar de inmediato (participante)
    up_part_preview = st.file_uploader("Adjuntar comprobante (imagen o PDF)", type=["png","jpg","jpeg","pdf"], key="up_part_temp")
    if up_part_preview is not None:
        st.caption("Previsualización del comprobante")
        try:
            if (up_part_preview.type or "").lower().startswith("image"):
                st.image(up_part_preview, width=220)
                _data = up_part_preview.getvalue()
                _b64prev = base64.b64encode(_data).decode("utf-8")
                img_mime = up_part_preview.type or "image/png"
                st.markdown(f"<a href='data:{img_mime};base64,{_b64prev}' target='_blank'>👁 Abrir imagen en pestaña nueva</a>", unsafe_allow_html=True)
            elif "pdf" in (up_part_preview.type or "").lower():
                _data = up_part_preview.getvalue()
                _b64prev = base64.b64encode(_data).decode("utf-8")
                st.markdown(f"<iframe src='data:application/pdf;base64,{_b64prev}' width='100%' height='260px'></iframe>", unsafe_allow_html=True)
                #st.markdown(f"<a href='data:application/pdf;base64,{_b64prev}' target='_blank'>👁 Abrir PDF en pestaña nueva</a>", unsafe_allow_html=True)
            else:
                st.info("Formato no soportado para vista previa")
        except Exception:
            st.info("No se pudo previsualizar el archivo")
    with st.form("participant_payment"):
        dbp = SessionLocal()
        regs = dbp.query(EventRegistration).filter(EventRegistration.participant_id == my_participant.id).all()
        ev_map = {}
        for r in regs:
            ev = dbp.query(Event).get(r.event_id)
            if not ev:
                continue
            # Solo mostrar eventos cuya inscripción NO esté confirmada definitivamente
            if (r.status or "").lower() == "confirmada":
                continue
            # Si existe un pago aprobado para esta referencia, no permitir nuevos registros
            pay = None
            if r.payment_reference:
                pay = dbp.query(Payment).filter(Payment.reference == r.payment_reference).first()
            if pay and (pay.status or "").lower() == "aprobado":
                continue
            ev_map[f"{ev.name} ({ev.event_date}) - Pendiente"] = r
        dbp.close()
        chosen = st.selectbox("Evento", list(ev_map.keys()) if ev_map else ["Sin eventos"])
        ref_in = st.text_input("🔖 Código de Operación / Referencia")
        col3, col4 = st.columns(2)
        monto_in = col3.number_input("💵 Monto (S/.)", min_value=0.0, step=0.01)
        metodo_in = col4.selectbox("💳 Método de Pago", ["Yape", "Plin", "Transferencia", "Efectivo"])
        submitted_p = st.form_submit_button("💾 Guardar")
        if submitted_p:
            if not ev_map or chosen == "Sin eventos":
                st.error("❌ Seleccione un evento válido")
            else:
                dbp = SessionLocal()
                reg = ev_map[chosen]
                pay = dbp.query(Payment).filter(Payment.reference == reg.payment_reference).first()
                if not pay:
                    # Evitar referencias duplicadas
                    new_ref = ref_in or (reg.payment_reference or "")
                    if new_ref and dbp.query(Payment).filter(Payment.reference == new_ref).first():
                        st.error("❌ Este código de referencia ya fue registrado por otro usuario.")
                        dbp.close()
                        st.stop()
                    pay = Payment(participant_id=my_participant.id, amount=monto_in, method=metodo_in, reference=new_ref, status="Pendiente")
                    dbp.add(pay)
                    dbp.commit()
                    # Guardar adjunto si se subió
                    upf = st.session_state.get("up_part_temp")
                    if upf is not None:
                        upload_dir = os.path.join(Config.BASE_DIR, "uploads_payments")
                        os.makedirs(upload_dir, exist_ok=True)
                        safe_name = f"pay_{pay.id}_{upf.name}"
                        dest = os.path.join(upload_dir, safe_name)
                        with open(dest, "wb") as out:
                            out.write(upf.getbuffer())
                        pf = PaymentFile(payment_id=pay.id, filename=safe_name, path=dest, mime_type=upf.type or "")
                        dbp.add(pf)
                        dbp.commit()
                    st.success("✅ Pago registrado (Pendiente de aprobación)")
                else:
                    if pay.participant_id != my_participant.id:
                        st.error("❌ No puede modificar pagos de otros participantes")
                    else:
                        pay.amount = monto_in
                        pay.method = metodo_in
                        if ref_in:
                            # Evitar referencias duplicadas al actualizar
                            dup = dbp.query(Payment).filter(Payment.reference == ref_in).first()
                            if dup and dup.id != pay.id:
                                dbp.close()
                                st.error("❌ Este código de referencia ya fue registrado por otro usuario.")
                                st.stop()
                            pay.reference = ref_in
                            reg.payment_reference = ref_in
                        pay.status = "Pendiente"
                        dbp.commit()
                        # Guardar adjunto si se subió
                        upf = st.session_state.get("up_part_temp")
                        if upf is not None:
                            upload_dir = os.path.join(Config.BASE_DIR, "uploads_payments")
                            os.makedirs(upload_dir, exist_ok=True)
                            safe_name = f"pay_{pay.id}_{upf.name}"
                            dest = os.path.join(upload_dir, safe_name)
                            with open(dest, "wb") as out:
                                out.write(upf.getbuffer())
                            pf = PaymentFile(payment_id=pay.id, filename=safe_name, path=dest, mime_type=upf.type or "")
                            dbp.add(pf)
                            dbp.commit()
                        st.success("✅ Pago actualizado (Pendiente de aprobación)")
                dbp.close()

# -----------------------------------------------------------------------------
# COMPROBANTE GENERADO
# -----------------------------------------------------------------------------

if "last_receipt" in st.session_state:
    st.markdown('<div class="receipt-section">', unsafe_allow_html=True)
    st.markdown('<div class="receipt-header">📄 Comprobante de Pago Generado</div>', unsafe_allow_html=True)
    
    r = st.session_state["last_receipt"]
    
    col_download, col_hide = st.columns([3, 1])
    with col_download:
        st.download_button(
            "📥 Descargar Comprobante (PDF)",
            data=r["pdf_bytes"],
            file_name=r["filename"],
            mime="application/pdf",
            use_container_width=True
        )
    with col_hide:
        if st.button("✖️ Ocultar", use_container_width=True):
            del st.session_state["last_receipt"]
            st.rerun()
    
    st.markdown(f"<iframe src='data:application/pdf;base64,{r['b64']}' width='100%' height='600px'></iframe>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HISTORIAL DE PAGOS
# -----------------------------------------------------------------------------

db = SessionLocal()
if role == "Participante" and my_participant:
    payments = db.query(Payment).options(selectinload(Payment.participant)).filter(Payment.participant_id == my_participant.id).all()
else:
    payments = db.query(Payment).options(selectinload(Payment.participant)).all()

if payments:
    st.markdown('<div class="history-table">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="table-header">
        <h3>📋 Historial de Pagos</h3>
        <span class="table-stats">Total: {len(payments)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros: Evento (izquierda) y Estado (derecha)
    c_event, c_state = st.columns([2, 2])
    eventos_disponibles = ["Todos"] + sorted([e for e in df["Evento"].dropna().unique().tolist() if e and e != "-"])
    estados_disponibles = ["Todos"] + sorted([e for e in df["Estado"].dropna().unique().tolist()])
    with c_event:
        evento_sel = st.selectbox("Filtrar por evento", eventos_disponibles, index=0)
    with c_state:
        estado_sel = st.selectbox("Filtrar por estado", estados_disponibles, index=0)
    df_view = df.copy()
    if evento_sel != "Todos":
        df_view = df_view[df_view["Evento"] == evento_sel]
    if estado_sel != "Todos":
        df_view = df_view[df_view["Estado"] == estado_sel]
    # Flags de visualización
    show_interactive = role in ("Admin", "Tesorero", "Participante")
    can_edit = role in ("Admin", "Tesorero")
    # Tabla estándar solo para otros perfiles no contemplados
    if not show_interactive:
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    
    # Lista interactiva con acciones (editable solo para Admin/Tesorero)
    if show_interactive:
        #st.markdown("**CUSTOM CRUD TABLE · INTERACTIVE LIST · TABLE WITH ACTION BUTTONS**")
        st.markdown("<style>.crud-list *{font-size:13px !important}</style>", unsafe_allow_html=True)
        def _event_label_for(payment):
            return ref_to_event.get(payment.reference, "-")
        payments_filtered = [
            p for p in payments
            if (estado_sel == "Todos" or p.status == estado_sel)
            and (evento_sel == "Todos" or _event_label_for(p) == evento_sel)
        ]
        st.markdown('<div class="crud-list">', unsafe_allow_html=True)
        # Encabezados
        h1, h2, h3, h4, h5 = st.columns([1.5, 3, 1, 1, 4])
        h1.markdown("**Ref**")
        h2.markdown("**Participante**")
        h3.markdown("**Monto**")
        h4.markdown("**Estado**")
        h5.markdown("**Acciones**")
        for p in payments_filtered:
            # Botones toggle: mantienen un panel abierto por tipo
            c1, c2, c3, c4, c5 = st.columns([1.5, 3, 1, 1, 4])
            with c1:
                st.markdown(f"{p.reference or '-'}")
            with c2:
                st.markdown(f"{p.participant.full_name if p.participant else '-'}")
            with c3:
                st.markdown(f"S/. {p.amount:.2f}")
            with c4:
                st.markdown(p.status or "-")
            with c5:
                b1, b2, b3 = st.columns(3)
                if can_edit:
                    if b1.button("✏️ Editar", key=f"edit_inline_{p.id}"):
                        st.session_state[f"edit_open_{p.id}"] = not st.session_state.get(f"edit_open_{p.id}", False)
                        st.session_state[f"view_open_{p.id}"] = False
                        st.session_state[f"voucher_open_{p.id}"] = False
                        st.session_state[f"delete_open_{p.id}"] = False
                if b2.button("👁 Adjunto", key=f"view_inline_{p.id}"):
                    st.session_state[f"view_open_{p.id}"] = not st.session_state.get(f"view_open_{p.id}", False)
                    st.session_state[f"edit_open_{p.id}"] = False
                    st.session_state[f"voucher_open_{p.id}"] = False
                    st.session_state[f"delete_open_{p.id}"] = False
                if b3.button("📄voucher", key=f"voucher_inline_{p.id}"):
                    st.session_state[f"voucher_open_{p.id}"] = not st.session_state.get(f"voucher_open_{p.id}", False)
                    st.session_state[f"edit_open_{p.id}"] = False
                    st.session_state[f"view_open_{p.id}"] = False

            # Panel Editar
            if can_edit and st.session_state.get(f"edit_open_{p.id}"):
                st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                header_l, header_r = st.columns([4, 1])
                with header_l:
                    st.markdown("**✏️ Editar Pago**")
                with header_r:
                    if st.button("✖ Cerrar", key=f"close_edit_{p.id}"):
                        st.session_state[f"edit_open_{p.id}"] = False
                        st.rerun()
                col_left, col_right = st.columns(2)
                new_amount_inline = col_left.number_input("💵 Monto", min_value=0.0, value=float(p.amount or 0.0), step=0.01, key=f"amt_{p.id}")
                new_method_inline = col_right.selectbox(
                    "💳 Método", ["Yape","Plin","Transferencia","Efectivo"],
                    index=["Yape","Plin","Transferencia","Efectivo"].index(p.method) if p.method in ["Yape","Plin","Transferencia","Efectivo"] else 0,
                    key=f"met_{p.id}"
                )
                new_status_inline = col_left.selectbox(
                    "🔖 Estado", ["Pendiente","Aprobado","Cancelado"],
                    index=["Pendiente","Aprobado","Cancelado"].index(p.status) if p.status in ["Pendiente","Aprobado","Cancelado"] else 0,
                    key=f"sts_{p.id}"
                )
                ac1, ac2, ac3 = st.columns(3)
                if ac1.button("💾 Guardar", key=f"save_inline_{p.id}"):
                    dbu = SessionLocal()
                    try:
                        obj = dbu.query(Payment).get(p.id)
                        if obj:
                            prev_status = obj.status or "Pendiente"
                            obj.amount = float(new_amount_inline or 0.0)
                            obj.method = new_method_inline
                            obj.status = new_status_inline
                            # Lógica de liberar cupo si se cancela un pago aprobado
                            if prev_status == "Aprobado" and new_status_inline == "Cancelado":
                                try:
                                    reg = dbu.query(EventRegistration).filter(EventRegistration.payment_reference == obj.reference).first()
                                    if reg:
                                        ev = dbu.query(Event).get(reg.event_id)
                                        if ev and getattr(ev, "current_count", None) is not None and ev.current_count > 0:
                                            ev.current_count -= 1
                                except Exception:
                                    pass
                            dbu.commit()
                            try:
                                actor = st.session_state.get("user")
                                log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="payments", registro_id=obj.id, detalle="Actualización de pago (tesorería)")
                            except Exception:
                                pass
                        st.success("✅ Pago actualizado")
                    except Exception as ex:
                        st.error(f"Error al actualizar: {ex}")
                    finally:
                        dbu.close()
                    st.session_state[f"edit_open_{p.id}"] = False
                    st.rerun()
                if ac2.button("🚫 Cancelar", key=f"cancel_inline_{p.id}"):
                    dbu = SessionLocal()
                    try:
                        obj = dbu.query(Payment).get(p.id)
                        if obj:
                            obj.status = "Cancelado"
                            reg = dbu.query(EventRegistration).filter(EventRegistration.payment_reference == obj.reference).first()
                            if reg and reg.status == "Confirmada":
                                ev = dbu.query(Event).get(reg.event_id)
                                if ev and ev.current_count > 0:
                                    ev.current_count = ev.current_count - 1
                                reg.status = "Cancelada"
                            dbu.commit()
                            try:
                                actor = st.session_state.get("user")
                                log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="payments", registro_id=obj.id, detalle="Cancelación de pago (tesorería)")
                            except Exception:
                                pass
                        st.warning("⚠️ Pago cancelado")
                    except Exception as ex:
                        st.error(f"Error al cancelar: {ex}")
                    finally:
                        dbu.close()
                    st.session_state[f"edit_open_{p.id}"] = False
                    st.rerun()
                if ac3.button("🗑️ Eliminar", key=f"del_edit_{p.id}"):
                    dbu = SessionLocal()
                    try:
                        obj = dbu.query(Payment).get(p.id)
                        if obj:
                            dbu.delete(obj)
                            dbu.commit()
                            try:
                                actor = st.session_state.get("user")
                                log_event(usuario=str(actor) if actor else None, accion="DELETE", tabla="payments", registro_id=obj.id, detalle="Eliminación de pago (tesorería)")
                            except Exception:
                                pass
                        st.warning("🗑️ Pago eliminado")
                    except Exception as ex:
                        st.error(f"Error al eliminar: {ex}")
                    finally:
                        dbu.close()
                    st.session_state[f"edit_open_{p.id}"] = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Panel Ver adjunto
            if st.session_state.get(f"view_open_{p.id}"):
                st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                vh_l, vh_r = st.columns([4, 1])
                with vh_l:
                    st.markdown("**👁 Comprobantes adjuntos**")
                with vh_r:
                    st.empty()
                dbf = SessionLocal()
                files = []
                try:
                    files = dbf.query(PaymentFile).filter(PaymentFile.payment_id == p.id).all()
                except Exception as ex:
                    st.error(f"Error al consultar archivos: {ex}")
                finally:
                    dbf.close()
                if not files:
                    cols = st.columns(5)
                    with cols[3]:
                        if st.button("✖ Cerrar", key=f"close_view_{p.id}"):
                            st.session_state[f"view_open_{p.id}"] = False
                            st.rerun()
                    st.info("Sin comprobantes adjuntos para este pago")
                else:
                    for f in files:
                        cols = st.columns(5)
                        with cols[1]:
                            try:
                                if (f.mime_type or "").lower().startswith("image"):
                                    st.image(f.path, width=260)
                                elif "pdf" in (f.mime_type or "").lower():
                                    try:
                                        with open(f.path, "rb") as rf:
                                            import base64 as _b64
                                            b64s = _b64.b64encode(rf.read()).decode("utf-8")
                                        st.markdown(f"<iframe src='data:application/pdf;base64,{b64s}' width='100%' height='300px'></iframe>", unsafe_allow_html=True)
                                    except FileNotFoundError:
                                        st.warning(f"No se encontró el archivo: {f.filename}")
                                else:
                                    st.text(f.filename)
                            except FileNotFoundError:
                                st.warning(f"No se encontró el archivo: {f.filename}")
                            except Exception:
                                st.text(f.filename)
                        with cols[3]:
                            if st.button("✖ Cerrar", key=f"close_view_{p.id}_{f.id}"):
                                st.session_state[f"view_open_{p.id}"] = False
                                st.rerun()
                            try:
                                with open(f.path, "rb") as rf:
                                    data_bytes = rf.read()
                                st.download_button("⬇️ Descargar evidencia", data=data_bytes, file_name=f.filename, mime=f.mime_type or "application/octet-stream", key=f"dl_inline_{f.id}")
                            except FileNotFoundError:
                                st.write("⬇️ Descargar evidencia")
                            except Exception:
                                st.write("⬇️ Descargar evidencia")
                st.markdown('</div>', unsafe_allow_html=True)

            # Panel Comprobante (voucher)
            if st.session_state.get(f"voucher_open_{p.id}"):
                st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                vh_l, vh_r = st.columns([4, 1])
                with vh_l:
                    st.markdown("**📄 Comprobante**")
                with vh_r:
                    if st.button("✖ Cerrar", key=f"close_voucher_{p.id}"):
                        st.session_state[f"voucher_open_{p.id}"] = False
                        st.rerun()
                dbv = SessionLocal()
                try:
                    obj = dbv.query(Payment).get(p.id)
                    part = dbv.query(Participant).get(obj.participant_id)
                    reg = dbv.query(EventRegistration).filter(EventRegistration.payment_reference == obj.reference).first()
                    ev_name = None
                    if reg:
                        ev = dbv.query(Event).get(reg.event_id)
                        ev_name = ev.name if ev else None
                    info = {
                        "receipt_no": f"{obj.id}",
                        "reference": obj.reference,
                        "participant_name": part.full_name if part else "-",
                        "dni": part.dni if part else "-",
                        "event_name": ev_name or "-",
                        "amount": obj.amount,
                        "method": obj.method,
                        "status": obj.status,
                        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else "-"
                    }
                except Exception as ex:
                    st.error(f"Error al generar comprobante: {ex}")
                    info = None
                finally:
                    dbv.close()
                if info:
                    pdf_bytes = ReportService.payment_voucher_pdf_bytes(info)
                    import base64 as _b64
                    b64v = _b64.b64encode(pdf_bytes).decode("utf-8")
                    vcols = st.columns([1, 2, 1, 1])
                    with vcols[1]:
                        st.markdown(f"<iframe src='data:application/pdf;base64,{b64v}' width='350px' height='500px' style='border-radius:8px;'></iframe>", unsafe_allow_html=True)
                    with vcols[3]:
                        st.download_button("📥 Descargar Comprobante", data=pdf_bytes, file_name=f"comprobante_{p.id}.pdf", mime="application/pdf", key=f"dl_voucher_{p.id}")
                st.markdown('</div>', unsafe_allow_html=True)

            # Panel Eliminar con confirmación
            if st.session_state.get(f"delete_open_{p.id}"):
                st.markdown('<div class="edit-panel">', unsafe_allow_html=True)
                dh_l, dh_r = st.columns([4, 1])
                with dh_l:
                    st.warning("¿Eliminar este pago? Esta acción no se puede deshacer.")
                with dh_r:
                    if st.button("✖ Cerrar", key=f"close_del_{p.id}"):
                        st.session_state[f"delete_open_{p.id}"] = False
                        st.rerun()
                dc1, dc2 = st.columns(2)
                if dc1.button("Confirmar", key=f"confirm_del_{p.id}"):
                    dbd = SessionLocal()
                    try:
                        obj = dbd.query(Payment).get(p.id)
                        if obj:
                            dbd.delete(obj)
                            dbd.commit()
                        st.warning("🗑 Pago eliminado")
                    except Exception as ex:
                        st.error(f"Error al eliminar: {ex}")
                    finally:
                        dbd.close()
                    st.session_state[f"delete_open_{p.id}"] = False
                    st.rerun()
                if dc2.button("Cancelar", key=f"cancel_del_{p.id}"):
                    st.session_state[f"delete_open_{p.id}"] = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Panel de edición (solo Admin/Tesorero)
    if role in ("Admin","Tesorero"):
        pass
    st.markdown('</div>', unsafe_allow_html=True)
    
else:
    st.info("ℹ️ No hay pagos registrados en el sistema")

db.close()
