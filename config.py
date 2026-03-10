import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "conitek_system")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "sa")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
    
    # URI para SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Rutas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REPORTS_DIR = os.path.join(BASE_DIR, "reports_output")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    
    # Constantes del Congreso
    CONGRESS_NAME = "I Congreso Nacional de Innovación y Tecnología - CONITEK 2026"
    CONGRESS_DATE = "15-18 Octubre 2026"
    LOCATION = "Universidad Nacional de Trujillo"