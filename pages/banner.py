import streamlit as st
import os, json
from config import Config
from services.audit import log_event

st.set_page_config(page_title="Banner", page_icon="🖼️", layout="centered")

role = str(st.session_state.get("role") or "").lower()
if role not in ["admin", "administrador", "tesorero", "tesoreria", "tesorería"]:
    st.warning("Solo administradores o tesorería pueden editar el banner")
    st.stop()

cfg_path = os.path.join(Config.ASSETS_DIR, "banner_config.json")
os.makedirs(Config.ASSETS_DIR, exist_ok=True)

def load_cfg():
    base = {
        "image_path": "",
        "image_url": "https://image2url.com/r2/default/images/1772822996355-d97c481b-c863-4935-837e-ffd88abee4a3.jpg",
        "title": "📋 Información del Evento",
        "description": "📋 Información del Evento\n- Fecha: 15-17 Nov 2026\n- Presencial y Virtual\n- Sede: UNT\n- Certificación incluida",
        "grad_top": "#000080",
        "grad_bottom": "#1e90ff",
        "text_color": "#ffffff",
        "title_color": "#ffffff",
        "desc_color": "#ffffff",
        "max_height_px": 420
    }
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as rf:
                data = json.load(rf)
                if isinstance(data, dict):
                    base.update(data)
    except Exception:
        pass
    return base

def save_cfg(data):
    with open(cfg_path, "w", encoding="utf-8") as wf:
        json.dump(data, wf, ensure_ascii=False, indent=2)

st.title("Editor de Banner (Login)")
cfg = load_cfg()

# Asegurar claves aunque bn_init exista de una versión previa
defaults_map = {
    "bn_grad_top": cfg["grad_top"],
    "bn_text_color": cfg["text_color"],
    "bn_grad_bottom": cfg["grad_bottom"],
    "bn_max_h": int(cfg["max_height_px"]),
    "bn_desc": cfg["description"],
    "bn_title": cfg["title"],
    "bn_title_color": cfg["title_color"],
    "bn_desc_color": cfg["desc_color"],
    "bn_same_colors": False,
}
for k, dv in defaults_map.items():
    if k not in st.session_state:
        st.session_state[k] = dv
st.session_state["bn_init"] = True

if st.session_state.get("bn_reset_pending"):
    cur = load_cfg()
    st.session_state["bn_grad_top"] = cur["grad_top"]
    st.session_state["bn_text_color"] = cur["text_color"]
    st.session_state["bn_grad_bottom"] = cur["grad_bottom"]
    st.session_state["bn_max_h"] = int(cur["max_height_px"])
    st.session_state["bn_desc"] = cur["description"]
    st.session_state["bn_title"] = cur["title"]
    st.session_state["bn_title_color"] = cur["title_color"]
    st.session_state["bn_desc_color"] = cur["desc_color"]
    st.session_state["preview_cfg"] = cur
    st.session_state["bn_reset_pending"] = False

left, right = st.columns([1, 1])
with left:
    with st.form("banner_form"):
        up = st.file_uploader("Imagen del banner (JPG/PNG)", type=["png","jpg","jpeg"])
        cta, ctb = st.columns(2)
        with cta:
            grad_top = st.color_picker("Color superior", st.session_state.get("bn_grad_top", cfg["grad_top"]), key="bn_grad_top")
            text_color = st.color_picker("Color del texto", st.session_state.get("bn_text_color", cfg["text_color"]), key="bn_text_color")
            title_text = st.text_input("Título", st.session_state.get("bn_title", cfg["title"]), key="bn_title")
        with ctb:
            grad_bottom = st.color_picker("Color inferior", st.session_state.get("bn_grad_bottom", cfg["grad_bottom"]), key="bn_grad_bottom")
            max_h = st.slider("Altura máxima (px)", min_value=240, max_value=720, value=int(st.session_state.get("bn_max_h", int(cfg["max_height_px"]))), step=10, key="bn_max_h")
        title_color = st.color_picker("Color del título", st.session_state.get("bn_title_color", cfg["title_color"]), key="bn_title_color")
        same = st.checkbox("Aplicar el mismo color a Título y Descripción", value=st.session_state.get("bn_same_colors", False), key="bn_same_colors")
        if same:
            desc_color_val = title_color
            st.session_state["bn_desc_color"] = title_color
        else:
            desc_color_val = st.color_picker("Color de la descripción", st.session_state.get("bn_desc_color", cfg["desc_color"]), key="bn_desc_color")
        desc = st.text_area("Descripción debajo de la imagen", st.session_state.get("bn_desc", cfg["description"]), height=140, key="bn_desc")
        c1, c2, c3 = st.columns(3)
        preview = c1.form_submit_button("Previsualizar")
        save = c2.form_submit_button("Guardar y Publicar")
        reset_btn = c3.form_submit_button("Restablecer")

if "preview_cfg" not in st.session_state:
    st.session_state["preview_cfg"] = cfg

if reset_btn:
    st.session_state["bn_reset_pending"] = True
    st.rerun()

if preview or save:
    new_cfg = cfg.copy()
    new_cfg["grad_top"] = grad_top
    new_cfg["grad_bottom"] = grad_bottom
    new_cfg["text_color"] = text_color
    new_cfg["max_height_px"] = int(max_h)
    new_cfg["title"] = title_text
    new_cfg["title_color"] = title_color
    new_cfg["desc_color"] = desc_color_val
    new_cfg["description"] = desc
    if up is not None:
        ext = os.path.splitext(up.name)[1].lower() or ".png"
        dest = os.path.join(Config.ASSETS_DIR, f"banner_image{ext}")
        with open(dest, "wb") as out:
            out.write(up.getbuffer())
        new_cfg["image_path"] = dest
        new_cfg["image_url"] = ""
    st.session_state["preview_cfg"] = new_cfg
    if save:
        save_cfg(new_cfg)
        st.success("Cambios guardados. El banner del login se actualizó.")
        try:
            actor = st.session_state.get("user")
            log_event(usuario=str(actor) if actor else None, accion="UPDATE", tabla="banner", detalle="Actualización de banner")
        except Exception:
            pass

with right:
    pcfg = st.session_state["preview_cfg"]
    st.markdown(
        f"<style>.demo-info{{background: linear-gradient(135deg, {pcfg['grad_top']} 0%, {pcfg['grad_bottom']} 100%); color:{pcfg['text_color']};}} .demo-img{{max-height:{pcfg['max_height_px']}px; overflow:hidden}}</style>",
        unsafe_allow_html=True
    )
    st.markdown("### Previsualización")
    with st.container(border=True):
        st.markdown('<div class="demo-img">', unsafe_allow_html=True)
        img_src = pcfg.get("image_path") or pcfg.get("image_url")
        st.image(img_src, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            f"<div class='demo-info' style='border-radius:10px;padding:10px 12px;margin-top:8px;'>"
            f"<div style='font-weight:700;margin-bottom:6px; color:{pcfg.get('title_color','#ffffff')}'>{pcfg.get('title','')}</div>"
            f"<div style='white-space:pre-line;font-size:13px; color:{pcfg.get('desc_color','#ffffff')}'>{pcfg.get('description') or ''}</div>"
            f"</div>", unsafe_allow_html=True
        )
