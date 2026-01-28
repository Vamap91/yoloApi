#!/usr/bin/env python3
"""
Test script for YOLO Damage Detection API v2.0
Validates annotated_image_base64, summary, and complete JSON contract
"""

import requests
import sys
import base64
import json
from pathlib import Path
from io import BytesIO
from PIL import Image

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"


def test_health():
    """Test health endpoint"""
    print("\n" + "=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert result.get("status") == "ok", "Status should be 'ok'"
        
        print("✓ PASSED: Health check working correctly\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_warmup():
    """Test warmup endpoint"""
    print("=" * 70)
    print("TEST 2: Warmup Endpoint")
    print("=" * 70)
    
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.post(f"{API_URL}/warmup", headers=headers)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert result.get("status") == "warmup_completed", "Warmup should complete"
        
        print("✓ PASSED: Warmup endpoint working correctly\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_damage_detection(image_path):
    """Test damage detection endpoint with full contract validation"""
    print("=" * 70)
    print("TEST 3: Damage Detection with Full Contract Validation")
    print("=" * 70)
    
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
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        
        # Validate contract
        print("\n--- Validating JSON Contract ---")
        
        # 1. Check request_id
        assert "request_id" in result, "Missing 'request_id'"
        print(f"✓ request_id: {result['request_id']}")
        
        # 2. Check model_version
        assert "model_version" in result, "Missing 'model_version'"
        print(f"✓ model_version: {result['model_version']}")
        
        # 3. Check image dimensions
        assert "image" in result, "Missing 'image'"
        assert "width" in result["image"], "Missing 'image.width'"
        assert "height" in result["image"], "Missing 'image.height'"
        print(f"✓ image dimensions: {result['image']['width']}x{result['image']['height']}")
        
        # 4. Check summary
        assert "summary" in result, "Missing 'summary'"
        summary = result["summary"]
        
        print("\n--- Validating Summary ---")
        assert "total_damages" in summary, "Missing 'summary.total_damages'"
        print(f"✓ total_damages: {summary['total_damages']}")
        
        assert "by_type" in summary, "Missing 'summary.by_type'"
        print(f"✓ by_type: {summary['by_type']}")
        
        assert "by_severity" in summary, "Missing 'summary.by_severity'"
        print(f"✓ by_severity: {summary['by_severity']}")
        
        assert "by_area_affected" in summary, "Missing 'summary.by_area_affected'"
        print(f"✓ by_area_affected: {summary['by_area_affected']}")
        
        assert "estimated_total_cost_range" in summary, "Missing 'summary.estimated_total_cost_range'"
        print(f"✓ estimated_total_cost_range: {summary['estimated_total_cost_range']}")
        
        # 5. Check detections array
        assert "detections" in result, "Missing 'detections'"
        detections = result["detections"]
        print(f"\n--- Validating Detections ({len(detections)} found) ---")
        
        if len(detections) > 0:
            # Validate first detection
            det = detections[0]
            
            assert "id" in det, "Missing detection 'id'"
            print(f"✓ detection.id: {det['id']}")
            
            assert "class" in det, "Missing detection 'class'"
            print(f"✓ detection.class: {det['class']}")
            
            assert "confidence" in det, "Missing detection 'confidence'"
            assert 0.0 <= det['confidence'] <= 1.0, "Confidence out of range"
            print(f"✓ detection.confidence: {det['confidence']:.2%}")
            
            assert "bbox" in det, "Missing detection 'bbox'"
            assert "x1" in det["bbox"], "Missing bbox.x1"
            assert "y1" in det["bbox"], "Missing bbox.y1"
            assert "x2" in det["bbox"], "Missing bbox.x2"
            assert "y2" in det["bbox"], "Missing bbox.y2"
            print(f"✓ detection.bbox: ({det['bbox']['x1']}, {det['bbox']['y1']}, {det['bbox']['x2']}, {det['bbox']['y2']})")
            
            assert "severity" in det, "Missing detection 'severity'"
            assert det['severity'] in ["Leve", "Moderado", "Severo"], f"Invalid severity: {det['severity']}"
            print(f"✓ detection.severity: {det['severity']}")
            
            assert "area_affected" in det, "Missing detection 'area_affected'"
            print(f"✓ detection.area_affected: {det['area_affected']}")
            
            assert "estimated_cost_range" in det, "Missing detection 'estimated_cost_range'"
            print(f"✓ detection.estimated_cost_range: {det['estimated_cost_range']}")
        
        # 6. Check annotated_image_base64
        print("\n--- Validating Annotated Image ---")
        assert "annotated_image_base64" in result, "Missing 'annotated_image_base64'"
        
        b64_str = result["annotated_image_base64"]
        assert isinstance(b64_str, str), "annotated_image_base64 should be string"
        assert len(b64_str) > 0, "annotated_image_base64 is empty"
        
        # Validate base64 encoding
        try:
            image_data = base64.b64decode(b64_str)
            print(f"✓ annotated_image_base64: Valid PNG ({len(image_data)} bytes)")
            
            # Save annotated image
            with open("/tmp/annotated_test.png", "wb") as f:
                f.write(image_data)
            print(f"✓ Annotated image saved to /tmp/annotated_test.png")
            
            # Verify it's a valid PNG
            img = Image.open(BytesIO(image_data))
            print(f"✓ PNG validation: {img.format} ({img.size[0]}x{img.size[1]})")
        except Exception as e:
            print(f"✗ Failed to decode base64 or validate PNG: {e}")
            return False
        
        # 7. Check timestamp
        assert "timestamp" in result, "Missing 'timestamp'"
        print(f"✓ timestamp: {result['timestamp']}")
        
        print("\n✓ PASSED: All contract validations passed!\n")
        return True
    
    except AssertionError as e:
        print(f"✗ FAILED: Contract validation error: {e}\n")
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_auth_failure():
    """Test authentication failure"""
    print("=" * 70)
    print("TEST 4: Authentication Failure (No API Key)")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_URL}/v1/models")
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PASSED: Correctly rejected request without API key\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_invalid_api_key():
    """Test invalid API key"""
    print("=" * 70)
    print("TEST 5: Invalid API Key")
    print("=" * 70)
    
    try:
        headers = {"X-API-Key": "invalid-key-12345"}
        response = requests.get(f"{API_URL}/v1/models", headers=headers)
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PASSED: Correctly rejected request with invalid API key\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_models_list():
    """Test models list endpoint"""
    print("=" * 70)
    print("TEST 6: List Models")
    print("=" * 70)
    
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{API_URL}/v1/models", headers=headers)
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        assert "models" in result, "Missing 'models'"
        
        models = result['models']
        print(f"Available models: {len(models)}")
        
        for model in models:
            print(f"  - {model['name']} ({model['version']})")
        
        print("✓ PASSED: Models list retrieved successfully\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def test_damage_classes():
    """Test damage classes endpoint"""
    print("=" * 70)
    print("TEST 7: List Damage Classes")
    print("=" * 70)
    
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{API_URL}/v1/damage-classes", headers=headers)
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        assert "damage_classes" in result, "Missing 'damage_classes'"
        
        classes = result['damage_classes']
        print(f"Available damage classes: {len(classes)}")
        
        for class_name, config in classes.items():
            print(f"  - {class_name}: {config['severity']} ({config['area_affected']})")
        
        print("✓ PASSED: Damage classes retrieved successfully\n")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False


def main():
    print("\n" + "=" * 70)
    print("YOLO DAMAGE DETECTION API v2.0 - TEST SUITE")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Warmup Endpoint", test_warmup()))
    results.append(("Authentication Failure", test_auth_failure()))
    results.append(("Invalid API Key", test_invalid_api_key()))
    results.append(("Models List", test_models_list()))
    results.append(("Damage Classes", test_damage_classes()))
    
    # Test damage detection if image is provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results.append(("Damage Detection", test_damage_detection(image_path)))
    else:
        print("=" * 70)
        print("TEST: Damage Detection")
        print("=" * 70)
        print("⊘ SKIPPED: No image provided")
        print("Usage: python test_api.py <image_path>\n")
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
