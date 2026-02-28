import React, { useState, useEffect } from 'react';
import './App.css';
import LiveTestRunner from './components/LiveTestRunner';
import TestSummary from './components/TestSummary';

function App() {
  const [currentRun, setCurrentRun] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Simulate WebSocket connection
    setWsConnected(true);
    setCurrentRun({
      id: 'test-run-1',
      total: 100,
      passed: 85,
      failed: 5,
      skipped: 2,
      duration_seconds: 120,
      coverage_pct: 94.2,
      mutation_score: 97.8,
      testResults: []
    });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chimera Quality Platform</h1>
        <span className={wsConnected ? 'status-connected' : 'status-disconnected'}>
          {wsConnected ? ' Live' : ' Offline'}
        </span>
      </header>

      <main className="App-main">
        {currentRun ? (
          <>
            <LiveTestRunner run={currentRun} />
            <TestSummary run={currentRun} />
          </>
        ) : (
          <div className="placeholder">
            <p>No test running. Start a test run to see live results.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
