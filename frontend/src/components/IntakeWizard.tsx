import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { IntakeData, Doctor, Prescription, Preferences } from '../types';
import { apiService } from '../services/api';

interface IntakeWizardProps {
  onComplete: (data: IntakeData) => void;
}

const STEPS = [
  { id: 'household', title: 'Household', description: 'Tell us about your household' },
  { id: 'income', title: 'Income', description: 'Your household income information' },
  { id: 'location', title: 'Location', description: 'Where do you live?' },
  { id: 'doctors', title: 'Doctors', description: 'Your healthcare providers' },
  { id: 'prescriptions', title: 'Prescriptions', description: 'Your current medications' },
  { id: 'preferences', title: 'Preferences', description: 'What matters most to you?' },
];

const IntakeWizard: React.FC<IntakeWizardProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<IntakeData>({
    household_size: 1,
    ages: [30],
    income: 50000,
    zip: '',
    doctors: [],
    prescriptions: [],
    preferences: {
      prefer_low_premium: false,
      prefer_low_deductible: false,
      prefer_broad_network: false,
      prefer_brand_drugs: false,
      important_features: [],
    },
  });

  const updateFormData = (updates: Partial<IntakeData>) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiService.submitIntake(formData);
      
      if (response.success && response.data) {
        onComplete(formData);
        navigate('/results');
      } else {
        setError(response.error || 'Failed to submit intake');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const progressPercentage = ((currentStep + 1) / STEPS.length) * 100;

  return (
    <div className="container-fluid">
      <div className="row justify-content-center">
        <div className="col-12 col-lg-8 col-xl-6">
          {/* Progress Header */}
          <div className="card step-card mb-4">
            <div className="step-header">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h4 className="mb-0">Plan Concierge</h4>
                <span className="badge bg-light text-dark">
                  Step {currentStep + 1} of {STEPS.length}
                </span>
              </div>
              <div className="progress" style={{ height: '4px' }}>
                <div 
                  className="wizard-progress" 
                  style={{ width: `${progressPercentage}%` }}
                ></div>
              </div>
              <div className="mt-2">
                <h5 className="mb-1">{STEPS[currentStep].title}</h5>
                <p className="mb-0 opacity-75">{STEPS[currentStep].description}</p>
              </div>
            </div>

            <div className="card-body">
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}

              {/* Step Content */}
              {currentStep === 0 && (
                <HouseholdStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}
              
              {currentStep === 1 && (
                <IncomeStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}
              
              {currentStep === 2 && (
                <LocationStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}
              
              {currentStep === 3 && (
                <DoctorsStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}
              
              {currentStep === 4 && (
                <PrescriptionsStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}
              
              {currentStep === 5 && (
                <PreferencesStep 
                  data={formData} 
                  onChange={updateFormData} 
                />
              )}

              {/* Navigation */}
              <div className="d-flex justify-content-between mt-4">
                <button 
                  type="button" 
                  className="btn btn-outline-secondary"
                  onClick={prevStep}
                  disabled={currentStep === 0}
                >
                  <i className="bi bi-arrow-left me-2"></i>
                  Previous
                </button>
                
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={nextStep}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Submitting...
                    </>
                  ) : currentStep === STEPS.length - 1 ? (
                    <>
                      Get My Plans
                      <i className="bi bi-arrow-right ms-2"></i>
                    </>
                  ) : (
                    <>
                      Next
                      <i className="bi bi-arrow-right ms-2"></i>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Individual Step Components
interface StepProps {
  data: IntakeData;
  onChange: (updates: Partial<IntakeData>) => void;
}

const HouseholdStep: React.FC<StepProps> = ({ data, onChange }) => {
  const updateHouseholdSize = (size: number) => {
    const newAges = Array(size).fill(0).map((_, i) => data.ages[i] || 30);
    onChange({ household_size: size, ages: newAges });
  };

  const updateAge = (index: number, age: number) => {
    const newAges = [...data.ages];
    newAges[index] = age;
    onChange({ ages: newAges });
  };

  return (
    <div>
      <div className="mb-4">
        <label htmlFor="householdSize" className="form-label">
          How many people are in your household?
        </label>
        <select
          id="householdSize"
          className="form-select"
          value={data.household_size}
          onChange={(e) => updateHouseholdSize(parseInt(e.target.value))}
        >
          {[1, 2, 3, 4, 5, 6, 7, 8].map(size => (
            <option key={size} value={size}>{size} {size === 1 ? 'person' : 'people'}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="form-label">Ages of household members</label>
        {data.ages.map((age, index) => (
          <div key={index} className="mb-3">
            <label htmlFor={`age-${index}`} className="form-label">
              {index === 0 ? 'Your age' : `Person ${index + 1} age`}
            </label>
            <input
              type="number"
              id={`age-${index}`}
              className="form-control"
              value={age}
              min="0"
              max="100"
              onChange={(e) => updateAge(index, parseInt(e.target.value))}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

const IncomeStep: React.FC<StepProps> = ({ data, onChange }) => {
  return (
    <div>
      <div className="mb-4">
        <label htmlFor="income" className="form-label">
          What is your household's annual income?
        </label>
        <div className="input-group">
          <span className="input-group-text">$</span>
          <input
            type="number"
            id="income"
            className="form-control"
            value={data.income}
            min="0"
            step="1000"
            onChange={(e) => onChange({ income: parseInt(e.target.value) })}
          />
        </div>
        <div className="form-text">
          Enter your modified adjusted gross income (MAGI) for {new Date().getFullYear()}.
          This helps us calculate your tax credits.
        </div>
      </div>

      <div className="alert alert-info">
        <i className="bi bi-info-circle me-2"></i>
        <strong>What is MAGI?</strong> Modified Adjusted Gross Income includes wages, 
        self-employment income, interest, dividends, and Social Security benefits.
      </div>
    </div>
  );
};

const LocationStep: React.FC<StepProps> = ({ data, onChange }) => {
  return (
    <div>
      <div className="mb-4">
        <label htmlFor="zip" className="form-label">
          What is your ZIP code?
        </label>
        <input
          type="text"
          id="zip"
          className="form-control"
          value={data.zip}
          placeholder="12345"
          maxLength={5}
          pattern="[0-9]{5}"
          onChange={(e) => onChange({ zip: e.target.value })}
        />
        <div className="form-text">
          This helps us find plans available in your area.
        </div>
      </div>

      {data.county && (
        <div className="alert alert-success">
          <i className="bi bi-check-circle me-2"></i>
          <strong>Location detected:</strong> {data.county}, {data.state}
        </div>
      )}
    </div>
  );
};

const DoctorsStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [newDoctor, setNewDoctor] = useState<Partial<Doctor>>({});

  const addDoctor = () => {
    if (newDoctor.npi && newDoctor.name) {
      const doctor: Doctor = {
        npi: newDoctor.npi,
        name: newDoctor.name,
        specialty: newDoctor.specialty || '',
        practice_name: newDoctor.practice_name || '',
      };
      onChange({ doctors: [...data.doctors, doctor] });
      setNewDoctor({});
    }
  };

  const removeDoctor = (index: number) => {
    const newDoctors = data.doctors.filter((_, i) => i !== index);
    onChange({ doctors: newDoctors });
  };

  return (
    <div>
      <div className="mb-4">
        <h6>Current Healthcare Providers</h6>
        {data.doctors.length === 0 ? (
          <p className="text-muted">No providers added yet. You can skip this step if you don't have specific providers.</p>
        ) : (
          <div className="d-flex flex-wrap gap-2 mb-3">
            {data.doctors.map((doctor, index) => (
              <div key={index} className="provider-pill">
                <div>
                  <strong>{doctor.name}</strong>
                  {doctor.specialty && <><br /><small>{doctor.specialty}</small></>}
                </div>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => removeDoctor(index)}
                  aria-label="Remove provider"
                ></button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h6 className="mb-0">Add a Healthcare Provider</h6>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6 mb-3">
              <label htmlFor="doctorName" className="form-label">Provider Name *</label>
              <input
                type="text"
                id="doctorName"
                className="form-control"
                value={newDoctor.name || ''}
                placeholder="Dr. Jane Smith"
                onChange={(e) => setNewDoctor({ ...newDoctor, name: e.target.value })}
              />
            </div>
            <div className="col-md-6 mb-3">
              <label htmlFor="doctorNpi" className="form-label">NPI Number *</label>
              <input
                type="text"
                id="doctorNpi"
                className="form-control"
                value={newDoctor.npi || ''}
                placeholder="1234567890"
                maxLength={10}
                onChange={(e) => setNewDoctor({ ...newDoctor, npi: e.target.value })}
              />
            </div>
          </div>
          <div className="row">
            <div className="col-md-6 mb-3">
              <label htmlFor="doctorSpecialty" className="form-label">Specialty</label>
              <input
                type="text"
                id="doctorSpecialty"
                className="form-control"
                value={newDoctor.specialty || ''}
                placeholder="Family Medicine"
                onChange={(e) => setNewDoctor({ ...newDoctor, specialty: e.target.value })}
              />
            </div>
            <div className="col-md-6 mb-3">
              <label htmlFor="doctorPractice" className="form-label">Practice Name</label>
              <input
                type="text"
                id="doctorPractice"
                className="form-control"
                value={newDoctor.practice_name || ''}
                placeholder="ABC Medical Group"
                onChange={(e) => setNewDoctor({ ...newDoctor, practice_name: e.target.value })}
              />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-outline-primary"
            onClick={addDoctor}
            disabled={!newDoctor.npi || !newDoctor.name}
          >
            <i className="bi bi-plus-circle me-2"></i>
            Add Provider
          </button>
        </div>
      </div>
    </div>
  );
};

const PrescriptionsStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [newRx, setNewRx] = useState<Partial<Prescription>>({});

  const addPrescription = () => {
    if (newRx.name && newRx.dosage && newRx.frequency) {
      const rx: Prescription = {
        rxcui: newRx.rxcui || '',
        name: newRx.name,
        dosage: newRx.dosage,
        frequency: newRx.frequency,
      };
      onChange({ prescriptions: [...data.prescriptions, rx] });
      setNewRx({});
    }
  };

  const removePrescription = (index: number) => {
    const newRx = data.prescriptions.filter((_, i) => i !== index);
    onChange({ prescriptions: newRx });
  };

  return (
    <div>
      <div className="mb-4">
        <h6>Current Prescriptions</h6>
        {data.prescriptions.length === 0 ? (
          <p className="text-muted">No prescriptions added yet. You can skip this step if you don't take any medications.</p>
        ) : (
          <div className="d-flex flex-wrap gap-2 mb-3">
            {data.prescriptions.map((rx, index) => (
              <div key={index} className="rx-pill">
                <div>
                  <strong>{rx.name}</strong>
                  <br />
                  <small>{rx.dosage}, {rx.frequency}</small>
                </div>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => removePrescription(index)}
                  aria-label="Remove prescription"
                ></button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h6 className="mb-0">Add a Prescription</h6>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6 mb-3">
              <label htmlFor="rxName" className="form-label">Medication Name *</label>
              <input
                type="text"
                id="rxName"
                className="form-control"
                value={newRx.name || ''}
                placeholder="Lisinopril"
                onChange={(e) => setNewRx({ ...newRx, name: e.target.value })}
              />
            </div>
            <div className="col-md-6 mb-3">
              <label htmlFor="rxDosage" className="form-label">Dosage *</label>
              <input
                type="text"
                id="rxDosage"
                className="form-control"
                value={newRx.dosage || ''}
                placeholder="10mg"
                onChange={(e) => setNewRx({ ...newRx, dosage: e.target.value })}
              />
            </div>
          </div>
          <div className="row">
            <div className="col-md-6 mb-3">
              <label htmlFor="rxFrequency" className="form-label">Frequency *</label>
              <select
                id="rxFrequency"
                className="form-select"
                value={newRx.frequency || ''}
                onChange={(e) => setNewRx({ ...newRx, frequency: e.target.value })}
              >
                <option value="">Select frequency</option>
                <option value="Once daily">Once daily</option>
                <option value="Twice daily">Twice daily</option>
                <option value="Three times daily">Three times daily</option>
                <option value="Four times daily">Four times daily</option>
                <option value="As needed">As needed</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
              </select>
            </div>
            <div className="col-md-6 mb-3">
              <label htmlFor="rxCui" className="form-label">RxCUI (optional)</label>
              <input
                type="text"
                id="rxCui"
                className="form-control"
                value={newRx.rxcui || ''}
                placeholder="29046"
                onChange={(e) => setNewRx({ ...newRx, rxcui: e.target.value })}
              />
              <div className="form-text">RxCUI is a unique identifier for medications</div>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-outline-primary"
            onClick={addPrescription}
            disabled={!newRx.name || !newRx.dosage || !newRx.frequency}
          >
            <i className="bi bi-plus-circle me-2"></i>
            Add Prescription
          </button>
        </div>
      </div>
    </div>
  );
};

const PreferencesStep: React.FC<StepProps> = ({ data, onChange }) => {
  const updatePreference = (key: keyof Preferences, value: any) => {
    onChange({
      preferences: {
        ...data.preferences,
        [key]: value,
      },
    });
  };

  const toggleFeature = (feature: string) => {
    const current = data.preferences.important_features;
    const updated = current.includes(feature)
      ? current.filter(f => f !== feature)
      : [...current, feature];
    updatePreference('important_features', updated);
  };

  const features = [
    'Low monthly premium',
    'Low deductible',
    'Broad provider network',
    'Prescription drug coverage',
    'Mental health benefits',
    'Specialist access',
    'Preventive care',
    'Emergency coverage',
  ];

  return (
    <div>
      <div className="mb-4">
        <h6>Plan Priorities</h6>
        <p className="text-muted">Help us understand what's most important to you in a health plan.</p>
        
        <div className="row">
          <div className="col-md-6">
            <div className="form-check mb-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="preferLowPremium"
                checked={data.preferences.prefer_low_premium}
                onChange={(e) => updatePreference('prefer_low_premium', e.target.checked)}
              />
              <label className="form-check-label" htmlFor="preferLowPremium">
                Prefer lower monthly premiums
              </label>
            </div>
            
            <div className="form-check mb-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="preferLowDeductible"
                checked={data.preferences.prefer_low_deductible}
                onChange={(e) => updatePreference('prefer_low_deductible', e.target.checked)}
              />
              <label className="form-check-label" htmlFor="preferLowDeductible">
                Prefer lower deductibles
              </label>
            </div>
          </div>
          
          <div className="col-md-6">
            <div className="form-check mb-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="preferBroadNetwork"
                checked={data.preferences.prefer_broad_network}
                onChange={(e) => updatePreference('prefer_broad_network', e.target.checked)}
              />
              <label className="form-check-label" htmlFor="preferBroadNetwork">
                Prefer broad provider networks
              </label>
            </div>
            
            <div className="form-check mb-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="preferBrandDrugs"
                checked={data.preferences.prefer_brand_drugs}
                onChange={(e) => updatePreference('prefer_brand_drugs', e.target.checked)}
              />
              <label className="form-check-label" htmlFor="preferBrandDrugs">
                Prefer brand-name drug coverage
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <h6>Important Features</h6>
        <p className="text-muted">Select the features that are most important to you.</p>
        
        <div className="row">
          {features.map((feature, index) => (
            <div key={feature} className="col-md-6 mb-2">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id={`feature-${index}`}
                  checked={data.preferences.important_features.includes(feature)}
                  onChange={() => toggleFeature(feature)}
                />
                <label className="form-check-label" htmlFor={`feature-${index}`}>
                  {feature}
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IntakeWizard;