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

### pytest-testmon

[pytest-testmon](https://github.com/tarpas/pytest-testmon) is the most popular and mature solution for running only affected tests.

**Installation:**
```bash
pip install pytest-testmon
pytest --testmon
```

**How it works:**
- Monitors test execution at runtime to track which code each test executes
- Stores dependency data in `.testmondata` database
- On subsequent runs, only executes tests affected by code changes

**Comparison:**

| Feature | pytest-testmon | pytest-smart-runner |
|---------|---------------|---------------------|
| **Method** | Runtime monitoring | Static analysis + git |
| **Accuracy** | Very high (tracks actual execution) | Medium (import-based) |
| **Indirect dependencies** | Yes (A→B→C chain) | Partial (one level) |
| **Setup overhead** | Full test run required first | None |
| **Runtime overhead** | Minimal after setup | None |
| **Database** | .testmondata file | None |
| **Git integration** | Optional | Built-in |
| **Branch comparison** | No | Yes |
| **Commit comparison** | No | Yes |

**When to use pytest-testmon:**
- Maximum accuracy is critical
- You have complex indirect dependencies
- You're okay with maintaining a dependency database
- You run tests frequently in the same environment

**When to use pytest-smart-runner:**
- You want zero setup/overhead
- You need git-aware comparisons (branches, commits)
- You prefer static analysis over runtime monitoring
- You want a lightweight solution without external databases
- You're working in CI/CD with fresh environments

### pytest-picked

[pytest-picked](https://github.com/anapaulagomes/pytest-picked) is a simpler git-based solution.

**Installation:**
```bash
pip install pytest-picked
pytest --picked
```

**How it works:**
- Uses git to find changed files
- Runs tests only from those changed files
- No import analysis or mapping

**Comparison to pytest-smart-runner:**
- pytest-picked: Runs tests only if the test file itself changed
- pytest-smart-runner: Also finds tests affected by source code changes through naming conventions and import analysis

### Other Alternatives

- **pytest-incremental**: Similar to testmon but less maintained
- **pytest-watcher**: Watches files and re-runs tests (not change-aware)

## Choosing the Right Tool

1. **Need maximum accuracy?** → Use **pytest-testmon**
2. **Want simplicity and only care about changed test files?** → Use **pytest-picked**
3. **Need git integration, branch/commit comparison, and smart mapping without databases?** → Use **pytest-smart-runner**
4. **Have complex projects with deep dependency chains?** → Use **pytest-testmon**
5. **Working in CI/CD with fresh clones?** → Use **pytest-smart-runner**

All three tools can complement each other - you could use pytest-smart-runner in CI and pytest-testmon locally!
