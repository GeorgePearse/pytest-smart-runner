"""Tests for the GitChangeAnalyzer class."""

import tempfile
from pathlib import Path
import pytest
import git

from pytest_smart_runner.analyzer import GitChangeAnalyzer


class TestGitChangeAnalyzer:
    """Test cases for GitChangeAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Initialize git repo
        self.repo = git.Repo.init(self.repo_path)
        self.repo.config_writer().set_value("user", "name", "Test User").release()
        self.repo.config_writer().set_value("user", "email", "test@example.com").release()

        self.analyzer = GitChangeAnalyzer(str(self.repo_path))

    def test_init_invalid_repo(self):
        """Test initialization with invalid repository."""
        invalid_path = "/tmp/not_a_git_repo_xyz123"
        with pytest.raises(ValueError, match="Not a git repository"):
            GitChangeAnalyzer(invalid_path)

    def test_get_changed_files_untracked(self):
        """Test detection of untracked files."""
        # Create an untracked Python file
        new_file = self.repo_path / "new_module.py"
        new_file.write_text("print('hello')")

        changed = self.analyzer.get_changed_files(include_untracked=True)
        assert Path("new_module.py") in changed

    def test_get_changed_files_exclude_untracked(self):
        """Test exclusion of untracked files."""
        # Create an untracked Python file
        new_file = self.repo_path / "new_module.py"
        new_file.write_text("print('hello')")

        changed = self.analyzer.get_changed_files(include_untracked=False)
        assert Path("new_module.py") not in changed

    def test_get_changed_files_staged(self):
        """Test detection of staged changes."""
        # Create and stage a file
        new_file = self.repo_path / "staged.py"
        new_file.write_text("# staged")
        self.repo.index.add([str(new_file)])

        changed = self.analyzer.get_changed_files(include_staged=True)
        assert Path("staged.py") in changed

    def test_get_changed_files_unstaged(self):
        """Test detection of unstaged changes."""
        # Create and commit a file
        existing_file = self.repo_path / "existing.py"
        existing_file.write_text("# original")
        self.repo.index.add([str(existing_file)])
        self.repo.index.commit("Initial commit")

        # Modify the file without staging
        existing_file.write_text("# modified")

        changed = self.analyzer.get_changed_files(include_unstaged=True)
        assert Path("existing.py") in changed

    def test_get_changed_files_filters_non_python(self):
        """Test that only Python files are included."""
        # Create various files
        (self.repo_path / "script.py").write_text("# python")
        (self.repo_path / "readme.md").write_text("# markdown")
        (self.repo_path / "data.json").write_text("{}")

        changed = self.analyzer.get_changed_files(include_untracked=True)

        # Only .py file should be included
        assert Path("script.py") in changed
        assert Path("readme.md") not in changed
        assert Path("data.json") not in changed

    def test_get_changed_files_since_commit(self):
        """Test detection of changes since a specific commit."""
        # Create initial commit
        file1 = self.repo_path / "file1.py"
        file1.write_text("# first")
        self.repo.index.add([str(file1)])
        commit1 = self.repo.index.commit("First commit")

        # Create second commit
        file2 = self.repo_path / "file2.py"
        file2.write_text("# second")
        self.repo.index.add([str(file2)])
        self.repo.index.commit("Second commit")

        # Get changes since first commit
        changed = self.analyzer.get_changed_files_since_commit(commit1.hexsha)
        assert Path("file2.py") in changed
        assert Path("file1.py") not in changed

    def test_get_changed_files_since_commit_invalid(self):
        """Test error handling for invalid commit SHA."""
        with pytest.raises(ValueError, match="Invalid commit SHA"):
            self.analyzer.get_changed_files_since_commit("invalid_sha_xyz")
