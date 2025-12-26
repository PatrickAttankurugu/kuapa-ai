#!/usr/bin/env python3
"""
Kuapa AI - Pre-flight System Check
Verifies all dependencies and configurations before starting the application
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text: str):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text: str):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text: str):
    print(f"{BLUE}ℹ{RESET} {text}")

class DependencyChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check_python_version(self) -> bool:
        """Check if Python version is 3.10+"""
        print_info("Checking Python version...")
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
            self.checks_passed += 1
            return True
        else:
            print_error(f"Python {version.major}.{version.minor} found. Need Python 3.10+")
            self.errors.append("Python version must be 3.10 or higher")
            self.checks_failed += 1
            return False

    def check_python_package(self, package: str, import_name: str = None) -> bool:
        """Check if a Python package is installed"""
        import_name = import_name or package
        try:
            __import__(import_name)
            print_success(f"{package} is installed")
            self.checks_passed += 1
            return True
        except ImportError:
            print_error(f"{package} is NOT installed")
            self.errors.append(f"Install {package}: pip install {package}")
            self.checks_failed += 1
            return False

    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed"""
        print_info("Checking FFmpeg...")
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print_success(f"FFmpeg is installed: {version_line}")
                self.checks_passed += 1
                return True
        except FileNotFoundError:
            print_error("FFmpeg is NOT installed")
            self.errors.append("Install FFmpeg - See: https://ffmpeg.org/download.html")
            self.checks_failed += 1
            return False
        except Exception as e:
            print_error(f"Error checking FFmpeg: {e}")
            self.errors.append("FFmpeg check failed")
            self.checks_failed += 1
            return False

    def check_node_version(self) -> bool:
        """Check if Node.js is installed"""
        print_info("Checking Node.js...")
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                major_version = int(version.replace('v', '').split('.')[0])
                if major_version >= 18:
                    print_success(f"Node.js {version} ✓")
                    self.checks_passed += 1
                    return True
                else:
                    print_error(f"Node.js {version} found. Need v18+")
                    self.errors.append("Upgrade Node.js to version 18 or higher")
                    self.checks_failed += 1
                    return False
        except FileNotFoundError:
            print_error("Node.js is NOT installed")
            self.errors.append("Install Node.js 18+ - See: https://nodejs.org/")
            self.checks_failed += 1
            return False
        except Exception as e:
            print_error(f"Error checking Node.js: {e}")
            self.checks_failed += 1
            return False

    def check_env_file(self) -> bool:
        """Check if .env file exists and has required variables"""
        print_info("Checking .env configuration...")
        env_file = Path(".env")
        
        if not env_file.exists():
            print_error(".env file NOT found")
            self.errors.append("Create .env file: cp .env.example .env")
            self.checks_failed += 1
            return False
        
        # Read .env file
        env_content = env_file.read_text()
        
        # Check for GEMINI_API_KEY
        if "GEMINI_API_KEY=" in env_content:
            # Extract the key value
            for line in env_content.split('\n'):
                if line.startswith('GEMINI_API_KEY='):
                    key_value = line.split('=', 1)[1].strip()
                    if key_value and key_value != 'your_gemini_api_key_here':
                        print_success("GEMINI_API_KEY is configured")
                        self.checks_passed += 1
                        return True
                    else:
                        print_error("GEMINI_API_KEY is empty or not set")
                        self.errors.append("Set your Gemini API key in .env file")
                        self.checks_failed += 1
                        return False
        else:
            print_error("GEMINI_API_KEY not found in .env")
            self.errors.append("Add GEMINI_API_KEY to .env file")
            self.checks_failed += 1
            return False

    def check_whatsapp_node_modules(self) -> bool:
        """Check if WhatsApp bot dependencies are installed"""
        print_info("Checking WhatsApp bot dependencies...")
        node_modules = Path("whatsapp-bot/node_modules")
        
        if node_modules.exists():
            # Check for specific packages
            required_packages = ['whatsapp-web.js', 'axios', 'form-data']
            all_found = True
            
            for package in required_packages:
                package_path = node_modules / package
                if package_path.exists():
                    print_success(f"  {package} ✓")
                else:
                    print_error(f"  {package} NOT found")
                    all_found = False
            
            if all_found:
                self.checks_passed += 1
                return True
            else:
                self.warnings.append("Run: cd whatsapp-bot && npm install")
                self.checks_failed += 1
                return False
        else:
            print_error("node_modules not found")
            self.errors.append("Install WhatsApp bot dependencies: cd whatsapp-bot && npm install")
            self.checks_failed += 1
            return False

    def check_data_files(self) -> bool:
        """Check if data files exist"""
        print_info("Checking data files...")
        data_file = Path("data/agriculture_qna_expanded.csv")
        
        if data_file.exists():
            print_success(f"Knowledge base found: {data_file}")
            self.checks_passed += 1
            return True
        else:
            print_warning(f"Knowledge base not found: {data_file}")
            self.warnings.append("Knowledge base file missing - app may have limited responses")
            return False

    def run_all_checks(self):
        """Run all dependency checks"""
        print_header("KUAPA AI - SYSTEM READINESS CHECK")
        
        print_info("Starting pre-flight checks...\n")
        
        # System requirements
        print(f"\n{BLUE}[1/7] System Requirements{RESET}")
        self.check_python_version()
        self.check_node_version()
        self.check_ffmpeg()
        
        # Python packages
        print(f"\n{BLUE}[2/7] Python Dependencies{RESET}")
        self.check_python_package("fastapi")
        self.check_python_package("uvicorn")
        self.check_python_package("pydub")
        self.check_python_package("google-generativeai", "google.generativeai")
        self.check_python_package("pandas")
        self.check_python_package("scikit-learn", "sklearn")
        
        # Configuration
        print(f"\n{BLUE}[3/7] Configuration{RESET}")
        self.check_env_file()
        
        # Node.js dependencies
        print(f"\n{BLUE}[4/7] WhatsApp Bot{RESET}")
        self.check_whatsapp_node_modules()
        
        # Data files
        print(f"\n{BLUE}[5/7] Data Files{RESET}")
        self.check_data_files()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print check summary"""
        print_header("SUMMARY")
        
        total_checks = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        print(f"Total Checks: {total_checks}")
        print(f"{GREEN}Passed: {self.checks_passed}{RESET}")
        print(f"{RED}Failed: {self.checks_failed}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")
        
        if self.errors:
            print(f"\n{RED}CRITICAL ISSUES (Must Fix):{RESET}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}WARNINGS:{RESET}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "=" * 60)
        
        if self.checks_failed == 0:
            print(f"\n{GREEN}✓ ALL CHECKS PASSED - READY TO RUN!{RESET}\n")
            print("Start the application with:")
            print(f"  {BLUE}Terminal 1:{RESET} python -m uvicorn api.main:app --reload")
            print(f"  {BLUE}Terminal 2:{RESET} cd whatsapp-bot && npm start")
            return 0
        else:
            print(f"\n{RED}✗ CHECKS FAILED - NOT READY{RESET}\n")
            print("Fix the issues above before running the application.")
            return 1

def main():
    checker = DependencyChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
