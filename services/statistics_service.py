from sqlalchemy.orm import Session
from sqlalchemy import func
from models.participant import Participant
from models.paper import Paper, Evaluation
from models.event import Event
from models.event_registration import EventRegistration
from models.payment import Payment
import pandas as pd

class StatisticsService:
    @staticmethod
    def get_participant_stats(db: Session):
        participants = db.query(Participant).all()
        if not participants:
            return None
        
        df = pd.DataFrame([{
            "p_type": p.p_type,
            "modality": p.modality,
            "university": p.university
        } for p in participants])
        
        stats = {
            "total": len(df),
            "by_type": df["p_type"].value_counts().to_dict(),
            "by_modality": df["modality"].value_counts().to_dict(),
            "top_university": df["university"].mode().iloc[0] if not df["university"].mode().empty else "N/A"
        }
        return stats

    @staticmethod
    def get_paper_stats(db: Session):
        papers = db.query(Paper).all()
        if not papers:
            return None
            
        df_papers = pd.DataFrame([{
            "status": p.status,
            "id": p.id
        } for p in papers])
        
        evaluations = db.query(Evaluation).all()
        avg_score = 0
        max_score = 0
        min_score = 0
        
        if evaluations:
            scores = [e.score for e in evaluations]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
        stats = {
            "total": len(df_papers),
            "by_status": df_papers["status"].value_counts().to_dict(),
            "avg_score": round(avg_score, 2),
            "max_score": max_score,
            "min_score": min_score
        }
        return stats

    @staticmethod
    def get_event_stats(db: Session):
        events = db.query(Event).filter(Event.is_active == True).all()
        if not events:
            return None
            
        df = pd.DataFrame([{
            "capacity": e.capacity,
            "current_count": e.current_count or 0,
            "name": e.name
        } for e in events])
        
        stats = {
            "total": len(df),
            "total_capacity": int(df["capacity"].sum()),
            "total_occupied": int(df["current_count"].sum()),
            "avg_capacity": round(df["capacity"].mean(), 2),
            "most_occupied": df.loc[df["current_count"].idxmax()]["name"] if not df.empty else "N/A",
            "least_occupied": df.loc[df["current_count"].idxmin()]["name"] if not df.empty else "N/A"
        }
        return stats

    @staticmethod
    def get_registration_stats(db: Session):
        registrations = db.query(EventRegistration).all()
        payments = db.query(Payment).filter(Payment.status == "Aprobado").all()
        
        if not registrations and not payments:
            return None
            
        df_reg = pd.DataFrame([{"status": r.status} for r in registrations]) if registrations else pd.DataFrame()
        df_pay = pd.DataFrame([{"amount": p.amount} for p in payments]) if payments else pd.DataFrame()
        
        stats = {
            "total_registrations": len(df_reg),
            "total_collected": float(df_pay["amount"].sum()) if not df_pay.empty else 0.0,
            "avg_payment": float(df_pay["amount"].mean()) if not df_pay.empty else 0.0,
            "max_payment": float(df_pay["amount"].max()) if not df_pay.empty else 0.0,
            "min_payment": float(df_pay["amount"].min()) if not df_pay.empty else 0.0,
            "by_status": df_reg["status"].value_counts().to_dict() if not df_reg.empty else {}
        }
        return stats
