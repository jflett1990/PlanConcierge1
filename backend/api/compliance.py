"""
Compliance API endpoints for automated tracking dashboard
"""

from flask_restx import Namespace, Resource, fields
from flask import request
import sys
import os
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

from models import ComplianceRule, ComplianceCheck, ComplianceAlert, Client, Intake
from compliance.engine import compliance_engine

api = Namespace('compliance', description='Compliance tracking and monitoring')

# Response models
compliance_rule_model = api.model('ComplianceRule', {
    'id': fields.Integer(required=True, description='Rule ID'),
    'name': fields.String(required=True, description='Rule name'),
    'description': fields.String(required=True, description='Rule description'),
    'category': fields.String(required=True, description='Rule category'),
    'regulation_source': fields.String(required=True, description='Regulation source'),
    'severity': fields.String(required=True, description='Severity level'),
    'auto_check': fields.Boolean(required=True, description='Auto-checkable'),
    'created_at': fields.String(required=True, description='Creation timestamp')
})

compliance_check_model = api.model('ComplianceCheck', {
    'id': fields.Integer(required=True, description='Check ID'),
    'rule_id': fields.Integer(required=True, description='Associated rule ID'),
    'client_id': fields.Integer(required=True, description='Client ID'),
    'intake_id': fields.Integer(required=True, description='Intake ID'),
    'status': fields.String(required=True, description='Check status'),
    'details': fields.Raw(required=True, description='Check details'),
    'checked_at': fields.String(required=True, description='Check timestamp'),
    'resolved_at': fields.String(description='Resolution timestamp')
})

compliance_alert_model = api.model('ComplianceAlert', {
    'id': fields.Integer(required=True, description='Alert ID'),
    'rule_id': fields.Integer(required=True, description='Associated rule ID'),
    'client_id': fields.Integer(required=True, description='Client ID'),
    'alert_type': fields.String(required=True, description='Alert type'),
    'message': fields.String(required=True, description='Alert message'),
    'due_date': fields.String(required=True, description='Due date'),
    'priority': fields.String(required=True, description='Priority level'),
    'status': fields.String(required=True, description='Alert status'),
    'created_at': fields.String(required=True, description='Creation timestamp')
})

dashboard_summary_model = api.model('DashboardSummary', {
    'status_counts': fields.Raw(required=True, description='Status count breakdown'),
    'alert_counts': fields.Raw(required=True, description='Alert count breakdown'),
    'total_checks': fields.Integer(required=True, description='Total checks'),
    'total_active_alerts': fields.Integer(required=True, description='Active alerts'),
    'compliance_percentage': fields.Float(required=True, description='Compliance percentage'),
    'recent_checks': fields.List(fields.Raw, description='Recent checks'),
    'recent_alerts': fields.List(fields.Raw, description='Recent alerts')
})

@api.route('/dashboard')
class ComplianceDashboard(Resource):
    @api.doc('get_compliance_dashboard')
    def get(self):
        """Get compliance dashboard summary"""
        try:
            client_id = request.args.get('client_id', type=int)
            summary = compliance_engine.get_compliance_summary(client_id)
            
            return {
                'success': True,
                'data': summary
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/rules')
class ComplianceRules(Resource):
    @api.doc('list_compliance_rules')
    def get(self):
        """List all compliance rules"""
        try:
            category = request.args.get('category')
            
            if category:
                rules = ComplianceRule.list_by_category(category)
            else:
                rules = ComplianceRule.list_all()
            
            return {
                'success': True,
                'data': [
                    {
                        'id': rule.id,
                        'name': rule.name,
                        'description': rule.description,
                        'category': rule.category,
                        'regulation_source': rule.regulation_source,
                        'severity': rule.severity,
                        'auto_check': rule.auto_check,
                        'created_at': rule.created_at
                    } for rule in rules
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/checks')
class ComplianceChecks(Resource):
    @api.doc('list_compliance_checks')
    def get(self):
        """List compliance checks"""
        try:
            client_id = request.args.get('client_id', type=int)
            status = request.args.get('status')
            
            if client_id:
                checks = ComplianceCheck.list_by_client(client_id)
            elif status:
                checks = ComplianceCheck.list_by_status(status)
            else:
                checks = ComplianceCheck.list_all()
            
            return {
                'success': True,
                'data': [
                    {
                        'id': check.id,
                        'rule_id': check.rule_id,
                        'client_id': check.client_id,
                        'intake_id': check.intake_id,
                        'status': check.status,
                        'details': check.details,
                        'checked_at': check.checked_at,
                        'resolved_at': check.resolved_at
                    } for check in checks
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/checks/run')
class RunComplianceChecks(Resource):
    @api.doc('run_compliance_checks')
    def post(self):
        """Run compliance checks for a client/intake"""
        try:
            data = request.get_json()
            client_id = data.get('client_id')
            intake_id = data.get('intake_id')
            
            if not client_id or not intake_id:
                return {
                    'success': False,
                    'error': 'client_id and intake_id are required'
                }, 400
            
            # Verify client and intake exist
            client = Client.get(client_id)
            intake = Intake.get(intake_id)
            
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found'
                }, 404
            
            if not intake:
                return {
                    'success': False,
                    'error': 'Intake not found'
                }, 404
            
            # Run compliance checks
            checks = compliance_engine.run_compliance_check(client_id, intake_id)
            
            return {
                'success': True,
                'data': {
                    'checks_performed': len(checks),
                    'checks': [
                        {
                            'id': check.id,
                            'rule_id': check.rule_id,
                            'status': check.status,
                            'details': check.details
                        } for check in checks
                    ]
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/alerts')
class ComplianceAlerts(Resource):
    @api.doc('list_compliance_alerts')
    def get(self):
        """List compliance alerts"""
        try:
            priority = request.args.get('priority')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            
            if active_only:
                alerts = ComplianceAlert.list_active()
            else:
                alerts = ComplianceAlert.list_all()
            
            if priority:
                alerts = [a for a in alerts if a.priority == priority]
            
            return {
                'success': True,
                'data': [
                    {
                        'id': alert.id,
                        'rule_id': alert.rule_id,
                        'client_id': alert.client_id,
                        'alert_type': alert.alert_type,
                        'message': alert.message,
                        'due_date': alert.due_date,
                        'priority': alert.priority,
                        'status': alert.status,
                        'created_at': alert.created_at
                    } for alert in alerts
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/alerts/<int:alert_id>/acknowledge')
class AcknowledgeAlert(Resource):
    @api.doc('acknowledge_alert')
    def post(self, alert_id):
        """Acknowledge a compliance alert"""
        try:
            alert = ComplianceAlert.get(alert_id)
            if not alert:
                return {
                    'success': False,
                    'error': 'Alert not found'
                }, 404
            
            alert.acknowledge()
            
            return {
                'success': True,
                'data': {
                    'id': alert.id,
                    'status': alert.status,
                    'acknowledged_at': alert.acknowledged_at
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/alerts/<int:alert_id>/resolve')
class ResolveAlert(Resource):
    @api.doc('resolve_alert')
    def post(self, alert_id):
        """Resolve a compliance alert"""
        try:
            alert = ComplianceAlert.get(alert_id)
            if not alert:
                return {
                    'success': False,
                    'error': 'Alert not found'
                }, 404
            
            alert.resolve()
            
            return {
                'success': True,
                'data': {
                    'id': alert.id,
                    'status': alert.status
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/deadlines/check')
class CheckDeadlines(Resource):
    @api.doc('check_deadlines')
    def post(self):
        """Check for upcoming compliance deadlines"""
        try:
            alerts = compliance_engine.check_deadlines()
            
            return {
                'success': True,
                'data': {
                    'new_alerts': len(alerts),
                    'alerts': [
                        {
                            'id': alert.id,
                            'message': alert.message,
                            'due_date': alert.due_date,
                            'priority': alert.priority
                        } for alert in alerts
                    ]
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/checks/<int:check_id>/resolve')
class ResolveCheck(Resource):
    @api.doc('resolve_check')
    def post(self, check_id):
        """Resolve a compliance check"""
        try:
            check = ComplianceCheck.get(check_id)
            if not check:
                return {
                    'success': False,
                    'error': 'Check not found'
                }, 404
            
            check.resolve()
            
            return {
                'success': True,
                'data': {
                    'id': check.id,
                    'status': check.status,
                    'resolved_at': check.resolved_at
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500