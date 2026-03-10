"""
10_audit.py — Módulo de Auditoría del Sistema Conitek
Registro compacto de todos los movimientos del sistema con filtros y búsqueda.
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURACIÓN Y CONEXIÓN
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Auditoría · Conitek",
    page_icon="🔍",
    layout="wide",
)

# Estilos compactos
st.markdown("""
<style>
  .audit-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #f1f5f9;
    padding: 12px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .audit-header h2 { margin: 0; font-size: 1.1rem; font-weight: 600; }
  .audit-header span { font-size: 0.78rem; color: #94a3b8; }

  .badge-row { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
  .badge {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.78rem;
    color: #475569;
  }
  .badge strong { color: #1e293b; font-size: 0.95rem; display: block; }

  .tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:600; }
  .tag-INSERT  { background:#dcfce7; color:#166534; }
  .tag-UPDATE  { background:#dbeafe; color:#1e40af; }
  .tag-DELETE  { background:#fee2e2; color:#991b1b; }
  .tag-LOGIN   { background:#fef9c3; color:#854d0e; }
  .tag-LOGOUT  { background:#f3e8ff; color:#6b21a8; }
  .tag-DEFAULT { background:#f1f5f9; color:#475569; }

  .stDataFrame { font-size: 0.8rem; }
  div[data-testid="stDataFrame"] table td { padding: 4px 8px !important; }

  .filter-bar { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:12px; }

  .block-container { padding-top: 1rem !important; }
  header[data-testid="stHeader"] { display:none; }

  [data-testid="stExpander"] > details > summary {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
  }
  [data-testid="stExpander"] > details > summary p {
    color: #f1f5f9 !important;
    font-weight: 600;
  }
  .filter-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    margin-top: 10px;
    box-shadow: 0 2px 10px rgba(2,6,23,0.06);
  }
  .filter-card input, .filter-card select {
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
  }
  .filter-card label {
    color: #0f172a;
    font-weight: 600;
    font-size: 0.85rem;
  }
  div[data-testid="stDataFrame"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(2,6,23,0.06);
  }
  div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #334155 !important;
  }
  div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: #f8fafc !important;
  }
  div[data-testid="stDataFrame"] tbody tr:hover td {
    background: #e2e8f0 !important;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "conitek_system"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "sa"),
    )


def ensure_audit_table(conn):
    """Crea la tabla de auditoría si no existe."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          SERIAL PRIMARY KEY,
                fecha       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                usuario     VARCHAR(100),
                accion      VARCHAR(20),   -- INSERT, UPDATE, DELETE, LOGIN, LOGOUT
                tabla       VARCHAR(60),
                registro_id VARCHAR(60),
                detalle     TEXT,
                ip          VARCHAR(45)
            );
            CREATE INDEX IF NOT EXISTS idx_audit_fecha   ON audit_log(fecha DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_accion  ON audit_log(accion);
            CREATE INDEX IF NOT EXISTS idx_audit_tabla   ON audit_log(tabla);
            CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_log(usuario);
        """)
        conn.commit()


def load_audit(conn, filters: dict) -> pd.DataFrame:
    conditions = ["1=1"]
    params = []

    if filters.get("usuario"):
        conditions.append("LOWER(usuario) LIKE %s")
        params.append(f"%{filters['usuario'].lower()}%")

    if filters.get("accion") and filters["accion"] != "Todas":
        conditions.append("accion = %s")
        params.append(filters["accion"])

    if filters.get("tabla") and filters["tabla"] != "Todas":
        conditions.append("tabla = %s")
        params.append(filters["tabla"])

    if filters.get("busqueda"):
        conditions.append("(LOWER(detalle) LIKE %s OR LOWER(registro_id) LIKE %s OR LOWER(tabla) LIKE %s)")
        term = f"%{filters['busqueda'].lower()}%"
        params += [term, term, term]

    if filters.get("fecha_desde"):
        conditions.append("fecha >= %s")
        params.append(filters["fecha_desde"])

    if filters.get("fecha_hasta"):
        conditions.append("fecha < %s")
        params.append(filters["fecha_hasta"] + timedelta(days=1))

    where = " AND ".join(conditions)
    limit = filters.get("limite", 500)

    query = f"""
        SELECT
            id,
            fecha AT TIME ZONE 'UTC' AS fecha,
            usuario,
            accion,
            tabla,
            registro_id AS "reg_id",
            detalle,
            ip
        FROM audit_log
        WHERE {where}
        ORDER BY fecha DESC
        LIMIT %s
    """
    params.append(limit)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["id", "fecha", "usuario", "accion", "tabla", "reg_id", "detalle", "ip"]
    )


def load_stats(conn) -> dict:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                COUNT(*)                                            AS total,
                COUNT(*) FILTER (WHERE fecha > NOW() - INTERVAL '24h') AS hoy,
                COUNT(DISTINCT usuario)                             AS usuarios,
                COUNT(*) FILTER (WHERE accion = 'DELETE')          AS eliminaciones
            FROM audit_log
        """)
        return dict(cur.fetchone() or {})


def get_distinct(conn, column: str) -> list:
    with conn.cursor() as cur:
        cur.execute(f"SELECT DISTINCT {column} FROM audit_log WHERE {column} IS NOT NULL ORDER BY 1")
        return [r[0] for r in cur.fetchall()]


def color_accion(accion: str) -> str:
    colors = {
        "INSERT": "background-color:#dcfce7; color:#166534",
        "UPDATE": "background-color:#dbeafe; color:#1e40af",
        "DELETE": "background-color:#fee2e2; color:#991b1b",
        "LOGIN":  "background-color:#fef9c3; color:#854d0e",
        "LOGOUT": "background-color:#f3e8ff; color:#6b21a8",
    }
    return colors.get(accion, "background-color:#f1f5f9; color:#475569")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # Conexión
    try:
        conn = get_connection()
        ensure_audit_table(conn)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        st.stop()

    # Header compacto
    st.markdown("""
    <div class="audit-header">
      🔍 <div>
        <h2>Auditoría del Sistema</h2>
        <span>Registro de todos los movimientos y acciones</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Estadísticas rápidas ──────────────────
    stats = load_stats(conn)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total registros",  f"{stats.get('total', 0):,}")
    c2.metric("⚡ Últimas 24h",       f"{stats.get('hoy', 0):,}")
    c3.metric("👤 Usuarios activos",  f"{stats.get('usuarios', 0):,}")
    c4.metric("🗑️ Eliminaciones",     f"{stats.get('eliminaciones', 0):,}")

    st.divider()

    # ── Filtros ───────────────────────────────
    with st.expander("🔧 Filtros y búsqueda", expanded=True):
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            busqueda = st.text_input("🔎 Buscar en detalle / tabla / ID", placeholder="ej: García, participante, 42…")

        with col2:
            acciones = ["Todas"] + get_distinct(conn, "accion")
            accion_sel = st.selectbox("Acción", acciones)

        with col3:
            tablas = ["Todas"] + get_distinct(conn, "tabla")
            tabla_sel = st.selectbox("Tabla", tablas)

        col4, col5, col6, col7 = st.columns([2, 1, 1, 1])

        with col4:
            usuario_fil = st.text_input("👤 Usuario", placeholder="nombre o email…")

        with col5:
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))

        with col6:
            fecha_hasta = st.date_input("Hasta", value=date.today())

        with col7:
            limite = st.selectbox("Máx. filas", [100, 250, 500, 1000, 5000], index=2)
        st.markdown('</div>', unsafe_allow_html=True)

    filters = {
        "busqueda":    busqueda,
        "accion":      accion_sel,
        "tabla":       tabla_sel,
        "usuario":     usuario_fil,
        "fecha_desde": datetime.combine(fecha_desde, datetime.min.time()),
        "fecha_hasta": datetime.combine(fecha_hasta, datetime.min.time()),
        "limite":      limite,
    }

    # ── Datos ─────────────────────────────────
    df = load_audit(conn, filters)

    if df.empty:
        st.info("📭 No se encontraron registros con los filtros aplicados.")
        return

    # Formatear fecha
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    total_rows = len(df)
    st.caption(f"Mostrando **{total_rows:,}** registro(s) · ordenados por fecha desc")

    # ── Tabla ─────────────────────────────────
    col_config = {
        "id":      st.column_config.NumberColumn("ID",      width="small"),
        "fecha":   st.column_config.TextColumn("Fecha/Hora", width="medium"),
        "usuario": st.column_config.TextColumn("Usuario",   width="medium"),
        "accion":  st.column_config.TextColumn("Acción",    width="small"),
        "tabla":   st.column_config.TextColumn("Tabla",     width="small"),
        "reg_id":  st.column_config.TextColumn("Reg. ID",   width="small"),
        "detalle": st.column_config.TextColumn("Detalle",   width="large"),
        "ip":      st.column_config.TextColumn("IP",        width="small"),
    }

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
        height=420,
    )

    # ── Exportar ──────────────────────────────
    col_exp1, col_exp2 = st.columns([1, 5])
    with col_exp1:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar CSV",
            data=csv,
            file_name=f"auditoria_{date.today()}.csv",
            mime="text/csv",
        )

    # ── Gráfico de actividad por acción ───────
    st.divider()
    if "accion" in df.columns and not df.empty:
        st.markdown("##### 📊 Distribución por acción")
        chart_df = df["accion"].value_counts().reset_index()
        chart_df.columns = ["Acción", "Cantidad"]
        st.bar_chart(chart_df.set_index("Acción"), use_container_width=True, height=160)


# ─────────────────────────────────────────────
# FUNCIONES AUXILIARES (importables desde otros módulos)
# ─────────────────────────────────────────────

def registrar_evento(conn, usuario: str, accion: str, tabla: str,
                     registro_id=None, detalle: str = "", ip: str = None):
    """
    Registra un evento en audit_log desde cualquier módulo del sistema.

    Uso:
        from pages.audit import registrar_evento
        registrar_evento(conn, usuario="ana@mail.com", accion="INSERT",
                         tabla="participantes", registro_id=42,
                         detalle="Nuevo participante: Ana Pérez")
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_log (usuario, accion, tabla, registro_id, detalle, ip)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario, accion.upper(), tabla, str(registro_id) if registro_id else None, detalle, ip))
            conn.commit()
    except Exception as e:
        # No interrumpir el flujo principal si falla el log
        print(f"[AUDIT WARNING] No se pudo registrar evento: {e}")


if __name__ == "__main__":
    main()
else:
    main()
