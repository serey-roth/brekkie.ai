#!/usr/bin/env python3
"""
End-to-End Test Runner for Food Agent Chat Flow

This script runs comprehensive E2E tests that test the complete chat flow
including authentication, threads, messages, and AI interactions.

Usage:
    python run_e2e_tests.py [--with-server] [--mock-ai]

Options:
    --with-server    Run tests with a real server (requires server to be running)
    --mock-ai        Use mocked AI responses (faster, no external API calls)
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_unit_tests():
    """Run the unit tests first to ensure everything is working"""
    print("🧪 Running unit tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"])

    if result.returncode != 0:
        print("❌ Unit tests failed!")
        return False

    print("✅ Unit tests passed!")
    return True


def run_auth_e2e_tests():
    """Run authentication E2E tests"""
    print("🔐 Running authentication E2E tests...")

    auth_tests = [
        "tests/e2e/test_signup.py",
        "tests/e2e/test_login.py",
        "tests/e2e/test_logout.py",
        "tests/e2e/test_ensure_access_token.py",
    ]

    for test_file in auth_tests:
        print(f"  📝 Running {test_file}...")
        result = subprocess.run([sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"])

        if result.returncode != 0:
            print(f"❌ {test_file} failed!")
            return False

    print("✅ Authentication E2E tests passed!")
    return True


def run_threads_e2e_tests():
    """Run threads E2E tests"""
    print("🧵 Running threads E2E tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/test_threads.py", "-v", "--tb=short"]
    )

    if result.returncode != 0:
        print("❌ Threads E2E tests failed!")
        return False

    print("✅ Threads E2E tests passed!")
    return True


def run_all_e2e_tests():
    """Run all E2E tests"""
    print("🌐 Running all E2E tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"])

    if result.returncode != 0:
        print("❌ E2E tests failed!")
        return False

    print("✅ All E2E tests passed!")
    return True


def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting server...")
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(5)
    return server_process


def check_server_health():
    """Check if the server is healthy"""
    try:
        import requests

        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def run_e2e_tests_with_server():
    """Run E2E tests with a real server"""
    print("🌐 Running E2E tests with real server...")

    # Check if server is already running
    if check_server_health():
        print("✅ Server is already running!")
        server_process = None
    else:
        server_process = start_server()
        time.sleep(3)

        if not check_server_health():
            print("❌ Failed to start server!")
            if server_process:
                server_process.terminate()
            return False

    try:
        # Run all E2E tests with server
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"])

        if result.returncode != 0:
            print("❌ E2E tests with server failed!")
            return False

        print("✅ E2E tests with server passed!")
        return True

    finally:
        if server_process:
            print("🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()


def run_coverage():
    """Run tests with coverage"""
    print("📊 Running tests with coverage...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "tests/",
        ],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def run_real_chat_flow_tests():
    """Run real chat flow E2E tests with WebSocket and AI integration"""
    print("🤖 Running real chat flow E2E tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/test_real_chat_flow.py", "-v", "--tb=short"]
    )

    if result.returncode != 0:
        print("❌ Real chat flow E2E tests failed!")
        return False

    print("✅ Real chat flow E2E tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run E2E tests for Food Agent")
    parser.add_argument("--with-server", action="store_true", help="Run tests with a real server")
    parser.add_argument("--mock-ai", action="store_true", help="Use mocked AI responses")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--all", action="store_true", help="Run all tests including server tests")
    parser.add_argument("--auth-only", action="store_true", help="Run only authentication tests")
    parser.add_argument("--threads-only", action="store_true", help="Run only threads tests")
    parser.add_argument("--signup-only", action="store_true", help="Run only signup tests")
    parser.add_argument("--login-only", action="store_true", help="Run only login tests")
    parser.add_argument("--logout-only", action="store_true", help="Run only logout tests")
    parser.add_argument(
        "--access-token-only", action="store_true", help="Run only access token tests"
    )
    parser.add_argument(
        "--chat-flow-only", action="store_true", help="Run only real chat flow tests"
    )

    args = parser.parse_args()

    print("🍽️  Food Agent E2E Test Runner")
    print("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent
    if backend_dir.name != "backend":
        print("❌ This script should be run from the backend directory")
        sys.exit(1)

    success = True

    # Run unit tests first
    if not run_unit_tests():
        success = False

    # Run specific test categories based on arguments
    if args.signup_only:
        print("📝 Running signup tests only...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/e2e/test_signup.py", "-v", "--tb=short"]
        )
        if result.returncode != 0:
            print("❌ Signup tests failed!")
            success = False
    elif args.login_only:
        print("🔑 Running login tests only...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/e2e/test_login.py", "-v", "--tb=short"]
        )
        if result.returncode != 0:
            print("❌ Login tests failed!")
            success = False
    elif args.logout_only:
        print("🚪 Running logout tests only...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/e2e/test_logout.py", "-v", "--tb=short"]
        )
        if result.returncode != 0:
            print("❌ Logout tests failed!")
            success = False
    elif args.access_token_only:
        print("🎫 Running access token tests only...")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/e2e/test_ensure_access_token.py",
                "-v",
                "--tb=short",
            ]
        )
        if result.returncode != 0:
            print("❌ Access token tests failed!")
            success = False
    elif args.chat_flow_only:
        if not run_real_chat_flow_tests():
            success = False
    elif args.auth_only:
        if not run_auth_e2e_tests():
            success = False
    elif args.threads_only:
        if not run_threads_e2e_tests():
            success = False
    elif args.with_server or args.all:
        if not run_e2e_tests_with_server():
            success = False
    else:
        # Run all E2E tests by default
        if not run_all_e2e_tests():
            success = False

    # Run coverage if requested
    if args.coverage:
        if not run_coverage():
            success = False

    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
