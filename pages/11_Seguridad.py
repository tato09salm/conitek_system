"""
11_Seguridad.py — Bitácora de Seguridad · CONITEK 2026
Historial de sesiones: quién ingresó, perfil, hora de entrada, hora de salida
y qué módulos visitó durante cada sesión.
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import timedelta, date
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Seguridad · Conitek",
    page_icon="🔒",
    layout="wide",
)

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────

st.markdown("""
<style>
  .sec-header {
    background: linear-gradient(135deg, #000080 0%, #1e3a8a 100%);
    color: #f1f5f9;
    padding: 14px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-left: 5px solid #ffd700;
  }
  .sec-header h2 { margin: 0; font-size: 1.15rem; font-weight: 700; color: #ffd700 !important; border:none !important; }
  .sec-header span { font-size: 0.78rem; color: #93c5fd; }

  .sec-metric {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  .sec-metric .met-label { font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }
  .sec-metric .met-value { font-size: 1.6rem; font-weight: 800; color: #000080; }
  .sec-metric .met-fail  { color: #dc2626 !important; }

  .filter-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    margin-top: 8px;
  }

  div[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }
  div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, #000080 0%, #1e3a8a 100%) !important;
    color: #ffd700 !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #1e40af !important;
  }
  div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: #f8fafc !important;
  }
  div[data-testid="stDataFrame"] tbody tr:hover td {
    background: #eff6ff !important;
  }

  [data-testid="stExpander"] > details > summary {
    background: linear-gradient(135deg, #000080 0%, #1e3a8a 100%);
    color: #ffd700;
    border: 1px solid #1e40af;
    border-radius: 8px;
    padding: 10px 14px;
  }
  [data-testid="stExpander"] > details > summary p {
    color: #ffd700 !important;
    font-weight: 600;
  }

  .block-container { padding-top: 1rem !important; }
  header[data-testid="stHeader"] { display: none; }
  .stDataFrame { font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONTROL DE ACCESO
# ─────────────────────────────────────────────

if "user" not in st.session_state or not st.session_state.get("authenticated"):
    st.error("⛔ Acceso no autorizado. Inicie sesión primero.")
    st.stop()

role = str(st.session_state.get("role", "")).lower()
if role not in ["admin", "administrador"]:
    st.error("⛔ Solo el Administrador puede acceder a este módulo.")
    st.stop()

# ─────────────────────────────────────────────
# CONEXIÓN
# ─────────────────────────────────────────────

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "conitek_system"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "sa"),
    )

# ─────────────────────────────────────────────
# CONSULTAS
# ─────────────────────────────────────────────

def load_security_stats(conn: psycopg2.extensions.connection) -> dict:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE accion = 'LOGIN')                             AS total_ingresos,
                COUNT(*) FILTER (WHERE accion = 'LOGIN'
                                   AND fecha > NOW() - INTERVAL '24h')              AS ingresos_hoy,
                COUNT(*) FILTER (WHERE accion = 'LOGIN_FAIL')                        AS intentos_fallidos,
                COUNT(DISTINCT usuario) FILTER (WHERE accion = 'LOGIN')              AS usuarios_unicos,
                COUNT(*) FILTER (WHERE accion = 'LOGOUT')                            AS total_salidas
            FROM audit_log
        """)
        return dict(cur.fetchone() or {})


def load_sessions(
    conn: psycopg2.extensions.connection,
    usuario_fil: str = None,
    fecha_desde=None,
    fecha_hasta=None,
    limite: int = 300,
) -> pd.DataFrame:
    """
    Construye una vista de sesiones emparejando eventos LOGIN con su
    LOGOUT correspondiente y listando todos los módulos visitados entre ambos.
    """
    params = []
    extra = ""

    if usuario_fil:
        extra += " AND LOWER(le.usuario) LIKE %s"
        params.append(f"%{usuario_fil.lower()}%")

    if fecha_desde:
        extra += " AND le.fecha >= %s"
        params.append(fecha_desde)

    if fecha_hasta:
        extra += " AND le.fecha < %s"
        params.append(fecha_hasta + timedelta(days=1))

    params.append(limite)

    query = f"""
        SELECT
            le.id                                                           AS id,
            le.fecha                                                        AS hora_ingreso,
            le.usuario,
            CASE
                WHEN le.detalle LIKE '%%Rol:%%'
                THEN TRIM(SPLIT_PART(le.detalle, 'Rol:', 2))
                ELSE 'N/D'
            END                                                             AS perfil,
            le.ip,
            (
                SELECT s.fecha
                FROM   audit_log s
                WHERE  s.usuario = le.usuario
                  AND  s.accion  = 'LOGOUT'
                  AND  s.fecha   > le.fecha
                ORDER  BY s.fecha ASC
                LIMIT  1
            )                                                               AS hora_salida,
            (
                SELECT STRING_AGG(d.detalle, ' → ' ORDER BY d.fecha)
                FROM   audit_log d
                WHERE  d.usuario  = le.usuario
                  AND  d.accion   = 'PAGE_VISIT'
                  AND  d.fecha    > le.fecha
                  AND  d.fecha    < COALESCE(
                           (SELECT s2.fecha FROM audit_log s2
                            WHERE  s2.usuario = le.usuario
                              AND  s2.accion  = 'LOGOUT'
                              AND  s2.fecha   > le.fecha
                            ORDER  BY s2.fecha ASC LIMIT 1),
                           NOW()
                       )
            )                                                               AS modulos_visitados
        FROM   audit_log le
        WHERE  le.accion = 'LOGIN'
          {extra}
        ORDER  BY le.fecha DESC
        LIMIT  %s
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(
        columns=["id", "hora_ingreso", "usuario", "perfil", "ip",
                 "hora_salida", "modulos_visitados"]
    )


def load_failed_logins(conn, fecha_desde=None, fecha_hasta=None, limite=100) -> pd.DataFrame:
    params = []
    extra = ""
    if fecha_desde:
        extra += " AND fecha >= %s"
        params.append(fecha_desde)
    if fecha_hasta:
        extra += " AND fecha < %s"
        params.append(fecha_hasta + timedelta(days=1))
    params.append(limite)

    query = f"""
        SELECT
            fecha,
            usuario,
            detalle,
            ip
        FROM audit_log
        WHERE accion = 'LOGIN_FAIL'
          {extra}
        ORDER BY fecha DESC
        LIMIT %s
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["fecha", "usuario", "detalle", "ip"]
    )

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

def _calc_duration(row) -> str:
    try:
        hora_salida = row["hora_salida"]
        hora_ingreso = row["hora_ingreso"]
        if hora_salida is None or pd.isna(hora_salida):
            return "🟢 En sesión"
        delta = pd.to_datetime(hora_salida) - pd.to_datetime(hora_ingreso)
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "-"
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m:02d}m"
        elif m > 0:
            return f"{m}m {s:02d}s"
        return f"{s}s"
    except Exception:
        return "-"


def _fmt_datetime(ts, fmt: str) -> str:
    try:
        if ts is None or (hasattr(ts, '__class__') and ts.__class__.__name__ == 'NaTType'):
            return "—"
        return pd.to_datetime(ts).strftime(fmt)
    except Exception:
        return "—"

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    st.markdown("""
    <div class="sec-header">
      🔒
      <div>
        <h2>Bitácora de Seguridad</h2>
        <span>Historial de accesos, sesiones y módulos visitados por cada usuario</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        conn = get_connection()
        conn.isolation_level  # ping para verificar conexión activa
    except Exception:
        try:
            # Reconectar si la conexión caducó
            get_connection.clear()
            conn = get_connection()
        except Exception as e:
            st.error(f"❌ Error de conexión a la base de datos: {e}")
            st.stop()

    # ── Métricas ────────────────────────────────────────────────────────────
    stats = load_security_stats(conn)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="sec-metric">
          <div class="met-label">🔐 Total Ingresos</div>
          <div class="met-value">{stats.get('total_ingresos', 0):,}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="sec-metric">
          <div class="met-label">⚡ Ingresos Hoy</div>
          <div class="met-value">{stats.get('ingresos_hoy', 0):,}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="sec-metric">
          <div class="met-label">🚫 Intentos Fallidos</div>
          <div class="met-value met-fail">{stats.get('intentos_fallidos', 0):,}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="sec-metric">
          <div class="met-label">👥 Usuarios Únicos</div>
          <div class="met-value">{stats.get('usuarios_unicos', 0):,}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ── Filtros ─────────────────────────────────────────────────────────────
    with st.expander("🔧 Filtros de búsqueda", expanded=True):
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            usuario_fil = st.text_input("👤 Buscar por usuario", placeholder="Nombre de usuario...")
        with col2:
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
        with col3:
            fecha_hasta = st.date_input("Hasta", value=date.today())
        with col4:
            limite = st.selectbox("Máx. registros", [50, 100, 200, 500], index=1)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabla de sesiones ────────────────────────────────────────────────────
    st.subheader("📋 Historial de Sesiones")

    with st.spinner("Cargando historial..."):
        df = load_sessions(
            conn,
            usuario_fil=usuario_fil.strip() or None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=limite,
        )

    if df.empty:
        st.info("ℹ️ No se encontraron sesiones con los filtros aplicados.")
    else:
        df["Fecha"]          = df["hora_ingreso"].apply(lambda x: _fmt_datetime(x, "%d/%m/%Y"))
        df["Hora Entrada"]   = df["hora_ingreso"].apply(lambda x: _fmt_datetime(x, "%H:%M:%S"))
        df["Hora Salida"]    = df["hora_salida"].apply(lambda x: _fmt_datetime(x, "%H:%M:%S") if pd.notna(x) else "🟢 En sesión")
        df["Duración"]       = df.apply(_calc_duration, axis=1)
        df["Módulos Visitados"] = df["modulos_visitados"].fillna("(sin registros)")

        display = df.rename(columns={
            "usuario": "Usuario",
            "perfil":  "Perfil / Rol",
        })[["Usuario", "Perfil / Rol", "Fecha", "Hora Entrada", "Hora Salida",
            "Duración", "Módulos Visitados"]]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Módulos Visitados": st.column_config.TextColumn(width="large"),
                "Usuario":           st.column_config.TextColumn(width="small"),
                "Perfil / Rol":      st.column_config.TextColumn(width="small"),
                "Duración":          st.column_config.TextColumn(width="small"),
            }
        )
        st.caption(f"Mostrando {len(display)} sesión(es) · ordenadas de más reciente a más antigua.")

    # ── Intentos fallidos ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🚫 Intentos de Ingreso Fallidos")

    with st.spinner("Cargando intentos fallidos..."):
        df_fail = load_failed_logins(conn, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)

    if df_fail.empty:
        st.success("✅ No se registraron intentos fallidos en el período seleccionado.")
    else:
        df_fail["Fecha"]    = df_fail["fecha"].apply(lambda x: _fmt_datetime(x, "%d/%m/%Y"))
        df_fail["Hora"]     = df_fail["fecha"].apply(lambda x: _fmt_datetime(x, "%H:%M:%S"))
        df_fail_display = df_fail.rename(columns={
            "usuario": "Usuario",
            "detalle": "Detalle",
        })[["Fecha", "Hora", "Usuario", "Detalle"]]

        st.dataframe(df_fail_display, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_fail_display)} intento(s) fallido(s) en el período seleccionado.")


main()
