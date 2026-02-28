import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function LiveTestRunner({ run }) {
  const [progress, setProgress] = useState(0);
  const [currentTest, setCurrentTest] = useState('');
  const [results, setResults] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + Math.random() * 5, 100));
      setCurrentTest(`tests/integration/test_service_${Math.floor(Math.random() * 8)}.py::test_example`);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const passed = results.filter(r => r.status === 'passed').length;
  const failed = results.filter(r => r.status === 'failed').length;

  return (
    <div className="LiveTestRunner" data-testid="live-test-runner">
      <h2>Live Test Execution</h2>

      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${progress}%` }} data-testid="progress-bar"></div>
        <span className="progress-text">{progress.toFixed(1)}%</span>
      </div>

      {currentTest && (
        <div className="current-test" data-testid="current-test">
          Running: {currentTest}
        </div>
      )}

      <div className="test-stats">
        <span data-testid="passed-count">Passed: {passed}</span>
        <span data-testid="failed-count">Failed: {failed}</span>
      </div>
    </div>
  );
}

export default LiveTestRunner;
