from prometheus_client import Counter, Histogram, Info

request_count = Counter('orchestrator_requests_total', 'Total requests', ['skill', 'status'])
request_duration = Histogram('orchestrator_request_duration_seconds', 'Request duration', ['skill'])

service_info = Info('orchestrator', 'Orchestrator info')

def init_service_info(service_name: str, version: str = "1.0.0"):
    service_info.info({'name': service_name, 'version': version})

def record_request(skill: str, status: int, duration: float):
    request_count.labels(skill=skill, status=status).inc()
    request_duration.labels(skill=skill).observe(duration)
