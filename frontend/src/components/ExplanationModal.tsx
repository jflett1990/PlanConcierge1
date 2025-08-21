import React from 'react';
import { ExplanationResponse } from '../types';

interface ExplanationModalProps {
  show: boolean;
  onHide: () => void;
  explanation: ExplanationResponse | null;
  planName?: string;
}

const ExplanationModal: React.FC<ExplanationModalProps> = ({ 
  show, 
  onHide, 
  explanation, 
  planName 
}) => {
  if (!explanation) return null;

  return (
    <div className={`modal fade ${show ? 'show d-block' : ''}`} style={{ backgroundColor: show ? 'rgba(0,0,0,0.5)' : 'transparent' }}>
      <div className="modal-dialog modal-lg explanation-modal">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-chat-heart text-primary me-2"></i>
              {explanation.title}
            </h5>
            <button type="button" className="btn-close" onClick={onHide}></button>
          </div>
          
          <div className="modal-body">
            {planName && (
              <div className="alert alert-info mb-3">
                <i className="bi bi-info-circle me-2"></i>
                This explanation is tailored for <strong>{planName}</strong>
              </div>
            )}

            {explanation.sections.map((section, index) => (
              <div key={index} className="explanation-section">
                <h6>{section.heading}</h6>
                <div 
                  className="text-muted"
                  dangerouslySetInnerHTML={{ 
                    __html: section.body.replace(/\n/g, '<br />') 
                  }}
                />
              </div>
            ))}

            {explanation.citations && explanation.citations.length > 0 && (
              <div className="mt-4">
                <h6 className="text-primary">Sources</h6>
                <ul className="list-unstyled">
                  {explanation.citations.map((citation, index) => (
                    <li key={index} className="mb-1">
                      <a 
                        href={citation.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="citation-link"
                      >
                        <i className="bi bi-box-arrow-up-right me-1"></i>
                        {citation.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="alert alert-warning mt-4">
              <i className="bi bi-exclamation-triangle me-2"></i>
              <strong>Important:</strong> Networks and formularies change. 
              Verify all details at enrollment.
            </div>
          </div>
          
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onHide}>
              Close
            </button>
            <button 
              type="button" 
              className="btn btn-primary"
              onClick={() => window.print()}
            >
              <i className="bi bi-printer me-2"></i>
              Print
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplanationModal;