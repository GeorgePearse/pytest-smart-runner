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

## Comprehensive Guide to Test Selection Tools and Approaches

This section provides detailed information about various test selection strategies, tools, and implementation patterns.

### 1. pytest-testmon (Most Popular for Python)

Tracks code coverage and runs only tests affected by changes.

```bash
pip install pytest-testmon

# First run - collects coverage data
pytest --testmon

# Subsequent runs - only runs affected tests
pytest --testmon

# Run all tests and update database
pytest --testmon-forceselect
```

**How it works:**
```python
# Automatically detects which tests to run based on:
# - Modified source files
# - Test dependencies
# - Coverage data from previous runs

# .testmondata database stores:
# - Test execution paths
# - File dependencies
# - Coverage information
```

### 2. pytest-incremental

Focuses on running tests incrementally based on git changes.

```bash
pip install pytest-incremental

# Run only tests affected by changes since last commit
pytest --inc

# Run tests affected since specific commit
pytest --inc --inc-base=HEAD~3
```

### 3. Coverage.py with Dynamic Analysis

```python
# coverage_selector.py
import coverage
import ast
import os

class TestSelector:
    def __init__(self):
        self.cov = coverage.Coverage()

    def find_affected_tests(self, changed_files):
        """Find tests that cover the changed files"""
        affected_tests = set()

        # Load coverage data
        self.cov.load()
        data = self.cov.get_data()

        for test_file in data.measured_files():
            if test_file.endswith('_test.py'):
                # Check if this test covers any changed files
                executed_files = data.executed_files(test_file)
                if any(cf in executed_files for cf in changed_files):
                    affected_tests.add(test_file)

        return affected_tests

# Usage
selector = TestSelector()
changed = ['src/module.py', 'src/utils.py']
tests_to_run = selector.find_affected_tests(changed)
```

### 4. pytest-picked (Git-based Selection)

Runs tests related to unstaged files in git.

```bash
pip install pytest-picked

# Run tests related to unstaged changes
pytest --picked

# Run tests for modified files
pytest --picked=first

# Include untracked files
pytest --picked --mode=branch
```

### 5. Mutation Testing with mutmut

Identifies which tests actually test which code.

```bash
pip install mutmut

# Run mutation testing to build test-to-code mapping
mutmut run

# Use results to determine test effectiveness
mutmut results

# Integration with test selection
mutmut run --paths-to-mutate src/module.py
```

### 6. Custom AST-based Dependency Analysis

```python
# test_mapper.py
import ast
import os
from pathlib import Path

class TestDependencyMapper:
    def __init__(self):
        self.import_graph = {}
        self.test_to_modules = {}

    def analyze_imports(self, filepath):
        """Extract imports from a Python file"""
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.append(module)

        return imports

    def build_dependency_graph(self, project_root):
        """Build complete dependency graph"""
        for pyfile in Path(project_root).rglob("*.py"):
            imports = self.analyze_imports(pyfile)
            self.import_graph[str(pyfile)] = imports

            if 'test' in str(pyfile):
                self.test_to_modules[str(pyfile)] = imports

    def find_affected_tests(self, changed_module):
        """Find all tests that import the changed module"""
        affected = []
        module_name = Path(changed_module).stem

        for test_file, imports in self.test_to_modules.items():
            if module_name in imports:
                affected.append(test_file)

        return affected

# Usage
mapper = TestDependencyMapper()
mapper.build_dependency_graph("/path/to/project")
tests = mapper.find_affected_tests("src/core/engine.py")
```

### 7. pytest-watch with Patterns

Watches files and runs related tests automatically.

```bash
pip install pytest-watch

# Watch and run tests
ptw

# Custom patterns
ptw -- --ignore=integration_tests/

# With specific test selection
ptw -- tests/unit/
```

**Configuration:**
```ini
# setup.cfg
[tool:pytest-watch]
ignore = ./integration_tests
patterns = *.py
runner = pytest --tb=short
```

### 8. Bazel Test Selection (for Python)

```python
# BUILD file
py_test(
    name = "engine_test",
    srcs = ["engine_test.py"],
    deps = [
        "//src/core:engine",
        "//src/utils:helpers",
    ],
)

py_library(
    name = "engine",
    srcs = ["engine.py"],
    deps = ["//src/utils:helpers"],
)
```

```bash
# Bazel automatically determines affected tests
bazel test //... --test_selection_mode=affected

# Query affected tests
bazel query "rdeps(//..., //src/core:engine)"
```

### 9. Machine Learning-based Selection

```python
# ml_test_selector.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import git

class MLTestSelector:
    def __init__(self):
        self.model = RandomForestClassifier()
        self.repo = git.Repo('.')

    def extract_features(self, commit):
        """Extract features from a commit"""
        stats = commit.stats.files
        features = {
            'files_changed': len(stats),
            'lines_added': sum(f.get('insertions', 0) for f in stats.values()),
            'lines_deleted': sum(f.get('deletions', 0) for f in stats.values()),
            'is_refactor': 'refactor' in commit.message.lower(),
            'is_fix': 'fix' in commit.message.lower(),
            'author': commit.author.name,
        }
        return features

    def train_on_history(self):
        """Train model on historical test failures"""
        history = []

        for commit in self.repo.iter_commits('main', max_count=1000):
            features = self.extract_features(commit)
            # Get test results (from CI system or logs)
            failed_tests = self.get_test_results(commit.hexsha)
            history.append({**features, 'failed_tests': failed_tests})

        df = pd.DataFrame(history)
        X = df.drop('failed_tests', axis=1)
        y = df['failed_tests']

        self.model.fit(X, y)

    def predict_tests_to_run(self, current_changes):
        """Predict which tests are likely to fail"""
        features = self.extract_features_from_diff(current_changes)
        predictions = self.model.predict_proba([features])

        # Return tests with >50% probability of failure
        likely_failures = [test for test, prob in predictions if prob > 0.5]
        return likely_failures
```

### 10. GitHub/GitLab Integration Systems

**pytest-split (for CI parallelization):**

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    # Splits tests based on duration
    pytest --splits 4 --group ${{ matrix.group }}
```

**pytest-benchmark with Historical Data:**

```python
# benchmark_selector.py
import json
from pathlib import Path

class BenchmarkBasedSelector:
    def __init__(self, benchmark_file='.benchmarks'):
        self.benchmark_file = benchmark_file

    def load_benchmarks(self):
        """Load historical test durations"""
        with open(self.benchmark_file) as f:
            return json.load(f)

    def select_quick_tests(self, max_duration=1.0):
        """Select tests that run under max_duration seconds"""
        benchmarks = self.load_benchmarks()
        quick_tests = []

        for test, stats in benchmarks.items():
            if stats['mean'] < max_duration:
                quick_tests.append(test)

        return quick_tests

    def select_critical_path(self, time_budget=60):
        """Select most important tests within time budget"""
        benchmarks = self.load_benchmarks()

        # Sort by importance score (duration * failure_rate)
        scored = []
        for test, stats in benchmarks.items():
            score = stats['mean'] * stats.get('failure_rate', 0.1)
            scored.append((test, stats['mean'], score))

        scored.sort(key=lambda x: x[2], reverse=True)

        # Select tests within budget
        selected = []
        total_time = 0

        for test, duration, score in scored:
            if total_time + duration <= time_budget:
                selected.append(test)
                total_time += duration

        return selected
```

### 11. Dynamic Test Generation

```python
# dynamic_test_selector.py
import hypothesis
from hypothesis import strategies as st
import pytest

class DynamicTestSelector:
    def __init__(self, changed_function):
        self.func = changed_function

    def generate_property_tests(self):
        """Generate property-based tests for changed function"""

        # Analyze function signature
        import inspect
        sig = inspect.signature(self.func)

        # Generate appropriate strategies
        strategies = {}
        for param in sig.parameters.values():
            if param.annotation == int:
                strategies[param.name] = st.integers()
            elif param.annotation == str:
                strategies[param.name] = st.text()
            # Add more type mappings

        @hypothesis.given(**strategies)
        def test_property(self, **kwargs):
            result = self.func(**kwargs)
            # Add assertions based on function contracts
            assert result is not None

        return test_property

# Usage with pytest
def pytest_generate_tests(metafunc):
    if "dynamic_test" in metafunc.fixturenames:
        # Generate tests for changed functions
        changed_funcs = get_changed_functions()
        metafunc.parametrize("dynamic_test",
                           [DynamicTestSelector(f) for f in changed_funcs])
```

### 12. Import Graph Analysis

```python
# import_graph_selector.py
import importlib
import sys
from typing import Set, Dict, List

class ImportGraphAnalyzer:
    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.reverse_graph: Dict[str, Set[str]] = {}

    def build_import_graph(self, root_module):
        """Build complete import dependency graph"""
        visited = set()
        self._traverse_imports(root_module, visited)

    def _traverse_imports(self, module_name: str, visited: Set[str]):
        if module_name in visited:
            return
        visited.add(module_name)

        try:
            module = importlib.import_module(module_name)

            # Get all imports
            for name, obj in module.__dict__.items():
                if hasattr(obj, '__module__'):
                    imported_from = obj.__module__
                    if imported_from and imported_from.startswith('your_package'):
                        self.graph.setdefault(module_name, set()).add(imported_from)
                        self.reverse_graph.setdefault(imported_from, set()).add(module_name)
                        self._traverse_imports(imported_from, visited)
        except ImportError:
            pass

    def find_affected_modules(self, changed_module: str) -> Set[str]:
        """Find all modules affected by a change"""
        affected = {changed_module}
        to_visit = [changed_module]

        while to_visit:
            current = to_visit.pop()
            dependents = self.reverse_graph.get(current, set())
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    to_visit.append(dep)

        return affected

    def find_test_modules(self, affected_modules: Set[str]) -> List[str]:
        """Filter test modules from affected modules"""
        return [m for m in affected_modules if 'test' in m]

# Usage
analyzer = ImportGraphAnalyzer()
analyzer.build_import_graph('your_package')
affected = analyzer.find_affected_modules('your_package.core.engine')
tests = analyzer.find_test_modules(affected)
```

## Best Practices & Recommendations

### For Small Projects

Use **pytest-testmon** or **pytest-picked**:
- Simple and effective out of the box
- Minimal configuration required

### For Large Monorepos

Use **Bazel** or **Buck2** for dependency tracking:
- Custom AST analysis for fine-grained control
- Scalable to thousands of tests

### For CI/CD

Example GitHub Actions workflow:

```yaml
# Example GitHub Actions workflow
name: Smart Test Selection
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0  # Full history for comparison

      - name: Identify changed files
        run: |
          echo "CHANGED_FILES=$(git diff --name-only HEAD~1)" >> $GITHUB_ENV

      - name: Run affected tests
        run: |
          pytest --testmon --cov=src

      - name: Run full suite on main
        if: github.ref == 'refs/heads/main'
        run: |
          pytest --testmon-forceselect
```

### For Maximum Efficiency

**Layer your approach:**

1. Quick smoke tests first
2. Affected unit tests second
3. Integration tests if needed
4. Full suite on main branch

**Cache aggressively:**

```ini
# pytest.ini
[tool:pytest]
cache_dir = .pytest_cache
testmon_data_file = .testmondata
```

**Combine multiple strategies:**

```bash
# Run affected tests first, then risky areas
pytest --testmon --picked || pytest tests/integration/
```

## Summary

The best system depends on your project structure, team size, and CI/CD setup. Start simple with **pytest-testmon** and add complexity as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
