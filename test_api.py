#!/usr/bin/env python3
"""
Test script for YOLO Damage Detection API
"""

import requests
import sys
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"


def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✓ Health check passed\n")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")
        return False


def test_damage_detection(image_path):
    """Test damage detection endpoint"""
    print(f"Testing /v1/damage:detect endpoint with {image_path}...")
    
    if not Path(image_path).exists():
        print(f"✗ Image file not found: {image_path}\n")
        return False
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": f}
            headers = {"X-API-Key": API_KEY}
            response = requests.post(
                f"{API_URL}/v1/damage:detect",
                files=files,
                headers=headers
            )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Model Version: {result.get('model_version')}")
        print(f"Image Size: {result.get('image_width')}x{result.get('image_height')}")
        print(f"Detections: {len(result.get('detections', []))}")
        
        if result.get('detections'):
            for i, det in enumerate(result['detections'], 1):
                print(f"  {i}. {det['class']} - Confidence: {det['confidence']:.2%}, Severity: {det['severity']}")
        
        assert response.status_code == 200
        print("✓ Damage detection test passed\n")
        return True
    except Exception as e:
        print(f"✗ Damage detection test failed: {e}\n")
        return False


def test_models_list():
    """Test models list endpoint"""
    print("Testing /v1/models endpoint...")
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{API_URL}/v1/models", headers=headers)
        print(f"Status: {response.status_code}")
        result = response.json()
        models = result.get('models', [])
        print(f"Available models: {len(models)}")
        for model in models:
            print(f"  - {model['name']} ({model['version']})")
        
        assert response.status_code == 200
        print("✓ Models list test passed\n")
        return True
    except Exception as e:
        print(f"✗ Models list test failed: {e}\n")
        return False


def test_damage_classes():
    """Test damage classes endpoint"""
    print("Testing /v1/damage-classes endpoint...")
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{API_URL}/v1/damage-classes", headers=headers)
        print(f"Status: {response.status_code}")
        result = response.json()
        classes = result.get('damage_classes', {})
        print(f"Available damage classes: {len(classes)}")
        for class_name, config in classes.items():
            print(f"  - {class_name}: {config['severity']} ({config['area_affected']})")
        
        assert response.status_code == 200
        print("✓ Damage classes test passed\n")
        return True
    except Exception as e:
        print(f"✗ Damage classes test failed: {e}\n")
        return False


def test_auth_failure():
    """Test authentication failure"""
    print("Testing authentication failure (no API key)...")
    try:
        response = requests.get(f"{API_URL}/v1/models")
        print(f"Status: {response.status_code}")
        assert response.status_code == 401
        print("✓ Authentication failure test passed (correctly rejected)\n")
        return True
    except Exception as e:
        print(f"✗ Authentication test failed: {e}\n")
        return False


def main():
    print("=" * 60)
    print("YOLO Damage Detection API - Test Suite")
    print("=" * 60)
    print(f"API URL: {API_URL}\n")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Authentication", test_auth_failure()))
    results.append(("Models List", test_models_list()))
    results.append(("Damage Classes", test_damage_classes()))
    
    # Test damage detection if image is provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results.append(("Damage Detection", test_damage_detection(image_path)))
    else:
        print("Skipping damage detection test (no image provided)")
        print("Usage: python test_api.py <image_path>\n")
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
