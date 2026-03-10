import streamlit as st
from services.reports import ReportService
import pandas as pd

def export_buttons_df(df: pd.DataFrame, base_filename: str, title: str, pdf_exclude_cols: list[str] | None = None):
    c1, c2 = st.columns(2)
    with c1:
        excel_bytes = ReportService.df_to_excel_bytes(df)
        st.download_button("📥 Exportar Excel", data=excel_bytes, file_name=f"{base_filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        pdf_df = df.drop(columns=pdf_exclude_cols) if pdf_exclude_cols else df
        data = pdf_df.to_dict(orient="records")
        pdf_bytes = ReportService.data_to_pdf_bytes(data, title)
        st.download_button("📄 Exportar PDF", data=pdf_bytes, file_name=f"{base_filename}.pdf", mime="application/pdf")
