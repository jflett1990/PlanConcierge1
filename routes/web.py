from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import clients_store, intakes_store

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Main dashboard"""
    recent_clients = list(clients_store.values())[-5:]  # Last 5 clients
    return render_template('index.html', recent_clients=recent_clients)

@web_bp.route('/intake')
def intake():
    """Client intake form"""
    return render_template('intake.html')

@web_bp.route('/results/<quote_result_id>')
def results(quote_result_id):
    """Display quote results"""
    return render_template('results.html', quote_result_id=quote_result_id)
