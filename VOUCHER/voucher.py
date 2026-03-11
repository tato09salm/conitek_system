from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
import qrcode
import urllib.parse

@dataclass
class VoucherData:
    """Clase para almacenar los datos del voucher"""
    numero_recibo: str
    fecha: str
    hora: str
    monto: str
    nombre: str
    carnet: str
    escuela: str
    monto_palabras: str
    concepto: str
    serie: str

def generar_voucher(datos: VoucherData) -> Image.Image:
    """
    Genera una imagen del voucher con los datos proporcionados
    
    Args:
        datos: Objeto VoucherData con toda la información del voucher
        
    Returns:
        Imagen PIL del voucher generado
    """
    # Crear imagen en blanco
    ancho, alto = 1200, 900
    img = Image.new('RGB', (ancho, alto), color='white')
    draw = ImageDraw.Draw(img)
    
    # Colores
    verde_unt = (45, 122, 62)
    rojo_serie = (255, 68, 68)
    negro = (0, 0, 0)
    gris_oscuro = (51, 51, 51)
    
    # Intentar cargar fuentes (con fallback)
    try:
        font_titulo = ImageFont.truetype("arial.ttf", 36)
        font_subtitulo = ImageFont.truetype("arial.ttf", 30)
        font_texto = ImageFont.truetype("arial.ttf", 26)#18
        font_recibo = ImageFont.truetype("cour.ttf", 28)
        font_datos = ImageFont.truetype("cour.ttf", 26) #18
        font_datos_bold = ImageFont.truetype("courbd.ttf", 20)
        font_serie = ImageFont.truetype("arial.ttf", 48)
        font_serie_text = ImageFont.truetype("arialbd.ttf", 24)

    except:
        # Fallback a fuente por defecto
        font_titulo = ImageFont.load_default()
        font_subtitulo = ImageFont.load_default()
        font_texto = ImageFont.load_default()
        font_recibo = ImageFont.load_default()
        font_datos = ImageFont.load_default()
        font_datos_bold = ImageFont.load_default()
        font_serie = ImageFont.load_default()
        font_serie_text = ImageFont.load_default()
    
    # ===== ENCABEZADO =====
    draw.text((600, 60), "UNIVERSIDAD NACIONAL DE TRUJILLO", 
              fill=verde_unt, font=font_titulo, anchor="mm")
    draw.text((600, 90), "DIRECCIÓN DE TESORERÍA", 
              fill=verde_unt, font=font_subtitulo, anchor="mm")
    draw.text((600, 115), "ÁREA DE GESTIÓN DE INGRESOS", 
              fill=verde_unt, font=font_subtitulo, anchor="mm")
    draw.text((600, 140), "Diego de Almagro N° 344 - TRUJILLO - PERÚ", 
              fill=verde_unt, font=font_texto, anchor="mm")
    draw.text((600, 165), "R.U.C. 20172857628", 
              fill=verde_unt, font=font_texto, anchor="mm")
    
    # RECIBO DE CAJA
    draw.text((600, 210), "RECIBO DE CAJA", 
              fill=verde_unt, font=font_titulo, anchor="mm")
    
    # Número de recibo (centro)
    draw.text((650, 260), datos.numero_recibo, 
              fill=verde_unt, font=font_titulo, anchor="rm")
    
    # ===== INFORMACIÓN DEL VOUCHER =====
    y_pos = 320
    
    # Línea 1: TASA
    draw.text((80, y_pos), 
              "TASA : 20  VENT:4      CTA.IP:122 .03.01 .01.01    SIAF:132.311",
              fill=negro, font=font_datos)
    
    # Línea 2: Fecha, Hora, Monto
    y_pos += 40
    texto_fecha_hora = f"FECHA : {datos.fecha}    HORA : {datos.hora}    S/. {datos.monto}"
    draw.text((80, y_pos), texto_fecha_hora, 
              fill=negro, font=font_datos)
    
    # Línea 3: He recibido de
    y_pos += 60
    texto_recibido = f"HE RECIBIDO DE : {datos.nombre} CARNET: {datos.carnet}"
    draw.text((80, y_pos), texto_recibido, 
              fill=negro, font=font_datos)
    
    # Línea 4: Escuela
    y_pos += 40
    texto_escuela = f"ESCUELA         : {datos.escuela}"
    draw.text((80, y_pos), texto_escuela, 
              fill=negro, font=font_datos)
    
    # Línea 5: La suma de
    y_pos += 40
    texto_suma = f"   LA SUMA DE   : {datos.monto_palabras}"
    draw.text((80, y_pos), texto_suma, 
              fill=negro, font=font_datos)
    
    # Línea 6: Por concepto de
    y_pos += 40
    draw.text((80, y_pos), "POR CONCEPTO DE:", 
              fill=negro, font=font_datos)
    
    # Línea 7: Concepto
    y_pos += 40
    draw.text((80, y_pos), f"      {datos.concepto}", 
              fill=negro, font=font_datos)
    
    # ===== QR DE VERIFICACIÓN =====
    params = urllib.parse.urlencode({
        "recibo": datos.numero_recibo,
        "serie": datos.serie,
        "monto": datos.monto
    })
    url_verificacion = f"https://conitek2026.unt.edu.pe/verificar?{params}"

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=5,
        border=2,
    )
    qr.add_data(url_verificacion)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((155, 155), Image.LANCZOS)

    qr_x, qr_y = 930, 645
    img.paste(qr_img, (qr_x, qr_y))

    # Etiqueta encima del QR
    draw.text((qr_x + 77, qr_y - 18), "VERIFICAR PAGO",
              fill=verde_unt, font=font_serie_text, anchor="mm")

    # ===== SERIE =====
    # Serie N° 1 (abajo izquierda)
    draw.text((80, 820), "Serie N° 1", 
              fill=verde_unt, font=font_serie_text)
    
    # Número de serie (abajo derecha)
    draw.text((1100, 820), datos.serie, 
              fill=rojo_serie, font=font_serie, anchor="rm")
    
    # ===== CÍRCULOS DE PERFORACIÓN =====
    for i in range(8):
        x = 1150
        y = 100 + i * 100
        draw.ellipse([x-15, y-15, x+15, y+15], fill=gris_oscuro)
    
    return img