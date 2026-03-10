import streamlit as st
from services.database import SessionLocal
from models.user import User
import pandas as pd
from components.downloads import export_buttons_df
from services.audit import log_event

st.title("Gestión de Usuarios")

role = str(st.session_state.get("role") or "").lower()
username_ss = st.session_state.get("user")  # normalmente string (DNI o username)

# Vista completa solo para Admin
if role in ("admin", "administrador"):
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    if users:
        data = [{"ID": u.id, "Usuario": u.username, "Email": u.email, "Rol": u.role, "Activo": u.is_active} for u in users]
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        export_buttons_df(df, "usuarios_conitek", "Listado de Usuarios")
    else:
        st.info("No hay usuarios registrados.")

    st.subheader("Cambiar Contraseña")
    with st.form("change_password_admin"):
        db = SessionLocal()
        users_min = db.query(User).with_entities(User.id, User.username).all()
        db.close()
        opts = {f"{u[1]}": u[0] for u in users_min}
        selected = st.selectbox("Usuario", list(opts.keys())) if opts else None
        new_pass = st.text_input("Nueva Contraseña", type="password")
        submitted = st.form_submit_button("Actualizar")
        if submitted and selected and new_pass:
            db = SessionLocal()
            obj = db.query(User).get(opts[selected])
            if obj:
                obj.password_hash = new_pass
                db.commit()
                st.success("Contraseña actualizada")
                try:
                    actor = st.session_state.get("user")
                    log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="users", registro_id=obj.id, detalle="Cambio de contraseña (admin)")
                except Exception:
                    pass
            db.close()

    st.subheader("Nuevo Usuario")
    with st.form("new_user"):
        username = st.text_input("Usuario")
        email = st.text_input("Email")
        role_sel = st.selectbox("Rol", ["Admin","Comite","Evaluador","Tesorero","Participante"])
        password = st.text_input("Contraseña", type="password")
        active = st.checkbox("Activo", value=True)
        add_btn = st.form_submit_button("Crear")
        if add_btn:
            if not username or not email or not password:
                st.error("Complete los campos obligatorios")
            else:
                db = SessionLocal()
                exists = db.query(User).filter(User.username == username).first()
                if exists:
                    st.error("El usuario ya existe")
                else:
                    u = User(username=username, email=email, password_hash=password, role=role_sel, is_active=active)
                    db.add(u)
                    db.commit()
                    st.success("Usuario creado")
                    try:
                        actor = st.session_state.get("user")
                        log_event(usuario=str(actor) if actor else None, accion="INSERT", tabla="users", registro_id=u.id, detalle=f"Nuevo usuario {username}")
                    except Exception:
                        pass
                db.close()
                st.rerun()

    st.subheader("Eliminar Usuario")
    with st.form("delete_user"):
        db = SessionLocal()
        users_min = db.query(User).with_entities(User.id, User.username).all()
        db.close()
        opts_del = {f"{u[1]}": u[0] for u in users_min}
        selected_del = st.selectbox("Usuario a eliminar", list(opts_del.keys())) if opts_del else None
        del_btn = st.form_submit_button("Eliminar")
        if del_btn and selected_del:
            db = SessionLocal()
            obj = db.query(User).get(opts_del[selected_del])
            if obj:
                db.delete(obj)
                db.commit()
                st.warning("Usuario eliminado")
                try:
                    actor = st.session_state.get("user")
                    log_event(usuario=str(actor) if actor else None, accion="DELETE", tabla="users", registro_id=obj.id, detalle=f"Eliminado usuario {obj.username}")
                except Exception:
                    pass
            db.close()
            st.rerun()
else:
    # Vista limitada: solo cambiar su propia contraseña
    #st.info("Solo puede cambiar su propia contraseña")
    # Obtener su usuario
    my_user = None
    if username_ss:
        db = SessionLocal()
        try:
            my_user = db.query(User).filter(User.username == str(username_ss)).first()
        finally:
            db.close()

    with st.form("change_password_self"):
        st.text_input("Usuario", value=str(username_ss or ""), disabled=True)
        new_pass = st.text_input("Nueva Contraseña", type="password")
        submitted = st.form_submit_button("Actualizar")
        if submitted and new_pass:
            if not my_user:
                st.error("No se encontró su usuario")
            else:
                db = SessionLocal()
                obj = db.query(User).get(my_user.id)
                if obj:
                    obj.password_hash = new_pass
                    db.commit()
                    st.success("Contraseña actualizada")
                    try:
                        actor = st.session_state.get("user")
                        log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="users", registro_id=obj.id, detalle="Cambio de contraseña (self)")
                    except Exception:
                        pass
                db.close()
