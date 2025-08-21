import React, { useState } from 'react';
import { apiService } from '../services/api';
import { ExplanationResponse } from '../types';
import ExplanationModal from './ExplanationModal';

interface ConciergeSidebarProps {
  onExplainTop3: () => void;
  hasTop3Plans: boolean;
}

const ConciergeSidebar: React.FC<ConciergeSidebarProps> = ({ onExplainTop3, hasTop3Plans }) => {
  const [showTermModal, setShowTermModal] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [termInput, setTermInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleExplainTerm = async () => {
    if (!termInput.trim()) return;

    setLoading(true);
    try {
      const response = await apiService.explainTerm(termInput.trim());
      if (response.success && response.data) {
        setExplanation(response.data);
        setShowExplanation(true);
        setShowTermModal(false);
        setTermInput('');
      }
    } catch (err) {
      console.error('Failed to get term explanation:', err);
    } finally {
      setLoading(false);
    }
  };

  const commonTerms = [
    'Premium', 'Deductible', 'Copayment', 'Coinsurance', 
    'Out-of-pocket maximum', 'Network', 'Formulary', 'Prior authorization'
  ];

  return (
    <>
      <div className="concierge-sidebar">
        <div className="concierge-header">
          <h5 className="mb-0">
            <i className="bi bi-chat-heart me-2"></i>
            Ask James
          </h5>
          <p className="mb-0 opacity-75">Your Plan Concierge</p>
        </div>

        <div className="p-3">
          <p className="text-muted mb-3">
            Get personalized explanations about your health insurance options.
          </p>

          {/* Definition Button */}
          <button
            className="concierge-button"
            onClick={() => setShowTermModal(true)}
          >
            <div>
              <i className="bi bi-book me-2"></i>
              <strong>Explain a Term</strong>
              <div className="small text-muted">
                Get definitions for insurance terms
              </div>
            </div>
          </button>

          {/* Top 3 Summary Button */}
          <button
            className="concierge-button"
            onClick={onExplainTop3}
            disabled={!hasTop3Plans}
          >
            <div>
              <i className="bi bi-list-stars me-2"></i>
              <strong>Compare Top 3 Plans</strong>
              <div className="small text-muted">
                {hasTop3Plans 
                  ? 'See how your best options compare' 
                  : 'Get quotes to compare plans'
                }
              </div>
            </div>
          </button>

          {/* Quick Term Buttons */}
          <div className="mt-4">
            <h6 className="text-muted mb-2">Quick Definitions</h6>
            <div className="d-flex flex-wrap gap-1">
              {commonTerms.slice(0, 4).map(term => (
                <button
                  key={term}
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => {
                    setTermInput(term);
                    setTimeout(handleExplainTerm, 100);
                  }}
                  disabled={loading}
                >
                  {term}
                </button>
              ))}
            </div>
          </div>

          {/* Help Text */}
          <div className="mt-4 p-3 bg-light rounded">
            <h6 className="text-primary mb-2">
              <i className="bi bi-lightbulb me-1"></i>
              Pro Tip
            </h6>
            <p className="small mb-0">
              Use the "Explain" button next to any plan to get personalized 
              insights about how it fits your specific needs and budget.
            </p>
          </div>
        </div>
      </div>

      {/* Term Input Modal */}
      <div className={`modal fade ${showTermModal ? 'show d-block' : ''}`} style={{ backgroundColor: showTermModal ? 'rgba(0,0,0,0.5)' : 'transparent' }}>
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Ask About a Term</h5>
              <button type="button" className="btn-close" onClick={() => setShowTermModal(false)}></button>
            </div>
            <div className="modal-body">
              <div className="mb-3">
                <label htmlFor="termInput" className="form-label">
                  What insurance term would you like explained?
                </label>
                <input
                  type="text"
                  id="termInput"
                  className="form-control"
                  value={termInput}
                  onChange={(e) => setTermInput(e.target.value)}
                  placeholder="e.g., deductible, copay, network"
                  onKeyPress={(e) => e.key === 'Enter' && handleExplainTerm()}
                />
              </div>

              <div>
                <h6>Common Terms</h6>
                <div className="d-flex flex-wrap gap-1">
                  {commonTerms.map(term => (
                    <button
                      key={term}
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => setTermInput(term)}
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setShowTermModal(false)}>
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={handleExplainTerm}
                disabled={!termInput.trim() || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                    Getting explanation...
                  </>
                ) : (
                  'Get Explanation'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Explanation Modal */}
      <ExplanationModal
        show={showExplanation}
        onHide={() => setShowExplanation(false)}
        explanation={explanation}
      />
    </>
  );
};

export default ConciergeSidebar;