#!/usr/bin/env python3
"""
Enhanced test runner for CI/CD integration
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


class EnhancedTestRunner:
    """Enhanced test runner for CI/CD"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {}
        
    def run_command(self, command, description=""):
        """Run a shell command and capture results"""
        print(f"\n🔄 {description}")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr and result.returncode != 0:
                print("STDERR:", result.stderr)
                
            self.results[description] = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running command: {e}")
            self.results[description] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_smoke_tests(self):
        """Run smoke tests"""
        smoke_code = '''
import sys
sys.path.append(".")
from core.amazon_fees import AmazonFeesCalculator
from core.roi_calculator import ROICalculator
from utils.config import Config

print("🔥 Smoke Tests...")
config = Config()
config.set_vat_rate(20.0)
config.set_apply_vat_on_cost(True)
assert config.get_vat_rate() == 20.0
fees_calc = AmazonFeesCalculator("france", config)
fees = fees_calc.calculate_fees(100.0, 0.5, "default")
assert fees > 0
roi_calc = ROICalculator(config)
result = roi_calc.calculate_roi(50.0, 100.0, 15.0)
assert result["cost_price"] == 60.0
print("✅ All smoke tests passed!")
'''
        return self.run_command(
            f'python -c "{smoke_code}"',
            "Smoke Tests"
        )
    
    def run_all_tests(self):
        """Run all test types"""
        success = True
        
        # Smoke tests
        if not self.run_smoke_tests():
            success = False
            
        # Unit tests
        if not self.run_command("python -m pytest tests/ -v", "Unit Tests"):
            success = False
            
        # Integration tests  
        if not self.run_command("python -m pytest tests/test_vat_integration.py -v", "Integration Tests"):
            success = False
            
        return success
    
    def generate_report(self):
        """Generate summary report"""
        print("\n" + "="*80)
        print("🎯 TEST SUMMARY")
        print("="*80)
        
        passed = 0
        total = 0
        
        for test_name, result in self.results.items():
            total += 1
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"{test_name:.<50} {status}")
            if result['success']:
                passed += 1
        
        print(f"\nOverall Result: {passed}/{total} tests passed")
        return passed == total


def main():
    runner = EnhancedTestRunner()
    
    print("🚀 AMZSCAN Enhanced Test Suite")
    print("="*80)
    
    success = runner.run_all_tests()
    overall_success = runner.generate_report()
    
    sys.exit(0 if success and overall_success else 1)


if __name__ == "__main__":
    main()
