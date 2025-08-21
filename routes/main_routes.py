"""Main web routes for the application"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Client, Intake, Agent, Artifact
from services.plan_service import generate_plan_comparison
from services.gpt_service import generate_plan_explanation, generate_soa_content
from datetime import datetime
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with client list and quick actions"""
    clients = Client.get_all()
    agent = Agent.get_default()
    return render_template('index.html', clients=clients, agent=agent)

@main_bp.route('/intake')
def intake_form():
    """Client intake form"""
    client_id = request.args.get('client_id')
    client = None
    if client_id:
        client = Client.get_by_id(client_id)
    
    return render_template('intake.html', client=client)

@main_bp.route('/intake', methods=['POST'])
def process_intake():
    """Process intake form submission"""
    try:
        # Get or create client
        client_id = request.form.get('client_id')
        if client_id:
            client = Client.get_by_id(client_id)
        else:
            agent = Agent.get_default()
            client = Client.create(
                agent_id=agent['id'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                email=request.form['email'],
                dob=request.form['dob'],
                zip_code=request.form['zip_code'],
                county=request.form['county'],
                state=request.form['state']
            )
            client_id = client['id']
        
        # Parse doctors and prescriptions
        doctors = []
        doctor_names = request.form.getlist('doctor_name[]')
        doctor_npis = request.form.getlist('doctor_npi[]')
        for name, npi in zip(doctor_names, doctor_npis):
            if name.strip():
                doctors.append({'name': name.strip(), 'npi': npi.strip()})
        
        prescriptions = []
        rx_names = request.form.getlist('prescription_name[]')
        rx_dosages = request.form.getlist('prescription_dosage[]')
        for name, dosage in zip(rx_names, rx_dosages):
            if name.strip():
                prescriptions.append({'name': name.strip(), 'dosage': dosage.strip()})
        
        # Parse ages
        ages = []
        age_inputs = request.form.getlist('age[]')
        for age in age_inputs:
            if age.strip():
                ages.append(int(age.strip()))
        
        # Create intake record
        intake_data = {
            'client_id': client_id,
            'plan_year': int(request.form['plan_year']),
            'household_size': int(request.form['household_size']),
            'ages': ages,
            'income': float(request.form['income']),
            'doctors': doctors,
            'prescriptions': prescriptions,
            'preferences': {
                'prefer_low_premium': request.form.get('prefer_low_premium') == 'on',
                'prefer_low_deductible': request.form.get('prefer_low_deductible') == 'on',
                'prefer_broad_network': request.form.get('prefer_broad_network') == 'on'
            },
            'zip_code': client['zip'],
            'county': client['county'],
            'state': client['state']
        }
        
        intake = Intake.create(**intake_data)
        
        # Store intake ID in session for results page
        session['current_intake_id'] = intake['id']
        
        flash('Intake completed successfully! Generating plan recommendations...', 'success')
        return redirect(url_for('main.results'))
        
    except Exception as e:
        flash(f'Error processing intake: {str(e)}', 'error')
        return redirect(url_for('main.intake_form'))

@main_bp.route('/results')
def results():
    """Show plan comparison results"""
    intake_id = session.get('current_intake_id')
    if not intake_id:
        flash('No intake data found. Please complete the intake form first.', 'error')
        return redirect(url_for('main.intake_form'))
    
    intake = Intake.get_by_id(intake_id)
    client = Client.get_by_id(intake['client_id'])
    
    # Generate plan comparison
    quote_result = generate_plan_comparison(intake)
    
    # Generate GPT explanation
    explanation = generate_plan_explanation(
        intake, 
        quote_result['top_3'],
        quote_result['aptc'],
        quote_result['csr_level']
    )
    
    # Store results in session for PDF generation
    session['current_explanation'] = explanation
    session['current_quote_result'] = {
        'aptc': quote_result['aptc'],
        'csr_level': quote_result['csr_level'],
        'top_3': quote_result['top_3']
    }
    
    return render_template('results.html', 
                         client=client,
                         intake=intake,
                         explanation=explanation,
                         quote_result=quote_result)

@main_bp.route('/client/<client_id>')
def client_dashboard(client_id):
    """Client dashboard showing history and artifacts"""
    client = Client.get_by_id(client_id)
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('main.index'))
    
    artifacts = Artifact.get_by_client_id(client_id)
    
    return render_template('client_dashboard.html', 
                         client=client, 
                         artifacts=artifacts)

@main_bp.route('/export-pdf')
def export_pdf():
    """Export current results as PDF"""
    from flask import make_response
    from services.pdf_service import generate_pdf_report
    
    intake_id = session.get('current_intake_id')
    explanation = session.get('current_explanation')
    quote_result = session.get('current_quote_result')
    
    if not all([intake_id, explanation, quote_result]):
        flash('No results available for export. Please complete an intake first.', 'error')
        return redirect(url_for('main.index'))
    
    intake = Intake.get_by_id(intake_id)
    client = Client.get_by_id(intake['client_id'])
    
    try:
        # Generate PDF
        pdf_bytes = generate_pdf_report(client, intake, explanation, quote_result)
        
        # Save as artifact
        Artifact.create(
            client_id=client['id'],
            artifact_type='pdf_report',
            payload={'explanation': explanation, 'quote_result': quote_result}
        )
        
        # Return PDF response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="plan_recommendations_{client["first_name"]}_{client["last_name"]}.pdf"'
        
        return response
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('main.results'))

@main_bp.route('/generate-soa')
def generate_soa():
    """Generate Statement of Advice"""
    intake_id = session.get('current_intake_id')
    quote_result = session.get('current_quote_result')
    
    if not all([intake_id, quote_result]):
        flash('No results available for SOA generation.', 'error')
        return redirect(url_for('main.index'))
    
    intake = Intake.get_by_id(intake_id)
    client = Client.get_by_id(intake['client_id'])
    
    # Generate SOA content
    soa_content = generate_soa_content(intake, quote_result, client)
    
    # Save as artifact
    artifact = Artifact.create(
        client_id=client['id'],
        artifact_type='soa',
        payload=soa_content
    )
    
    flash('Statement of Advice generated successfully!', 'success')
    return redirect(url_for('main.client_dashboard', client_id=client['id']))
