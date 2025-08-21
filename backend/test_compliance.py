#!/usr/bin/env python3
"""
Test compliance tracking dashboard functionality
"""

import sys
import os
sys.path.insert(0, '.')
import requests
import json

def test_compliance_dashboard():
    """Test complete compliance tracking system"""
    
    print("🎯 Testing Compliance Tracking Dashboard")
    print("=" * 50)
    
    try:
        # Setup test data
        from models import Agent, Client, _storage
        from compliance.engine import compliance_engine
        
        # Clear storage
        for key in _storage:
            _storage[key].clear()
        
        # Create test client
        agent = Agent.create("Compliance Test Agent", "test@compliance.gov", "Compliance Health", "")
        client = Client.create(agent.id, "John", "Doe", "john@compliance.gov", 
                              "1980-01-01", "10001", "New York", "NY")
        
        print(f"1. Setup test client: {client.first_name} {client.last_name}")
        
        # Create test intake through API
        intake_data = {
            'client_id': client.id,
            'plan_year': 2025,
            'household_size': 1,
            'ages': [44],
            'income': 55000.0,
            'doctors': [{'npi': '1234567890', 'name': 'Dr. Compliance', 'specialty': 'Internal Medicine'}],
            'prescriptions': [{'rxcui': '198440', 'name': 'Metformin', 'dosage': '500mg', 'frequency': 'Daily'}],
            'prefs': {'max_premium': 300.0}
        }
        
        response = requests.post('http://localhost:5000/api/intake', json=intake_data, timeout=10)
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                intake_id = result['data']['id']
                print(f"   ✅ Test intake created: ID {intake_id}")
            else:
                print(f"   ❌ Intake failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Intake API failed: HTTP {response.status_code}")
            return False
        
        # Test 1: Get compliance dashboard summary
        print("2. Testing compliance dashboard summary...")
        response = requests.get('http://localhost:5000/api/compliance/dashboard', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                summary = result['data']
                print(f"   ✅ Dashboard loaded")
                print(f"   ✅ Compliance percentage: {summary.get('compliance_percentage', 0)}%")
                print(f"   ✅ Total checks: {summary.get('total_checks', 0)}")
                print(f"   ✅ Active alerts: {summary.get('total_active_alerts', 0)}")
            else:
                print(f"   ❌ Dashboard failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Dashboard API failed: HTTP {response.status_code}")
            return False
        
        # Test 2: List compliance rules
        print("3. Testing compliance rules...")
        response = requests.get('http://localhost:5000/api/compliance/rules', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                rules = result['data']
                print(f"   ✅ Rules loaded: {len(rules)} rules")
                
                # Show sample rules
                for i, rule in enumerate(rules[:3], 1):
                    print(f"      {i}. {rule['name']} ({rule['category']}, {rule['severity']})")
            else:
                print(f"   ❌ Rules failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Rules API failed: HTTP {response.status_code}")
            return False
        
        # Test 3: Run compliance checks
        print("4. Running compliance checks...")
        check_data = {
            'client_id': client.id,
            'intake_id': intake_id
        }
        
        response = requests.post('http://localhost:5000/api/compliance/checks/run', 
                               json=check_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                check_data = result['data']
                checks_performed = check_data.get('checks_performed', 0)
                print(f"   ✅ Compliance checks completed: {checks_performed} checks")
                
                # Show sample check results
                checks = check_data.get('checks', [])
                for i, check in enumerate(checks[:3], 1):
                    status = check['status']
                    print(f"      {i}. Check ID {check['id']}: {status}")
            else:
                print(f"   ❌ Checks failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Checks API failed: HTTP {response.status_code}")
            return False
        
        # Test 4: Check for alerts
        print("5. Testing compliance alerts...")
        response = requests.get('http://localhost:5000/api/compliance/alerts', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                alerts = result['data']
                print(f"   ✅ Alerts loaded: {len(alerts)} alerts")
                
                # Show active alerts
                active_alerts = [a for a in alerts if a['status'] == 'active']
                for i, alert in enumerate(active_alerts[:2], 1):
                    print(f"      {i}. {alert['message']} (Priority: {alert['priority']})")
            else:
                print(f"   ❌ Alerts failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Alerts API failed: HTTP {response.status_code}")
            return False
        
        # Test 5: Check deadline monitoring
        print("6. Testing deadline monitoring...")
        response = requests.post('http://localhost:5000/api/compliance/deadlines/check', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                deadline_data = result['data']
                new_alerts = deadline_data.get('new_alerts', 0)
                print(f"   ✅ Deadline check completed: {new_alerts} new alerts")
                
                alerts = deadline_data.get('alerts', [])
                for alert in alerts[:2]:
                    print(f"      • {alert['message']} (Due: {alert['due_date']})")
            else:
                print(f"   ❌ Deadline check failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Deadline API failed: HTTP {response.status_code}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 COMPLIANCE DASHBOARD TEST COMPLETE")
        print("✅ Dashboard summary with compliance metrics")
        print("✅ Automated compliance rule loading and checking")
        print("✅ Real-time alert generation and monitoring")
        print("✅ Deadline tracking for ACA/Medicare compliance")
        print("✅ Complete API functionality for frontend integration")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Compliance test failed: {str(e)[:200]}...")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_compliance_dashboard()
    
    if success:
        print("\n🎯 Compliance tracking dashboard test passed!")
        print("Ready for integration with frontend dashboard.")
        sys.exit(0)
    else:
        print("\n❌ Compliance dashboard test failed.")
        sys.exit(1)