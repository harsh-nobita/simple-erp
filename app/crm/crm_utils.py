import uuid
from datetime import datetime
from app.crm.crm_models import Lead
from app import db


def generate_lead_id():
    return f"LD-{uuid.uuid4().hex[:8].upper()}"


def create_lead_record(name, email=None, phone=None, source=None):
    lid = generate_lead_id()
    lead = Lead(lead_id=lid, name=name, email=email, phone=phone, source=source)
    db.session.add(lead)
    db.session.commit()
    return lead


def set_lead_status(lead, status):
    lead.status = status
    db.session.add(lead)
    db.session.commit()
    return lead
