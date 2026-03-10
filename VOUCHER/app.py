#app
import streamlit as st
from voucher import generar_voucher, VoucherData
from PIL import Image
import io

# Configuración de la página
st.set_page_config(
    page_title="Editor de Vouchers UNT",
    page_icon="🎓",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #e8f5e9 0%, #e3f2fd 100%);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2e7d32 0%, #1b5e20 100%);
        color: white;
        font-weight: bold;
        padding: 12px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown("""
    <div style='background: linear-gradient(90deg, #2e7d32 0%, #1b5e20 100%); 
                padding: 30px; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>🎓 Editor de Vouchers UNT</h1>
        <p style='color: #e8f5e9; margin: 5px 0 0 0;'>
            Universidad Nacional de Trujillo - Generador de Recibos de Caja
        </p>
    </div>
""", unsafe_allow_html=True)

# Layout en columnas
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 Datos del Voucher")
    
    # Formulario con los datos editables
    with st.form("voucher_form"):
        numero_recibo = st.text_input(
            "Número de Recibo (XXXX-XX-X)",
            value="1124-20-4",
            help="Formato: 1124-20-4"
        )

        
        
        col_fecha, col_hora = st.columns(2)
        with col_fecha:
            fecha = st.text_input("Fecha (DD/MM/YYYY)", value="13/10/2025")
        with col_hora:
            hora = st.text_input("Hora (HH:MM:SS)", value="12:09:16")
        
        monto = st.text_input("Monto (S/.)", value="180.00")
        
        nombre = st.text_input(
            "Nombre Completo",
            value="LOPEZ MALCA STIVEN ADRIAN"
        )
        
        carnet = st.text_input("Número de Carnet", value="1023300123")
        
        escuela = st.text_input(
            "Escuela",
            value="INGENIERIA DE SISTEMAS"
        )
        
        monto_palabras = st.text_input(
            "Monto en Palabras",
            value="CIENTO OCHENTA Y 00/100 NUEVOS SOLES"
        )
        
        concepto = st.text_input(
            "Concepto",
            value="SERVICIOS ORDINARIOS-COMEDOR UNIVERSITARIO"
        )
        
        serie = st.text_input(
            "Número de Serie (XXXXXXX)",
            value="0077349",
            max_chars=7
        )
        
        # Botón para generar
        submit_button = st.form_submit_button("🚀 Generar Voucher")

with col2:
    st.markdown("### 👁️ Vista Previa")
    
    if submit_button:
        # Crear objeto con los datos
        datos = VoucherData(
            numero_recibo=numero_recibo,
            fecha=fecha,
            hora=hora,
            monto=monto,
            nombre=nombre,
            carnet=carnet,
            escuela=escuela,
            monto_palabras=monto_palabras,
            concepto=concepto,
            serie=serie
        )
        
        # Generar el voucher
        with st.spinner("Generando voucher..."):
            imagen_voucher = generar_voucher(datos)
        
        # Mostrar la imagen
        st.image(imagen_voucher, use_container_width=True)
        
        # Botón de descarga
        buf = io.BytesIO()
        imagen_voucher.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="📥 Descargar Voucher",
            data=byte_im,
            file_name=f"voucher_{serie}.png",
            mime="image/png"
        )
        
        st.success("✅ ¡Voucher generado exitosamente!")
    else:
        st.info("👈 Completa el formulario y haz clic en 'Generar Voucher'")
        
        # Mostrar un voucher de ejemplo
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; 
                    border: 2px dashed #ccc; text-align: center;'>
            <p style='color: #666; margin: 0;'>
                El voucher generado aparecerá aquí
            </p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>💚 Desarrollado para la Universidad Nacional de Trujillo</p>
    </div>
""", unsafe_allow_html=True)