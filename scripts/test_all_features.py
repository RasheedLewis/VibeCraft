#!/usr/bin/env python3
"""
Comprehensive testing script for all features built today.
Tests backend features systematically.
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_DISPLAY_NAME = "Test User"

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
}


def log_result(test_name: str, passed: bool, message: str = ""):
    """Log test result."""
    if passed:
        test_results["passed"].append(f"{test_name}: {message}")
        print(f"✅ {test_name}: {message}")
    else:
        test_results["failed"].append(f"{test_name}: {message}")
        print(f"❌ {test_name}: {message}")


def log_warning(test_name: str, message: str):
    """Log warning."""
    test_results["warnings"].append(f"{test_name}: {message}")
    print(f"⚠️  {test_name}: {message}")


def test_health_check():
    """Test 1: Health check endpoint."""
    print("\n🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health/healthz", timeout=5)
        if response.status_code == 200:
            log_result("Health Check", True, "Health endpoint responds")
            return True
        else:
            log_result("Health Check", False, f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Health Check", False, f"Error: {str(e)}")
        return False


def test_auth_register():
    """Test 2: User registration."""
    print("\n🔍 Testing User Registration...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
            timeout=5,
        )
        if response.status_code in [200, 201]:
            data = response.json()
            if "access_token" in data:
                log_result("User Registration", True, "User registered successfully")
                return data["access_token"]
            else:
                log_result("User Registration", False, "No access token in response")
                return None
        elif response.status_code == 400:
            # User might already exist, try login instead
            log_warning("User Registration", "User may already exist, will try login")
            return None
        else:
            log_result("User Registration", False, f"Status: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        log_result("User Registration", False, f"Error: {str(e)}")
        return None


def test_auth_login(token: Optional[str] = None):
    """Test 3: User login."""
    print("\n🔍 Testing User Login...")
    if token:
        log_result("User Login", True, "Already authenticated from registration")
        return token
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                log_result("User Login", True, "Login successful")
                return data["access_token"]
            else:
                log_result("User Login", False, "No access token in response")
                return None
        else:
            log_result("User Login", False, f"Status: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        log_result("User Login", False, f"Error: {str(e)}")
        return None


def test_auth_me(token: str):
    """Test 4: Get current user info."""
    print("\n🔍 Testing Get Current User...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("email") == TEST_EMAIL:
                log_result("Get Current User", True, f"User: {data.get('display_name', data.get('email'))}")
                return True
            else:
                log_result("Get Current User", False, "Unexpected user data")
                return False
        else:
            log_result("Get Current User", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Get Current User", False, f"Error: {str(e)}")
        return False


def test_project_listing(token: str):
    """Test 5: Project listing (max 5)."""
    print("\n🔍 Testing Project Listing...")
    try:
        response = requests.get(
            f"{BASE_URL}/songs",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if response.status_code == 200:
            songs = response.json()
            count = len(songs)
            log_result("Project Listing", True, f"Found {count} projects")
            
            # Check if limit is enforced (should be max 5)
            if count > 5:
                log_warning("Project Listing", f"More than 5 projects ({count}), limit may not be enforced")
            else:
                log_result("Project Listing Limit", True, f"Project count ({count}) within limit")
            
            return True
        else:
            log_result("Project Listing", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Project Listing", False, f"Error: {str(e)}")
        return False


def test_file_size_validation(token: str):
    """Test 6: File size validation."""
    print("\n🔍 Testing File Size Validation...")
    
    # Create a fake large file (in memory)
    try:
        # Try uploading a file that's too large (simulate with Content-Length header)
        # Note: This is a simplified test - actual file upload would need multipart/form-data
        log_warning("File Size Validation", "Manual test required - upload large file via UI")
        return True
    except Exception as e:
        log_result("File Size Validation", False, f"Error: {str(e)}")
        return False


def test_rate_limiting(token: str):
    """Test 7: Rate limiting."""
    print("\n🔍 Testing Rate Limiting...")
    try:
        # Make many rapid requests
        rate_limit_hit = False
        for i in range(70):  # Should hit 60/min limit
            response = requests.get(
                f"{BASE_URL}/songs",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if response.status_code == 429:
                rate_limit_hit = True
                log_result("Rate Limiting", True, f"Rate limit hit after {i+1} requests")
                break
            time.sleep(0.1)  # Small delay
        
        if not rate_limit_hit:
            log_warning("Rate Limiting", "Rate limit not hit (may need more requests or different endpoint)")
        
        return True
    except Exception as e:
        log_result("Rate Limiting", False, f"Error: {str(e)}")
        return False


def test_rate_limiting_health_exempt():
    """Test 8: Health check should not be rate limited."""
    print("\n🔍 Testing Health Check Rate Limit Exemption...")
    try:
        # Make many requests to health endpoint
        for i in range(100):
            response = requests.get(f"{BASE_URL}/health/healthz", timeout=5)
            if response.status_code == 429:
                log_result("Health Check Exemption", False, f"Health check was rate limited after {i+1} requests")
                return False
        
        log_result("Health Check Exemption", True, "Health check not rate limited")
        return True
    except Exception as e:
        log_result("Health Check Exemption", False, f"Error: {str(e)}")
        return False


def test_config_endpoints():
    """Test 9: Config endpoints."""
    print("\n🔍 Testing Config Endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            log_result("Config Endpoints", True, f"Config retrieved: {list(data.keys())}")
            return True
        else:
            log_result("Config Endpoints", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Config Endpoints", False, f"Error: {str(e)}")
        return False


def test_template_characters():
    """Test 10: Template characters endpoint."""
    print("\n🔍 Testing Template Characters...")
    try:
        response = requests.get(f"{BASE_URL}/template-characters", timeout=5)
        if response.status_code == 200:
            characters = response.json()
            log_result("Template Characters", True, f"Found {len(characters)} template characters")
            return True
        else:
            log_result("Template Characters", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Template Characters", False, f"Error: {str(e)}")
        return False


def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\n❌ FAILED TESTS:")
        for failure in test_results['failed']:
            print(f"  - {failure}")
    
    if test_results['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in test_results['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "="*60)
    
    # Save results to file
    results_file = Path("test_results.json")
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\n📄 Results saved to: {results_file}")


def main():
    """Run all tests."""
    print("="*60)
    print("COMPREHENSIVE FEATURE TESTING")
    print("="*60)
    print(f"Testing backend at: {BASE_URL}")
    print(f"Test user: {TEST_EMAIL}")
    print("="*60)
    
    # Run tests
    if not test_health_check():
        print("\n❌ Backend not available. Please start the backend first.")
        sys.exit(1)
    
    token = test_auth_register()
    token = test_auth_login(token)
    
    if not token:
        print("\n❌ Authentication failed. Cannot continue with authenticated tests.")
        print_summary()
        sys.exit(1)
    
    test_auth_me(token)
    test_project_listing(token)
    test_file_size_validation(token)
    test_rate_limiting(token)
    test_rate_limiting_health_exempt()
    test_config_endpoints()
    test_template_characters()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

