import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import IntakeWizard from './components/IntakeWizard';
import Results from './components/Results';
import { IntakeData } from './types';
import './bootstrap.css';
import './App.css';

function App() {
  const [intakeData, setIntakeData] = useState<IntakeData | null>(null);

  return (
    <Router>
      <div className="App">
        <header className="navbar navbar-dark bg-dark">
          <div className="container-fluid">
            <span className="navbar-brand mb-0 h1">Plan Concierge</span>
            <span className="navbar-text">Find the right health plan for you</span>
          </div>
        </header>
        
        <main className="container-fluid py-4">
          <Routes>
            <Route 
              path="/" 
              element={
                <IntakeWizard 
                  onComplete={(data) => setIntakeData(data)} 
                />
              } 
            />
            <Route 
              path="/results" 
              element={
                intakeData ? (
                  <Results intakeData={intakeData} />
                ) : (
                  <Navigate to="/" replace />
                )
              } 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;