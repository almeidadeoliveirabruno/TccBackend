import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import engine
from sqlalchemy.orm import Session
from services.dashboard_service import dentists_billing, appointments_count_by_period
from services.home_service import (
    last_patients,
    appointments_today,
    expenses_not_paid,
    total_active_dentists,
    pending_appointments,
    get_next_appointments_by_dentist,
    procedures_category_distribution,
)
from services.patient_service import get_statistics_patients

with Session(engine) as db:
    clinic_id = "test-clinic-id"
    print("Testing get_statistics_patients...")
    get_statistics_patients(db, clinic_id)
    print("Testing dentists_billing...")
    dentists_billing(db, clinic_id)
    print("Testing appointments_count_by_period...")
    appointments_count_by_period(db, clinic_id, "month")
    print("Testing home service functions...")
    last_patients(db, clinic_id)
    appointments_today(db, clinic_id)
    expenses_not_paid(db, clinic_id)
    total_active_dentists(db, clinic_id)
    procedures_category_distribution(db, clinic_id)
    print("ALL QUERIES AND SERVICES RUN CLEANLY ON NEON POSTGRESQL!")
