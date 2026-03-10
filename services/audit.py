import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
_init_done = False

def _get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "conitek_system"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "sa"),
    )

def _ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                usuario VARCHAR(100),
                accion VARCHAR(20),
                tabla VARCHAR(60),
                registro_id VARCHAR(60),
                detalle TEXT,
                ip VARCHAR(45)
            );
            CREATE INDEX IF NOT EXISTS idx_audit_fecha ON audit_log(fecha DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_accion ON audit_log(accion);
            CREATE INDEX IF NOT EXISTS idx_audit_tabla ON audit_log(tabla);
            CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_log(usuario);
        """)
        conn.commit()

def log_event(usuario, accion, tabla, registro_id=None, detalle="", ip=None):
    global _init_done
    try:
        conn = _get_conn()
        if not _init_done:
            _ensure_table(conn)
            _init_done = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log (usuario, accion, tabla, registro_id, detalle, ip) VALUES (%s,%s,%s,%s,%s,%s)",
                (str(usuario) if usuario is not None else None, str(accion).upper(), str(tabla), str(registro_id) if registro_id is not None else None, detalle, ip)
            )
            conn.commit()
        conn.close()
    except Exception:
        pass
