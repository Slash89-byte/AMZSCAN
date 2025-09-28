"""
Test runner for the Amazon Profitability Analyzer
Run all unit tests with a simple command
"""

import unittest
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_all_tests():
    """Discover and run all tests"""
    print("=" * 60)
    print("Amazon Profitability Analyzer - Test Suite")
    print("=" * 60)
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFAILED TESTS:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}")
    print("=" * 60)
    
    return success

def run_specific_test(test_module):
    """Run a specific test module"""
    print(f"Running tests for: {test_module}")
    suite = unittest.TestLoader().loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test module
        test_module = sys.argv[1]
        success = run_specific_test(test_module)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
