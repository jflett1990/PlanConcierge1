import os
from flask import Flask
from flask_restx import Api
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Initialize Flask-RESTX API
api = Api(app, 
          version='1.0', 
          title='Plan Concierge API',
          description='ACA/Medicare Plan Comparison API',
          doc='/api/docs/')

# In-memory data stores (MVP - will migrate to PostgreSQL later)
clients_store = {}
intakes_store = {}
plans_store = {}
quote_results_store = {}
plan_fits_store = {}
artifacts_store = {}

# Helper functions for in-memory store
def get_next_id(store):
    return max(store.keys(), default=0) + 1

def filter_by_field(store, field, value):
    return [item for item in store.values() if getattr(item, field, None) == value]