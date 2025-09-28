# CI/CD Integration Setup

This document describes the continuous integration and deployment setup for the AMZSCAN project.

## Overview

The project now includes comprehensive CI/CD integration with:
- **Automated testing** on every pull request
- **Code quality checks** and linting
- **Coverage reporting** 
- **Multi-platform testing** (Ubuntu, Windows)
- **Security vulnerability scanning**
- **Automated build and packaging**

## GitHub Actions Workflows

### 1. Main CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Features:**
- **Multi-Python version testing** (3.9, 3.10, 3.11, 3.12)
- **Comprehensive test suite** (unit, integration, validation)
- **Code quality checks** (Black, isort, mypy, pylint, bandit)
- **Security scanning** with Safety
- **Automated executable building** with PyInstaller
- **Coverage reporting** with Codecov integration
- **Build artifact upload**

### 2. Pull Request Validation (`pr-validation.yml`)

**Triggers:**
- Pull requests to `main` branch
- Ready for review status

**Features:**
- **Full test validation** before merge
- **VAT functionality verification**
- **Coverage threshold enforcement** (70% minimum)
- **Automated PR status comments**
- **Security vulnerability scanning**
- **Dependabot auto-merge** for passing dependency updates

## Test Organization

### Test Structure
```
tests/
├── test_config.py           # Configuration system tests
├── test_amazon_fees.py      # Fee calculation tests
├── test_roi_calculator.py   # ROI calculation tests
├── test_vat_integration.py  # Comprehensive integration tests
└── __init__.py

# Root level validation tests
├── test_france_domain.py    # Domain configuration validation
├── test_real_data_alignment.py # Real data validation
├── test_buybox_price.py     # Price extraction tests
```

### Test Categories

**Unit Tests:**
- Configuration system validation
- Individual component functionality
- Error handling and edge cases

**Integration Tests:**
- End-to-end VAT workflow testing
- Multi-component interaction validation
- Configuration persistence testing
- Different VAT rate scenarios

**Validation Tests:**
- Real marketplace data alignment
- Domain configuration accuracy
- Buy Box price extraction validation

## Test Runners

### Enhanced Test Runner (`test_runner_enhanced.py`)
```bash
# Run all tests
python test_runner_enhanced.py

# Run specific test categories
python test_runner_enhanced.py --unit
python test_runner_enhanced.py --integration
python test_runner_enhanced.py --smoke
```

### Original Test Runner (`run_tests.py`)
```bash
# Run all tests with unittest
python run_tests.py

# Run specific test module
python run_tests.py test_config
```

### Pytest Integration
```bash
# Run with pytest (recommended)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run integration tests only
pytest tests/test_vat_integration.py -v
```

## Coverage Requirements

- **Minimum coverage threshold:** 70%
- **Coverage includes:** `core/`, `utils/`, `gui/` modules
- **Coverage reports:** HTML, XML, and terminal formats
- **Branch coverage:** Enabled for comprehensive testing

## Code Quality Standards

### Linting Tools
- **Flake8:** Python syntax and style checking
- **Black:** Code formatting standardization
- **isort:** Import statement organization
- **MyPy:** Static type checking
- **Pylint:** Advanced code analysis
- **Bandit:** Security vulnerability detection

### Quality Gates
- No syntax errors or undefined names
- Maximum line length: 127 characters
- Maximum complexity: 10
- Import sorting compliance
- Code formatting compliance

## Local Development Workflow

### 1. Pre-commit Setup
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 2. Running Tests Locally
```bash
# Quick smoke test
python test_runner_enhanced.py --smoke

# Full test suite
python test_runner_enhanced.py

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### 3. Quality Checks
```bash
# Format code
black .
isort .

# Lint code
flake8 .
pylint **/*.py

# Security check
bandit -r .
safety check
```

## Pull Request Workflow

1. **Create feature branch** from `main`
2. **Implement changes** with tests
3. **Run local tests** to verify functionality
4. **Create pull request** 
5. **Automated validation** runs on PR
6. **Code review** after validation passes
7. **Merge** after approval

## Automated Validation Checks

### On Pull Request Creation:
✅ **Smoke Tests** - Basic functionality verification  
✅ **Unit Tests** - Individual component testing  
✅ **Integration Tests** - End-to-end workflow validation  
✅ **Coverage Check** - Minimum 70% threshold  
✅ **VAT Functionality** - Critical feature validation  
✅ **Security Scan** - Vulnerability detection  

### PR Status Comments
The system automatically posts comments on pull requests with:
- Test execution results
- Coverage information
- Pass/fail status for each check
- Next steps guidance

## Monitoring and Reporting

### Build Artifacts
- **Windows executable** built on successful CI runs
- **Coverage reports** generated for each test run
- **Security scan results** uploaded to GitHub Security tab

### Notifications
- **Success notifications** when all checks pass
- **Failure notifications** with detailed information
- **Automated merge** for approved Dependabot updates

## Configuration Files

### `pytest.ini`
- Test discovery settings
- Coverage configuration
- Test markers and filtering
- Output formatting

### `.github/workflows/ci.yml`
- Main CI/CD pipeline
- Multi-platform testing
- Build and deployment

### `.github/workflows/pr-validation.yml`
- Pull request specific validation
- Automated PR comments
- Security scanning

## Troubleshooting

### Common Issues

**Tests failing locally but passing in CI:**
- Ensure virtual environment is activated
- Check Python version compatibility
- Verify all dependencies are installed

**Coverage below threshold:**
- Add tests for uncovered code paths
- Remove excluded files from coverage if appropriate
- Check coverage report (`htmlcov/index.html`)

**Quality checks failing:**
- Run `black .` and `isort .` for formatting
- Address linting issues highlighted by flake8
- Fix security issues identified by bandit

### Getting Help

1. Check the **Actions tab** in GitHub for detailed logs
2. Review **pull request comments** for specific failures
3. Run tests locally with verbose output: `pytest -v -s`
4. Check **coverage reports** for missing test areas

## Future Enhancements

- **Performance testing** integration
- **Cross-browser testing** for GUI components
- **Automated deployment** to staging environment
- **Release automation** with semantic versioning
- **Integration with external monitoring** systems
