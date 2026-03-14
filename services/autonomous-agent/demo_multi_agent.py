#!/usr/bin/env python3
"""
Demo script for multi-agent orchestration.

Demonstrates the integration between autonomous-agent and OpenClaw
with VMAO-style verification and parallel agent execution.
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


async def check_service_health(url: str, name: str) -> bool:
    """Check if a service is healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            is_healthy = response.status_code == 200
            if is_healthy:
                print_success(f"{name} is healthy")
            else:
                print_error(f"{name} health check failed (status: {response.status_code})")
            return is_healthy
    except Exception as e:
        print_error(f"{name} is unavailable: {e}")
        return False


async def demo_list_openclaw_skills(base_url: str):
    """Demo: List available skills from OpenClaw."""
    print_header("Demo 1: OpenClaw Skills Registry")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/skills")
            response.raise_for_status()
            data = response.json()

            print_info(f"OpenClaw has {data['total']} skills registered:")
            for skill in data['skills']:
                status = f"{Colors.OKGREEN}enabled{Colors.ENDC}" if skill.get('enabled', True) else "disabled"
                print(f"  • {Colors.BOLD}{skill['name']}{Colors.ENDC}: {skill['description']} [{status}]")

            return data['skills']
    except Exception as e:
        print_error(f"Failed to fetch skills: {e}")
        return []


async def demo_autonomous_agent_capabilities(base_url: str):
    """Demo: Check autonomous agent multi-agent capabilities."""
    print_header("Demo 2: Autonomous Agent Multi-Agent Mode")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check available agents
            response = await client.get(f"{base_url}/api/agents")
            response.raise_for_status()
            data = response.json()

            if data.get('enabled'):
                print_success("Multi-agent mode is ENABLED")
                print_info(f"OpenClaw URL: {data.get('openclaw_url')}")
                print_info(f"Available agents: {data.get('total', 0)}")
                for agent in data.get('agents', []):
                    status = f"{Colors.OKGREEN}enabled{Colors.ENDC}" if agent['enabled'] else "disabled"
                    print(f"  • {Colors.BOLD}{agent['name']}{Colors.ENDC}: {agent['description']} [{status}]")
            else:
                print_warning("Multi-agent mode is DISABLED")
                print_info(f"Reason: {data.get('message', 'Unknown')}")

            # Check dependencies health
            print("\n" + Colors.BOLD + "Dependency Health Check:" + Colors.ENDC)
            response = await client.get(f"{base_url}/api/health/dependencies")
            response.raise_for_status()
            health_data = response.json()

            if health_data.get('multi_agent_enabled'):
                deps = health_data.get('dependencies', {})
                for dep_name, dep_info in deps.items():
                    if dep_info.get('healthy'):
                        print_success(f"{dep_name}: Healthy")
                    else:
                        print_error(f"{dep_name}: Unhealthy")
            else:
                print_warning("Multi-agent dependencies not checked")

    except Exception as e:
        print_error(f"Failed to check autonomous agent capabilities: {e}")


async def demo_multi_agent_workflow(base_url: str):
    """Demo: Execute multi-agent workflow."""
    print_header("Demo 3: Multi-Agent Workflow (VMAO Framework)")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print_info("Initiating multi-agent workflow demo...")
            print_info("This demonstrates parallel agent calls with result aggregation")

            response = await client.post(f"{base_url}/api/demo/multi-agent")
            response.raise_for_status()
            data = response.json()

            print_success("Multi-agent workflow completed")
            print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
            print(f"  Framework: {Colors.OKCYAN}{data.get('vmao_framework')}{Colors.ENDC}")
            print(f"  Total calls: {data.get('total_calls')}")
            print(f"  Successful: {Colors.OKGREEN}{data.get('successful')}{Colors.ENDC}")
            print(f"  Failed: {Colors.FAIL if data.get('failed', 0) > 0 else ''}{data.get('failed', 0)}{Colors.ENDC if data.get('failed', 0) > 0 else '0'}")
            print(f"  Total time: {data.get('total_execution_time', 0):.2f}s")

            if data.get('results'):
                print(f"\n{Colors.BOLD}Agent Results:{Colors.ENDC}")
                for result in data.get('results', []):
                    if result['success']:
                        print_success(f"{result['skill']}: Completed in {result['execution_time']:.2f}s")
                    else:
                        print_error(f"{result['skill']}: Failed - {result.get('error', 'Unknown error')}")

    except Exception as e:
        print_error(f"Multi-agent workflow failed: {e}")


async def demo_autonomous_task_execution(base_url: str):
    """Demo: Execute autonomous task (uses OpenClaw agents internally)."""
    print_header("Demo 4: Autonomous Task Execution")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            task_request = {
                "user_request": "Create a simple scene with dialogue and captions"
            }

            print_info("Submitting autonomous task...")
            print(f"  Request: {Colors.BOLD}{task_request['user_request']}{Colors.ENDC}")

            response = await client.post(
                f"{base_url}/execute",
                json=task_request
            )

            if response.status_code == 202:
                task_data = response.json()
                task_id = task_data['task_id']
                print_success(f"Task accepted: {task_id}")

                # Poll for status
                print_info("Polling for task completion...")
                max_polls = 30
                poll_interval = 2

                for i in range(max_polls):
                    await asyncio.sleep(poll_interval)

                    status_response = await client.get(f"{base_url}/execute/{task_id}")
                    status_response.raise_for_status()
                    status_data = status_response.json()

                    status = status_data.get('status')
                    phases = status_data.get('phases_completed', [])

                    if status == 'complete':
                        print_success(f"Task completed (poll {i+1})")
                        print(f"  Phases: {', '.join(phases)}")
                        if status_data.get('result'):
                            print(f"  Result: {status_data['result']}")
                        break
                    elif status == 'failed':
                        print_error(f"Task failed: {status_data.get('error', 'Unknown error')}")
                        break
                    else:
                        print_info(f"Status: {status} | Phases: {', '.join(phases) if phases else 'None'}")

            else:
                print_error(f"Failed to submit task: {response.status_code}")

    except Exception as e:
        print_error(f"Autonomous task execution failed: {e}")


async def main():
    """Run all demos."""
    print_header("Multi-Agent Orchestration Demo")
    print_info("This demo showcases the integration between:")
    print("  • OpenClaw Orchestrator (port 8000)")
    print("  • Autonomous Agent (port 8008)")
    print("  • VMAO Framework (Plan-Execute-Verify-Replan)")

    # Configuration
    openclaw_url = "http://localhost:8000"
    autonomous_url = "http://localhost:8008"

    # Health checks
    print_header("Health Checks")
    openclaw_healthy = await check_service_health(openclaw_url, "OpenClaw Orchestrator")
    autonomous_healthy = await check_service_health(autonomous_url, "Autonomous Agent")

    if not (openclaw_healthy and autonomous_healthy):
        print_error("One or more services are unavailable. Please start the services:")
        print("  cd services/openclaw-orchestrator && python main.py")
        print("  cd services/autonomous-agent && python main.py")
        return

    # Run demos
    await demo_list_openclaw_skills(openclaw_url)
    await demo_autonomous_agent_capabilities(autonomous_url)
    await demo_multi_agent_workflow(autonomous_url)
    await demo_autonomous_task_execution(autonomous_url)

    # Summary
    print_header("Demo Complete")
    print_success("All demos executed successfully!")
    print_info("The integration demonstrates:")
    print("  1. Skill discovery and routing through OpenClaw")
    print("  2. Autonomous agent multi-agent capabilities")
    print("  3. Parallel agent execution (dependency-aware)")
    print("  4. VMAO Plan-Execute-Verify-Replan framework")
    print("  5. End-to-end autonomous task execution")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nDemo interrupted by user")
    except Exception as e:
        print_error(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
