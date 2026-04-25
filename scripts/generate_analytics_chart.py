#!/usr/bin/env python3
"""
Track 3: DevOps Analytics Extractor
===================================
Student 3: Execute this script to parse your CSV files and dynamically output visual graphs of system performance and audience sentiment latency.

Usage: 
  python3 generate_analytics_chart.py <path_to_chimera_export.csv>
"""

import sys
import csv
import matplotlib.pyplot as plt
from datetime import datetime

def generate_chart(csv_path):
    print(f"Loading metrics from {csv_path}...")
    
    timestamps = []
    latencies = []
    sentiments = []
    
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse timestamp and latency
                    ts = datetime.fromtimestamp(float(row['timestamp']))
                    latency = float(row['latency_ms'])
                    
                    timestamps.append(ts)
                    latencies.append(latency)
                    sentiments.append(row['sentiment'])
                except (ValueError, KeyError) as e:
                    print(f"Skipping malformed row: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"ERROR: Could not find '{csv_path}'.")
        print("Export a session CSV from the Web Dashboard first!")
        sys.exit(1)
        
    if not latencies:
        print("ERROR: No valid data points found in CSV to graph.")
        sys.exit(1)

    print(f"Successfully loaded {len(latencies)} performance metrics.")
    print("Generating Latency vs. Execution Graph...")
    
    # Render the Chart utilizing Matplotlib
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Map sentiment colors to the scatter plot
    colors = {'POSITIVE': '#10b981', 'NEGATIVE': '#ef4444', 'NEUTRAL': '#64748b'}
    point_colors = [colors.get(s, '#000000') for s in sentiments]
    
    ax.scatter(timestamps, latencies, c=point_colors, s=100, alpha=0.7, edgecolors='none')
    ax.plot(timestamps, latencies, color='#3b82f6', alpha=0.3, linestyle='--')
    
    ax.set_title('Chimera Operator: AI Generation Latency Over Time')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Generation Latency (ms)')
    
    # Format graph cleanly
    plt.gcf().autofmt_xdate()
    
    # Add simple legend
    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color='#10b981', label='Positive Sentiment'),
        mpatches.Patch(color='#ef4444', label='Negative Sentiment'),
        mpatches.Patch(color='#64748b', label='Neutral Sentiment')
    ]
    ax.legend(handles=legend_handles)
    
    output_file = 'metrics_chart.png'
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"SUCCESS: Architectural chart generated and saved to '{output_file}'.")
    print("Track 3 Student: You can expand this file to track 'Confidence Score' as well!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_analytics_chart.py <chimera_export.csv>")
        sys.exit(1)
    target = sys.argv[1]
    generate_chart(target)
