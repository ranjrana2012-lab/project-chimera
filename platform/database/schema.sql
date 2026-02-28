-- Chimera Quality Platform Database Schema
-- PostgreSQL Schema for Test Management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Test Runs Table
-- Stores metadata about each test execution run
CREATE TABLE test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_number SERIAL,
    commit_sha VARCHAR(40) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    triggered_by VARCHAR(255),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL,
    total_tests INT NOT NULL,
    passed INT,
    failed INT,
    skipped INT,
    duration_seconds INT
);

CREATE INDEX idx_test_runs_commit_sha ON test_runs(commit_sha);
CREATE INDEX idx_test_runs_branch ON test_runs(branch);
CREATE INDEX idx_test_runs_started_at ON test_runs(started_at DESC);

-- Test Results Table
-- Stores individual test results within a run
CREATE TABLE test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    test_id VARCHAR(500) NOT NULL,
    test_file VARCHAR(500),
    test_class VARCHAR(255),
    test_function VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    duration_ms INT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    output TEXT,
    error_message TEXT
);

CREATE INDEX idx_test_results_run_id ON test_results(run_id);
CREATE INDEX idx_test_results_test_id ON test_results(test_id);
CREATE INDEX idx_test_results_status ON test_results(status);

-- Coverage Snapshots Table
-- Stores code coverage metrics for each service
CREATE TABLE coverage_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    line_coverage DECIMAL(5,2),
    branch_coverage DECIMAL(5,2),
    lines_covered INT,
    lines_total INT
);

CREATE INDEX idx_coverage_snapshots_run_service ON coverage_snapshots(run_id, service_name);

-- Mutation Results Table
-- Stores mutation testing results for each service
CREATE TABLE mutation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    total_mutations INT,
    killed_mutations INT,
    survived_mutations INT,
    timeout_mutations INT,
    mutation_score DECIMAL(5,2)
);

CREATE INDEX idx_mutation_results_run_service ON mutation_results(run_id, service_name);

-- Performance Metrics Table
-- Stores performance benchmark results
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    endpoint_name VARCHAR(255) NOT NULL,
    requests_per_second DECIMAL(10,2),
    avg_response_time_ms INT,
    p95_response_time_ms INT,
    p99_response_time_ms INT,
    error_rate DECIMAL(5,2)
);

CREATE INDEX idx_performance_metrics_run_endpoint ON performance_metrics(run_id, endpoint_name);

-- Daily Summaries Table
-- Stores aggregated daily metrics per service
CREATE TABLE daily_summaries (
    date DATE NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    total_runs INT,
    avg_coverage DECIMAL(5,2),
    avg_mutation_score DECIMAL(5,2),
    avg_duration_seconds INT,
    PRIMARY KEY (date, service_name)
);

-- Quality Gate Results Table
-- Stores quality gate evaluation results
CREATE TABLE quality_gate_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(id) ON DELETE CASCADE,
    gate_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    threshold DECIMAL(5,2),
    actual_value DECIMAL(5,2),
    message TEXT
);

CREATE INDEX idx_quality_gate_results_run_id ON quality_gate_results(run_id);
