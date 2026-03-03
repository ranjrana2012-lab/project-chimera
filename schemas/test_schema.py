#!/usr/bin/env python3
"""
Schema validation tests for scene configuration.

Tests that all example scene configurations conform to the schema.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Installing jsonschema...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    from jsonschema import validate, ValidationError


def load_json_file(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_scene_config(config: dict, schema: dict) -> bool:
    """
    Validate scene configuration against schema.

    Args:
        config: Scene configuration to validate
        schema: JSON schema

    Returns:
        True if valid, False otherwise
    """
    try:
        validate(instance=config, schema=schema)
        return True
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.message}")
        print(f"     Path: {'.'.join(str(p) for p in e.path)}")
        return False


def test_schema_validation():
    """Test all example scene configurations against the schema."""
    print("=" * 60)
    print("Scene Configuration Schema Validation")
    print("=" * 60)

    # Load schema
    schema_path = Path(__file__).parent / "scene-config.json"
    print(f"\n📋 Loading schema from: {schema_path}")
    schema = load_json_file(schema_path)
    print("✅ Schema loaded")

    # Find and validate all example configs
    examples_dir = Path(__file__).parent / "examples"
    example_files = sorted(examples_dir.glob("*.json"))

    print(f"\n📁 Found {len(example_files)} example configuration(s)")
    print()

    results = []
    for example_file in example_files:
        print(f"Testing: {example_file.name}")
        try:
            config = load_json_file(example_file)
            is_valid = validate_scene_config(config, schema)
            results.append((example_file.name, is_valid))
            if is_valid:
                print(f"  ✅ Valid configuration")
            print()
        except Exception as e:
            print(f"  ❌ Error loading file: {e}")
            results.append((example_file.name, False))
            print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    total = len(results)
    passed = sum(1 for _, valid in results if valid)
    failed = total - passed

    print(f"Total: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")

    if failed > 0:
        print("\nFailed configurations:")
        for name, valid in results:
            if not valid:
                print(f"  - {name}")
        return False
    else:
        print("\n✅ All scene configurations are valid!")
        return True


def test_schema_properties():
    """Test that schema has all required properties."""
    print("\n" + "=" * 60)
    print("Schema Structure Tests")
    print("=" * 60)

    schema_path = Path(__file__).parent / "scene-config.json"
    schema = load_json_file(schema_path)

    required_properties = [
        "scene_id",
        "name",
        "version",
        "scene_type",
        "agents",
        "timing"
    ]

    missing = []
    for prop in required_properties:
        if prop not in schema.get("required", []):
            missing.append(prop)

    if missing:
        print(f"❌ Missing required properties: {missing}")
        return False
    else:
        print(f"✅ All {len(required_properties)} required properties present")

    # Check agent configurations
    required_agents = ["scenespeak", "sentiment", "captioning"]
    agents_required = schema["properties"]["agents"].get("required", [])

    for agent in required_agents:
        if agent not in agents_required:
            print(f"⚠️  Warning: {agent} not in required agents")
        else:
            print(f"✅ Agent {agent} is required")

    # Check scene types
    scene_types = schema["properties"]["scene_type"].get("enum", [])
    print(f"\n✅ Scene types defined: {', '.join(scene_types)}")

    # Check transition types
    transition_def = schema.get("definitions", {}).get("transitionConfig", {})
    transition_types = transition_def.get("properties", {}).get("type", {}).get("enum", [])
    print(f"✅ Transition types defined: {', '.join(transition_types)}")

    return True


def main():
    """Run all schema tests."""
    print("\n🧪 Running Scene Configuration Schema Tests\n")

    # Run tests
    schema_valid = test_schema_properties()
    examples_valid = test_schema_validation()

    # Exit with appropriate code
    if schema_valid and examples_valid:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
