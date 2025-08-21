import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './components/HomePage'
import IntakePage from './components/IntakePage'
import ResultsPage from './components/ResultsPage'
import DashboardPage from './components/DashboardPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/intake" element={<IntakePage />} />
          <Route path="/results/:quoteId" element={<ResultsPage />} />
          <Route path="/dashboard/:clientId" element={<DashboardPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App