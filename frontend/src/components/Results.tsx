import React, { useState, useEffect } from 'react';
import { IntakeData, QuoteResult, PlanFit, ExplanationResponse } from '../types';
import { apiService } from '../services/api';
import ConciergeSidebar from './ConciergeSidebar';
import ExplanationModal from './ExplanationModal';

interface ResultsProps {
  intakeData: IntakeData;
}

const Results: React.FC<ResultsProps> = ({ intakeData }) => {
  const [quoteResult, setQuoteResult] = useState<QuoteResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<PlanFit | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [intakeId, setIntakeId] = useState<number | null>(null);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  useEffect(() => {
    loadQuoteResults();
  }, []);

  const loadQuoteResults = async () => {
    setLoading(true);
    setError(null);

    try {
      // First submit intake to get ID
      const intakeResponse = await apiService.submitIntake(intakeData);
      if (!intakeResponse.success || !intakeResponse.data) {
        throw new Error(intakeResponse.error || 'Failed to submit intake');
      }

      const newIntakeId = intakeResponse.data.intake_id;
      setIntakeId(newIntakeId);

      // Then get quote results
      const quoteResponse = await apiService.getQuotePreview(newIntakeId);
      if (!quoteResponse.success || !quoteResponse.data) {
        throw new Error(quoteResponse.error || 'Failed to get quote results');
      }

      setQuoteResult(quoteResponse.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleExplainPlan = async (planFit: PlanFit) => {
    try {
      const response = await apiService.explainPlan(planFit.plan.id, intakeId || undefined);
      if (response.success && response.data) {
        setExplanation(response.data);
        setSelectedPlan(planFit);
        setShowExplanation(true);
      }
    } catch (err) {
      console.error('Failed to get plan explanation:', err);
    }
  };

  const handleExplainTop3 = async () => {
    if (!quoteResult?.plan_fits || quoteResult.plan_fits.length < 3) return;

    try {
      const top3Ids = quoteResult.plan_fits.slice(0, 3).map(pf => pf.plan.id);
      const response = await apiService.explainTop3(top3Ids, intakeId || undefined);
      if (response.success && response.data) {
        setExplanation(response.data);
        setSelectedPlan(null);
        setShowExplanation(true);
      }
    } catch (err) {
      console.error('Failed to get top 3 explanation:', err);
    }
  };

  const getFitScoreClass = (score: number) => {
    if (score >= 90) return 'fit-score-excellent';
    if (score >= 75) return 'fit-score-good';
    if (score >= 60) return 'fit-score-fair';
    return 'fit-score-poor';
  };

  const getFitScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent Fit';
    if (score >= 75) return 'Good Fit';
    if (score >= 60) return 'Fair Fit';
    return 'Poor Fit';
  };

  const getMetalBadgeClass = (metal: string) => {
    return `badge metal-badge metal-${metal.toLowerCase()}`;
  };

  const handleDownloadPDF = async () => {
    if (!quoteResult || !intakeId) return;

    setIsGeneratingPDF(true);
    try {
      // Prepare data for PDF export
      const pdfData = {
        client_id: intakeId,
        plans: quoteResult.plan_fits.map(pf => ({
          name: pf.plan.name,
          issuer: pf.plan.issuer,
          metal: pf.plan.metal,
          premium_full: pf.plan.premium_full,
          net_premium: pf.net_premium,
          deductible: pf.plan.deductible,
          moop: pf.plan.moop,
          fit_score: pf.fit_score
        })),
        quote_data: {
          aptc: quoteResult.aptc,
          csr_level: quoteResult.csr_level,
          income: intakeData.income,
          household_size: intakeData.householdSize
        },
        explanation: explanation || {}
      };

      const response = await apiService.exportPDF(pdfData);
      if (response.success && response.data?.download_url) {
        // Create a temporary link to download the PDF
        const link = document.createElement('a');
        link.href = `${window.location.origin}${response.data.download_url}`;
        link.download = response.data.filename || 'plan_comparison.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        throw new Error(response.error || 'Failed to generate PDF');
      }
    } catch (err) {
      console.error('Failed to generate PDF:', err);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="row justify-content-center">
          <div className="col-12 text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading your plan options...</span>
            </div>
            <p className="mt-3">Finding the best plans for you...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container-fluid">
        <div className="row justify-content-center">
          <div className="col-12 col-md-8">
            <div className="alert alert-danger" role="alert">
              <h4 className="alert-heading">Unable to Load Plan Results</h4>
              <p>{error}</p>
              <hr />
              <button className="btn btn-outline-danger" onClick={loadQuoteResults}>
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!quoteResult) {
    return (
      <div className="container-fluid">
        <div className="row justify-content-center">
          <div className="col-12 col-md-8">
            <div className="alert alert-warning" role="alert">
              No plan results available. Please try again.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12 col-xl-8">
          {/* Results Header */}
          <div className="card mb-4">
            <div className="card-body">
              <div className="row align-items-center">
                <div className="col-md-8">
                  <h3 className="card-title mb-2">Your Health Plan Options</h3>
                  <p className="text-muted mb-0">
                    Based on your household income of ${intakeData.income.toLocaleString()}, 
                    you qualify for ${quoteResult.aptc > 0 ? `$${quoteResult.aptc}/month in tax credits` : 'marketplace plans'}.
                    {quoteResult.csr_level !== 'None' && (
                      <> You also qualify for {quoteResult.csr_level} cost-sharing reductions.</>
                    )}
                  </p>
                </div>
                <div className="col-md-4 text-md-end">
                  <div className="d-flex gap-2 justify-content-md-end align-items-center">
                    <div className="badge bg-success fs-6">
                      {quoteResult.plan_fits.length} plans found
                    </div>
                    <button 
                      className="btn btn-outline-primary btn-sm"
                      onClick={handleDownloadPDF}
                      disabled={isGeneratingPDF}
                    >
                      {isGeneratingPDF ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                          Generating...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-file-earmark-pdf me-2"></i>
                          Download PDF
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Plan Results Table */}
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Recommended Plans</h5>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Plan</th>
                      <th>Net Premium</th>
                      <th>Deductible</th>
                      <th>Max Out-of-Pocket</th>
                      <th>Fit Score</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {quoteResult.plan_fits.map((planFit, index) => (
                      <tr key={planFit.plan.id} className={index < 3 ? 'table-warning' : ''}>
                        <td>
                          <div>
                            <div className="d-flex align-items-center gap-2 mb-1">
                              <strong>{planFit.plan.name}</strong>
                              <span className={getMetalBadgeClass(planFit.plan.metal)}>
                                {planFit.plan.metal}
                              </span>
                              {index < 3 && (
                                <span className="badge bg-warning text-dark">
                                  Top {index + 1}
                                </span>
                              )}
                            </div>
                            <div className="text-muted small">
                              {planFit.plan.issuer}
                            </div>
                            {/* Coverage Summary */}
                            {(planFit.provider_summary || planFit.rx_summary) && (
                              <div className="mt-1">
                                {planFit.provider_summary && (
                                  <div className="text-success small">
                                    <i className="bi bi-check-circle me-1"></i>
                                    {planFit.provider_summary.in_network_count}/{planFit.provider_summary.total_count} providers in-network
                                  </div>
                                )}
                                {planFit.rx_summary && (
                                  <div className="text-info small">
                                    <i className="bi bi-capsule me-1"></i>
                                    {planFit.rx_summary.covered_count}/{planFit.rx_summary.total_count} prescriptions covered
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                        <td>
                          <div>
                            <strong className="text-success">
                              ${planFit.net_premium}/month
                            </strong>
                            {quoteResult.aptc > 0 && (
                              <div className="text-muted small">
                                (${planFit.plan.premium_full} - ${quoteResult.aptc} credit)
                              </div>
                            )}
                          </div>
                        </td>
                        <td>${planFit.plan.deductible.toLocaleString()}</td>
                        <td>${planFit.plan.moop.toLocaleString()}</td>
                        <td>
                          <div className="text-center">
                            <div className={`fit-score ${getFitScoreClass(planFit.fit_score)}`}>
                              {planFit.fit_score}
                            </div>
                            <small className={getFitScoreClass(planFit.fit_score)}>
                              {getFitScoreLabel(planFit.fit_score)}
                            </small>
                          </div>
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => handleExplainPlan(planFit)}
                          >
                            <i className="bi bi-chat-dots me-1"></i>
                            Explain
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Plan Details */}
          {quoteResult.plan_fits.length > 0 && (
            <div className="card mt-4">
              <div className="card-header">
                <h6 className="mb-0">Understanding Your Results</h6>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-4">
                    <h6>Fit Score</h6>
                    <p className="small text-muted">
                      Our algorithm considers your income, providers, prescriptions, 
                      and preferences to calculate how well each plan fits your needs.
                    </p>
                  </div>
                  <div className="col-md-4">
                    <h6>Net Premium</h6>
                    <p className="small text-muted">
                      The amount you'll actually pay each month after applying 
                      any tax credits you qualify for.
                    </p>
                  </div>
                  <div className="col-md-4">
                    <h6>Coverage Details</h6>
                    <p className="small text-muted">
                      Green checkmarks show your providers and prescriptions 
                      that are covered by each plan.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Concierge Sidebar */}
        <div className="col-12 col-xl-4">
          <ConciergeSidebar
            onExplainTop3={handleExplainTop3}
            hasTop3Plans={quoteResult.plan_fits.length >= 3}
          />
        </div>
      </div>

      {/* Explanation Modal */}
      <ExplanationModal
        show={showExplanation}
        onHide={() => setShowExplanation(false)}
        explanation={explanation}
        planName={selectedPlan?.plan.name}
      />
    </div>
  );
};

export default Results;