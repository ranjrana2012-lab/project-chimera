#!/usr/bin/env python3
"""Analyze a specific trace from Jaeger for performance issues.

This script fetches a trace from Jaeger and analyzes it for:
- Slow operations (spans taking longer than 2 seconds)
- Error/warning spans
- Missing expected spans
- Overall quality score

Usage:
    ./scripts/analyze-trace.py <trace-id> [--jaeger-url URL]

Examples:
    ./scripts/analyze-trace.py abc123def456
    ./scripts/analyze-trace.py abc123def456 --jaeger-url http://localhost:16686
"""

import sys
import os
import argparse
from typing import Optional

# Add the platform/monitoring/trace-analyzer directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
chimera_root = os.path.dirname(script_dir)
analyzer_path = os.path.join(chimera_root, 'platform', 'monitoring', 'trace-analyzer')
sys.path.insert(0, analyzer_path)

from analyzer import TraceAnalyzer, TraceIssue, TraceReport


def format_report(report: TraceReport) -> str:
    """Format a trace report for human-readable output.

    Args:
        report: The TraceReport to format

    Returns:
        Formatted string representation of the report
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"Trace Analysis Report: {report.trace_id}")
    lines.append("=" * 70)
    lines.append("")

    # Basic info
    lines.append("Basic Information:")
    lines.append(f"  Duration: {report.duration_ms / 1000:.2f} seconds")
    lines.append(f"  Span Count: {report.span_count}")
    lines.append(f"  Quality Score: {report.score:.2%}")
    lines.append("")

    # Score interpretation
    lines.append("Score Interpretation:")
    if report.score >= 0.9:
        lines.append("  ✓ Excellent - No significant issues detected")
    elif report.score >= 0.7:
        lines.append("  ⚠ Good - Minor issues detected")
    elif report.score >= 0.5:
        lines.append("  ⚠ Fair - Several issues detected")
    else:
        lines.append("  ✗ Poor - Major issues detected")
    lines.append("")

    # Issues
    if report.issues:
        lines.append("Issues Found:")
        lines.append("")

        # Group by severity
        errors = [i for i in report.issues if i.severity == "error"]
        warnings = [i for i in report.issues if i.severity == "warning"]

        if errors:
            lines.append("  Errors:")
            for issue in errors:
                lines.append(f"    ✗ [{issue.span}] {issue.message}")
            lines.append("")

        if warnings:
            lines.append("  Warnings:")
            for issue in warnings:
                lines.append(f"    ⚠ [{issue.span}] {issue.message}")
            lines.append("")
    else:
        lines.append("Issues Found:")
        lines.append("  ✓ No issues detected")
        lines.append("")

    # Recommendations
    lines.append("Recommendations:")
    if report.score >= 0.9:
        lines.append("  • No action needed - trace is healthy")
    else:
        if any(i.span == "trace_flow" and "Missing expected spans" in i.message
               for i in report.issues):
            lines.append("  • Investigate missing spans in the trace flow")
            lines.append("  • Ensure all required operations are being traced")

        if any("Slow operation" in i.message for i in report.issues):
            lines.append("  • Review slow operations for optimization opportunities")
            lines.append("  • Check for:")
            lines.append("    - Database query performance")
            lines.append("    - External API call latency")
            lines.append("    - Cache hit rates")
            lines.append("    - Resource contention")

        if any("warnings or errors" in i.message for i in report.issues):
            lines.append("  • Review error logs for failing spans")
            lines.append("  • Check application logs for stack traces")
            lines.append("  • Verify error handling and retry logic")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze a Jaeger trace for performance issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s abc123def456
  %(prog)s abc123def456 --jaeger-url http://localhost:16686
  %(prog)s abc123def456 --json
        """
    )

    parser.add_argument(
        "trace_id",
        help="The Jaeger trace ID to analyze"
    )

    parser.add_argument(
        "--jaeger-url",
        default="http://jaeger.shared.svc.cluster.local:16686",
        help="Jaeger API URL (default: %(default)s)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"Analyzing trace: {args.trace_id}")
        print(f"Jaeger URL: {args.jaeger_url}")
        print("")

    # Create analyzer and analyze trace
    analyzer = TraceAnalyzer(jaeger_url=args.jaeger_url)
    report = analyzer.analyze_trace(args.trace_id)

    # Output report
    if args.json:
        import json
        from dataclasses import asdict

        # Convert dataclasses to dicts for JSON serialization
        report_dict = {
            "trace_id": report.trace_id,
            "duration_ms": report.duration_ms,
            "span_count": report.span_count,
            "score": report.score,
            "issues": [
                {
                    "severity": issue.severity,
                    "span": issue.span,
                    "message": issue.message
                }
                for issue in report.issues
            ]
        }
        print(json.dumps(report_dict, indent=2))
    else:
        print(format_report(report))

    # Exit with error code if score is low
    if report.score < 0.5:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
