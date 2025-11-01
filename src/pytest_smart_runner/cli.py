"""Command-line interface for pytest-smart-runner."""

import argparse
import sys
from pathlib import Path

from .runner import SmartTestRunner


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Run pytest only on tests affected by code changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests for all uncommitted changes
  pytest-smart

  # Run tests for staged changes only
  pytest-smart --staged-only

  # Run tests for changes since specific commit
  pytest-smart --from-commit abc123

  # Run tests for changes between branches
  pytest-smart --base-branch main --target-branch feature/new-feature

  # Dry run to see what would be tested
  pytest-smart --dry-run

  # Pass additional arguments to pytest
  pytest-smart -- -v --cov
        """
    )

    parser.add_argument(
        "--base",
        default="HEAD",
        help="Base commit/branch to compare against (default: HEAD)"
    )

    parser.add_argument(
        "--from-commit",
        dest="from_commit",
        help="Run tests for changes since this commit SHA"
    )

    parser.add_argument(
        "--base-branch",
        dest="base_branch",
        help="Base branch for comparison"
    )

    parser.add_argument(
        "--target-branch",
        dest="target_branch",
        default="HEAD",
        help="Target branch for comparison (default: HEAD)"
    )

    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Only include staged changes"
    )

    parser.add_argument(
        "--unstaged-only",
        action="store_true",
        help="Only include unstaged changes"
    )

    parser.add_argument(
        "--no-untracked",
        action="store_true",
        help="Exclude untracked files"
    )

    parser.add_argument(
        "--test-dir",
        action="append",
        dest="test_dirs",
        help="Directory to search for tests (can be used multiple times)"
    )

    parser.add_argument(
        "--repo-path",
        help="Path to git repository (default: current directory)"
    )

    parser.add_argument(
        "--project-root",
        help="Path to project root (default: current directory)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which tests would be run without executing them"
    )

    # Collect remaining args for pytest
    args, pytest_args = parser.parse_known_args()

    # Create runner
    try:
        runner = SmartTestRunner(
            repo_path=args.repo_path,
            project_root=args.project_root
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Determine which mode to run in
    if args.from_commit:
        # Run from specific commit
        exit_code = runner.run_from_commit(
            commit_sha=args.from_commit,
            test_dirs=args.test_dirs,
            pytest_args=pytest_args,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
    elif args.base_branch:
        # Run between branches
        exit_code = runner.run_between_branches(
            base_branch=args.base_branch,
            target_branch=args.target_branch,
            test_dirs=args.test_dirs,
            pytest_args=pytest_args,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
    else:
        # Run for current changes
        include_staged = not args.unstaged_only
        include_unstaged = not args.staged_only
        include_untracked = not args.no_untracked and not args.staged_only

        exit_code = runner.run(
            base=args.base,
            include_untracked=include_untracked,
            include_staged=include_staged,
            include_unstaged=include_unstaged,
            test_dirs=args.test_dirs,
            pytest_args=pytest_args,
            verbose=args.verbose,
            dry_run=args.dry_run
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
