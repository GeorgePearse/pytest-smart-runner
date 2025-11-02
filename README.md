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

pytest-smart-runner is designed to work seamlessly in CI/CD environments where fresh clones don't have persistent state.

### GitHub Actions

**Pull Request Testing:**
```yaml
name: Test

on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch full history for accurate branch comparison

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest-cov

      - name: Run affected tests
        run: |
          pytest-smart --base-branch origin/${{ github.base_ref }} \
                       --target-branch HEAD \
                       -- --cov --junitxml=test-results.xml

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml
```

**Push to Main (Compare with Previous Commit):**
```yaml
- name: Run tests for new changes
  run: |
    pytest-smart --from-commit HEAD~1 -- -v
```

### GitLab CI

**Merge Request Pipeline:**
```yaml
test:
  stage: test
  script:
    - pip install -e .
    - |
      pytest-smart --base-branch origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME \
                   --target-branch HEAD \
                   -- --cov --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
    paths:
      - htmlcov/
  only:
    - merge_requests
```

**Commit-based Testing:**
```yaml
test:
  script:
    - pytest-smart --from-commit $CI_MERGE_REQUEST_DIFF_BASE_SHA -- --cov
```

### CircleCI

```yaml
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -e . pytest-cov
      - run:
          name: Run affected tests
          command: |
            pytest-smart --base-branch origin/main -- \
              --cov --junitxml=test-results/junit.xml
      - store_test_results:
          path: test-results
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh '''
                    pip install -e .
                    pytest-smart --base-branch origin/${CHANGE_TARGET} \
                                 -- --junitxml=results.xml
                '''
            }
        }
    }
    post {
        always {
            junit 'results.xml'
        }
    }
}
```

### Azure Pipelines

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install -e .
    pytest-smart --base-branch origin/main -- --junitxml=TEST-results.xml
  displayName: 'Run affected tests'

- task: PublishTestResults@2
  inputs:
    testResultsFiles: '**/TEST-*.xml'
```

### CI/CD Best Practices

**1. Fetch Full Git History**
```yaml
# GitHub Actions
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Required for accurate branch comparison
```

**2. Handle First Commit (Empty Repository)**
```bash
# Gracefully handle repos with no commit history
pytest-smart --base-branch origin/main || pytest tests/
```

**3. Combine with Full Test Runs**
```yaml
# Run affected tests on PR, full suite on main
- name: Test
  run: |
    if [ "${{ github.event_name }}" == "pull_request" ]; then
      pytest-smart --base-branch origin/main -- --cov
    else
      pytest tests/ --cov
    fi
```

**4. Save Time with Dry Run First**
```bash
# Check if any tests would run before setting up heavy dependencies
pytest-smart --dry-run || exit 0
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

## Key Differentiators Explained

Understanding how different pytest test selection tools work helps you choose the right one for your use case.

### 1. Runtime Monitoring (pytest-testmon)

**How it works:**
```python
# During test execution, pytest-testmon instruments the code
# and tracks which lines are executed by each test

# File: calculator.py
def add(a, b):           # Line tracked during test_add()
    return a + b         # Line tracked during test_add()

def multiply(a, b):      # Line tracked during test_multiply()
    return a * b         # Line tracked during test_multiply()

# Change line 2 → test_add() re-runs
# Change line 5 → test_multiply() re-runs
```

**Advantages:**
- **Highest accuracy**: Knows exactly which code each test executes
- **Handles indirect dependencies**: If A→B→C, changing C triggers tests for A
- **Dynamic behavior**: Catches runtime imports, conditional logic, monkey patching

**Disadvantages:**
- **Requires full run first**: Need to execute all tests to build dependency map
- **State management**: Maintains `.testmondata` database that can become stale
- **CI/CD friction**: Database doesn't transfer between environments
- **Runtime overhead**: Slight performance cost during instrumentation

**Best for:**
- Local development with long-running test suites
- Projects with complex, dynamic dependencies
- When you need maximum accuracy

### 2. Static Analysis + Git (pytest-smart-runner)

**How it works:**
```python
# Step 1: Git detects changed files
$ git diff --name-only HEAD
calculator.py

# Step 2: Parse AST to find imports
# File: test_calculator.py
import pytest
from myapp import calculator    # ← Found import!
from myapp.utils import helper  # ← Found import!

# Step 3: Match changed files to imports
# calculator.py changed → test_calculator.py runs (import match)

# Step 4: Apply naming conventions
# calculator.py changed → test_calculator.py runs (naming match)
```

**Advantages:**
- **Zero setup**: No initial run required, works immediately
- **Stateless**: No database to maintain or get out of sync
- **Git-native**: Built-in branch/commit comparison
- **CI/CD friendly**: Works perfectly with fresh clones
- **No runtime cost**: Pure static analysis, no instrumentation

**Disadvantages:**
- **Medium accuracy**: Can miss indirect dependencies (A imports B, B imports C)
- **Static only**: Doesn't catch dynamic imports or runtime behavior
- **Naming dependent**: Works best with conventional test naming

**Best for:**
- CI/CD pipelines with fresh environments
- Branch-based workflows (PR testing)
- Teams wanting low maintenance overhead
- Projects with clear import structures

### 3. Simple File-Based (pytest-picked)

**How it works:**
```bash
# Step 1: Find changed files with git
$ git diff --name-only HEAD
calculator.py
test_utils.py

# Step 2: Filter to test files only
test_utils.py

# Step 3: Run only those tests
pytest test_utils.py
```

**Advantages:**
- **Simplest possible approach**: Minimal logic, easy to understand
- **Fast**: No analysis overhead
- **Transparent**: Obvious what will run

**Disadvantages:**
- **Lowest accuracy**: Only runs tests if test file itself changed
- **Misses affected tests**: Source changes don't trigger related tests
- **Limited usefulness**: Catches only direct test file edits

**Best for:**
- Quick sanity checks during development
- When you mostly edit test files
- Projects where source/test files are tightly coupled (1:1)

### Practical Comparison Example

```python
# Project structure:
# src/
#   calculator.py      → defines Calculator class
#   formatter.py       → imports calculator, uses it
# tests/
#   test_calculator.py → imports calculator directly
#   test_formatter.py  → imports formatter

# Scenario: You change calculator.py
```

**What each tool does:**

| Tool | Tests Run | Why |
|------|-----------|-----|
| **pytest-testmon** | `test_calculator.py`, `test_formatter.py` | Runtime tracking shows both tests execute calculator.py code |
| **pytest-smart-runner** | `test_calculator.py` | Import analysis finds direct import, misses formatter→calculator chain |
| **pytest-picked** | _(none)_ | calculator.py isn't a test file |

**Scenario: You change test_calculator.py**

| Tool | Tests Run | Why |
|------|-----------|-----|
| **pytest-testmon** | `test_calculator.py` | Test file changed |
| **pytest-smart-runner** | `test_calculator.py` | Test file changed |
| **pytest-picked** | `test_calculator.py` | Test file changed |

### When Accuracy Differences Matter

**Critical projects** (payment, security, healthcare):
- Use `pytest-testmon` for maximum safety
- Consider running full suite on main branch

**Fast-moving projects** (startups, prototypes):
- Use `pytest-smart-runner` for speed
- Accept occasional missed dependencies

**Hybrid approach**:
```yaml
# .github/workflows/test.yml
- name: Fast feedback
  run: pytest-smart --base-branch origin/main

- name: Full suite (weekly)
  if: github.event.schedule
  run: pytest tests/
```

### Performance Comparison

```bash
# Full test suite: 1000 tests, 5 minutes

# Scenario: Changed 2 source files affecting 50 tests

pytest-testmon:
  First run:  5 min (full suite + instrumentation)
  Next run:   30 sec (50 affected tests)
  Setup:      ~10% overhead for tracking

pytest-smart-runner:
  First run:  30 sec (50 affected tests)
  Next run:   30 sec (50 affected tests)
  Setup:      0 sec (instant)

pytest-picked:
  First run:  0 sec (no test files changed)
  Next run:   0 sec (no test files changed)
  Setup:      0 sec (instant)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Comparison with Other Tools

> **💡 Tip**: See the [Key Differentiators Explained](#key-differentiators-explained) section above for detailed technical explanations and practical examples.

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
| **CI/CD in fresh env** | Poor (needs database) | Excellent (stateless) |
| **PR testing** | Requires workarounds | Native support |
| **Database sync** | Can become stale | N/A (no database) |

**When to use pytest-testmon:**
- Maximum accuracy is critical
- You have complex indirect dependencies
- You're okay with maintaining a dependency database
- You run tests frequently in the same environment
- **Local development** where state persists between runs

**When to use pytest-smart-runner:**
- You want zero setup/overhead
- You need git-aware comparisons (branches, commits)
- You prefer static analysis over runtime monitoring
- You want a lightweight solution without external databases
- **CI/CD environments** with fresh clones on every run
- **Pull request testing** comparing feature branches to main

**CI/CD Integration Notes:**

pytest-testmon in CI/CD:
```yaml
# Requires caching the database between runs
- uses: actions/cache@v3
  with:
    path: .testmondata
    key: testmon-${{ github.sha }}
    restore-keys: testmon-

# First run on new branch = full suite (no cache)
# Subsequent runs = incremental (with cache)
# Database can become stale across branches
```

pytest-smart-runner in CI/CD:
```yaml
# No caching needed - compares git directly
- run: pytest-smart --base-branch origin/main

# Works immediately on fresh clones
# Always accurate for branch comparisons
# No state management required
```

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
