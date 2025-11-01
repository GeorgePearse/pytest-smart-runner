"""Git change analyzer to detect modified files."""

import os
from pathlib import Path
from typing import Set, Optional
import git


class GitChangeAnalyzer:
    """Analyzes git repository to detect changed files."""

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path or os.getcwd())
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def get_changed_files(
        self,
        base: str = "HEAD",
        include_untracked: bool = True,
        include_staged: bool = True,
        include_unstaged: bool = True
    ) -> Set[Path]:
        """
        Get files that have changed compared to a base commit.

        Args:
            base: Base commit/branch to compare against (default: HEAD)
            include_untracked: Include untracked files
            include_staged: Include staged changes
            include_unstaged: Include unstaged changes

        Returns:
            Set of Path objects representing changed files
        """
        changed_files = set()

        # Get staged changes
        if include_staged:
            try:
                diff_staged = self.repo.index.diff(base)
                for diff in diff_staged:
                    if diff.a_path:
                        changed_files.add(Path(diff.a_path))
                    if diff.b_path:
                        changed_files.add(Path(diff.b_path))
            except git.exc.BadName:
                # If HEAD doesn't exist (empty repo), get all staged files
                diff_staged = self.repo.index.diff(None)
                for diff in diff_staged:
                    if diff.a_path:
                        changed_files.add(Path(diff.a_path))

        # Get unstaged changes
        if include_unstaged:
            diff_unstaged = self.repo.index.diff(None)
            for diff in diff_unstaged:
                if diff.a_path:
                    changed_files.add(Path(diff.a_path))
                if diff.b_path:
                    changed_files.add(Path(diff.b_path))

        # Get untracked files
        if include_untracked:
            for file_path in self.repo.untracked_files:
                changed_files.add(Path(file_path))

        # Filter to only Python files
        python_files = {f for f in changed_files if f.suffix == '.py'}

        return python_files

    def get_changed_files_since_commit(self, commit_sha: str) -> Set[Path]:
        """
        Get files changed since a specific commit.

        Args:
            commit_sha: SHA of the commit to compare against

        Returns:
            Set of Path objects representing changed files
        """
        try:
            commit = self.repo.commit(commit_sha)
            diff = commit.diff('HEAD')
            changed_files = set()

            for diff_item in diff:
                if diff_item.a_path:
                    changed_files.add(Path(diff_item.a_path))
                if diff_item.b_path:
                    changed_files.add(Path(diff_item.b_path))

            # Filter to only Python files
            python_files = {f for f in changed_files if f.suffix == '.py'}
            return python_files
        except git.exc.BadName:
            raise ValueError(f"Invalid commit SHA: {commit_sha}")

    def get_changed_files_between_branches(self, base_branch: str, target_branch: str = "HEAD") -> Set[Path]:
        """
        Get files changed between two branches.

        Args:
            base_branch: Base branch name
            target_branch: Target branch name (default: HEAD)

        Returns:
            Set of Path objects representing changed files
        """
        try:
            diff = self.repo.git.diff(f"{base_branch}...{target_branch}", name_only=True)
            changed_files = {Path(f) for f in diff.split('\n') if f}

            # Filter to only Python files
            python_files = {f for f in changed_files if f.suffix == '.py'}
            return python_files
        except git.exc.GitCommandError as e:
            raise ValueError(f"Error comparing branches: {e}")
