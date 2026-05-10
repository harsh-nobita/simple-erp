from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.crm import bp
from app.crm.crm_models import Lead, Ticket, Note, Quotation
from app.crm.crm_forms import LeadForm, TicketForm, NoteForm, QuotationForm, FollowUpForm
from app.crm.crm_utils import generate_lead_id, create_lead_record


@bp.route('/')
@login_required
def crm_dashboard():
    leads_count = Lead.query.count()
    tickets_count = Ticket.query.count()
    quotations_count = Quotation.query.count()
    return render_template('crm_dashboard.html', leads_count=leads_count, tickets_count=tickets_count, quotations_count=quotations_count)


@bp.route('/leads', methods=['GET', 'POST'])
@login_required
def leads():
    form = LeadForm()
    if form.validate_on_submit():
        lid = generate_lead_id()
        l = Lead(lead_id=lid, name=form.name.data, email=form.email.data, phone=form.phone.data, source=form.source.data)
        db.session.add(l)
        db.session.commit()
        flash('Lead created.')
        return redirect(url_for('crm.leads'))
    lead_list = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('leads.html', leads=lead_list, form=form)


@bp.route('/tickets', methods=['GET', 'POST'])
@login_required
def tickets():
    form = TicketForm()
    form.lead_id.choices = [(0, '- None -')] + [(l.id, f"{l.lead_id} - {l.name}") for l in Lead.query.order_by(Lead.created_at.desc()).all()]
    if form.validate_on_submit():
        ticket = Ticket(ticket_id=f"TKT-{generate_lead_id()}", lead_id=form.lead_id.data if form.lead_id.data != 0 else None, subject=form.subject.data, description=form.description.data)
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket created.')
        return redirect(url_for('crm.tickets'))
    ticket_list = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=ticket_list, form=form)


@bp.route('/followups', methods=['GET', 'POST'])
@login_required
def followups():
    form = FollowUpForm()
    form.quotation_id.choices = [(q.id, f"{q.reference} - {q.amount}") for q in Quotation.query.order_by(Quotation.created_at.desc()).all()]
    if form.validate_on_submit():
        # in a fuller app we'd create a followup schedule entry; for now we flash and redirect
        flash('Follow-up scheduled.')
        return redirect(url_for('crm.followups'))
    return render_template('followups.html', form=form)


@bp.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    form = NoteForm()
    form.lead_id.choices = [(l.id, f"{l.lead_id} - {l.name}") for l in Lead.query.order_by(Lead.created_at.desc()).all()]
    if form.validate_on_submit():
        note = Note(lead_id=form.lead_id.data, content=form.content.data)
        db.session.add(note)
        db.session.commit()
        flash('Note added.')
        return redirect(url_for('crm.notes'))
    notes_list = Note.query.order_by(Note.created_at.desc()).limit(200).all()
    return render_template('notes.html', notes=notes_list, form=form)


@bp.route('/quotations', methods=['GET', 'POST'])
@login_required
def quotations():
    form = QuotationForm()
    form.lead_id.choices = [(0, '- None -')] + [(l.id, f"{l.lead_id} - {l.name}") for l in Lead.query.order_by(Lead.created_at.desc()).all()]
    if form.validate_on_submit():
        q = Quotation(lead_id=form.lead_id.data if form.lead_id.data != 0 else None, reference=form.reference.data, amount=form.amount.data)
        db.session.add(q)
        db.session.commit()
        flash('Quotation created.')
        return redirect(url_for('crm.quotations'))
    quotation_list = Quotation.query.order_by(Quotation.created_at.desc()).all()
    return render_template('quotation.html', quotations=quotation_list, form=form)
