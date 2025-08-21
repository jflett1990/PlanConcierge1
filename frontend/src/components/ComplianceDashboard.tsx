import React, { useState, useEffect } from 'react';

interface ComplianceCheck {
  id: number;
  rule_id: number;
  client_id: number;
  intake_id: number;
  status: 'compliant' | 'non_compliant' | 'warning' | 'pending';
  details: Record<string, any>;
  checked_at: string;
  resolved_at?: string;
}

interface ComplianceAlert {
  id: number;
  rule_id: number;
  client_id: number;
  alert_type: string;
  message: string;
  due_date: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
}

interface ComplianceRule {
  id: number;
  name: string;
  description: string;
  category: string;
  regulation_source: string;
  severity: string;
  auto_check: boolean;
  created_at: string;
}

interface DashboardSummary {
  status_counts: {
    compliant: number;
    non_compliant: number;
    warning: number;
    pending: number;
  };
  alert_counts: {
    urgent: number;
    high: number;
    medium: number;
    low: number;
  };
  total_checks: number;
  total_active_alerts: number;
  compliance_percentage: number;
  recent_checks: Array<{
    id: number;
    rule_name: string;
    client_id: number;
    status: string;
    checked_at: string;
  }>;
  recent_alerts: Array<{
    id: number;
    rule_name: string;
    message: string;
    priority: string;
    due_date: string;
  }>;
}

const ComplianceDashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [checks, setChecks] = useState<ComplianceCheck[]>([]);
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'rules' | 'checks' | 'alerts'>('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load dashboard summary
      const summaryResponse = await fetch('/api/compliance/dashboard');
      if (summaryResponse.ok) {
        const summaryResult = await summaryResponse.json();
        if (summaryResult.success) {
          setSummary(summaryResult.data);
        }
      }

      // Load rules
      const rulesResponse = await fetch('/api/compliance/rules');
      if (rulesResponse.ok) {
        const rulesResult = await rulesResponse.json();
        if (rulesResult.success) {
          setRules(rulesResult.data);
        }
      }

      // Load checks
      const checksResponse = await fetch('/api/compliance/checks');
      if (checksResponse.ok) {
        const checksResult = await checksResponse.json();
        if (checksResult.success) {
          setChecks(checksResult.data);
        }
      }

      // Load alerts
      const alertsResponse = await fetch('/api/compliance/alerts');
      if (alertsResponse.ok) {
        const alertsResult = await alertsResponse.json();
        if (alertsResult.success) {
          setAlerts(alertsResult.data);
        }
      }
    } catch (error) {
      console.error('Failed to load compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId: number) => {
    try {
      const response = await fetch(`/api/compliance/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh alerts
        const alertsResponse = await fetch('/api/compliance/alerts');
        if (alertsResponse.ok) {
          const alertsResult = await alertsResponse.json();
          if (alertsResult.success) {
            setAlerts(alertsResult.data);
          }
        }
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const resolveCheck = async (checkId: number) => {
    try {
      const response = await fetch(`/api/compliance/checks/${checkId}/resolve`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh checks and summary
        loadDashboardData();
      }
    } catch (error) {
      console.error('Failed to resolve check:', error);
    }
  };

  const runComplianceChecks = async () => {
    try {
      // For demo purposes, use client_id=1 and intake_id=1
      const response = await fetch('/api/compliance/checks/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_id: 1,
          intake_id: 1
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Refresh all data
          loadDashboardData();
          alert(`Compliance checks completed: ${result.data.checks_performed} checks performed`);
        }
      }
    } catch (error) {
      console.error('Failed to run compliance checks:', error);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'compliant': return 'badge bg-success';
      case 'non_compliant': return 'badge bg-danger';
      case 'warning': return 'badge bg-warning text-dark';
      case 'pending': return 'badge bg-secondary';
      default: return 'badge bg-light text-dark';
    }
  };

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'badge bg-danger';
      case 'high': return 'badge bg-warning text-dark';
      case 'medium': return 'badge bg-info';
      case 'low': return 'badge bg-secondary';
      default: return 'badge bg-light text-dark';
    }
  };

  if (loading) {
    return (
      <div className="container mt-4">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Loading compliance dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid mt-4">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h1 className="h3">Compliance Tracking Dashboard</h1>
            <div>
              <button 
                className="btn btn-primary me-2"
                onClick={runComplianceChecks}
              >
                Run Compliance Checks
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={loadDashboardData}
              >
                Refresh
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <ul className="nav nav-tabs mb-4">
            <li className="nav-item">
              <button 
                className={`nav-link ${selectedTab === 'overview' ? 'active' : ''}`}
                onClick={() => setSelectedTab('overview')}
              >
                Overview
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${selectedTab === 'rules' ? 'active' : ''}`}
                onClick={() => setSelectedTab('rules')}
              >
                Rules ({rules.length})
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${selectedTab === 'checks' ? 'active' : ''}`}
                onClick={() => setSelectedTab('checks')}
              >
                Checks ({checks.length})
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${selectedTab === 'alerts' ? 'active' : ''}`}
                onClick={() => setSelectedTab('alerts')}
              >
                Alerts ({alerts.filter(a => a.status === 'active').length})
              </button>
            </li>
          </ul>

          {/* Overview Tab */}
          {selectedTab === 'overview' && summary && (
            <div className="row">
              {/* Compliance Score */}
              <div className="col-lg-3 col-md-6 mb-4">
                <div className="card">
                  <div className="card-body text-center">
                    <h5 className="card-title">Compliance Score</h5>
                    <div className="display-6 text-primary">{summary.compliance_percentage}%</div>
                    <p className="text-muted">{summary.total_checks} total checks</p>
                  </div>
                </div>
              </div>

              {/* Active Alerts */}
              <div className="col-lg-3 col-md-6 mb-4">
                <div className="card">
                  <div className="card-body text-center">
                    <h5 className="card-title">Active Alerts</h5>
                    <div className="display-6 text-warning">{summary.total_active_alerts}</div>
                    <p className="text-muted">
                      {summary.alert_counts.urgent} urgent, {summary.alert_counts.high} high priority
                    </p>
                  </div>
                </div>
              </div>

              {/* Status Breakdown */}
              <div className="col-lg-6 col-md-12 mb-4">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title">Status Breakdown</h5>
                    <div className="row text-center">
                      <div className="col-3">
                        <div className="text-success fw-bold">{summary.status_counts.compliant}</div>
                        <small className="text-muted">Compliant</small>
                      </div>
                      <div className="col-3">
                        <div className="text-danger fw-bold">{summary.status_counts.non_compliant}</div>
                        <small className="text-muted">Non-Compliant</small>
                      </div>
                      <div className="col-3">
                        <div className="text-warning fw-bold">{summary.status_counts.warning}</div>
                        <small className="text-muted">Warning</small>
                      </div>
                      <div className="col-3">
                        <div className="text-secondary fw-bold">{summary.status_counts.pending}</div>
                        <small className="text-muted">Pending</small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="col-12">
                <div className="row">
                  <div className="col-lg-6 mb-4">
                    <div className="card">
                      <div className="card-header">
                        <h6 className="mb-0">Recent Checks</h6>
                      </div>
                      <div className="card-body">
                        {summary.recent_checks.length > 0 ? (
                          <div className="list-group list-group-flush">
                            {summary.recent_checks.slice(0, 5).map((check) => (
                              <div key={check.id} className="list-group-item">
                                <div className="d-flex justify-content-between align-items-start">
                                  <div>
                                    <div className="fw-bold">{check.rule_name}</div>
                                    <small className="text-muted">Client {check.client_id}</small>
                                  </div>
                                  <span className={getStatusBadgeClass(check.status)}>
                                    {check.status.replace('_', ' ')}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-muted">No recent checks</p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="col-lg-6 mb-4">
                    <div className="card">
                      <div className="card-header">
                        <h6 className="mb-0">Recent Alerts</h6>
                      </div>
                      <div className="card-body">
                        {summary.recent_alerts.length > 0 ? (
                          <div className="list-group list-group-flush">
                            {summary.recent_alerts.slice(0, 5).map((alert) => (
                              <div key={alert.id} className="list-group-item">
                                <div className="d-flex justify-content-between align-items-start">
                                  <div>
                                    <div className="fw-bold">{alert.rule_name}</div>
                                    <small className="text-muted">{alert.message}</small>
                                  </div>
                                  <span className={getPriorityBadgeClass(alert.priority)}>
                                    {alert.priority}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-muted">No recent alerts</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Rules Tab */}
          {selectedTab === 'rules' && (
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Compliance Rules</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Rule Name</th>
                        <th>Category</th>
                        <th>Source</th>
                        <th>Severity</th>
                        <th>Auto Check</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rules.map((rule) => (
                        <tr key={rule.id}>
                          <td className="fw-bold">{rule.name}</td>
                          <td>
                            <span className="badge bg-info">{rule.category}</span>
                          </td>
                          <td>
                            <span className="badge bg-secondary">{rule.regulation_source}</span>
                          </td>
                          <td>
                            <span className={`badge ${
                              rule.severity === 'critical' ? 'bg-danger' :
                              rule.severity === 'high' ? 'bg-warning text-dark' :
                              rule.severity === 'medium' ? 'bg-info' : 'bg-secondary'
                            }`}>
                              {rule.severity}
                            </span>
                          </td>
                          <td>
                            {rule.auto_check ? (
                              <span className="badge bg-success">Yes</span>
                            ) : (
                              <span className="badge bg-warning text-dark">Manual</span>
                            )}
                          </td>
                          <td>
                            <small className="text-muted">{rule.description}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Checks Tab */}
          {selectedTab === 'checks' && (
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Compliance Checks</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Check ID</th>
                        <th>Client</th>
                        <th>Status</th>
                        <th>Details</th>
                        <th>Checked At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checks.map((check) => (
                        <tr key={check.id}>
                          <td>#{check.id}</td>
                          <td>Client {check.client_id}</td>
                          <td>
                            <span className={getStatusBadgeClass(check.status)}>
                              {check.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td>
                            <small className="text-muted">
                              {check.details.message || 'No details'}
                            </small>
                          </td>
                          <td>
                            <small>{new Date(check.checked_at).toLocaleDateString()}</small>
                          </td>
                          <td>
                            {check.status !== 'compliant' && (
                              <button 
                                className="btn btn-sm btn-outline-success"
                                onClick={() => resolveCheck(check.id)}
                              >
                                Resolve
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Alerts Tab */}
          {selectedTab === 'alerts' && (
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Compliance Alerts</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Alert ID</th>
                        <th>Message</th>
                        <th>Priority</th>
                        <th>Due Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {alerts.map((alert) => (
                        <tr key={alert.id}>
                          <td>#{alert.id}</td>
                          <td>{alert.message}</td>
                          <td>
                            <span className={getPriorityBadgeClass(alert.priority)}>
                              {alert.priority}
                            </span>
                          </td>
                          <td>
                            <small>{new Date(alert.due_date).toLocaleDateString()}</small>
                          </td>
                          <td>
                            <span className={`badge ${
                              alert.status === 'active' ? 'bg-warning text-dark' :
                              alert.status === 'acknowledged' ? 'bg-info' : 'bg-success'
                            }`}>
                              {alert.status}
                            </span>
                          </td>
                          <td>
                            {alert.status === 'active' && (
                              <button 
                                className="btn btn-sm btn-outline-primary"
                                onClick={() => acknowledgeAlert(alert.id)}
                              >
                                Acknowledge
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComplianceDashboard;