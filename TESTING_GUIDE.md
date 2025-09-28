# Testing Guide

## Overview

The AMZSCAN project includes comprehensive testing infrastructure to ensure code quality and reliability.

## Quick Start

### Running All Tests
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Install test dependencies
pip install -r requirements.txt

# Run all tests
python test_runner_enhanced.py
```

### Running Specific Test Categories
```bash
# Smoke tests (quick validation)
python test_runner_enhanced.py --smoke

# Unit tests only
pytest tests/ -v -m "not integration"

# Integration tests only
pytest tests/test_vat_integration.py -v

# With coverage report
pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### 1. Smoke Tests
Quick validation of core functionality:
- Configuration system
- Fee calculations
- ROI calculations
- VAT integration

### 2. Unit Tests
Individual component testing:
- `test_config.py` - Configuration management
- `test_amazon_fees.py` - Fee calculation engine
- `test_roi_calculator.py` - ROI calculation logic
- `test_keepa_api.py` - API integration

### 3. Integration Tests
End-to-end workflow validation:
- `test_vat_integration.py` - Complete VAT functionality
- Cross-component interaction testing
- Configuration persistence validation

### 4. Validation Tests
Real-world data verification:
- `test_france_domain.py` - Domain configuration
- `test_real_data_alignment.py` - Keepa data alignment
- `test_buybox_price.py` - Price extraction accuracy

## Coverage Requirements

- **Minimum threshold:** 70%
- **Tracked modules:** `core/`, `utils/`, `gui/`
- **Reports:** HTML, XML, terminal formats

View coverage report: `htmlcov/index.html`

## Continuous Integration

### GitHub Actions
- **Automated testing** on pull requests
- **Multi-Python version** support (3.9-3.12)
- **Code quality checks** (Black, flake8, pylint)
- **Security scanning** (Bandit, Safety)
- **Build verification** (PyInstaller)

### Local Pre-commit Hooks
Install pre-commit hooks to run tests before commits:
```bash
pip install pre-commit
pre-commit install
```

## Test Configuration

### pytest.ini
Controls test discovery, coverage settings, and output formatting.

### Key Settings
- Test discovery patterns
- Coverage thresholds
- Marker definitions
- Warning filters

## Writing Tests

### Unit Test Example
```python
class TestVATCalculations(unittest.TestCase):
    def test_vat_application(self):
        config = Config()
        config.set_vat_rate(20.0)
        config.set_apply_vat_on_cost(True)
        
        calc = ROICalculator(config)
        result = calc.calculate_roi(100.0, 200.0, 30.0)
        
        # VAT should increase cost from 100 to 120
        self.assertEqual(result['cost_price'], 120.0)
```

### Integration Test Example
```python
def test_end_to_end_vat_workflow(self):
    # Configure VAT settings
    config = Config()
    config.set_vat_rate(20.0)
    config.set_apply_vat_on_cost(True)
    
    # Initialize calculators
    fees_calc = AmazonFeesCalculator('france', config)
    roi_calc = ROICalculator(config)
    
    # Test complete workflow
    fees = fees_calc.calculate_fees(100.0, 0.5, 'default')
    result = roi_calc.calculate_roi(50.0, 100.0, fees)
    
    # Verify VAT was applied correctly
    self.assertEqual(result['cost_price'], 60.0)
```

## Troubleshooting

### Common Issues

**ImportError in tests:**
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:."
# Or run from project root
cd /path/to/project
python -m pytest tests/
```

**GUI tests failing:**
```bash
# Install display dependencies
sudo apt-get install xvfb  # Ubuntu
pip install pytest-xvfb

# Run with virtual display
xvfb-run python -m pytest tests/
```

**Coverage too low:**
- Add tests for uncovered code paths
- Check `htmlcov/index.html` for specific lines
- Consider excluding non-testable code

### Getting Help

1. **Check test logs:** Run with `-v` flag for detailed output
2. **Review coverage:** Open `htmlcov/index.html` 
3. **Run individual tests:** `pytest tests/test_specific.py::TestClass::test_method -v`
4. **Check CI logs:** View GitHub Actions logs for remote failures

## Best Practices

1. **Write tests first** (TDD approach)
2. **Test edge cases** and error conditions
3. **Use descriptive test names** that explain intent
4. **Keep tests independent** - no shared state
5. **Mock external dependencies** appropriately
6. **Maintain test data** separate from test logic
7. **Document complex test scenarios**

## Test Markers

Use pytest markers to categorize tests:
```python
@pytest.mark.integration
def test_full_workflow():
    pass

@pytest.mark.slow
def test_comprehensive_analysis():
    pass

@pytest.mark.vat
def test_vat_calculation():
    pass
```

Run specific markers:
```bash
pytest -m integration  # Integration tests only
pytest -m "not slow"   # Exclude slow tests
pytest -m vat          # VAT-related tests only
```
