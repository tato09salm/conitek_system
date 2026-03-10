import pandas as pd
from fpdf import FPDF
import streamlit as st
from config import Config
import os
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

class ReportService:
    @staticmethod
    def generate_excel(data, filename, headers=None):
        df = pd.DataFrame(data)
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(Config.REPORTS_DIR, filename)
        df.to_excel(output_path, index=False, sheet_name='Reporte')
        return output_path

    @staticmethod
    def generate_pdf(data, filename, title="Reporte"):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.ln(6)
        if not data:
            os.makedirs(Config.REPORTS_DIR, exist_ok=True)
            output_path = os.path.join(Config.REPORTS_DIR, filename)
            pdf.output(output_path)
            return output_path
        headers = list(data[0].keys())
        # Cálculo de anchos por contenido
        padding = 4
        max_width = pdf.w - 20
        content_widths = []
        for h in headers:
            max_str = len(str(h))
            for row in data:
                max_str = max(max_str, len(str(row.get(h, ""))))
            w = min(max(pdf.get_string_width("W") * max_str + padding, 24), 95)
            content_widths.append(w)
        total = sum(content_widths)
        if total > max_width:
            scale = max_width / total
            content_widths = [w * scale for w in content_widths]
        # Encabezados
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("Arial", 'B', 10)
        x0 = pdf.get_x()
        for w, htxt in zip(content_widths, headers):
            pdf.cell(w, 8, str(htxt), border=1, fill=True, align='L')
        pdf.ln()
        # Filas con altura uniforme por fila
        pdf.set_font("Arial", size=10)
        line_h = 6
        def wrap_text(txt, width):
            s = str(txt)
            if " " not in s:
                return [s]
            words = s.split(" ")
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if pdf.get_string_width(test) + padding <= width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                        cur = w
                    else:
                        lines.append(w)
                        cur = ""
            if cur:
                lines.append(cur)
            return lines or [""]
        for row in data:
            cell_lines = []
            for w, h in zip(content_widths, headers):
                lines = wrap_text(row.get(h, ""), w)
                cell_lines.append(lines)
            max_lines = max(len(lines) for lines in cell_lines)
            row_h = line_h * max_lines
            x = x0
            y = pdf.get_y()
            for w, lines in zip(content_widths, cell_lines):
                if len(lines) < max_lines:
                    lines = lines + [""] * (max_lines - len(lines))
                pdf.set_xy(x, y)
                pdf.multi_cell(w, line_h, "\n".join(lines), border=1, align='L')
                x += w
            pdf.set_y(y + row_h)
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(Config.REPORTS_DIR, filename)
        pdf.output(output_path)
        return output_path
    
    @staticmethod
    def df_to_excel_bytes(df: pd.DataFrame):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte')
            try:
                ws = writer.sheets['Reporte']
                from openpyxl.utils import get_column_letter
                for i, col in enumerate(df.columns, 1):
                    max_len = max(
                        [len(str(col))] + [len(str(v)) for v in df[col].astype(str).tolist()]
                    )
                    ws.column_dimensions[get_column_letter(i)].width = min(max_len + 2, 50)
            except Exception:
                pass
        return output.getvalue()
    
    @staticmethod
    def data_to_pdf_bytes(data, title="Reporte"):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.ln(6)
        #pdf.cell(0, 8, f"Generado por: {Config.CONGRESS_NAME}", ln=True)
        pdf.ln(4)
        if not data:
            return bytes(pdf.output(dest='S'))
        headers = list(data[0].keys())
        # Calcular anchos por contenido
        pdf.set_font("Arial", size=10)
        padding = 4
        max_width = pdf.w - 20  # ancho útil considerando márgenes
        content_widths = []
        for h in headers:
            max_str = len(str(h))
            for row in data:
                max_str = max(max_str, len(str(row.get(h, ""))))
            # Estimación de ancho por caracteres
            w = min(max(pdf.get_string_width("W") * max_str + padding, 24), 95)
            content_widths.append(w)
        total = sum(content_widths)
        if total > max_width:
            scale = max_width / total
            content_widths = [w * scale for w in content_widths]
        # Encabezados
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("Arial", 'B', 10)
        x0 = pdf.get_x()
        for w, htxt in zip(content_widths, headers):
            pdf.cell(w, 8, str(htxt), border=1, fill=True, align='L')
        pdf.ln()
        # Filas con ajuste de texto
        pdf.set_font("Arial", size=10)
        line_h = 6
        def wrap_text(txt, width):
            s = str(txt)
            if " " not in s:
                return [s]
            words = s.split(" ")
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if pdf.get_string_width(test) + padding <= width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                        cur = w
                    else:
                        # palabra más larga que el ancho: agréguela como una sola línea y continúe
                        lines.append(w)
                        cur = ""
            if cur:
                lines.append(cur)
            return lines or [""]
        for row in data:
            # Calcular altura máxima de la fila
            cell_lines = []
            for w, h in zip(content_widths, headers):
                lines = wrap_text(row.get(h, ""), w)
                cell_lines.append(lines)
            max_lines = max(len(lines) for lines in cell_lines)
            row_h = line_h * max_lines
            # Dibujar celdas
            x = x0
            y = pdf.get_y()
            for w, lines in zip(content_widths, cell_lines):
                if len(lines) < max_lines:
                    lines = lines + [""] * (max_lines - len(lines))
                pdf.set_xy(x, y)
                # Dibujar borde de la celda
                pdf.multi_cell(w, line_h, "\n".join(lines), border=1, align='L')
                x += w
            pdf.set_y(y + row_h)
        return bytes(pdf.output(dest='S'))
    
    @staticmethod
    def dashboard_pdf_bytes(figures, title="Dashboard CONITEK", kpis: dict | None = None):
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.set_font("Arial", size=11)
        pdf.ln(4)
        pdf.cell(0, 8, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        if kpis:
            pdf.ln(2)
            for k, v in kpis.items():
                pdf.cell(0, 8, f"- {k}: {v}", ln=True)
        try:
            import plotly.io as pio
        except Exception:
            return bytes(pdf.output(dest='S'))
        tmp_img_paths = []
        for idx, fig in enumerate(figures or []):
            try:
                img_bytes = fig.to_image(format="png", scale=2)
                img_path = os.path.join(Config.REPORTS_DIR, f"dash_fig_{idx+1}.png")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                tmp_img_paths.append(img_path)
            except Exception:
                continue
        for img_path in tmp_img_paths:
            pdf.add_page()
            page_width = pdf.w - 20
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Gráfico", ln=True)
            pdf.image(img_path, x=10, y=20, w=page_width)
            pdf.set_y(280)
            pdf.set_font("Arial", size=9)
            pdf.cell(0, 6, f"{Config.CONGRESS_NAME} - {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        return bytes(pdf.output(dest='S'))
    
    @staticmethod
    def event_attendees_pdf_bytes(event_info: dict, speakers: list[str], audience: list[str]):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Lista de Participantes", ln=True, align='C')
        pdf.set_font("Arial", size=11)
        pdf.ln(2)
        # Normalizador a Latin-1 (evita errores por “…” y similares)
        def _ascii(s: str) -> str:
            if s is None:
                return ""
            txt = str(s)
            repl = {
                "…": "...",
                "—": "-",
                "–": "-",
                "“": '"',
                "”": '"',
                "‘": "'",
                "’": "'",
            }
            for k, v in repl.items():
                txt = txt.replace(k, v)
            try:
                txt.encode('latin-1')
                return txt
            except UnicodeEncodeError:
                return txt.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 7, _ascii(f"Evento: {event_info.get('name','-')}"), ln=True)
        pdf.cell(0, 7, _ascii(f"Lugar: {event_info.get('location','-')}    Fecha: {event_info.get('date','-')}"), ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Ponentes", ln=True)
        pdf.set_font("Arial", 'B', 10)
        cw1, cw2, cw3 = 25, 60, 80
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(cw1, 8, _ascii("DNI"), border=1, fill=True)
        pdf.cell(cw2, 8, _ascii("Ponente"), border=1, fill=True)
        pdf.cell(cw3, 8, _ascii("Nombre Ponencia"), border=1, ln=True, fill=True)
        pdf.set_font("Arial", size=10)
        if speakers:
            for row in speakers:
                parts = row.split(" ", 1)
                dni = parts[0] if len(parts) > 0 else ""
                rest = parts[1] if len(parts) > 1 else ""
                cols = rest.split(" - ", 1)
                ponente = cols[0] if len(cols) > 0 else ""
                titulo = cols[1] if len(cols) > 1 else ""
                y = pdf.get_y()
                x = pdf.get_x()
                pdf.multi_cell(cw1, 6, _ascii(dni), border=1)
                h = pdf.get_y() - y
                pdf.set_xy(x + cw1, y)
                pdf.multi_cell(cw2, 6, _ascii(ponente), border=1)
                h2 = pdf.get_y() - y
                pdf.set_xy(x + cw1 + cw2, y)
                pdf.multi_cell(cw3, 6, _ascii(titulo), border=1)
                hh = max(h, h2, pdf.get_y() - y)
                pdf.set_y(y + hh)
        else:
            pdf.cell(cw1 + cw2 + cw3, 8, _ascii("(sin registros)"), border=1, ln=True)
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, _ascii("Público"), ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 8, _ascii("DNI"), border=1, fill=True)
        pdf.cell(125, 8, _ascii("Nombre"), border=1, ln=True, fill=True)
        pdf.set_font("Arial", size=10)
        if audience:
            for row in audience:
                parts = row.split(" ", 1)
                dni = parts[0] if len(parts) > 0 else ""
                nombre = parts[1] if len(parts) > 1 else ""
                y = pdf.get_y()
                x = pdf.get_x()
                pdf.multi_cell(40, 6, _ascii(dni), border=1)
                h = pdf.get_y() - y
                pdf.set_xy(x + 40, y)
                pdf.multi_cell(125, 6, _ascii(nombre), border=1)
                hh = max(h, pdf.get_y() - y)
                pdf.set_y(y + hh)
        else:
            pdf.cell(40 + 125, 8, _ascii("(sin registros)"), border=1, ln=True)
        return bytes(pdf.output(dest='S'))
    
    @staticmethod
    def payment_receipt_pdf_bytes(info: dict):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "Comprobante de Pago", ln=True, align='C')
        pdf.set_font("Arial", size=11)
        pdf.ln(5)
        pdf.cell(0, 8, f"Evento: {info.get('event_name','-')}", ln=True)
        pdf.cell(0, 8, f"Referencia: {info.get('reference','-')}", ln=True)
        pdf.cell(0, 8, f"Comprobante N°: {info.get('receipt_no','-')}", ln=True)
        pdf.cell(0, 8, f"Fecha: {info.get('created_at','-')}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Datos del Participante", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Nombre: {info.get('participant_name','-')}", ln=True)
        pdf.cell(0, 8, f"DNI: {info.get('dni','-')}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Detalle del Pago", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Método: {info.get('method','-')}", ln=True)
        pdf.cell(0, 8, f"Monto: S/. {float(info.get('amount',0)):.2f}", ln=True)
        pdf.cell(0, 8, f"Estado: {info.get('status','-')}", ln=True)
        pdf.ln(10)
        pdf.cell(0, 8, f"Generado por: {Config.CONGRESS_NAME}", ln=True)
        return bytes(pdf.output(dest='S'))

    @staticmethod
    def dashboard_report_pdf_bytes(figures, captions: list[str] | None = None, title="Reporte del Dashboard", kpis: dict | None = None):
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 14, title, ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"{Config.CONGRESS_NAME}", ln=True, align='C')
        pdf.ln(6)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        if kpis:
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Indicadores Clave", ln=True)
            pdf.set_font("Arial", size=11)
            for k, v in kpis.items():
                pdf.cell(0, 8, f"- {k}: {v}", ln=True)
        try:
            import plotly.io as pio
        except Exception:
            return bytes(pdf.output(dest='S'))
        tmp_imgs = []
        for idx, fig in enumerate(figures or []):
            try:
                img_bytes = fig.to_image(format="png", scale=2)
                path = os.path.join(Config.REPORTS_DIR, f"dash_report_{idx+1}.png")
                with open(path, "wb") as f:
                    f.write(img_bytes)
                tmp_imgs.append(path)
            except Exception:
                continue
        page_num = 1
        for i, path in enumerate(tmp_imgs):
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            if captions and i < len(captions):
                pdf.cell(0, 8, captions[i], ln=True)
            else:
                pdf.cell(0, 8, "Gráfico", ln=True)
            pdf.image(path, x=10, y=20, w=190)
            pdf.set_xy(10, 285)
            pdf.set_font("Arial", size=9)
            pdf.cell(0, 6, f"{Config.CONGRESS_NAME} - Pagina {i+2}", ln=True, align='R')
            page_num += 1
        return bytes(pdf.output(dest='S'))

    @staticmethod
    def payment_voucher_pdf_bytes(info: dict):
        w, h = 1200, 900
        img = Image.new('RGB', (w, h), color='white')
        dr = ImageDraw.Draw(img)
        verde = (45, 122, 62)
        rojo = (255, 68, 68)
        negro = (0, 0, 0)
        gris = (51, 51, 51)
        try:
            ft = ImageFont.truetype("arial.ttf", 36)
            fs = ImageFont.truetype("arial.ttf", 30)
            ftx = ImageFont.truetype("arial.ttf", 26)
            frc = ImageFont.truetype("cour.ttf", 28)
            fdat = ImageFont.truetype("cour.ttf", 26)
            fserien = ImageFont.truetype("arialbd.ttf", 24)
            fserie = ImageFont.truetype("arial.ttf", 48)
        except:
            ft = fs = ftx = frc = fdat = fserien = fserie = ImageFont.load_default()
        dr.text((600, 60), "UNIVERSIDAD NACIONAL DE TRUJILLO", fill=verde, font=ft, anchor="mm")
        dr.text((600, 90), "DIRECCIÓN DE TESORERÍA", fill=verde, font=fs, anchor="mm")
        dr.text((600, 115), "ÁREA DE GESTIÓN DE INGRESOS", fill=verde, font=fs, anchor="mm")
        dr.text((600, 140), "Diego de Almagro N° 344 - TRUJILLO - PERÚ", fill=verde, font=ftx, anchor="mm")
        dr.text((600, 165), "R.U.C. 20172857628", fill=verde, font=ftx, anchor="mm")
        dr.text((600, 210), "RECIBO DE CAJA", fill=verde, font=ft, anchor="mm")
        # Mostrar la referencia del pago como número principal bajo el título
        ref_text = str(info.get("reference", "")) or str(info.get("receipt_no", ""))
        dr.text((650, 260), ref_text, fill=verde, font=ft, anchor="rm")
        y = 320
        dr.text((80, y), "TASA : 20  VENT:4      CTA.IP:122 .03.01 .01.01    SIAF:132.311", fill=negro, font=fdat)
        y += 40
        created = info.get("created_at","")
        fecha = created.split(" ")[0] if " " in created else created
        hora = created.split(" ")[1] if " " in created else ""
        monto = f"S/. {float(info.get('amount',0)):.2f}"
        dr.text((80, y), f"FECHA : {fecha}    HORA : {hora}    {monto}", fill=negro, font=fdat)
        y += 60
        nombre = info.get("participant_name","-")
        dni = info.get("dni","-")
        dr.text((80, y), f"HE RECIBIDO DE : {nombre} DNI: {dni}", fill=negro, font=fdat)
        y += 40
        evento = info.get("event_name","-")
        dr.text((80, y), f"EVENTO         : {evento}", fill=negro, font=fdat)
        y += 40
        dr.text((80, y), f"   LA SUMA DE   : {monto}", fill=negro, font=fdat)
        y += 40
        dr.text((80, y), "POR CONCEPTO DE:", fill=negro, font=fdat)
        y += 40
        concepto = f"Pago por {info.get('method','-')} - {evento}"
        dr.text((80, y), f"      {consepto if (consepto:=concepto) else concepto}", fill=negro, font=fdat)
        dr.text((80, 820), "Serie N° 1", fill=verde, font=fserien)
        # Mostrar REG-[ID] en la parte inferior derecha
        rec_id = str(info.get("receipt_no", "")).strip()
        reg_text = f"REG-{rec_id}" if rec_id else "REG-"
        dr.text((1100, 820), reg_text, fill=rojo, font=fserie, anchor="rm")
        for i in range(8):
            x = 1150
            yy = 100 + i * 100
            dr.ellipse([x-15, yy-15, x+15, yy+15], fill=gris)
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        tmp = os.path.join(Config.REPORTS_DIR, f"voucher_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png")
        img.save(tmp, "PNG")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.image(tmp, x=0, y=0, w=210, h=297)
        return bytes(pdf.output(dest='S'))

def download_button_excel(df, filename, label="Descargar Excel"):
    processed_data = ReportService.df_to_excel_bytes(df)
    return st.download_button(
        label=label,
        data=processed_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
