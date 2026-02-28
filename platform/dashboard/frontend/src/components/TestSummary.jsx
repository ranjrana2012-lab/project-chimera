import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';

function TestSummary({ run }) {
  const data = [
    { name: 'Passed', value: run.passed, color: '#10b981' },
    { name: 'Failed', value: run.failed, color: '#ef4444' },
    { name: 'Skipped', value: run.skipped, color: '#6b7280' }
  ];

  return (
    <div className="TestSummary" data-testid="run-summary">
      <h2>Test Run Summary</h2>

      <div className="summary-stats">
        <div className="stat">
          <span className="stat-label">Total Tests</span>
          <span className="stat-value" data-testid="total-tests">{run.total}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Duration</span>
          <span className="stat-value">{run.duration_seconds}s</span>
        </div>
        <div className="stat">
          <span className="stat-label">Coverage</span>
          <span className="stat-value">{run.coverage_pct}%</span>
        </div>
        <div className="stat">
          <span className="stat-label">Mutation Score</span>
          <span className="stat-value">{run.mutation_score}%</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data} label>
            <Cell fill="#10b981" />
            <Cell fill="#ef4444" />
            <Cell fill="#6b7280" />
          </Pie>
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      <div className="quality-gates">
        <h3>Quality Gates</h3>
        <div className="gate passed">Coverage 95%: {run.coverage_pct}%</div>
        <div className="gate passed">Mutation 2%: {100 - run.mutation_score}% survived</div>
      </div>
    </div>
  );
}

export default TestSummary;
