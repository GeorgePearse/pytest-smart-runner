# pytest-smart-runner

A pytest runner that intelligently runs only tests affected by code changes, saving you time and CI resources.

## Features

- **Git-aware**: Automatically detects changed files using git
- **Smart test mapping**: Finds affected tests through multiple strategies:
  - Direct test file changes
  - Naming convention mapping (e.g., `test_foo.py` tests `foo.py`)
  - Import analysis (tests that import changed modules)
- **Flexible comparison**: Compare against commits, branches, or working directory changes
- **Pytest integration**: Passes through additional pytest arguments seamlessly
- **Multiple modes**: Staged only, unstaged only, or all changes

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Run tests for all uncommitted changes (staged, unstaged, and untracked):

```bash
pytest-smart
```

### Common Scenarios

Run tests for staged changes only:

```bash
pytest-smart --staged-only
```

Run tests for unstaged changes only:

```bash
pytest-smart --unstaged-only
```

Run tests for changes since a specific commit:

```bash
pytest-smart --from-commit abc123
```

Run tests for changes between branches:

```bash
pytest-smart --base-branch main --target-branch feature/new-feature
```

See what tests would run without executing them:

```bash
pytest-smart --dry-run
```

### Passing Arguments to pytest

Pass additional arguments to pytest after `--`:

```bash
pytest-smart -- -v --cov
pytest-smart -- -x --pdb
pytest-smart --staged-only -- -v -s
```

### Advanced Options

```bash
pytest-smart \
  --verbose \                      # Show detailed output
  --test-dir tests \               # Specify test directory
  --test-dir integration_tests \   # Can specify multiple test directories
  --repo-path /path/to/repo \      # Specify git repository path
  --project-root /path/to/project  # Specify project root
```

## How It Works

1. **Change Detection**: Analyzes git to find modified Python files
2. **Test Discovery**: Scans configured test directories for test files
3. **Impact Mapping**: Determines which tests are affected using:
   - Direct changes to test files
   - Naming conventions (test_module.py ↔ module.py)
   - Import analysis (which tests import the changed code)
4. **Execution**: Runs only the affected tests with pytest

## Example Workflow

```bash
# Make some changes to your code
vim src/myapp/calculator.py
vim src/myapp/utils.py

# Run only the affected tests
pytest-smart -v

# Output:
# Analyzing git changes...
# Found 2 changed Python files:
#   - src/myapp/calculator.py
#   - src/myapp/utils.py
#
# Found 3 affected test file(s):
#   - tests/test_calculator.py
#   - tests/test_utils.py
#   - tests/integration/test_math_operations.py
#
# Running tests...
# [pytest output]
```

## Configuration

The tool uses sensible defaults but can be customized:

- Test directories: `tests`, `test` (use `--test-dir` to add more)
- Comparison base: `HEAD` (use `--base` to change)
- File types: Only Python files (`.py`) are analyzed

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run affected tests
  run: |
    pytest-smart --base-branch origin/main -- --cov --junitxml=test-results.xml
```

### GitLab CI

```yaml
test:
  script:
    - pytest-smart --from-commit $CI_MERGE_REQUEST_DIFF_BASE_SHA -- --cov
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest tests/
```

Run tests with coverage:

```bash
pytest tests/ --cov=pytest_smart_runner --cov-report=html
```

Format code:

```bash
black src/ tests/
```

Lint code:

```bash
ruff check src/ tests/
```

## Limitations

- Only works with git repositories
- Only analyzes Python files (`.py`)
- Import analysis uses static analysis (doesn't execute code)
- May not detect indirect dependencies (e.g., A imports B, test tests A, you changed C that B imports)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Comparison with Other Tools

- **pytest-testmon**: Monitors test execution and dependencies at runtime
- **pytest-smart-runner**: Uses static analysis and git changes (lighter weight, no runtime overhead)

Both approaches have merits - choose based on your needs!
