#!/usr/bin/env python3
"""
Project Chimera Phase 2 - Performance Benchmarking Suite

Comprehensive performance testing for all Phase 2 services including:
- Load testing
- Latency measurement
- Resource profiling
- Throughput analysis
- Stress testing

Usage:
    python benchmark_phase2.py --service dmx --clients 10 --duration 60
    python benchmark_phase2.py --all --stress-test
"""

import asyncio
import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import threading
import psutil
import requests
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    name: str
    service: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    cpu_percent: float
    memory_mb: float
    errors: List[str] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    latencies: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "service": self.service,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "duration_seconds": self.duration_seconds,
            "requests_per_second": self.requests_per_second,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "errors": self.errors[:10],  # Limit errors in output
        }


class ResourceMonitor:
    """Monitor system resources during benchmarking."""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []

    def _monitor(self):
        """Monitor resources in background thread."""
        process = psutil.Process()
        while self.running:
            try:
                self.cpu_samples.append(process.cpu_percent())
                self.memory_samples.append(process.memory_info().rss / 1024 / 1024)
                time.sleep(self.interval)
            except Exception:
                pass

    def start(self):
        """Start monitoring."""
        self.running = True
        self.cpu_samples = []
        self.memory_samples = []
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self) -> tuple[float, float]:
        """Stop monitoring and return averages."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        avg_cpu = statistics.mean(self.cpu_samples) if self.cpu_samples else 0
        avg_memory = statistics.mean(self.memory_samples) if self.memory_samples else 0
        return avg_cpu, avg_memory


class Phase2Benchmark:
    """Main benchmarking class for Phase 2 services."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.services = {
            "dmx": {"base_url": "http://localhost:8001", "name": "DMX Controller"},
            "audio": {"base_url": "http://localhost:8002", "name": "Audio Controller"},
            "bsl": {"base_url": "http://localhost:8003", "name": "BSL Avatar Service"},
        }

    def _measure_latency(self, func: Callable) -> float:
        """Measure latency of a function call in milliseconds."""
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        return latency_ms, result

    async def _health_check(self, service: str) -> bool:
        """Check if service is healthy."""
        service_config = self.services.get(service)
        if not service_config:
            return False
        try:
            response = requests.get(
                f"{service_config['base_url']}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services."""
        results = {}
        for service in self.services:
            results[service] = await self._health_check(service)
        return results

    def benchmark_dmx_controller(
        self,
        clients: int = 10,
        requests_per_client: int = 100,
        duration: Optional[int] = None,
    ) -> BenchmarkResult:
        """Benchmark DMX Controller service."""
        service_config = self.services["dmx"]
        base_url = service_config["base_url"]

        print(f"\n🎭 Benchmarking {service_config['name']}...")
        print(f"   Clients: {clients}, Requests per client: {requests_per_client}")

        monitor = ResourceMonitor()
        monitor.start()

        latencies = []
        errors = []
        successful = 0
        failed = 0
        timestamps = []

        start_time = time.time()

        def make_request(client_id: int, request_id: int) -> tuple[float, bool, str]:
            """Make a single request to the service."""
            request_start = time.time()

            try:
                # Simulate various DMX operations
                operations = [
                    lambda: requests.get(f"{base_url}/api/status", timeout=10),
                    lambda: requests.get(f"{base_url}/api/fixtures", timeout=10),
                    lambda: requests.get(f"{base_url}/api/scenes", timeout=10),
                ]
                response = operations[request_id % len(operations)]()
                request_end = time.time()

                latency_ms = (request_end - request_start) * 1000
                success = response.status_code == 200
                error = "" if success else f"HTTP {response.status_code}"

                return latency_ms, success, error

            except Exception as e:
                request_end = time.time()
                latency_ms = (request_end - request_start) * 1000
                return latency_ms, False, str(e)

        # Execute requests using thread pool
        with ThreadPoolExecutor(max_workers=clients) as executor:
            futures = []
            for client_id in range(clients):
                for request_id in range(requests_per_client):
                    future = executor.submit(make_request, client_id, request_id)
                    futures.append(future)

            for future in as_completed(futures):
                if duration and (time.time() - start_time) > duration:
                    break

                latency_ms, success, error = future.result()
                latencies.append(latency_ms)
                timestamps.append(time.time() - start_time)

                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(error)

        end_time = time.time()
        total_duration = end_time - start_time

        avg_cpu, avg_memory = monitor.stop()

        # Calculate statistics
        sorted_latencies = sorted(latencies)
        result = BenchmarkResult(
            name="DMX Controller Load Test",
            service="dmx",
            total_requests=len(latencies),
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=total_duration,
            requests_per_second=len(latencies) / total_duration if total_duration > 0 else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(sorted_latencies) if sorted_latencies else 0,
            p95_latency_ms=np.percentile(sorted_latencies, 95) if sorted_latencies else 0,
            p99_latency_ms=np.percentile(sorted_latencies, 99) if sorted_latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            cpu_percent=avg_cpu,
            memory_mb=avg_memory,
            errors=errors,
            timestamps=timestamps,
            latencies=latencies,
        )

        self._print_result(result)
        return result

    def benchmark_audio_controller(
        self,
        clients: int = 10,
        requests_per_client: int = 100,
        duration: Optional[int] = None,
    ) -> BenchmarkResult:
        """Benchmark Audio Controller service."""
        service_config = self.services["audio"]
        base_url = service_config["base_url"]

        print(f"\n🔊 Benchmarking {service_config['name']}...")
        print(f"   Clients: {clients}, Requests per client: {requests_per_client}")

        monitor = ResourceMonitor()
        monitor.start()

        latencies = []
        errors = []
        successful = 0
        failed = 0
        timestamps = []

        start_time = time.time()

        def make_request(client_id: int, request_id: int) -> tuple[float, bool, str]:
            """Make a single request to the service."""
            request_start = time.time()

            try:
                # Simulate various audio operations
                operations = [
                    lambda: requests.get(f"{base_url}/api/status", timeout=10),
                    lambda: requests.get(f"{base_url}/api/tracks", timeout=10),
                    lambda: requests.get(f"{base_url}/api/volume", timeout=10),
                ]
                response = operations[request_id % len(operations)]()
                request_end = time.time()

                latency_ms = (request_end - request_start) * 1000
                success = response.status_code == 200
                error = "" if success else f"HTTP {response.status_code}"

                return latency_ms, success, error

            except Exception as e:
                request_end = time.time()
                latency_ms = (request_end - request_start) * 1000
                return latency_ms, False, str(e)

        # Execute requests using thread pool
        with ThreadPoolExecutor(max_workers=clients) as executor:
            futures = []
            for client_id in range(clients):
                for request_id in range(requests_per_client):
                    future = executor.submit(make_request, client_id, request_id)
                    futures.append(future)

            for future in as_completed(futures):
                if duration and (time.time() - start_time) > duration:
                    break

                latency_ms, success, error = future.result()
                latencies.append(latency_ms)
                timestamps.append(time.time() - start_time)

                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(error)

        end_time = time.time()
        total_duration = end_time - start_time

        avg_cpu, avg_memory = monitor.stop()

        # Calculate statistics
        sorted_latencies = sorted(latencies)
        result = BenchmarkResult(
            name="Audio Controller Load Test",
            service="audio",
            total_requests=len(latencies),
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=total_duration,
            requests_per_second=len(latencies) / total_duration if total_duration > 0 else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(sorted_latencies) if sorted_latencies else 0,
            p95_latency_ms=np.percentile(sorted_latencies, 95) if sorted_latencies else 0,
            p99_latency_ms=np.percentile(sorted_latencies, 99) if sorted_latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            cpu_percent=avg_cpu,
            memory_mb=avg_memory,
            errors=errors,
            timestamps=timestamps,
            latencies=latencies,
        )

        self._print_result(result)
        return result

    def benchmark_bsl_service(
        self,
        clients: int = 10,
        requests_per_client: int = 100,
        duration: Optional[int] = None,
    ) -> BenchmarkResult:
        """Benchmark BSL Avatar Service."""
        service_config = self.services["bsl"]
        base_url = service_config["base_url"]

        print(f"\n🤟 Benchmarking {service_config['name']}...")
        print(f"   Clients: {clients}, Requests per client: {requests_per_client}")

        monitor = ResourceMonitor()
        monitor.start()

        latencies = []
        errors = []
        successful = 0
        failed = 0
        timestamps = []

        start_time = time.time()

        def make_request(client_id: int, request_id: int) -> tuple[float, bool, str]:
            """Make a single request to the service."""
            request_start = time.time()

            try:
                # Simulate various BSL operations
                test_texts = [
                    "Hello",
                    "Good morning",
                    "How are you",
                    "Thank you",
                    "Goodbye",
                ]

                operations = [
                    lambda: requests.get(f"{base_url}/api/status", timeout=10),
                    lambda: requests.get(f"{base_url}/api/gestures", timeout=10),
                    lambda: requests.post(
                        f"{base_url}/api/translate",
                        json={"text": test_texts[request_id % len(test_texts)]},
                        timeout=10,
                    ),
                ]
                response = operations[request_id % len(operations)]()
                request_end = time.time()

                latency_ms = (request_end - request_start) * 1000
                success = response.status_code == 200
                error = "" if success else f"HTTP {response.status_code}"

                return latency_ms, success, error

            except Exception as e:
                request_end = time.time()
                latency_ms = (request_end - request_start) * 1000
                return latency_ms, False, str(e)

        # Execute requests using thread pool
        with ThreadPoolExecutor(max_workers=clients) as executor:
            futures = []
            for client_id in range(clients):
                for request_id in range(requests_per_client):
                    future = executor.submit(make_request, client_id, request_id)
                    futures.append(future)

            for future in as_completed(futures):
                if duration and (time.time() - start_time) > duration:
                    break

                latency_ms, success, error = future.result()
                latencies.append(latency_ms)
                timestamps.append(time.time() - start_time)

                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(error)

        end_time = time.time()
        total_duration = end_time - start_time

        avg_cpu, avg_memory = monitor.stop()

        # Calculate statistics
        sorted_latencies = sorted(latencies)
        result = BenchmarkResult(
            name="BSL Avatar Service Load Test",
            service="bsl",
            total_requests=len(latencies),
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=total_duration,
            requests_per_second=len(latencies) / total_duration if total_duration > 0 else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(sorted_latencies) if sorted_latencies else 0,
            p95_latency_ms=np.percentile(sorted_latencies, 95) if sorted_latencies else 0,
            p99_latency_ms=np.percentile(sorted_latencies, 99) if sorted_latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            cpu_percent=avg_cpu,
            memory_mb=avg_memory,
            errors=errors,
            timestamps=timestamps,
            latencies=latencies,
        )

        self._print_result(result)
        return result

    def stress_test(
        self,
        service: str,
        max_clients: int = 100,
        requests_per_client: int = 50,
        step: int = 10,
    ) -> List[BenchmarkResult]:
        """Run stress test by gradually increasing load."""
        print(f"\n🔥 Running stress test for {self.services[service]['name']}...")
        print(f"   Max clients: {max_clients}, Step: {step}")

        results = []
        for clients in range(step, max_clients + 1, step):
            print(f"\n   Testing with {clients} clients...")

            if service == "dmx":
                result = self.benchmark_dmx_controller(
                    clients=clients,
                    requests_per_client=requests_per_client,
                )
            elif service == "audio":
                result = self.benchmark_audio_controller(
                    clients=clients,
                    requests_per_client=requests_per_client,
                )
            elif service == "bsl":
                result = self.benchmark_bsl_service(
                    clients=clients,
                    requests_per_client=requests_per_client,
                )
            else:
                continue

            results.append(result)

            # Stop if error rate is too high
            error_rate = result.failed_requests / result.total_requests
            if error_rate > 0.5:
                print(f"\n   ⚠️  Error rate exceeded 50% at {clients} clients")
                print(f"   Stopping stress test...")
                break

        return results

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result to console."""
        print(f"\n   📊 Results:")
        print(f"      Total requests: {result.total_requests}")
        print(f"      Successful: {result.successful_requests}")
        print(f"      Failed: {result.failed_requests}")
        print(f"      Duration: {result.duration_seconds:.2f}s")
        print(f"      Throughput: {result.requests_per_second:.2f} req/s")
        print(f"      Latency (avg/p50/p95/p99): "
              f"{result.avg_latency_ms:.1f}/"
              f"{result.p50_latency_ms:.1f}/"
              f"{result.p95_latency_ms:.1f}/"
              f"{result.p99_latency_ms:.1f} ms")
        print(f"      CPU: {result.cpu_percent:.1f}%, Memory: {result.memory_mb:.1f} MB")

        if result.errors:
            print(f"      Errors: {len(result.errors)} (showing first 5)")
            for error in result.errors[:5]:
                print(f"        - {error}")

    def generate_report(self, results: Optional[List[BenchmarkResult]] = None):
        """Generate comprehensive benchmark report."""
        if results is None:
            results = self.results

        if not results:
            print("\n⚠️  No results to report")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"benchmark_report_{timestamp}.md"
        json_file = self.output_dir / f"benchmark_results_{timestamp}.json"

        # Generate JSON report
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [r.to_dict() for r in results],
        }

        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)

        # Generate Markdown report
        with open(report_file, "w") as f:
            f.write("# Project Chimera Phase 2 - Performance Benchmark Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"| Service | Total Requests | Successful | Failed | Throughput (req/s) | Avg Latency (ms) | P95 Latency (ms) |\n")
            f.write(f"|---------|---------------|------------|--------|-------------------|------------------|------------------|\n")

            for result in results:
                f.write(f"| {result.service} | "
                       f"{result.total_requests} | "
                       f"{result.successful_requests} | "
                       f"{result.failed_requests} | "
                       f"{result.requests_per_second:.2f} | "
                       f"{result.avg_latency_ms:.1f} | "
                       f"{result.p95_latency_ms:.1f} |\n")

            f.write("\n---\n\n")

            # Detailed results
            f.write("## Detailed Results\n\n")

            for result in results:
                f.write(f"### {result.name}\n\n")
                f.write(f"**Service:** {result.service}\n\n")
                f.write(f"**Duration:** {result.duration_seconds:.2f} seconds\n\n")
                f.write(f"**Total Requests:** {result.total_requests}\n\n")
                f.write(f"**Successful:** {result.successful_requests}\n\n")
                f.write(f"**Failed:** {result.failed_requests}\n\n")
                f.write(f"**Throughput:** {result.requests_per_second:.2f} requests/second\n\n")
                f.write(f"**Success Rate:** "
                       f"{(result.successful_requests / result.total_requests * 100):.1f}%\n\n")

                f.write("#### Latency Statistics\n\n")
                f.write(f"| Metric | Value (ms) |\n")
                f.write(f"|--------|----------|\n")
                f.write(f"| Average | {result.avg_latency_ms:.2f} |\n")
                f.write(f"| Minimum | {result.min_latency_ms:.2f} |\n")
                f.write(f"| Maximum | {result.max_latency_ms:.2f} |\n")
                f.write(f"| P50 | {result.p50_latency_ms:.2f} |\n")
                f.write(f"| P95 | {result.p95_latency_ms:.2f} |\n")
                f.write(f"| P99 | {result.p99_latency_ms:.2f} |\n\n")

                f.write("#### Resource Usage\n\n")
                f.write(f"- **CPU:** {result.cpu_percent:.1f}%\n")
                f.write(f"- **Memory:** {result.memory_mb:.1f} MB\n\n")

                if result.errors:
                    f.write("#### Errors\n\n")
                    for error in result.errors[:10]:
                        f.write(f"- {error}\n")
                    f.write("\n")

                f.write("---\n\n")

            # Recommendations
            f.write("## Recommendations\n\n")

            for result in results:
                f.write(f"### {result.service.upper()}\n\n")

                # Performance recommendations
                if result.p95_latency_ms > 1000:
                    f.write("- ⚠️ **High P95 latency detected** (>1s). Consider:\n")
                    f.write("  - Implementing caching\n")
                    f.write("  - Optimizing database queries\n")
                    f.write("  - Scaling horizontally\n\n")

                if result.failed_requests / result.total_requests > 0.05:
                    f.write("- ⚠️ **High error rate detected** (>5%). Consider:\n")
                    f.write("  - Reviewing error logs\n")
                    f.write("  - Implementing retry logic\n")
                    f.write("  - Adding circuit breakers\n\n")

                if result.cpu_percent > 80:
                    f.write("- ⚠️ **High CPU usage detected** (>80%). Consider:\n")
                    f.write("  - Profiling for bottlenecks\n")
                    f.write("  - Optimizing algorithms\n")
                    f.write("  - Scaling vertically\n\n")

                if result.requests_per_second < 100:
                    f.write("- ℹ️ **Moderate throughput**. For higher load:\n")
                    f.write("  - Consider async processing\n")
                    f.write("  - Implement connection pooling\n")
                    f.write("  - Use load balancing\n\n")

                f.write("\n")

        print(f"\n📄 Report generated:")
        print(f"   Markdown: {report_file}")
        print(f"   JSON: {json_file}")

    def plot_results(self, results: Optional[List[BenchmarkResult]] = None):
        """Generate performance plots."""
        if results is None:
            results = self.results

        if not results:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Throughput comparison
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Project Chimera Phase 2 - Performance Benchmarks", fontsize=14)

        services = [r.service for r in results]
        throughputs = [r.requests_per_second for r in results]
        avg_latencies = [r.avg_latency_ms for r in results]
        p95_latencies = [r.p95_latency_ms for r in results]
        error_rates = [r.failed_requests / r.total_requests * 100 for r in results]

        # Throughput plot
        axes[0, 0].bar(services, throughputs, color='steelblue')
        axes[0, 0].set_title('Throughput (requests/second)')
        axes[0, 0].set_ylabel('Requests/sec')
        axes[0, 0].grid(axis='y', alpha=0.3)

        # Average latency plot
        axes[0, 1].bar(services, avg_latencies, color='coral')
        axes[0, 1].set_title('Average Latency (ms)')
        axes[0, 1].set_ylabel('Latency (ms)')
        axes[0, 1].grid(axis='y', alpha=0.3)

        # P95 latency plot
        axes[1, 0].bar(services, p95_latencies, color='lightgreen')
        axes[1, 0].set_title('P95 Latency (ms)')
        axes[1, 0].set_ylabel('Latency (ms)')
        axes[1, 0].grid(axis='y', alpha=0.3)

        # Error rate plot
        axes[1, 1].bar(services, error_rates, color='salmon')
        axes[1, 1].set_title('Error Rate (%)')
        axes[1, 1].set_ylabel('Error Rate (%)')
        axes[1, 1].grid(axis='y', alpha=0.3)

        plt.tight_layout()

        plot_file = self.output_dir / f"benchmark_plots_{timestamp}.png"
        plt.savefig(plot_file, dpi=300)
        print(f"   Plots: {plot_file}")

        # Latency distribution plot
        if results and results[0].latencies:
            plt.figure(figsize=(12, 6))

            for result in results:
                if result.latencies:
                    plt.hist(result.latencies, bins=50, alpha=0.5, label=result.service)

            plt.xlabel('Latency (ms)')
            plt.ylabel('Frequency')
            plt.title('Latency Distribution')
            plt.legend()
            plt.grid(alpha=0.3)

            dist_file = self.output_dir / f"latency_distribution_{timestamp}.png"
            plt.savefig(dist_file, dpi=300)
            print(f"   Distribution: {dist_file}")


async def run_all_benchmarks(
    clients: int = 10,
    requests: int = 100,
    stress: bool = False,
):
    """Run benchmarks for all Phase 2 services."""
    benchmark = Phase2Benchmark()

    # Check service health
    print("🔍 Checking service health...")
    health = await benchmark.check_all_services()

    unhealthy = [s for s, h in health.items() if not h]
    if unhealthy:
        print(f"\n⚠️  Warning: Some services are unhealthy: {unhealthy}")
        print("   Continuing with benchmarks anyway...\n")

    results = []

    # Benchmark each service
    if "dmx" in health:
        result = benchmark.benchmark_dmx_controller(
            clients=clients,
            requests_per_client=requests,
        )
        results.append(result)

    if "audio" in health:
        result = benchmark.benchmark_audio_controller(
            clients=clients,
            requests_per_client=requests,
        )
        results.append(result)

    if "bsl" in health:
        result = benchmark.benchmark_bsl_service(
            clients=clients,
            requests_per_client=requests,
        )
        results.append(result)

    # Stress tests if requested
    if stress:
        for service in health:
            stress_results = benchmark.stress_test(
                service=service,
                max_clients=100,
                requests_per_client=50,
                step=20,
            )
            results.extend(stress_results)

    # Generate reports
    benchmark.generate_report(results)
    benchmark.plot_results(results)

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Project Chimera Phase 2 Performance Benchmarking"
    )
    parser.add_argument(
        "--service",
        choices=["dmx", "audio", "bsl", "all"],
        default="all",
        help="Service to benchmark",
    )
    parser.add_argument(
        "--clients",
        type=int,
        default=10,
        help="Number of concurrent clients",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Number of requests per client",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Duration in seconds (overrides requests)",
    )
    parser.add_argument(
        "--stress-test",
        action="store_true",
        help="Run stress test",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmark_results",
        help="Output directory for results",
    )

    args = parser.parse_args()

    print("🚀 Project Chimera Phase 2 - Performance Benchmarking Suite")
    print("=" * 60)

    # Run benchmarks
    asyncio.run(run_all_benchmarks(
        clients=args.clients,
        requests=args.requests,
        stress=args.stress_test,
    ))


if __name__ == "__main__":
    main()
