import os
from sqlalchemy import create_engine, text
from config import Config

def run_sql_file(filename):
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        with open(filename, 'r', encoding='utf-8') as f:
            sql = f.read()
        # Split by semicolon to execute multiple statements
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        for stmt in statements:
            if stmt:
                try:
                    conn.execute(text(stmt))
                    print(f"Executed: {stmt[:50]}...")
                except Exception as e:
                    print(f"Error in statement: {e}")
        conn.commit()
    print(f"Finished executing {filename}")

if __name__ == "__main__":
    base_dir = Config.BASE_DIR
    files = ['schemal.sql', 'datos.sql', 'modificacionesBD.sql']
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            print(f"Running {f}...")
            run_sql_file(path)
        else:
            print(f"File {f} not found")