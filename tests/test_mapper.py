"""Tests for the TestMapper class."""

import tempfile
from pathlib import Path
import pytest

from pytest_smart_runner.mapper import TestMapper


class TestTestMapper:
    """Test cases for TestMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.mapper = TestMapper(str(self.project_root))

    def test_is_test_file(self):
        """Test identification of test files."""
        assert self.mapper._is_test_file(Path("test_foo.py"))
        assert self.mapper._is_test_file(Path("foo_test.py"))
        assert not self.mapper._is_test_file(Path("foo.py"))
        assert not self.mapper._is_test_file(Path("testing.py"))

    def test_get_module_path(self):
        """Test conversion of file paths to module paths."""
        # Create a sample file structure
        source_file = self.project_root / "src" / "mypackage" / "module.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        module_path = self.mapper.get_module_path(source_file)
        assert module_path == "mypackage.module"

    def test_get_module_path_without_src(self):
        """Test module path conversion without src directory."""
        source_file = self.project_root / "mypackage" / "module.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        module_path = self.mapper.get_module_path(source_file)
        assert module_path == "mypackage.module"

    def test_extract_imports(self):
        """Test extraction of imports from a Python file."""
        test_file = self.project_root / "test.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from mypackage import module
from mypackage.submodule import func
""")

        imports = self.mapper.extract_imports(test_file)
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "mypackage" in imports

    def test_find_test_files(self):
        """Test discovery of test files."""
        # Create test directory structure
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()

        (tests_dir / "test_foo.py").touch()
        (tests_dir / "test_bar.py").touch()
        (tests_dir / "helper.py").touch()

        test_files = self.mapper.find_test_files()
        assert len(test_files) == 2
        assert any("test_foo.py" in str(f) for f in test_files)
        assert any("test_bar.py" in str(f) for f in test_files)

    def test_get_test_candidates(self):
        """Test generation of test file candidates for a source file."""
        source_file = self.project_root / "src" / "mypackage" / "foo.py"
        candidates = self.mapper._get_test_candidates(source_file)

        # Should generate test_foo.py and foo_test.py in various locations
        assert any("test_foo.py" in str(c) for c in candidates)
        assert any("foo_test.py" in str(c) for c in candidates)

    def test_find_affected_tests_direct_change(self):
        """Test finding affected tests when a test file itself changes."""
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.touch()

        changed_files = {test_file}
        affected = self.mapper.find_affected_tests(changed_files)

        assert test_file in affected

    def test_find_affected_tests_naming_convention(self):
        """Test finding affected tests using naming conventions."""
        # Create source file
        src_dir = self.project_root / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "foo.py"
        source_file.touch()

        # Create corresponding test
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.touch()

        changed_files = {source_file}
        test_files = {test_file}
        affected = self.mapper.find_affected_tests(changed_files, test_files)

        assert test_file in affected

    def test_find_affected_tests_by_imports(self):
        """Test finding affected tests by analyzing imports."""
        # Create source file
        src_dir = self.project_root / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "calculator.py"
        source_file.write_text("def add(a, b): return a + b")

        # Create test that imports the module
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_math.py"
        test_file.write_text("from mypackage import calculator")

        changed_files = {source_file}
        affected = self.mapper.find_affected_tests(changed_files)

        assert test_file in affected
