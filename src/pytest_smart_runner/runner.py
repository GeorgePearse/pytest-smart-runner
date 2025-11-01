"""Smart test runner that executes only affected tests."""

import sys
from pathlib import Path
from typing import Set, Optional, List
import pytest

from .analyzer import GitChangeAnalyzer
from .mapper import TestMapper


class SmartTestRunner:
    """Orchestrates the smart test running process."""

    def __init__(self, repo_path: Optional[str] = None, project_root: Optional[str] = None):
        """
        Initialize the smart test runner.

        Args:
            repo_path: Path to git repository. Defaults to current directory.
            project_root: Path to project root. Defaults to current directory.
        """
        self.analyzer = GitChangeAnalyzer(repo_path)
        self.mapper = TestMapper(project_root)

    def run(
        self,
        base: str = "HEAD",
        include_untracked: bool = True,
        include_staged: bool = True,
        include_unstaged: bool = True,
        test_dirs: Optional[List[str]] = None,
        pytest_args: Optional[List[str]] = None,
        verbose: bool = False,
        dry_run: bool = False
    ) -> int:
        """
        Run tests affected by code changes.

        Args:
            base: Base commit/branch to compare against
            include_untracked: Include untracked files
            include_staged: Include staged changes
            include_unstaged: Include unstaged changes
            test_dirs: Directories to search for tests
            pytest_args: Additional arguments to pass to pytest
            verbose: Print verbose output
            dry_run: Print tests that would be run without executing them

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if pytest_args is None:
            pytest_args = []

        # Get changed files
        if verbose:
            print("Analyzing git changes...")

        changed_files = self.analyzer.get_changed_files(
            base=base,
            include_untracked=include_untracked,
            include_staged=include_staged,
            include_unstaged=include_unstaged
        )

        if verbose:
            print(f"Found {len(changed_files)} changed Python files:")
            for f in sorted(changed_files):
                print(f"  - {f}")

        if not changed_files:
            print("No Python files changed. Nothing to test.")
            return 0

        # Find affected tests
        if verbose:
            print("\nFinding affected tests...")

        affected_tests = self.mapper.find_affected_tests(changed_files, test_files=None)

        if not affected_tests:
            print("No tests affected by the changes.")
            return 0

        # Convert to strings for pytest
        test_paths = [str(t) for t in sorted(affected_tests)]

        print(f"\nFound {len(test_paths)} affected test file(s):")
        for test_path in test_paths:
            print(f"  - {test_path}")

        if dry_run:
            print("\nDry run mode - tests not executed")
            return 0

        # Run pytest
        print("\nRunning tests...\n")
        exit_code = pytest.main(test_paths + pytest_args)

        return exit_code

    def run_from_commit(
        self,
        commit_sha: str,
        test_dirs: Optional[List[str]] = None,
        pytest_args: Optional[List[str]] = None,
        verbose: bool = False,
        dry_run: bool = False
    ) -> int:
        """
        Run tests affected by changes since a specific commit.

        Args:
            commit_sha: SHA of the commit to compare against
            test_dirs: Directories to search for tests
            pytest_args: Additional arguments to pass to pytest
            verbose: Print verbose output
            dry_run: Print tests that would be run without executing them

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if pytest_args is None:
            pytest_args = []

        if verbose:
            print(f"Analyzing changes since commit {commit_sha}...")

        changed_files = self.analyzer.get_changed_files_since_commit(commit_sha)

        if verbose:
            print(f"Found {len(changed_files)} changed Python files:")
            for f in sorted(changed_files):
                print(f"  - {f}")

        if not changed_files:
            print("No Python files changed. Nothing to test.")
            return 0

        affected_tests = self.mapper.find_affected_tests(changed_files, test_files=None)

        if not affected_tests:
            print("No tests affected by the changes.")
            return 0

        test_paths = [str(t) for t in sorted(affected_tests)]

        print(f"\nFound {len(test_paths)} affected test file(s):")
        for test_path in test_paths:
            print(f"  - {test_path}")

        if dry_run:
            print("\nDry run mode - tests not executed")
            return 0

        print("\nRunning tests...\n")
        exit_code = pytest.main(test_paths + pytest_args)

        return exit_code

    def run_between_branches(
        self,
        base_branch: str,
        target_branch: str = "HEAD",
        test_dirs: Optional[List[str]] = None,
        pytest_args: Optional[List[str]] = None,
        verbose: bool = False,
        dry_run: bool = False
    ) -> int:
        """
        Run tests affected by changes between two branches.

        Args:
            base_branch: Base branch name
            target_branch: Target branch name
            test_dirs: Directories to search for tests
            pytest_args: Additional arguments to pass to pytest
            verbose: Print verbose output
            dry_run: Print tests that would be run without executing them

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if pytest_args is None:
            pytest_args = []

        if verbose:
            print(f"Analyzing changes between {base_branch} and {target_branch}...")

        changed_files = self.analyzer.get_changed_files_between_branches(base_branch, target_branch)

        if verbose:
            print(f"Found {len(changed_files)} changed Python files:")
            for f in sorted(changed_files):
                print(f"  - {f}")

        if not changed_files:
            print("No Python files changed. Nothing to test.")
            return 0

        affected_tests = self.mapper.find_affected_tests(changed_files, test_files=None)

        if not affected_tests:
            print("No tests affected by the changes.")
            return 0

        test_paths = [str(t) for t in sorted(affected_tests)]

        print(f"\nFound {len(test_paths)} affected test file(s):")
        for test_path in test_paths:
            print(f"  - {test_path}")

        if dry_run:
            print("\nDry run mode - tests not executed")
            return 0

        print("\nRunning tests...\n")
        exit_code = pytest.main(test_paths + pytest_args)

        return exit_code
