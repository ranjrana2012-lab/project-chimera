"""
Test suite for AlertManager configuration.

Tests follow TDD: Write failing test first, then implement.
"""
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ALERTMANAGER_CONFIG = REPO_ROOT / "platform/monitoring/config/alertmanager.yaml"
ALERTMANAGER_DEPLOYMENT = REPO_ROOT / "infrastructure/kubernetes/alertmanager/deployment.yaml"
ALERTMANAGER_SERVICE = REPO_ROOT / "infrastructure/kubernetes/alertmanager/service.yaml"


class TestAlertManagerConfig:
    """Test AlertManager configuration file."""

    def test_alertmanager_config_exists(self):
        """Test that alertmanager.yaml configuration file exists."""
        config_path = ALERTMANAGER_CONFIG
        assert config_path.exists(), f"AlertManager config file not found at {config_path}"

    def test_alertmanager_config_valid_yaml(self):
        """Test that alertmanager.yaml is valid YAML."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert config is not None, "Config file is empty or invalid"

    def test_alertmanager_global_config(self):
        """Test that global configuration has required fields."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'global' in config, "Missing 'global' section"
        assert 'resolve_timeout' in config['global'], "Missing 'resolve_timeout' in global config"
        assert 'slack_api_url' in config['global'], "Missing 'slack_api_url' in global config"

    def test_alertmanager_route_config(self):
        """Test that route configuration is properly set up."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'route' in config, "Missing 'route' section"
        route = config['route']

        # Check required route fields
        assert 'group_by' in route, "Missing 'group_by' in route"
        assert 'group_wait' in route, "Missing 'group_wait' in route"
        assert 'group_interval' in route, "Missing 'group_interval' in route"
        assert 'repeat_interval' in route, "Missing 'repeat_interval' in route"
        assert 'receiver' in route, "Missing 'receiver' in route"

        # Check values
        assert 'alertname' in route['group_by'], "'alertname' should be in group_by"
        assert route['receiver'] == 'default', "Default receiver should be 'default'"

    def test_alertmanager_receivers(self):
        """Test that receivers are properly configured."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'receivers' in config, "Missing 'receivers' section"
        receivers = config['receivers']

        # Check for required receivers
        receiver_names = [r['name'] for r in receivers]
        assert 'default' in receiver_names, "Missing 'default' receiver"
        assert 'critical-alerts' in receiver_names, "Missing 'critical-alerts' receiver"
        assert 'warning-alerts' in receiver_names, "Missing 'warning-alerts' receiver"

    def test_alertmanager_slack_configs(self):
        """Test that Slack configurations are present."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        receivers = config['receivers']

        for receiver in receivers:
            if receiver['name'] == 'critical-alerts':
                assert 'slack_configs' in receiver, "Missing slack_configs in critical-alerts"
                slack_config = receiver['slack_configs'][0]
                assert 'channel' in slack_config, "Missing channel in critical-alerts slack config"
                assert slack_config['channel'] == '#chimera-critical', "Critical alerts should go to #chimera-critical"
                assert slack_config.get('send_resolved') == True, "Critical alerts should send resolved notifications"

    def test_alertmanager_inhibit_rules(self):
        """Test that inhibit rules are configured."""
        config_path = ALERTMANAGER_CONFIG
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert 'inhibit_rules' in config, "Missing 'inhibit_rules' section"
        inhibit_rules = config['inhibit_rules']

        # Should have at least one rule to inhibit warnings when critical exists
        assert len(inhibit_rules) > 0, "Should have at least one inhibit rule"

        rule = inhibit_rules[0]
        assert 'source_match' in rule, "Inhibit rule missing source_match"
        assert 'target_match' in rule, "Inhibit rule missing target_match"


class TestAlertManagerKubernetesManifests:
    """Test AlertManager Kubernetes deployment manifests."""

    def test_deployment_exists(self):
        """Test that AlertManager deployment manifest exists."""
        deployment_path = ALERTMANAGER_DEPLOYMENT
        assert deployment_path.exists(), f"Deployment manifest not found at {deployment_path}"

    def test_service_exists(self):
        """Test that AlertManager service manifest exists."""
        service_path = ALERTMANAGER_SERVICE
        assert service_path.exists(), f"Service manifest not found at {service_path}"

    def test_deployment_valid_yaml(self):
        """Test that deployment.yaml is valid YAML."""
        deployment_path = ALERTMANAGER_DEPLOYMENT
        with open(deployment_path, 'r') as f:
            # Load all documents from multi-document YAML
            documents = list(yaml.safe_load_all(f))
        assert len(documents) == 3, "YAML should contain 3 documents (Deployment, PVC, Service)"
        assert documents[0] is not None, "First document (Deployment) should not be empty"

    def test_deployment_structure(self):
        """Test that deployment has correct structure."""
        deployment_path = ALERTMANAGER_DEPLOYMENT
        with open(deployment_path, 'r') as f:
            documents = list(yaml.safe_load_all(f))
        deployment = documents[0]  # First document is the Deployment

        assert deployment['kind'] == 'Deployment', "Should be a Deployment"
        assert deployment['metadata']['name'] == 'alertmanager', "Deployment name should be 'alertmanager'"
        assert deployment['metadata']['namespace'] == 'project-chimera', "Namespace should be 'project-chimera'"

        # Check spec
        spec = deployment['spec']
        assert spec['replicas'] == 1, "Should have 1 replica"
        assert spec['selector']['matchLabels']['app'] == 'alertmanager', "Selector should match app=alertmanager"

    def test_deployment_container_config(self):
        """Test that AlertManager container is properly configured."""
        deployment_path = ALERTMANAGER_DEPLOYMENT
        with open(deployment_path, 'r') as f:
            documents = list(yaml.safe_load_all(f))
        deployment = documents[0]  # First document is the Deployment

        container = deployment['spec']['template']['spec']['containers'][0]
        assert container['name'] == 'alertmanager', "Container name should be 'alertmanager'"
        assert 'prom/alertmanager:v0.26.0' in container['image'], "Should use prom/alertmanager:v0.26.0 image"

        # Check args
        assert '--config.file=/etc/alertmanager/alertmanager.yaml' in container['args'], "Missing config file arg"
        assert '--storage.path=/alertmanager' in container['args'], "Missing storage path arg"

        # Check ports
        ports = container['ports']
        assert any(p['containerPort'] == 9093 for p in ports), "Should expose port 9093"

        # Check resources
        resources = container['resources']
        assert 'requests' in resources, "Missing resource requests"
        assert 'limits' in resources, "Missing resource limits"

    def test_deployment_volumes(self):
        """Test that deployment has proper volume mounts."""
        deployment_path = ALERTMANAGER_DEPLOYMENT
        with open(deployment_path, 'r') as f:
            documents = list(yaml.safe_load_all(f))
        deployment = documents[0]  # First document is the Deployment

        volumes = deployment['spec']['template']['spec']['volumes']
        volume_names = [v['name'] for v in volumes]

        assert 'config' in volume_names, "Missing config volume"
        assert 'storage' in volume_names, "Missing storage volume"

        # Check config volume is a ConfigMap
        config_volume = next(v for v in volumes if v['name'] == 'config')
        assert 'configMap' in config_volume, "Config volume should be a ConfigMap"
        assert config_volume['configMap']['name'] == 'alertmanager-config', "ConfigMap name should be 'alertmanager-config'"

    def test_service_valid_yaml(self):
        """Test that service.yaml is valid YAML."""
        service_path = ALERTMANAGER_SERVICE
        with open(service_path, 'r') as f:
            service = yaml.safe_load(f)
        assert service is not None, "Service file is empty or invalid"

    def test_service_structure(self):
        """Test that service has correct structure."""
        service_path = ALERTMANAGER_SERVICE
        with open(service_path, 'r') as f:
            service = yaml.safe_load(f)

        assert service['kind'] == 'Service', "Should be a Service"
        assert service['metadata']['name'] == 'alertmanager', "Service name should be 'alertmanager'"
        assert service['metadata']['namespace'] == 'shared', "Namespace should be 'shared'"
        assert service['spec']['selector']['app'] == 'alertmanager', "Selector should match app=alertmanager"

    def test_service_ports(self):
        """Test that service exposes correct port."""
        service_path = ALERTMANAGER_SERVICE
        with open(service_path, 'r') as f:
            service = yaml.safe_load(f)

        ports = service['spec']['ports'][0]
        assert ports['port'] == 9093, "Service port should be 9093"
        assert ports['targetPort'] == 9093, "Target port should be 9093"

    def test_service_type(self):
        """Test that service is ClusterIP."""
        service_path = ALERTMANAGER_SERVICE
        with open(service_path, 'r') as f:
            service = yaml.safe_load(f)

        assert service['spec']['type'] == 'ClusterIP', "Service type should be ClusterIP"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
