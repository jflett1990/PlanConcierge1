"""
Compliance Engine - Automated compliance checking and monitoring
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import os
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

from models import (ComplianceRule, ComplianceCheck, ComplianceAlert, 
                   Client, Intake, Artifact)

class ComplianceEngine:
    """Main engine for compliance checking and monitoring"""
    
    def __init__(self):
        self.rules_loaded = False
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default ACA/Medicare compliance rules"""
        if self.rules_loaded:
            return
            
        default_rules = [
            {
                'name': 'Summary of Benefits Required',
                'description': 'All plan recommendations must include Summary of Benefits and Coverage (SBC)',
                'category': 'documentation',
                'regulation_source': 'ACA',
                'severity': 'critical',
                'auto_check': True,
                'check_logic': {
                    'type': 'artifact_required',
                    'artifact_type': 'sbc',
                    'trigger': 'plan_recommendation'
                }
            },
            {
                'name': 'Income Verification Documentation',
                'description': 'APTC eligibility requires income verification within acceptable ranges',
                'category': 'documentation', 
                'regulation_source': 'ACA',
                'severity': 'high',
                'auto_check': True,
                'check_logic': {
                    'type': 'income_verification',
                    'max_aptc_percentage': 400,  # 400% FPL limit
                    'trigger': 'quote_calculation'
                }
            },
            {
                'name': 'Plan Comparison Disclosure',
                'description': 'Clients must receive disclosure about plan comparison limitations',
                'category': 'disclosure',
                'regulation_source': 'ACA',
                'severity': 'high',
                'auto_check': True,
                'check_logic': {
                    'type': 'disclosure_required',
                    'disclosure_type': 'plan_comparison',
                    'trigger': 'plan_recommendation'
                }
            },
            {
                'name': 'Network Provider Verification',
                'description': 'Provider network status must be verified before plan recommendations',
                'category': 'verification',
                'regulation_source': 'ACA',
                'severity': 'medium',
                'auto_check': True,
                'check_logic': {
                    'type': 'provider_verification',
                    'required_fields': ['doctor_hits', 'network_status'],
                    'trigger': 'plan_recommendation'
                }
            },
            {
                'name': 'Medicare Open Enrollment Deadline',
                'description': 'Medicare Annual Open Enrollment ends December 7',
                'category': 'timing',
                'regulation_source': 'Medicare',
                'severity': 'critical',
                'auto_check': True,
                'check_logic': {
                    'type': 'deadline_check',
                    'deadline_date': '2025-12-07',
                    'warning_days': 30,
                    'trigger': 'date_based'
                }
            },
            {
                'name': 'ACA Open Enrollment Deadline',
                'description': 'ACA Marketplace Open Enrollment deadline varies by state',
                'category': 'timing',
                'regulation_source': 'ACA',
                'severity': 'critical',
                'auto_check': True,
                'check_logic': {
                    'type': 'deadline_check',
                    'deadline_date': '2025-01-15',  # Federal deadline
                    'warning_days': 14,
                    'trigger': 'date_based'
                }
            },
            {
                'name': 'Agent License Verification',
                'description': 'Insurance agents must maintain valid licenses in client states',
                'category': 'licensing',
                'regulation_source': 'State',
                'severity': 'critical',
                'auto_check': False,  # Requires external verification
                'check_logic': {
                    'type': 'license_verification',
                    'check_frequency': 'monthly',
                    'trigger': 'client_interaction'
                }
            },
            {
                'name': 'Privacy Notice Acknowledgment',
                'description': 'Clients must acknowledge receipt of privacy notices',
                'category': 'disclosure',
                'regulation_source': 'HIPAA',
                'severity': 'high',
                'auto_check': True,
                'check_logic': {
                    'type': 'acknowledgment_required',
                    'document_type': 'privacy_notice',
                    'trigger': 'intake_submission'
                }
            }
        ]
        
        for rule_data in default_rules:
            existing_rules = ComplianceRule.list_all()
            rule_exists = any(r.name == rule_data['name'] for r in existing_rules)
            
            if not rule_exists:
                ComplianceRule.create(**rule_data)
        
        self.rules_loaded = True
    
    def run_compliance_check(self, client_id: int, intake_id: int) -> List[ComplianceCheck]:
        """Run all applicable compliance checks for a client/intake"""
        self._load_default_rules()
        
        checks = []
        rules = ComplianceRule.list_all()
        client = Client.get(client_id)
        intake = Intake.get(intake_id)
        
        if not client or not intake:
            return checks
        
        for rule in rules:
            if rule.auto_check:
                check_result = self._execute_rule_check(rule, client, intake)
                if check_result:
                    checks.append(check_result)
        
        return checks
    
    def _execute_rule_check(self, rule: ComplianceRule, client: Client, intake: Intake) -> Optional[ComplianceCheck]:
        """Execute a specific compliance rule check"""
        check_logic = rule.check_logic
        check_type = check_logic.get('type')
        
        try:
            if check_type == 'artifact_required':
                return self._check_artifact_required(rule, client, intake, check_logic)
            elif check_type == 'income_verification':
                return self._check_income_verification(rule, client, intake, check_logic)
            elif check_type == 'disclosure_required':
                return self._check_disclosure_required(rule, client, intake, check_logic)
            elif check_type == 'provider_verification':
                return self._check_provider_verification(rule, client, intake, check_logic)
            elif check_type == 'acknowledgment_required':
                return self._check_acknowledgment_required(rule, client, intake, check_logic)
            else:
                # Unknown check type
                return ComplianceCheck.create(
                    rule.id, client.id, intake.id, 'warning',
                    {'message': f'Unknown check type: {check_type}'}
                )
        except Exception as e:
            # Error in check execution
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'warning',
                {'message': f'Check execution error: {str(e)}'}
            )
    
    def _check_artifact_required(self, rule: ComplianceRule, client: Client, intake: Intake, logic: Dict) -> Optional[ComplianceCheck]:
        """Check if required artifacts are present"""
        required_type = logic.get('artifact_type')
        artifacts = Artifact.list_by_client(client.id)
        
        has_required = any(a.type == required_type for a in artifacts)
        
        if has_required:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'compliant',
                {'message': f'Required {required_type} artifact found'}
            )
        else:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'non_compliant',
                {'message': f'Missing required {required_type} artifact', 'required_type': required_type}
            )
    
    def _check_income_verification(self, rule: ComplianceRule, client: Client, intake: Intake, logic: Dict) -> Optional[ComplianceCheck]:
        """Check income verification for APTC eligibility"""
        max_percentage = logic.get('max_aptc_percentage', 400)
        
        # Basic income range check (would integrate with FPL calculations)
        if intake.income <= 0:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'non_compliant',
                {'message': 'Invalid income amount', 'income': intake.income}
            )
        
        # For a family of 2, approximate 400% FPL is around $70k (simplified)
        estimated_400_fpl = 70000 * (intake.household_size / 2)
        
        if intake.income > estimated_400_fpl:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'warning',
                {'message': f'Income may exceed {max_percentage}% FPL limit', 'income': intake.income}
            )
        else:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'compliant',
                {'message': 'Income within acceptable range', 'income': intake.income}
            )
    
    def _check_disclosure_required(self, rule: ComplianceRule, client: Client, intake: Intake, logic: Dict) -> Optional[ComplianceCheck]:
        """Check if required disclosures are present"""
        disclosure_type = logic.get('disclosure_type')
        
        # Check if disclosure artifact exists
        artifacts = Artifact.list_by_client(client.id)
        has_disclosure = any(
            a.type == 'disclosure' and 
            a.payload and 
            a.payload.get('disclosure_type') == disclosure_type 
            for a in artifacts
        )
        
        if has_disclosure:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'compliant',
                {'message': f'{disclosure_type} disclosure provided'}
            )
        else:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'non_compliant',
                {'message': f'Missing {disclosure_type} disclosure', 'disclosure_type': disclosure_type}
            )
    
    def _check_provider_verification(self, rule: ComplianceRule, client: Client, intake: Intake, logic: Dict) -> Optional[ComplianceCheck]:
        """Check provider network verification"""
        required_fields = logic.get('required_fields', [])
        
        # Check if client has specified doctors
        if not intake.doctors or len(intake.doctors) == 0:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'compliant',
                {'message': 'No provider verification needed (no doctors specified)'}
            )
        
        # In a full implementation, this would check if doctor network verification was performed
        # For now, we'll check if plan_fits have doctor_hits data
        from models import PlanFit
        
        # Look for plan fits associated with this intake (would need quote_result_id)
        plan_fits = PlanFit.list_all()
        intake_fits = [pf for pf in plan_fits if pf.quote_result_id]  # Simplified check
        
        if intake_fits:
            has_verification = any(pf.doctor_hits for pf in intake_fits)
            if has_verification:
                return ComplianceCheck.create(
                    rule.id, client.id, intake.id, 'compliant',
                    {'message': 'Provider network verification completed'}
                )
            else:
                return ComplianceCheck.create(
                    rule.id, client.id, intake.id, 'warning',
                    {'message': 'Provider network verification may be incomplete'}
                )
        else:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'pending',
                {'message': 'Provider verification pending plan selection'}
            )
    
    def _check_acknowledgment_required(self, rule: ComplianceRule, client: Client, intake: Intake, logic: Dict) -> Optional[ComplianceCheck]:
        """Check if required acknowledgments are present"""
        document_type = logic.get('document_type')
        
        # Check for acknowledgment artifact
        artifacts = Artifact.list_by_client(client.id)
        has_acknowledgment = any(
            a.type == 'acknowledgment' and 
            a.payload and 
            a.payload.get('document_type') == document_type 
            for a in artifacts
        )
        
        if has_acknowledgment:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'compliant',
                {'message': f'{document_type} acknowledgment received'}
            )
        else:
            return ComplianceCheck.create(
                rule.id, client.id, intake.id, 'non_compliant',
                {'message': f'Missing {document_type} acknowledgment', 'document_type': document_type}
            )
    
    def check_deadlines(self) -> List[ComplianceAlert]:
        """Check for upcoming compliance deadlines"""
        alerts = []
        rules = ComplianceRule.list_all()
        current_date = datetime.now()
        
        for rule in rules:
            if rule.check_logic.get('type') == 'deadline_check':
                deadline_str = rule.check_logic.get('deadline_date')
                warning_days = rule.check_logic.get('warning_days', 30)
                
                if deadline_str:
                    try:
                        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d')
                        warning_date = deadline_date - timedelta(days=warning_days)
                        
                        if current_date >= warning_date and current_date <= deadline_date:
                            days_remaining = (deadline_date - current_date).days
                            
                            priority = 'urgent' if days_remaining <= 7 else 'high'
                            
                            alert = ComplianceAlert.create(
                                rule.id, 0,  # 0 for system-wide alerts
                                'deadline',
                                f'{rule.name}: {days_remaining} days remaining',
                                deadline_str,
                                priority
                            )
                            alerts.append(alert)
                    except ValueError:
                        continue
        
        return alerts
    
    def get_compliance_summary(self, client_id: Optional[int] = None) -> Dict[str, Any]:
        """Get compliance summary dashboard data"""
        checks = ComplianceCheck.list_all()
        alerts = ComplianceAlert.list_active()
        
        if client_id:
            checks = [c for c in checks if c.client_id == client_id]
            alerts = [a for a in alerts if a.client_id == client_id]
        
        # Count checks by status
        status_counts = {
            'compliant': len([c for c in checks if c.status == 'compliant']),
            'non_compliant': len([c for c in checks if c.status == 'non_compliant']),
            'warning': len([c for c in checks if c.status == 'warning']),
            'pending': len([c for c in checks if c.status == 'pending'])
        }
        
        # Count alerts by priority
        alert_counts = {
            'urgent': len([a for a in alerts if a.priority == 'urgent']),
            'high': len([a for a in alerts if a.priority == 'high']),
            'medium': len([a for a in alerts if a.priority == 'medium']),
            'low': len([a for a in alerts if a.priority == 'low'])
        }
        
        # Recent activity
        recent_checks = sorted(checks, key=lambda x: x.checked_at, reverse=True)[:10]
        recent_alerts = sorted(alerts, key=lambda x: x.created_at, reverse=True)[:10]
        
        return {
            'status_counts': status_counts,
            'alert_counts': alert_counts,
            'total_checks': len(checks),
            'total_active_alerts': len(alerts),
            'compliance_percentage': round(
                (status_counts['compliant'] / max(len(checks), 1)) * 100, 1
            ),
            'recent_checks': [
                {
                    'id': c.id,
                    'rule_name': ComplianceRule.get(c.rule_id).name if ComplianceRule.get(c.rule_id) else 'Unknown',
                    'client_id': c.client_id,
                    'status': c.status,
                    'checked_at': c.checked_at
                } for c in recent_checks
            ],
            'recent_alerts': [
                {
                    'id': a.id,
                    'rule_name': ComplianceRule.get(a.rule_id).name if ComplianceRule.get(a.rule_id) else 'Unknown',
                    'message': a.message,
                    'priority': a.priority,
                    'due_date': a.due_date
                } for a in recent_alerts
            ]
        }

# Global compliance engine instance
compliance_engine = ComplianceEngine()