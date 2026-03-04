#!/usr/bin/env python3
"""Generate service dependency graph from Jaeger traces"""

import argparse
import json
import requests
import sys
from typing import Dict, List


def get_dependencies(jaeger_url: str) -> Dict[str, List[str]]:
    """Query Jaeger for service dependencies"""

    # Get all services
    try:
        services_response = requests.get(f"{jaeger_url}/api/services", timeout=30)
        services_response.raise_for_status()
        services = services_response.json().get("data", [])
    except requests.RequestException as e:
        print(f"Error fetching services from Jaeger: {e}", file=sys.stderr)
        sys.exit(1)

    dependencies = {}

    for service in services:
        # Get traces for each service
        try:
            traces_response = requests.get(
                f"{jaeger_url}/api/traces",
                params={
                    "service": service,
                    "limit": 100
                },
                timeout=30
            )
            traces_response.raise_for_status()
            traces = traces_response.json().get("data", [])
        except requests.RequestException as e:
            print(f"Warning: Could not fetch traces for {service}: {e}", file=sys.stderr)
            continue

        service_deps = set()

        for trace in traces:
            for span in trace.get("spans", []):
                # Extract process and service info
                process = span.get("process", {})
                process_tags = process.get("tags", [])

                # Look for peer service tags
                for tag in process_tags:
                    if tag.get("key") == "peer.service":
                        service_deps.add(tag.get("value"))

        dependencies[service] = list(service_deps)

    return dependencies


def generate_graph(dependencies: Dict[str, List[str]]) -> str:
    """Generate Graphviz DOT format"""

    dot = ["digraph chimera_services {"]
    dot.append("  rankdir=LR;")
    dot.append("  node [shape=box, style=rounded];")
    dot.append("")

    # Add nodes
    for service in dependencies.keys():
        dot.append(f'  "{service}" [label="{service}"];')

    dot.append("")

    # Add edges
    for service, deps in dependencies.items():
        for dep in deps:
            dot.append(f'  "{service}" -> "{dep}";')

    dot.append("}")

    return "\n".join(dot)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Generate service dependency graph from Jaeger traces"
    )
    parser.add_argument(
        "--jaeger-url",
        default="http://jaeger.shared.svc.cluster.local:16686",
        help="Jaeger API URL (default: http://jaeger.shared.svc.cluster.local:16686)"
    )
    parser.add_argument(
        "--output",
        default="platform/monitoring/docs/dependency-graph.json",
        help="Output JSON file path (default: platform/monitoring/docs/dependency-graph.json)"
    )
    parser.add_argument(
        "--dot-only",
        action="store_true",
        help="Only output DOT format to stdout, don't save files"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only output JSON to stdout, don't save files"
    )

    args = parser.parse_args()

    print("Fetching service dependencies from Jaeger...")

    dependencies = get_dependencies(args.jaeger_url)

    if args.dot_only:
        # Generate and print DOT only
        dot_graph = generate_graph(dependencies)
        print(dot_graph)
        return 0

    if args.json_only:
        # Print JSON only
        print(json.dumps(dependencies, indent=2))
        return 0

    # Save JSON
    try:
        with open(args.output, "w") as f:
            json.dump(dependencies, f, indent=2)

        # Generate DOT
        dot_graph = generate_graph(dependencies)

        dot_file = args.output.replace(".json", ".dot")
        with open(dot_file, "w") as f:
            f.write(dot_graph)

        print(f"Dependency graph saved to {args.output}")
        print(f"DOT format saved to {dot_file}")
        print(f"Render with: dot -Tpng {dot_file} -o dependency-graph.png")

        return 0
    except IOError as e:
        print(f"Error writing output files: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
