// Main application JavaScript
class PlanConcierge {
    constructor() {
        this.currentStep = 1;
        this.intakeData = {};
        this.quoteResults = null;
        this.explanationData = null;
        
        this.init();
    }
    
    init() {
        // Initialize event listeners
        this.setupEventListeners();
        
        // Initialize tooltips and other Bootstrap components
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }
    
    setupEventListeners() {
        // Intake form submission
        const intakeForm = document.getElementById('intake-form');
        if (intakeForm) {
            intakeForm.addEventListener('submit', (e) => this.handleIntakeSubmit(e));
        }
        
        // Add doctor button
        const addDoctorBtn = document.getElementById('add-doctor');
        if (addDoctorBtn) {
            addDoctorBtn.addEventListener('click', () => this.addDoctorField());
        }
        
        // Add prescription button  
        const addRxBtn = document.getElementById('add-prescription');
        if (addRxBtn) {
            addRxBtn.addEventListener('click', () => this.addPrescriptionField());
        }
        
        // Quote results actions
        const explainBtn = document.getElementById('explain-plans');
        if (explainBtn) {
            explainBtn.addEventListener('click', () => this.generateExplanation());
        }
        
        const exportBtn = document.getElementById('export-pdf');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPDF());
        }
        
        // New quote button
        const newQuoteBtn = document.getElementById('new-quote');
        if (newQuoteBtn) {
            newQuoteBtn.addEventListener('click', () => this.startNewQuote());
        }
    }
    
    async handleIntakeSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const loadingSpinner = document.getElementById('loading-spinner');
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        try {
            // Show loading state
            if (loadingSpinner) loadingSpinner.classList.remove('d-none');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }
            
            // Collect form data
            const intake = this.collectIntakeData(formData);
            
            // Step 1: Create intake
            const intakeResponse = await this.apiCall('/api/intake', 'POST', intake);
            this.intakeData = { ...intake, ...intakeResponse };
            
            // Step 2: Get quote preview
            const quoteResponse = await this.apiCall('/api/quote/preview', 'POST', {
                intake_id: intakeResponse.intake_id
            });
            
            this.quoteResults = quoteResponse;
            
            // Display results
            this.displayQuoteResults(quoteResponse);
            
        } catch (error) {
            console.error('Error processing intake:', error);
            this.showError('Failed to process intake. Please try again.');
        } finally {
            // Hide loading state
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Get Plan Recommendations';
            }
        }
    }
    
    collectIntakeData(formData) {
        // Collect basic info
        const intake = {
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'), 
            email: formData.get('email'),
            dob: formData.get('dob'),
            zip_code: formData.get('zip_code'),
            county: formData.get('county'),
            state: formData.get('state'),
            plan_year: parseInt(formData.get('plan_year')),
            household_size: parseInt(formData.get('household_size')),
            annual_income: parseFloat(formData.get('annual_income')),
            ages: formData.get('ages').split(',').map(age => parseInt(age.trim())),
            doctors: [],
            prescriptions: [],
            preferences: {
                max_premium: formData.get('max_premium') ? parseFloat(formData.get('max_premium')) : null,
                prefer_low_deductible: formData.get('prefer_low_deductible') === 'on',
                prefer_broad_network: formData.get('prefer_broad_network') === 'on'
            }
        };
        
        // Collect doctors
        const doctorElements = document.querySelectorAll('.doctor-entry');
        doctorElements.forEach((element, index) => {
            const name = element.querySelector(`input[name="doctor_name_${index}"]`)?.value;
            const npi = element.querySelector(`input[name="doctor_npi_${index}"]`)?.value || '';
            const specialty = element.querySelector(`input[name="doctor_specialty_${index}"]`)?.value || '';
            
            if (name) {
                intake.doctors.push({ name, npi, specialty });
            }
        });
        
        // Collect prescriptions
        const rxElements = document.querySelectorAll('.prescription-entry');
        rxElements.forEach((element, index) => {
            const name = element.querySelector(`input[name="rx_name_${index}"]`)?.value;
            const dosage = element.querySelector(`input[name="rx_dosage_${index}"]`)?.value || '';
            const quantity = element.querySelector(`input[name="rx_quantity_${index}"]`)?.value || '30';
            
            if (name) {
                intake.prescriptions.push({ 
                    name, 
                    dosage, 
                    quantity: parseInt(quantity) 
                });
            }
        });
        
        return intake;
    }
    
    displayQuoteResults(results) {
        const resultsSection = document.getElementById('quote-results');
        const intakeSection = document.getElementById('intake-section');
        
        if (resultsSection && intakeSection) {
            // Hide intake form
            intakeSection.classList.add('d-none');
            
            // Show results
            resultsSection.classList.remove('d-none');
            
            // Update results content
            this.updateResultsDisplay(results);
        }
    }
    
    updateResultsDisplay(results) {
        // Update APTC display
        const aptcElement = document.getElementById('aptc-amount');
        if (aptcElement) {
            aptcElement.textContent = `$${results.aptc.toFixed(2)}`;
        }
        
        // Update CSR display
        const csrElement = document.getElementById('csr-level');
        if (csrElement) {
            csrElement.textContent = results.csr_level;
        }
        
        // Update plan cards
        const planCardsContainer = document.getElementById('plan-cards');
        if (planCardsContainer) {
            planCardsContainer.innerHTML = '';
            
            results.top_3_plans.forEach((planData, index) => {
                const card = this.createPlanCard(planData, index + 1);
                planCardsContainer.appendChild(card);
            });
        }
    }
    
    createPlanCard(planData, rank) {
        const { plan, plan_fit } = planData;
        
        const cardDiv = document.createElement('div');
        cardDiv.className = 'col-md-4 mb-3';
        
        const fitScore = plan_fit.fit_score;
        const scoreClass = fitScore >= 80 ? 'success' : fitScore >= 60 ? 'warning' : 'danger';
        
        cardDiv.innerHTML = `
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span class="fw-bold">#${rank} Recommendation</span>
                    <span class="badge bg-${scoreClass}">Fit: ${fitScore.toFixed(0)}%</span>
                </div>
                <div class="card-body">
                    <h5 class="card-title">${plan.name}</h5>
                    <p class="card-text text-muted">${plan.issuer} • ${plan.metal} Level</p>
                    
                    <div class="row text-center mb-3">
                        <div class="col-4">
                            <div class="fs-5 fw-bold text-primary">$${plan_fit.net_premium.toFixed(2)}</div>
                            <small class="text-muted">Monthly Premium</small>
                        </div>
                        <div class="col-4">
                            <div class="fs-5 fw-bold">$${plan.deductible.toLocaleString()}</div>
                            <small class="text-muted">Deductible</small>
                        </div>
                        <div class="col-4">
                            <div class="fs-5 fw-bold">$${plan.moop.toLocaleString()}</div>
                            <small class="text-muted">Max OOP</small>
                        </div>
                    </div>
                    
                    ${this.createCoverageInfo(plan_fit)}
                </div>
            </div>
        `;
        
        return cardDiv;
    }
    
    createCoverageInfo(planFit) {
        const doctorsInNetwork = planFit.rationale.doctors_in_network;
        const totalDoctors = planFit.rationale.total_doctors;
        const rxCovered = planFit.rationale.rx_covered;
        const totalRx = planFit.rationale.total_rx;
        
        let html = '<div class="coverage-info">';
        
        if (totalDoctors > 0) {
            const doctorPercentage = ((doctorsInNetwork / totalDoctors) * 100).toFixed(0);
            const doctorClass = doctorPercentage >= 80 ? 'success' : doctorPercentage >= 50 ? 'warning' : 'danger';
            html += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>Your Doctors</span>
                    <span class="badge bg-${doctorClass}">${doctorsInNetwork}/${totalDoctors} In Network</span>
                </div>
            `;
        }
        
        if (totalRx > 0) {
            const rxPercentage = ((rxCovered / totalRx) * 100).toFixed(0);
            const rxClass = rxPercentage >= 80 ? 'success' : rxPercentage >= 50 ? 'warning' : 'danger';
            html += `
                <div class="d-flex justify-content-between align-items-center">
                    <span>Your Prescriptions</span>
                    <span class="badge bg-${rxClass}">${rxCovered}/${totalRx} Covered</span>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    async generateExplanation() {
        const explainBtn = document.getElementById('explain-plans');
        const explanationSection = document.getElementById('explanation-section');
        
        try {
            if (explainBtn) {
                explainBtn.disabled = true;
                explainBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating Explanation...';
            }
            
            const response = await this.apiCall('/api/explain/top3', 'POST', {
                quote_result_id: this.quoteResults.quote_result_id
            });
            
            this.explanationData = response;
            
            // Display explanation
            const explanationContent = document.getElementById('explanation-content');
            if (explanationContent) {
                explanationContent.innerHTML = this.formatExplanation(response.explanation);
            }
            
            if (explanationSection) {
                explanationSection.classList.remove('d-none');
            }
            
            // Enable PDF export
            const exportBtn = document.getElementById('export-pdf');
            if (exportBtn) {
                exportBtn.disabled = false;
            }
            
        } catch (error) {
            console.error('Error generating explanation:', error);
            this.showError('Failed to generate explanation. Please try again.');
        } finally {
            if (explainBtn) {
                explainBtn.disabled = false;
                explainBtn.innerHTML = 'Generate Explanation';
            }
        }
    }
    
    formatExplanation(explanation) {
        // Convert plain text explanation to formatted HTML
        return explanation
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    async exportPDF() {
        const exportBtn = document.getElementById('export-pdf');
        
        try {
            if (exportBtn) {
                exportBtn.disabled = true;
                exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating PDF...';
            }
            
            const response = await fetch('/api/export/pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    quote_result_id: this.quoteResults.quote_result_id,
                    explanation: this.explanationData.explanation
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
            
            // Download the PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `plan_recommendations_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showSuccess('PDF downloaded successfully!');
            
        } catch (error) {
            console.error('Error exporting PDF:', error);
            this.showError('Failed to generate PDF. Please try again.');
        } finally {
            if (exportBtn) {
                exportBtn.disabled = false;
                exportBtn.innerHTML = 'Download PDF Report';
            }
        }
    }
    
    startNewQuote() {
        // Reset application state
        this.intakeData = {};
        this.quoteResults = null;
        this.explanationData = null;
        
        // Show intake section, hide results
        const intakeSection = document.getElementById('intake-section');
        const resultsSection = document.getElementById('quote-results');
        const explanationSection = document.getElementById('explanation-section');
        
        if (intakeSection) intakeSection.classList.remove('d-none');
        if (resultsSection) resultsSection.classList.add('d-none');
        if (explanationSection) explanationSection.classList.add('d-none');
        
        // Reset form
        const form = document.getElementById('intake-form');
        if (form) form.reset();
        
        // Reset dynamic fields
        this.resetDynamicFields();
    }
    
    addDoctorField() {
        const container = document.getElementById('doctors-container');
        const index = container.children.length;
        
        const doctorEntry = document.createElement('div');
        doctorEntry.className = 'doctor-entry mb-3 p-3 border rounded';
        doctorEntry.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Doctor Name *</label>
                    <input type="text" class="form-control" name="doctor_name_${index}" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label">NPI (if known)</label>
                    <input type="text" class="form-control" name="doctor_npi_${index}">
                </div>
                <div class="col-md-3">
                    <label class="form-label">Specialty</label>
                    <input type="text" class="form-control" name="doctor_specialty_${index}">
                </div>
                <div class="col-md-1 d-flex align-items-end">
                    <button type="button" class="btn btn-outline-danger btn-sm remove-doctor">
                        <i data-feather="x"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(doctorEntry);
        
        // Add remove functionality
        doctorEntry.querySelector('.remove-doctor').addEventListener('click', () => {
            container.removeChild(doctorEntry);
        });
        
        // Refresh feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    addPrescriptionField() {
        const container = document.getElementById('prescriptions-container');
        const index = container.children.length;
        
        const rxEntry = document.createElement('div');
        rxEntry.className = 'prescription-entry mb-3 p-3 border rounded';
        rxEntry.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Medication Name *</label>
                    <input type="text" class="form-control" name="rx_name_${index}" required>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Dosage</label>
                    <input type="text" class="form-control" name="rx_dosage_${index}" placeholder="e.g., 10mg">
                </div>
                <div class="col-md-3">
                    <label class="form-label">Monthly Quantity</label>
                    <input type="number" class="form-control" name="rx_quantity_${index}" value="30" min="1">
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="button" class="btn btn-outline-danger btn-sm remove-prescription">
                        <i data-feather="x"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(rxEntry);
        
        // Add remove functionality
        rxEntry.querySelector('.remove-prescription').addEventListener('click', () => {
            container.removeChild(rxEntry);
        });
        
        // Refresh feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    resetDynamicFields() {
        // Clear dynamic doctor fields
        const doctorsContainer = document.getElementById('doctors-container');
        if (doctorsContainer) {
            doctorsContainer.innerHTML = '';
        }
        
        // Clear dynamic prescription fields
        const rxContainer = document.getElementById('prescriptions-container');
        if (rxContainer) {
            rxContainer.innerHTML = '';
        }
    }
    
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PlanConcierge();
});
