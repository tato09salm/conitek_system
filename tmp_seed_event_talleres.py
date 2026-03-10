from services.database import SessionLocal
from models.event import Event
from datetime import date
from config import Config

def main():
    db = SessionLocal()
    try:
        name = "CONITEK 2026 - Talleres"
        dt = date(2026, 10, 17)
        ev = db.query(Event).filter(Event.name == name, Event.event_date == dt).first()
        if not ev:
            ev = Event(
                name=name,
                event_date=dt,
                location=Config.LOCATION,
                capacity=500,
                current_count=0,
                is_active=True
            )
            db.add(ev)
            db.commit()
            print("Evento insertado")
        else:
            print("Evento ya existe")
    finally:
        db.close()

if __name__ == "__main__":
    main()
